#!/usr/bin/env python3
"""UOS standalone single-repository orchestration CLI.

The deterministic state machine can run in two transports:
- local: one shared working tree guarded by a repository-local mutex;
- git-cas: latest-canonical isolated-worktree transactions for independent clones.

`auto` is the default. A Git repository with the configured remote uses git-cas;
a non-Git test/work directory uses local mode. A configured canonical remote that
is temporarily unreachable never silently falls back to local ownership.

This repository still manages only projects stored inside the UOS repository.
No AI_book dispatch or multi-repository routing is enabled here.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import secrets
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath

try:
    from control_extensions import (
        ControlExtensionError,
        build_work_market,
        enforce_execution_epoch,
        execution_epoch,
        validate_project_output_scope,
        write_durability_receipt,
    )
except ModuleNotFoundError:
    from tools.control_extensions import (
        ControlExtensionError,
        build_work_market,
        enforce_execution_epoch,
        execution_epoch,
        validate_project_output_scope,
        write_durability_receipt,
    )

try:
    from claim_broker_v2 import (
        ClaimBrokerError,
        claim_exact as broker_claim_exact,
        validate_owned_lock as broker_validate_owned_lock,
    )
except ModuleNotFoundError:
    from tools.claim_broker_v2 import (
        ClaimBrokerError,
        claim_exact as broker_claim_exact,
        validate_owned_lock as broker_validate_owned_lock,
    )

TASK_FIELDS = [
    "id", "priority", "status", "role", "title", "deps", "inputs", "output",
    "project_id", "phase", "workstream", "exclusive_keys", "size_class",
    "quality_tier", "risk_tier", "wave_id", "batch_hint", "acceptance",
    "compliance_profile", "notes", "min_capability_tier", "context_class",
    "tool_requirements", "context_refs",
]


class UOSError(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    return (dt or utcnow()).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "orchestration").exists() or (candidate / ".git").exists():
            return candidate
    raise UOSError("run inside a UOS repository")


def safe_id(value: str, label: str = "id") -> str:
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
    if not value or any(ch not in allowed for ch in value):
        raise UOSError(f"invalid {label}: {value!r}")
    return value


def safe_repo_path(value: str, label: str = "path") -> str:
    raw = (value or "").strip().replace("\\", "/")
    if not raw:
        raise UOSError(f"empty {label}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise UOSError(f"{label} must stay inside repository: {value!r}")
    return str(path)


def safe_repo_path_list(value: str, label: str, *, allow_empty: bool = True) -> str:
    items = [item.strip() for item in (value or "").split(";") if item.strip()]
    if not items:
        if allow_empty:
            return ""
        raise UOSError(f"at least one {label} is required")
    return ";".join(safe_repo_path(item, label) for item in items)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    try:
        temp.write_text(content, encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def parse_scalar_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in raw or raw.lstrip().startswith("-"):
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip().strip('"')
    return out


def write_kv(path: Path, values: dict[str, object]) -> None:
    atomic_write_text(path, "".join(f"{key}: {value}\n" for key, value in values.items()))


def read_catalog(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_catalog(path: Path, rows: list[dict[str, str]]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=TASK_FIELDS)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in TASK_FIELDS})
    atomic_write_text(path, buffer.getvalue())


def project_dirs(root: Path) -> list[tuple[dict[str, str], Path]]:
    base = root / "orchestration/projects"
    if not base.exists():
        return []
    result: list[tuple[dict[str, str], Path]] = []
    for directory in sorted(item for item in base.iterdir() if item.is_dir()):
        meta = parse_scalar_file(directory / "PROJECT.yaml")
        if meta.get("ProjectID"):
            result.append((meta, directory))
    return result


def all_tasks(root: Path) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for _meta, directory in project_dirs(root):
        for source in read_catalog(directory / "TASK_CATALOG.csv"):
            row = dict(source)
            row["_catalog"] = str(directory / "TASK_CATALOG.csv")
            result.append(row)
    return result


def dependencies(row: dict[str, str]) -> list[str]:
    return [item for item in (row.get("deps") or "").split(";") if item]


def done_path(root: Path, task_id: str) -> Path:
    return root / "coordination/completed" / f"{task_id}.done"


def claim_path(root: Path, task_id: str) -> Path:
    return root / "coordination/claims" / f"{task_id}.lock"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def is_stale(lock: dict[str, str]) -> bool:
    try:
        return parse_time(lock["LeaseExpiresAt"]) <= utcnow()
    except Exception:
        return True


def effective_states(root: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows = all_tasks(root)
    completed = {row["id"] for row in rows if done_path(root, row["id"]).exists()}
    states: dict[str, str] = {}
    for row in rows:
        task_id = row["id"]
        if task_id in completed:
            state = "DONE"
        else:
            lock = parse_scalar_file(claim_path(root, task_id))
            if lock and not is_stale(lock):
                state = "CLAIMED"
            elif all(dep in completed for dep in dependencies(row)) and (
                row.get("status") or ""
            ).upper() not in {"CANCELLED", "PAUSED"}:
                state = "READY"
            else:
                state = "BLOCKED"
        states[task_id] = state
    return rows, states


def reconcile(root: Path) -> dict[str, object]:
    """Build deterministic derived views from source-of-truth project/claim/done files."""
    rows, states = effective_states(root)
    runtime = root / "coordination/runtime"
    runtime.mkdir(parents=True, exist_ok=True)

    status_fields = [
        "id", "project_id", "priority", "role", "title", "effective_status", "deps", "output"
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=status_fields)
    writer.writeheader()
    for row in sorted(
        rows,
        key=lambda item: (
            item.get("project_id", ""),
            int(item.get("priority") or 9999),
            item["id"],
        ),
    ):
        writer.writerow(
            {
                "id": row.get("id", ""),
                "project_id": row.get("project_id", ""),
                "priority": row.get("priority", ""),
                "role": row.get("role", ""),
                "title": row.get("title", ""),
                "effective_status": states[row["id"]],
                "deps": row.get("deps", ""),
                "output": row.get("output", ""),
            }
        )
    atomic_write_text(runtime / "TASK_STATUS.csv", buffer.getvalue())
    build_work_market(runtime, rows, states)

    summary: dict[str, dict[str, int]] = {}
    for row in rows:
        project_id = row.get("project_id") or "UNKNOWN"
        bucket = summary.setdefault(
            project_id,
            {"total": 0, "ready": 0, "claimed": 0, "blocked": 0, "done": 0},
        )
        bucket["total"] += 1
        bucket[states[row["id"]].lower()] += 1

    payload: dict[str, object] = {
        "schema": "UOS_SINGLE_REPO_STATUS_V1",
        "scope": "SAME_REPOSITORY_ONLY",
        "projects": summary,
        "work_market": "coordination/runtime/WORK_MARKET.csv",
    }
    atomic_write_text(
        runtime / "STATUS.json",
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return payload


class RepoMutex:
    """Short same-working-tree control-plane mutex used only by local transport."""

    def __init__(self, root: Path, timeout: float = 10.0):
        self.path = root / "coordination/runtime/.pilot_mutex"
        self.timeout = timeout

    def __enter__(self) -> "RepoMutex":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + self.timeout
        while True:
            try:
                self.path.mkdir()
                (self.path / "owner").write_text(f"{os.getpid()} {iso()}\n", encoding="utf-8")
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > 30:
                        shutil.rmtree(self.path, ignore_errors=True)
                        continue
                except FileNotFoundError:
                    continue
                if time.time() >= deadline:
                    raise UOSError("control-plane mutex busy")
                time.sleep(0.05)

    def __exit__(self, *_exc: object) -> None:
        shutil.rmtree(self.path, ignore_errors=True)


def command_boot(_args: argparse.Namespace) -> int:
    root = repo_root()
    with RepoMutex(root):
        payload = reconcile(root)
    payload["repository_root"] = os.environ.get("UOS_CALLER_ROOT") or str(root)
    payload["execution_epoch"] = execution_epoch(root) or None
    payload["commands"] = [
        "project init", "task publish", "status", "claim", "renew", "complete", "reconcile"
    ]
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_project_init(args: argparse.Namespace) -> int:
    root = repo_root()
    project_id = safe_id(args.project_id, "project id")
    directory = root / "orchestration/projects" / project_id
    with RepoMutex(root):
        if directory.exists():
            raise UOSError(f"project exists: {project_id}")
        directory.mkdir(parents=True)
        title = json.dumps(args.title, ensure_ascii=False)
        goal = json.dumps(args.goal or args.title, ensure_ascii=False)
        atomic_write_text(
            directory / "PROJECT.yaml",
            "Schema: UOS_PROJECT_V1\n"
            f"ProjectID: {project_id}\n"
            f"Title: {title}\n"
            "State: ACTIVE\n"
            f"IntentVersion: {project_id}_INTENT_V1\n"
            "RepositoryMode: SAME_REPOSITORY\n"
            f"WorkRoot: projects/{project_id}\n"
            f"Goal: {goal}\n",
        )
        write_catalog(directory / "TASK_CATALOG.csv", [])
        reconcile(root)
    print(project_id)
    return 0


def command_task_publish(args: argparse.Namespace) -> int:
    root = repo_root()
    project_id = safe_id(args.project, "project id")
    task_id = safe_id(args.task_id, "task id")
    output = safe_repo_path_list(args.output, "output path", allow_empty=False)
    inputs = safe_repo_path_list(args.inputs or "", "input path", allow_empty=True)
    catalog = root / "orchestration/projects" / project_id / "TASK_CATALOG.csv"

    with RepoMutex(root):
        if not catalog.exists():
            raise UOSError(f"unknown project: {project_id}")
        try:
            validate_project_output_scope(root, project_id, output)
        except ControlExtensionError as exc:
            raise UOSError(str(exc)) from exc
        current = all_tasks(root)
        if any(row["id"] == task_id for row in current):
            raise UOSError(f"duplicate task id: {task_id}")
        deps = [item for item in (args.deps or "").split(";") if item]
        known = {row["id"] for row in current}
        missing = [item for item in deps if item not in known]
        if missing:
            raise UOSError(f"unknown dependencies: {missing}")

        row = {field: "" for field in TASK_FIELDS}
        row.update(
            {
                "id": task_id,
                "priority": str(args.priority),
                "status": "READY" if not deps else "BLOCKED",
                "role": args.role,
                "title": args.title,
                "deps": ";".join(deps),
                "inputs": inputs,
                "output": output,
                "project_id": project_id,
                "phase": args.phase,
                "workstream": args.workstream,
                "exclusive_keys": args.exclusive_key or f"PROJECT:{project_id}:{task_id}",
                "size_class": args.size,
                "quality_tier": "STANDARD",
                "risk_tier": "LOW",
                "acceptance": args.acceptance,
                "compliance_profile": "SOFTWARE_V1",
                "min_capability_tier": str(args.min_capability),
                "context_class": args.context,
            }
        )
        rows = read_catalog(catalog)
        rows.append(row)
        write_catalog(catalog, rows)
        reconcile(root)
    print(task_id)
    return 0


def choose_task(root: Path, args: argparse.Namespace) -> dict[str, str] | None:
    rows, states = effective_states(root)
    candidates = [row for row in rows if states[row["id"]] == "READY"]
    if args.project:
        candidates = [row for row in candidates if row.get("project_id") == args.project]
    if args.task:
        candidates = [row for row in candidates if row["id"] == args.task]
    candidates.sort(key=lambda row: (int(row.get("priority") or 9999), row["id"]))
    return candidates[0] if candidates else None


def command_claim(args: argparse.Namespace) -> int:
    root = repo_root()
    safe_id(args.agent_id, "agent id")
    with RepoMutex(root):
        row = choose_task(root, args)
        if not row:
            print(json.dumps({"status": "NO_MATCH"}))
            return 4
        try:
            claim = broker_claim_exact(
                root,
                row,
                agent_id=args.agent_id,
                lease_minutes=args.lease_minutes,
                execution_epoch=execution_epoch(root),
            )
        except ClaimBrokerError as exc:
            raise UOSError(str(exc)) from exc
        if str(claim.get("status", "")).upper() == "NO_MATCH":
            print(json.dumps(claim, ensure_ascii=False, indent=2))
            return 4
        reconcile(root)
    print(json.dumps(claim, ensure_ascii=False, indent=2))
    return 0


def current_owned_lock(root: Path, args: argparse.Namespace) -> tuple[Path, dict[str, str]]:
    try:
        return broker_validate_owned_lock(
            root,
            task_id=args.task,
            agent_id=args.agent_id,
            lease_token=args.lease_token,
            require_unexpired=True,
        )
    except ClaimBrokerError as exc:
        raise UOSError(str(exc)) from exc


def command_renew(args: argparse.Namespace) -> int:
    root = repo_root()
    with RepoMutex(root):
        path, lock = current_owned_lock(root, args)
        lock["LeaseExpiresAt"] = iso(utcnow() + timedelta(minutes=args.lease_minutes))
        write_kv(path, lock)
        reconcile(root)
    print(json.dumps(lock, ensure_ascii=False, indent=2))
    return 0


def command_complete(args: argparse.Namespace) -> int:
    root = repo_root()
    with RepoMutex(root):
        path, lock = current_owned_lock(root, args)
        target = done_path(root, args.task)
        if target.exists():
            raise UOSError("task already completed")
        rows = {row["id"]: row for row in all_tasks(root)}
        if args.task not in rows:
            raise UOSError("unknown task")
        row = rows[args.task]
        output_spec = safe_repo_path_list(row.get("output") or "", "declared output", allow_empty=True)
        try:
            validate_project_output_scope(root, row.get("project_id", ""), output_spec)
        except ControlExtensionError as exc:
            raise UOSError(str(exc)) from exc
        outputs = [item for item in output_spec.split(";") if item]
        missing = [item for item in outputs if not (root / item).exists()]
        if missing and not args.allow_missing_output:
            raise UOSError(f"missing declared outputs: {missing}")
        durability = write_durability_receipt(
            root,
            args.task,
            row.get("project_id", ""),
            outputs,
        )
        if durability.get("status") != "DURABLE_READY" and not args.allow_missing_output:
            raise UOSError(f"artifact durability incomplete: {durability.get('missing')}")
        write_kv(
            target,
            {
                "Schema": "UOS_DONE_V1",
                "CanonicalID": args.task,
                "ProjectID": row.get("project_id", ""),
                "AgentID": args.agent_id,
                "LeaseGeneration": lock.get("LeaseGeneration", ""),
                "LeaseToken": args.lease_token,
                "CompletedAt": iso(),
                "Result": args.result,
                "DurabilityReceipt": f"coordination/quality/durability/{args.task}.json",
            },
        )
        path.unlink(missing_ok=True)
        payload = reconcile(root)
    print(
        json.dumps(
            {
                "status": "DONE",
                "task": args.task,
                "project": row.get("project_id"),
                "durability": durability,
                "summary": payload["projects"].get(row.get("project_id")),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_status(args: argparse.Namespace) -> int:
    root = repo_root()
    with RepoMutex(root):
        payload = reconcile(root)
    if args.project:
        projects = payload["projects"]
        assert isinstance(projects, dict)
        payload["projects"] = {args.project: projects.get(args.project, {})}
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_reconcile(_args: argparse.Namespace) -> int:
    root = repo_root()
    with RepoMutex(root):
        payload = reconcile(root)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0



def command_outbox_status(args: argparse.Namespace) -> int:
    root = repo_root()
    try:
        from completion_outbox import status as outbox_status
    except ModuleNotFoundError:
        from tools.completion_outbox import status as outbox_status
    payload = outbox_status(root, remote=args.remote, branch=args.target_branch)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_outbox_ingest(args: argparse.Namespace) -> int:
    root = repo_root()
    # Ingest can complete tasks and delete canonical locks, so it carries the
    # same stale-agent ExecutionEpoch requirement as `complete`.
    try:
        enforce_execution_epoch(root, "complete", args.ack_execution_epoch)
    except ControlExtensionError as exc:
        raise UOSError(str(exc)) from exc
    try:
        from completion_outbox import ingest as outbox_ingest
    except ModuleNotFoundError:
        from tools.completion_outbox import ingest as outbox_ingest
    payload = outbox_ingest(
        root,
        remote=args.remote,
        branch=args.target_branch,
        max_batch=args.max_batch,
        retries=args.ingest_retries,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="uos")
    parser.add_argument(
        "--transport",
        choices=["auto", "local", "git-cas"],
        default=os.environ.get("UOS_TRANSPORT", "auto"),
        help="auto uses canonical Git CAS when a remote is configured; local is test/single-worktree mode",
    )
    parser.add_argument("--remote", default=os.environ.get("UOS_REMOTE", "origin"))
    parser.add_argument("--target-branch", default=os.environ.get("UOS_TARGET_BRANCH", "main"))
    parser.add_argument("--cas-retries", type=int, default=int(os.environ.get("UOS_CAS_RETRIES", "8")))
    parser.add_argument(
        "--ack-execution-epoch",
        default=os.environ.get("UOS_ACK_EXECUTION_EPOCH", ""),
        help="required for critical commands when .uos/EXECUTION_CONTRACT.yaml is present",
    )
    subs = parser.add_subparsers(dest="command", required=True)

    item = subs.add_parser("boot")
    item.set_defaults(func=command_boot)
    item = subs.add_parser("reconcile")
    item.set_defaults(func=command_reconcile)
    item = subs.add_parser("status")
    item.add_argument("--project")
    item.set_defaults(func=command_status)

    project = subs.add_parser("project")
    project_subs = project.add_subparsers(dest="project_command", required=True)
    item = project_subs.add_parser("init")
    item.add_argument("--project-id", required=True)
    item.add_argument("--title", required=True)
    item.add_argument("--goal")
    item.set_defaults(func=command_project_init)

    task = subs.add_parser("task")
    task_subs = task.add_subparsers(dest="task_command", required=True)
    item = task_subs.add_parser("publish")
    item.add_argument("--project", required=True)
    item.add_argument("--task-id", required=True)
    item.add_argument("--title", required=True)
    item.add_argument("--role", default="WORKER")
    item.add_argument("--priority", type=int, default=10)
    item.add_argument("--deps", default="")
    item.add_argument("--inputs", default="")
    item.add_argument("--output", required=True)
    item.add_argument("--phase", default="BUILD")
    item.add_argument("--workstream", default="general")
    item.add_argument("--exclusive-key")
    item.add_argument("--size", default="S")
    item.add_argument("--context", default="S")
    item.add_argument("--min-capability", type=int, default=1)
    item.add_argument("--acceptance", required=True)
    item.set_defaults(func=command_task_publish)

    item = subs.add_parser("claim")
    item.add_argument("--agent-id", required=True)
    item.add_argument("--task")
    item.add_argument("--project")
    item.add_argument("--lease-minutes", type=int, default=90)
    item.set_defaults(func=command_claim)

    item = subs.add_parser("renew")
    item.add_argument("--agent-id", required=True)
    item.add_argument("--task", required=True)
    item.add_argument("--lease-token", required=True)
    item.add_argument("--lease-minutes", type=int, default=90)
    item.set_defaults(func=command_renew)

    item = subs.add_parser("complete")
    item.add_argument("--agent-id", required=True)
    item.add_argument("--task", required=True)
    item.add_argument("--lease-token", required=True)
    item.add_argument("--result", default="PASS")
    item.add_argument("--allow-missing-output", action="store_true")
    item.set_defaults(func=command_complete)

    outbox = subs.add_parser("outbox")
    outbox_subs = outbox.add_subparsers(dest="outbox_command", required=True)
    item = outbox_subs.add_parser("status")
    item.set_defaults(func=command_outbox_status)
    item = outbox_subs.add_parser("ingest")
    item.add_argument("--max-batch", type=int, default=16)
    item.add_argument("--ingest-retries", type=int, default=8)
    item.add_argument("--dry-run", action="store_true")
    item.set_defaults(func=command_outbox_ingest)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        root = repo_root()
        try:
            enforce_execution_epoch(root, args.command, args.ack_execution_epoch)
        except ControlExtensionError as exc:
            raise UOSError(str(exc)) from exc

        if args.command == "outbox":
            return args.func(args)

        try:
            from canonical_runner import resolve_transport, run_canonical
        except ModuleNotFoundError:
            from tools.canonical_runner import resolve_transport, run_canonical

        mode = resolve_transport(root, args.transport, args.remote, args.target_branch)
        if mode == "git-cas":
            proc = run_canonical(
                root,
                list(sys.argv[1:]),
                remote=args.remote,
                branch=args.target_branch,
                retries=args.cas_retries,
            )
            if proc.stdout:
                print(proc.stdout, end="")
            if proc.stderr:
                print(proc.stderr, end="", file=sys.stderr)
            return proc.returncode
        return args.func(args)
    except UOSError as exc:
        print(f"UOS_ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        name = exc.__class__.__name__
        if name in {"CanonicalRunError", "PublishError", "ControlExtensionError"}:
            print(f"UOS_CAS_ERROR: {exc}", file=sys.stderr)
            return 2
        raise


if __name__ == "__main__":
    raise SystemExit(main())
