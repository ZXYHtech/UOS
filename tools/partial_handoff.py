#!/usr/bin/env python3
"""Partial handoff for standalone UOS.

A handoff preserves recoverable partial work and context but is never completion
and never ownership transfer. HANDOFF_READY atomically records the handoff and
expires the current owner's canonical lease. A successor still obtains ownership
through the ordinary `tools/uos.py claim` path, which increments LeaseGeneration
and issues a new LeaseToken.

Partial artifacts are copied into immutable handoff checkpoint paths rather than
published onto final task output paths. This prevents an unfinished draft from
blocking the successor's later no-clobber completion.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

try:
    from canonical_publish import PublishError, blob_at, git, publish, verify_identity
    from control_extensions import execution_epoch, validate_project_output_scope
except ModuleNotFoundError:
    from tools.canonical_publish import PublishError, blob_at, git, publish, verify_identity
    from tools.control_extensions import execution_epoch, validate_project_output_scope


class HandoffError(RuntimeError):
    pass


STATES = {
    "PARTIAL",
    "BLOCKED",
    "NEEDS_DIFFERENT_CAPABILITY",
    "INTERRUPTED_SAFE_POINT",
    "HANDOFF_READY",
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    return (dt or utcnow()).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def repo_root() -> Path:
    proc = git(["rev-parse", "--show-toplevel"], cwd=Path.cwd(), check=False)
    if proc.returncode == 0:
        return Path(proc.stdout.strip()).resolve()
    return Path.cwd().resolve()


def require_epoch(root: Path, ack: str) -> None:
    current = execution_epoch(root)
    if current and ack != current:
        raise HandoffError(
            f"REBOOT_REQUIRED: current ExecutionEpoch is {current}; run `python tools/uos.py boot` "
            f"and retry with --ack-execution-epoch {current}"
        )


def safe_rel(value: str) -> str:
    raw = (value or "").strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise HandoffError(f"repository path escape: {value!r}")
    return str(path)


def split_paths(value: str) -> list[str]:
    return [safe_rel(item) for item in (value or "").replace(",", ";").split(";") if item.strip()]


def parse_scalar_text(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in (text or "").splitlines():
        if ":" not in raw or raw.lstrip().startswith(("#", "-")):
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def scalar_text(values: dict[str, object]) -> str:
    return "".join(f"{key}: {value}\n" for key, value in values.items())


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    try:
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def copy_one(source: Path, target: Path) -> None:
    if not source.exists() and not source.is_symlink():
        raise HandoffError(f"partial artifact missing: {source}")
    if source.is_dir() and not source.is_symlink():
        raise HandoffError("partial handoff artifacts must be files or symlinks; package directories explicitly")
    if target.exists() or target.is_symlink():
        raise HandoffError(f"handoff checkpoint path unexpectedly exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        target.symlink_to(os.readlink(source))
    else:
        shutil.copy2(source, target)


def task_row(root: Path, task_id: str) -> dict[str, str]:
    import csv

    base = root / "orchestration/projects"
    if not base.exists():
        raise HandoffError(f"unknown task: {task_id}")
    for catalog in sorted(base.glob("*/TASK_CATALOG.csv")):
        with catalog.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("id") == task_id:
                    return dict(row)
    raise HandoffError(f"unknown task: {task_id}")


def lock_path(task_id: str) -> str:
    return f"coordination/claims/{task_id}.lock"


def handoff_path(task_id: str) -> str:
    return f"coordination/handoffs/{task_id}.handoff"


def checkpoint_path(task_id: str, handoff_id: str, source_rel: str) -> str:
    return f"coordination/handoff_artifacts/{task_id}/{handoff_id}/{safe_rel(source_rel)}"


def _validate_owned_lock(lock: dict[str, str], agent_id: str, lease_token: str) -> None:
    if not lock:
        raise HandoffError("claim not found")
    if lock.get("AgentID") != agent_id:
        raise HandoffError("FENCED: wrong owner")
    if lock.get("LeaseToken") != lease_token:
        raise HandoffError("FENCED: stale lease token")
    try:
        if parse_time(lock["LeaseExpiresAt"]) <= utcnow():
            raise HandoffError("FENCED: lease expired")
    except KeyError as exc:
        raise HandoffError("invalid claim: LeaseExpiresAt missing") from exc


def _session_updates(snapshot: Path, agent_id: str, task_id: str) -> list[str]:
    changed: list[str] = []
    base = snapshot / "coordination/work_sessions" / agent_id
    if not base.exists():
        return changed
    for path in sorted(base.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or str(data.get("current_task") or "") != task_id:
            continue
        if str(data.get("state") or "") not in {"ACTIVE", "STOPPING"}:
            continue
        data["state"] = "STOPPED"
        data["stop_reason"] = "HANDOFF_READY"
        data["handoff_task"] = task_id
        data["handoff_at"] = iso()
        atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        changed.append(str(path.relative_to(snapshot)))
    return changed


def _artifact_manifest(task_id: str, handoff_id: str, source_artifacts: list[str]) -> list[dict[str, str]]:
    return [
        {
            "source_path": rel,
            "checkpoint_path": checkpoint_path(task_id, handoff_id, rel),
        }
        for rel in source_artifacts
    ]


def _build_handoff(
    *,
    handoff_id: str,
    task_id: str,
    row: dict[str, str],
    lock: dict[str, str],
    state: str,
    completed: str,
    artifacts: list[dict[str, str]],
    validation_run: str,
    known_failures: str,
    next_action: str,
    context_refs: list[str],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "UOS_PARTIAL_HANDOFF_V1",
        "handoff_id": handoff_id,
        "canonical_id": task_id,
        "project": row.get("project_id", ""),
        "agent_id": lock.get("AgentID", ""),
        "at": iso(),
        "state": state,
        "lease_generation": int(lock.get("LeaseGeneration") or 0),
        "lease_token": lock.get("LeaseToken", ""),
        "completed": completed,
        "artifacts": artifacts,
        "validation_run": validation_run,
        "known_failures": known_failures,
        "next_action": next_action,
        "context_refs": context_refs,
        "authority": {
            "is_completion": False,
            "transfers_ownership": False,
            "successor_must_claim": True,
            "successor_must_revalidate_acceptance": True,
        },
    }
    if state == "HANDOFF_READY":
        payload["release"] = {
            "mode": "EXPIRE_CURRENT_LEASE",
            "successor_claim_required": True,
            "expected_successor_generation": int(lock.get("LeaseGeneration") or 0) + 1,
        }
    return payload


def create_handoff(
    root: Path,
    *,
    agent_id: str,
    task_id: str,
    lease_token: str,
    state: str,
    completed: str,
    artifacts: list[str],
    validation_run: str,
    known_failures: str,
    next_action: str,
    context_refs: list[str],
    ack_execution_epoch: str,
    remote: str,
    branch: str,
) -> dict[str, object]:
    require_epoch(root, ack_execution_epoch)
    state = state.upper()
    if state not in STATES:
        raise HandoffError(f"invalid handoff state: {state}")
    if not next_action.strip():
        raise HandoffError("--next-action is required")
    handoff_id = f"HO_{utcnow().strftime('%Y%m%dT%H%M%SZ')}_{secrets.token_hex(3).upper()}"

    has_git = git(["rev-parse", "--git-dir"], cwd=root, check=False).returncode == 0
    has_remote = has_git and git(["remote", "get-url", remote], cwd=root, check=False).returncode == 0
    if not has_remote:
        row = task_row(root, task_id)
        rel_lock = lock_path(task_id)
        lock_file = root / rel_lock
        lock = parse_scalar_text(lock_file.read_text(encoding="utf-8") if lock_file.exists() else "")
        _validate_owned_lock(lock, agent_id, lease_token)
        validate_project_output_scope(root, row.get("project_id", ""), ";".join(artifacts))
        manifest = _artifact_manifest(task_id, handoff_id, artifacts)
        for item in manifest:
            source = root / item["source_path"]
            target = root / item["checkpoint_path"]
            copy_one(source, target)
        data = _build_handoff(
            handoff_id=handoff_id, task_id=task_id, row=row, lock=lock, state=state,
            completed=completed, artifacts=manifest, validation_run=validation_run,
            known_failures=known_failures, next_action=next_action, context_refs=context_refs,
        )
        atomic_write(root / handoff_path(task_id), json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        if state == "HANDOFF_READY":
            lock["LeaseExpiresAt"] = iso()
            lock["HandoffState"] = "HANDOFF_READY"
            lock["HandoffPath"] = handoff_path(task_id)
            atomic_write(lock_file, scalar_text(lock))
            _session_updates(root, agent_id, task_id)
        return data

    verify_identity(root, remote, branch)
    git(["fetch", "--quiet", remote, branch], cwd=root)
    base = git(["rev-parse", f"refs/remotes/{remote}/{branch}"], cwd=root).stdout.strip()
    worktree = Path(tempfile.mkdtemp(prefix="uos-handoff-"))
    added = False
    try:
        add = git(["worktree", "add", "--detach", "--force", str(worktree), base], cwd=root, check=False)
        if add.returncode:
            raise HandoffError(add.stderr.strip() or add.stdout.strip())
        added = True
        row = task_row(worktree, task_id)
        rel_lock = lock_path(task_id)
        lock_file = worktree / rel_lock
        lock = parse_scalar_text(lock_file.read_text(encoding="utf-8") if lock_file.exists() else "")
        _validate_owned_lock(lock, agent_id, lease_token)
        if (worktree / f"coordination/completed/{task_id}.done").exists():
            raise HandoffError("task already completed; handoff is not a revision mechanism")

        validate_project_output_scope(worktree, row.get("project_id", ""), ";".join(artifacts))
        manifest = _artifact_manifest(task_id, handoff_id, artifacts)
        checkpoint_paths: list[str] = []
        for item in manifest:
            source = root / item["source_path"]
            target = worktree / item["checkpoint_path"]
            copy_one(source, target)
            checkpoint_paths.append(item["checkpoint_path"])

        data = _build_handoff(
            handoff_id=handoff_id, task_id=task_id, row=row, lock=lock, state=state,
            completed=completed, artifacts=manifest, validation_run=validation_run,
            known_failures=known_failures, next_action=next_action, context_refs=context_refs,
        )
        rel_handoff = handoff_path(task_id)
        atomic_write(worktree / rel_handoff, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

        paths = [rel_handoff, *checkpoint_paths]
        lock_blob = blob_at(worktree, base, rel_lock)
        if not lock_blob:
            raise HandoffError("canonical claim blob missing")
        # Every handoff write, including a non-releasing PARTIAL checkpoint,
        # is conditioned on the exact current Claim blob. A stale owner cannot
        # publish context after ownership changes.
        expected: dict[str, str] = {rel_lock: lock_blob}
        old_handoff = blob_at(worktree, base, rel_handoff)
        if old_handoff:
            expected[rel_handoff] = old_handoff

        if state == "HANDOFF_READY":
            lock["LeaseExpiresAt"] = iso()
            lock["HandoffState"] = "HANDOFF_READY"
            lock["HandoffPath"] = rel_handoff
            atomic_write(lock_file, scalar_text(lock))
            paths.append(rel_lock)
            session_paths = _session_updates(worktree, agent_id, task_id)
            for rel in session_paths:
                old = blob_at(worktree, base, rel)
                if old:
                    expected[rel] = old
                paths.append(rel)

        require_absent = [] if old_handoff else [rel_handoff]
        publish(
            worktree,
            paths=list(dict.fromkeys(paths)),
            deletes=[],
            require_absent=require_absent,
            expect_blobs=expected,
            message=f"partial handoff {state.lower()} {task_id}",
            remote=remote,
            branch=branch,
            retries=8,
            allow_replace=True,
        )
        return data
    finally:
        if added:
            git(["worktree", "remove", "--force", str(worktree)], cwd=root, check=False)
        shutil.rmtree(worktree, ignore_errors=True)
        git(["worktree", "prune"], cwd=root, check=False)


def read_handoff(
    root: Path,
    *,
    task_id: str,
    agent_id: str,
    lease_token: str,
    remote: str,
    branch: str,
) -> dict[str, object]:
    has_git = git(["rev-parse", "--git-dir"], cwd=root, check=False).returncode == 0
    has_remote = has_git and git(["remote", "get-url", remote], cwd=root, check=False).returncode == 0
    if has_remote:
        verify_identity(root, remote, branch)
        git(["fetch", "--quiet", remote, branch], cwd=root)
        base = git(["rev-parse", f"refs/remotes/{remote}/{branch}"], cwd=root).stdout.strip()
        handoff_proc = git(["show", f"{base}:{handoff_path(task_id)}"], cwd=root, check=False)
        lock_proc = git(["show", f"{base}:{lock_path(task_id)}"], cwd=root, check=False)
        if handoff_proc.returncode:
            raise HandoffError(f"handoff not found: {task_id}")
        if lock_proc.returncode:
            raise HandoffError("successor must hold current canonical claim before reading handoff")
        data = json.loads(handoff_proc.stdout)
        lock = parse_scalar_text(lock_proc.stdout)
    else:
        path = root / handoff_path(task_id)
        if not path.exists():
            raise HandoffError(f"handoff not found: {task_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        lock_file = root / lock_path(task_id)
        lock = parse_scalar_text(lock_file.read_text(encoding="utf-8") if lock_file.exists() else "")

    if lock.get("AgentID") != agent_id or lock.get("LeaseToken") != lease_token:
        raise HandoffError("successor must hold current canonical claim before reading handoff")
    if not isinstance(data, dict):
        raise HandoffError("invalid handoff payload")
    origin_generation = int(data.get("lease_generation") or 0)
    successor_generation = int(lock.get("LeaseGeneration") or 0)
    result = dict(data)
    result["successor"] = {
        "agent_id": agent_id,
        "lease_generation": successor_generation,
        "ownership_verified": True,
        "generation_advanced": successor_generation > origin_generation,
    }
    result["warning"] = "UNVERIFIED_PARTIAL_WORK: restore from checkpoint artifacts as needed and re-run task Acceptance before final completion."
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create/read PARTIAL_HANDOFF_V1-style recovery records.")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--target-branch", default="main")
    parser.add_argument("--ack-execution-epoch", default="")
    sub = parser.add_subparsers(dest="command", required=True)

    item = sub.add_parser("create")
    item.add_argument("--agent-id", required=True)
    item.add_argument("--task", required=True)
    item.add_argument("--lease-token", required=True)
    item.add_argument("--state", choices=sorted(STATES), default="PARTIAL")
    item.add_argument("--completed", default="")
    item.add_argument("--artifact", action="append", default=[])
    item.add_argument("--validation-run", default="")
    item.add_argument("--known-failures", default="")
    item.add_argument("--next-action", required=True)
    item.add_argument("--context-ref", action="append", default=[])

    item = sub.add_parser("read")
    item.add_argument("--task", required=True)
    item.add_argument("--agent-id", required=True)
    item.add_argument("--lease-token", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    try:
        if args.command == "create":
            artifacts: list[str] = []
            for raw in args.artifact:
                artifacts.extend(split_paths(raw))
            context_refs: list[str] = []
            for raw in args.context_ref:
                context_refs.extend(split_paths(raw))
            result = create_handoff(
                root,
                agent_id=args.agent_id,
                task_id=args.task,
                lease_token=args.lease_token,
                state=args.state,
                completed=args.completed,
                artifacts=list(dict.fromkeys(artifacts)),
                validation_run=args.validation_run,
                known_failures=args.known_failures,
                next_action=args.next_action,
                context_refs=list(dict.fromkeys(context_refs)),
                ack_execution_epoch=args.ack_execution_epoch,
                remote=args.remote,
                branch=args.target_branch,
            )
        else:
            result = read_handoff(
                root,
                task_id=args.task,
                agent_id=args.agent_id,
                lease_token=args.lease_token,
                remote=args.remote,
                branch=args.target_branch,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (HandoffError, PublishError, json.JSONDecodeError) as exc:
        print(f"UOS_HANDOFF_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
