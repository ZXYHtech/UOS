#!/usr/bin/env python3
"""Provider-neutral UOS completion Outbox / Integration Lane.

The Outbox is Work-Plane persistence, never ownership and never completion.

Fast path:
    valid complete -> latest-main Git CAS -> canonical Done

Contention fallback:
    valid complete candidate -> direct main ref races exhausted
    -> immutable non-canonical ``uos-outbox/...`` ref
    -> later mechanical batch ingest
    -> latest-main ownership + fencing + path read-set revalidation
    -> one non-force main transaction

Only task completion candidates are eligible. Claim/Renew/Project/Task publication
must never be converted into outbox success.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:
    from canonical_publish import PublishError, blob_at, git, is_ref_race, verify_identity
    from claim_broker_v2 import ClaimBrokerError, is_stale, parse_kv, safe_rel
except ModuleNotFoundError:
    from tools.canonical_publish import PublishError, blob_at, git, is_ref_race, verify_identity
    from tools.claim_broker_v2 import ClaimBrokerError, is_stale, parse_kv, safe_rel


SCHEMA = "UOS_COMPLETION_OUTBOX_V1"
MANIFEST_PATH = ".uos/outbox/COMPLETION.json"
OUTBOX_PREFIX = "uos-outbox"
RECEIPT_ROOT = "coordination/outbox_receipts"
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


class CompletionOutboxError(RuntimeError):
    pass


@dataclass
class Candidate:
    request_id: str
    ref_name: str
    commit: str
    manifest: dict[str, Any]
    publish_paths: list[str]


def iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _safe_id(value: str, label: str) -> str:
    text = (value or "").strip()
    if not SAFE_ID.fullmatch(text):
        raise CompletionOutboxError(f"unsafe {label}: {value!r}")
    return text


def _safe_rel(value: str) -> str:
    raw = (value or "").strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CompletionOutboxError(f"unsafe repository path: {value!r}")
    if raw == ".git" or raw.startswith(".git/"):
        raise CompletionOutboxError(".git paths are forbidden")
    return str(path)


def _show(root: Path, commit: str, rel: str) -> str | None:
    proc = git(["show", f"{commit}:{rel}"], cwd=root, check=False)
    return proc.stdout if proc.returncode == 0 else None


def _json_at(root: Path, commit: str, rel: str) -> dict[str, Any] | None:
    text = _show(root, commit, rel)
    if text is None:
        return None
    try:
        value = json.loads(text)
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _kv_at(root: Path, commit: str, rel: str) -> dict[str, str]:
    text = _show(root, commit, rel)
    if text is None:
        return {}
    out: dict[str, str] = {}
    for raw in text.splitlines():
        if not raw or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _first_parent(root: Path, commit: str) -> str:
    proc = git(["rev-parse", f"{commit}^"], cwd=root, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _tree_object(root: Path, commit: str, rel: str) -> str | None:
    proc = git(["rev-parse", f"{commit}:{rel}"], cwd=root, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def _task_row_at(root: Path, commit: str, task_id: str) -> dict[str, str]:
    names = git(
        ["ls-tree", "-r", "--name-only", commit, "orchestration/projects"],
        cwd=root,
        check=False,
    ).stdout.splitlines()
    for rel in sorted(name for name in names if name.endswith("/TASK_CATALOG.csv")):
        text = _show(root, commit, rel)
        if not text:
            continue
        for row in csv.DictReader(text.splitlines()):
            if row.get("id") == task_id:
                return dict(row)
    raise CompletionOutboxError(f"unknown task at canonical main: {task_id}")


def _declared_output_paths(row: dict[str, str]) -> list[str]:
    return [_safe_rel(item) for item in (row.get("output") or "").split(";") if item.strip()]


def _control_paths(task_id: str, candidate_root: Path | None = None) -> list[str]:
    paths = [
        f"coordination/completed/{task_id}.done",
        f"coordination/quality/durability/{task_id}.json",
    ]
    event = f"coordination/quality/events/{task_id}.json"
    if candidate_root is None or (candidate_root / event).exists():
        paths.append(event)
    return paths


def completion_publish_paths(candidate_root: Path, task_id: str, row: dict[str, str]) -> list[str]:
    """Return semantic completion paths; derived runtime views are excluded."""
    outputs = _declared_output_paths(row)
    paths = list(outputs)
    for rel in _control_paths(task_id, candidate_root):
        if (candidate_root / rel).exists() and rel not in paths:
            paths.append(rel)
    required = f"coordination/completed/{task_id}.done"
    if required not in paths:
        raise CompletionOutboxError("completion candidate is missing DonePath")
    durability = f"coordination/quality/durability/{task_id}.json"
    if durability not in paths:
        raise CompletionOutboxError("completion candidate is missing durability receipt")
    return paths


def _expected_objects(root: Path, base: str, paths: Iterable[str]) -> dict[str, str | None]:
    return {rel: _tree_object(root, base, rel) for rel in paths}


def _hash_json(root: Path, value: dict[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    proc = git(["hash-object", "-w", "--stdin"], cwd=root, input_text=text)
    return proc.stdout.strip()


def _outbox_ref(project: str, task: str, agent: str, request_id: str) -> str:
    return "/".join(
        [
            OUTBOX_PREFIX,
            _safe_id(project, "project id"),
            _safe_id(task, "task id"),
            _safe_id(agent, "agent id"),
            _safe_id(request_id, "publish request id"),
        ]
    )


def receipt_path(request_id: str) -> str:
    return f"{RECEIPT_ROOT}/{_safe_id(request_id, 'publish request id')}.json"


def stage_completion_candidate(
    root: Path,
    *,
    candidate_root: Path,
    base: str,
    candidate_commit: str,
    task_id: str,
    owner_lock: dict[str, str],
    owner_lock_blob_sha: str,
    remote: str = "origin",
    branch: str = "main",
) -> dict[str, Any]:
    """Persist a validated completion candidate on a unique non-canonical ref."""
    verify_identity(root, remote, branch)
    if not owner_lock:
        raise CompletionOutboxError("completion fallback requires canonical ownership lock")
    if owner_lock.get("CanonicalID") != task_id:
        raise CompletionOutboxError("completion fallback task/lock mismatch")
    if is_stale(owner_lock):
        raise CompletionOutboxError("completion fallback refuses expired lease")
    grant_rel = _safe_rel(owner_lock.get("GrantPath", ""))
    grant_id = _safe_id(owner_lock.get("GrantID", ""), "grant id")
    agent = _safe_id(owner_lock.get("AgentID", ""), "agent id")
    project = _safe_id(owner_lock.get("ProjectID", ""), "project id")
    generation = int(owner_lock.get("LeaseGeneration") or 0)
    token = owner_lock.get("LeaseToken", "")
    if generation < 1 or not token or not owner_lock_blob_sha:
        raise CompletionOutboxError("completion fallback ownership checkpoint incomplete")

    row = _task_row_at(root, base, task_id)
    if (row.get("project_id") or "") != project:
        raise CompletionOutboxError("completion fallback project mismatch")
    publish_paths = completion_publish_paths(candidate_root, task_id, row)
    for rel in publish_paths:
        if _tree_object(root, candidate_commit, rel) is None:
            raise CompletionOutboxError(f"completion candidate object missing: {rel}")

    request_id = f"PUB-{grant_id}"
    ref_name = _outbox_ref(project, task_id, agent, request_id)
    full_ref = f"refs/heads/{ref_name}"
    receipt = receipt_path(request_id)

    # Idempotence: one publish request per immutable Grant.
    existing = git(["ls-remote", "--heads", remote, full_ref], cwd=root, check=False)
    if existing.returncode == 0 and existing.stdout.strip():
        return {
            "status": "OUTBOX_ALREADY_STAGED",
            "request_id": request_id,
            "outbox_ref": ref_name,
            "receipt_path": receipt,
            "canonical_done": False,
        }

    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "protocol": "DIRECT_COMPLETE_REF_RACE_FALLBACK_V1",
        "status": "READY",
        "request_id": request_id,
        "requested_at": iso(),
        "base_main": base,
        "candidate_commit": "SELF",
        "outbox_ref": ref_name,
        "task_id": task_id,
        "project_id": project,
        "agent_id": agent,
        "grant_id": grant_id,
        "grant_path": grant_rel,
        "lease_generation": generation,
        "lease_token": token,
        "fencing_token": owner_lock.get("FencingToken", ""),
        "staged_from_lock_git_blob_sha": owner_lock_blob_sha,
        "publish_paths": publish_paths,
        "expected_base_objects": _expected_objects(root, base, publish_paths),
        "done_path": f"coordination/completed/{task_id}.done",
        "lock_path": f"coordination/claims/{task_id}.lock",
        "receipt_path": receipt,
    }
    manifest_blob = _hash_json(root, manifest)

    # Build an outbox commit with candidate content + manifest, parented directly
    # by the main snapshot on which the completion was validated.
    fd, index_name = tempfile.mkstemp(prefix="uos-completion-outbox-index-")
    os.close(fd)
    try:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = index_name
        os.unlink(index_name)
        git(["read-tree", f"{candidate_commit}^{{tree}}"], cwd=root, env=env)
        git(
            ["update-index", "--add", "--cacheinfo", "100644", manifest_blob, MANIFEST_PATH],
            cwd=root,
            env=env,
        )
        tree = git(["write-tree"], cwd=root, env=env).stdout.strip()
    finally:
        try:
            os.unlink(index_name)
        except FileNotFoundError:
            pass

    staged_commit = git(
        ["commit-tree", tree, "-p", base, "-m", f"outbox: staged completion {task_id}"],
        cwd=root,
    ).stdout.strip()
    push = git(["push", "--porcelain", remote, f"{staged_commit}:{full_ref}"], cwd=root, check=False)
    if push.returncode:
        # A concurrent idempotent stage may have won the same unique ref.
        if is_ref_race(push):
            existing = git(["ls-remote", "--heads", remote, full_ref], cwd=root, check=False)
            if existing.returncode == 0 and existing.stdout.strip():
                return {
                    "status": "OUTBOX_ALREADY_STAGED",
                    "request_id": request_id,
                    "outbox_ref": ref_name,
                    "receipt_path": receipt,
                    "canonical_done": False,
                }
        raise CompletionOutboxError("outbox ref create failed: " + (push.stderr.strip() or push.stdout.strip()))

    return {
        "status": "COMPLETION_STAGED",
        "request_id": request_id,
        "outbox_ref": ref_name,
        "outbox_commit": staged_commit,
        "base_main": base,
        "receipt_path": receipt,
        "publish_paths": publish_paths,
        "canonical_done": False,
    }


def _fetch_outbox_refs(root: Path, remote: str) -> None:
    git(
        [
            "fetch", "--quiet", "--prune", remote,
            f"+refs/heads/{OUTBOX_PREFIX}/*:refs/remotes/{remote}/{OUTBOX_PREFIX}/*",
        ],
        cwd=root,
        check=False,
    )


def _list_outbox_refs(root: Path, remote: str) -> list[tuple[str, str]]:
    prefix = f"refs/remotes/{remote}/{OUTBOX_PREFIX}/"
    proc = git(["for-each-ref", "--format=%(refname) %(objectname)", prefix], cwd=root, check=False)
    values: list[tuple[str, str]] = []
    for raw in proc.stdout.splitlines():
        if " " not in raw:
            continue
        ref, commit = raw.strip().split(" ", 1)
        short = ref[len(f"refs/remotes/{remote}/"):] if ref.startswith(f"refs/remotes/{remote}/") else ref
        values.append((short, commit.strip()))
    return sorted(values)


def _validate_manifest(manifest: dict[str, Any], ref_name: str, commit: str) -> tuple[str, list[str]]:
    if manifest.get("schema") != SCHEMA or manifest.get("status") != "READY":
        raise CompletionOutboxError("OUTBOX_MANIFEST_BAD_SCHEMA_OR_STATUS")
    if manifest.get("candidate_commit") not in {"SELF", commit}:
        raise CompletionOutboxError("OUTBOX_MANIFEST_CANDIDATE_MISMATCH")
    if manifest.get("outbox_ref") != ref_name:
        raise CompletionOutboxError("OUTBOX_MANIFEST_REF_MISMATCH")
    request_id = _safe_id(str(manifest.get("request_id") or ""), "publish request id")
    paths_raw = manifest.get("publish_paths")
    if not isinstance(paths_raw, list) or not paths_raw:
        raise CompletionOutboxError("OUTBOX_MANIFEST_NO_PUBLISH_PATHS")
    paths = [_safe_rel(str(item)) for item in paths_raw]
    if len(set(paths)) != len(paths):
        raise CompletionOutboxError("OUTBOX_MANIFEST_DUPLICATE_PATHS")
    return request_id, paths


def _validate_candidate(root: Path, base: str, ref_name: str, commit: str) -> Candidate:
    manifest = _json_at(root, commit, MANIFEST_PATH)
    if not manifest:
        raise CompletionOutboxError("OUTBOX_MANIFEST_MISSING")
    request_id, publish_paths = _validate_manifest(manifest, ref_name, commit)
    if _first_parent(root, commit) != str(manifest.get("base_main") or ""):
        raise CompletionOutboxError("OUTBOX_PARENT_BASE_MISMATCH")

    task = _safe_id(str(manifest.get("task_id") or ""), "task id")
    project = _safe_id(str(manifest.get("project_id") or ""), "project id")
    agent = _safe_id(str(manifest.get("agent_id") or ""), "agent id")
    grant_id = _safe_id(str(manifest.get("grant_id") or ""), "grant id")
    grant_rel = _safe_rel(str(manifest.get("grant_path") or ""))
    done_rel = _safe_rel(str(manifest.get("done_path") or ""))
    lock_rel = _safe_rel(str(manifest.get("lock_path") or ""))
    if done_rel != f"coordination/completed/{task}.done" or lock_rel != f"coordination/claims/{task}.lock":
        raise CompletionOutboxError("OUTBOX_TASK_CONTROL_PATH_MISMATCH")
    if _tree_object(root, base, done_rel) is not None:
        raise CompletionOutboxError("OUTBOX_ALREADY_COMPLETED")

    row = _task_row_at(root, base, task)
    if (row.get("project_id") or "") != project:
        raise CompletionOutboxError("OUTBOX_LATEST_TASK_PROJECT_MISMATCH")
    allowed = set(_declared_output_paths(row)) | set(_control_paths(task))
    illegal = [rel for rel in publish_paths if rel not in allowed]
    if illegal:
        raise CompletionOutboxError("OUTBOX_PATH_NOT_TASK_OWNED: " + ",".join(illegal))
    if done_rel not in publish_paths or f"coordination/quality/durability/{task}.json" not in publish_paths:
        raise CompletionOutboxError("OUTBOX_COMPLETION_CONTROL_PATHS_MISSING")

    lock = _kv_at(root, base, lock_rel)
    if not lock:
        raise CompletionOutboxError("OUTBOX_CURRENT_LOCK_MISSING")
    if is_stale(lock):
        raise CompletionOutboxError("OUTBOX_CURRENT_LEASE_EXPIRED")
    checks = {
        "CanonicalID": (lock.get("CanonicalID", ""), task),
        "ProjectID": (lock.get("ProjectID", ""), project),
        "AgentID": (lock.get("AgentID", ""), agent),
        "GrantID": (lock.get("GrantID", ""), grant_id),
        "LeaseGeneration": (lock.get("LeaseGeneration", ""), str(manifest.get("lease_generation") or "")),
        "LeaseToken": (lock.get("LeaseToken", ""), str(manifest.get("lease_token") or "")),
        "FencingToken": (lock.get("FencingToken", ""), str(manifest.get("fencing_token") or "")),
        "GrantPath": (lock.get("GrantPath", ""), grant_rel),
    }
    mismatch = [name for name, pair in checks.items() if not pair[0] or pair[0] != pair[1]]
    if mismatch:
        raise CompletionOutboxError("OUTBOX_FENCED: " + ",".join(mismatch))

    grant = _kv_at(root, base, grant_rel)
    grant_checks = {
        "CanonicalID": (grant.get("CanonicalID", ""), task),
        "ProjectID": (grant.get("ProjectID", ""), project),
        "AgentID": (grant.get("AgentID", ""), agent),
        "GrantID": (grant.get("GrantID", ""), grant_id),
        "LeaseGeneration": (grant.get("LeaseGeneration", ""), str(manifest.get("lease_generation") or "")),
        "LeaseToken": (grant.get("LeaseToken", ""), str(manifest.get("lease_token") or "")),
    }
    grant_bad = [name for name, pair in grant_checks.items() if not pair[0] or pair[0] != pair[1]]
    if grant_bad:
        raise CompletionOutboxError("OUTBOX_GRANT_MISMATCH: " + ",".join(grant_bad))

    expected = manifest.get("expected_base_objects")
    if not isinstance(expected, dict):
        raise CompletionOutboxError("OUTBOX_READ_SET_MISSING")
    for rel in publish_paths:
        if rel not in expected:
            raise CompletionOutboxError(f"OUTBOX_READ_SET_PATH_MISSING: {rel}")
        expected_obj = expected.get(rel)
        actual = _tree_object(root, base, rel)
        candidate_obj = _tree_object(root, commit, rel)
        if candidate_obj is None:
            raise CompletionOutboxError(f"OUTBOX_CANDIDATE_PATH_MISSING: {rel}")
        if actual == candidate_obj:
            continue
        if actual != expected_obj:
            raise CompletionOutboxError(
                f"OUTBOX_BASE_OBJECT_CONFLICT: {rel} expected={expected_obj or 'ABSENT'} actual={actual or 'ABSENT'}"
            )

    receipt = _safe_rel(str(manifest.get("receipt_path") or receipt_path(request_id)))
    if _tree_object(root, base, receipt) is not None:
        raise CompletionOutboxError("OUTBOX_ALREADY_INGESTED")
    return Candidate(request_id, ref_name, commit, manifest, publish_paths)


def _collect(root: Path, base: str, remote: str, max_batch: int) -> tuple[list[Candidate], list[str]]:
    staged: list[tuple[str, str, str]] = []
    for ref_name, commit in _list_outbox_refs(root, remote):
        manifest = _json_at(root, commit, MANIFEST_PATH) or {}
        staged.append((str(manifest.get("requested_at") or ""), ref_name, commit))

    accepted: list[Candidate] = []
    messages: list[str] = []
    occupied: set[str] = set()
    for _requested, ref_name, commit in sorted(staged):
        if len(accepted) >= max_batch:
            break
        try:
            candidate = _validate_candidate(root, base, ref_name, commit)
        except Exception as exc:
            reason = str(exc)
            if "OUTBOX_ALREADY_INGESTED" not in reason and "OUTBOX_ALREADY_COMPLETED" not in reason:
                messages.append(f"SKIP {ref_name}: {reason}")
            continue
        overlap = sorted(occupied & set(candidate.publish_paths))
        if overlap:
            messages.append(f"SKIP {ref_name}: OUTBOX_BATCH_PATH_CONFLICT paths={';'.join(overlap)}")
            continue
        occupied.update(candidate.publish_paths)
        accepted.append(candidate)
    return accepted, messages


def _checkout_candidate_paths(root: Path, worktree: Path, candidate: Candidate) -> None:
    for rel in candidate.publish_paths:
        proc = git(["checkout", candidate.commit, "--", rel], cwd=worktree, check=False)
        if proc.returncode:
            raise CompletionOutboxError(
                f"OUTBOX_APPLY_FAILED {candidate.request_id} {rel}: {proc.stderr.strip() or proc.stdout.strip()}"
            )


def _write_receipt(worktree: Path, candidate: Candidate, *, batch_id: str, batch_size: int) -> str:
    rel = receipt_path(candidate.request_id)
    path = worktree / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = candidate.manifest
    payload = {
        "schema": "UOS_COMPLETION_OUTBOX_RECEIPT_V1",
        "status": "INGESTED",
        "request_id": candidate.request_id,
        "task_id": manifest.get("task_id"),
        "project_id": manifest.get("project_id"),
        "agent_id": manifest.get("agent_id"),
        "grant_id": manifest.get("grant_id"),
        "lease_generation": manifest.get("lease_generation"),
        "candidate_ref": candidate.ref_name,
        "candidate_commit": candidate.commit,
        "ingested_at": iso(),
        "batch_id": batch_id,
        "batch_size": batch_size,
        "publish_paths": candidate.publish_paths,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rel


def ingest(
    root: Path,
    *,
    remote: str = "origin",
    branch: str = "main",
    max_batch: int = 16,
    retries: int = 8,
    dry_run: bool = False,
) -> dict[str, Any]:
    if max_batch < 1 or max_batch > 128:
        raise CompletionOutboxError("max_batch must be 1..128")
    if retries < 1 or retries > 50:
        raise CompletionOutboxError("retries must be 1..50")
    verify_identity(root, remote, branch)
    remote_ref = f"refs/remotes/{remote}/{branch}"
    target_ref = f"refs/heads/{branch}"

    for attempt in range(1, retries + 1):
        git(["fetch", "--quiet", remote, branch], cwd=root)
        _fetch_outbox_refs(root, remote)
        base = git(["rev-parse", remote_ref], cwd=root).stdout.strip()
        candidates, messages = _collect(root, base, remote, max_batch)
        if not candidates:
            return {
                "status": "OUTBOX_INGEST_NOOP",
                "base_main": base,
                "accepted": 0,
                "messages": messages,
            }
        if dry_run:
            return {
                "status": "OUTBOX_INGEST_DRY_RUN",
                "base_main": base,
                "accepted": len(candidates),
                "requests": [item.request_id for item in candidates],
                "messages": messages,
            }

        worktree = Path(tempfile.mkdtemp(prefix="uos-outbox-ingest-worktree-"))
        added = False
        try:
            proc = git(["worktree", "add", "--detach", "--force", str(worktree), base], cwd=root, check=False)
            if proc.returncode:
                raise CompletionOutboxError("OUTBOX_WORKTREE_CREATE_FAILED: " + (proc.stderr.strip() or proc.stdout.strip()))
            added = True
            batch_id = f"OBX-{base[:10]}-{attempt}-{len(candidates)}"
            receipts: list[str] = []
            for candidate in candidates:
                _checkout_candidate_paths(root, worktree, candidate)
                lock_rel = str(candidate.manifest["lock_path"])
                lock_path = worktree / lock_rel
                if not lock_path.exists():
                    raise CompletionOutboxError(f"OUTBOX_LOCK_DISAPPEARED_IN_BATCH: {lock_rel}")
                lock_path.unlink()
                receipts.append(_write_receipt(worktree, candidate, batch_id=batch_id, batch_size=len(candidates)))

            # Runtime views are derived from the latest base plus this whole batch,
            # never copied from stale completion candidates.
            env = os.environ.copy()
            env["UOS_INTERNAL_LOCAL"] = "1"
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            reconcile = subprocess.run(
                [sys.executable, str(worktree / "tools/uos.py"), "--transport", "local", "reconcile"],
                cwd=worktree,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if reconcile.returncode:
                raise CompletionOutboxError("OUTBOX_RECONCILE_FAILED: " + (reconcile.stderr.strip() or reconcile.stdout.strip()))

            git(["add", "-A", "-f"], cwd=worktree)
            tree = git(["write-tree"], cwd=worktree).stdout.strip()
            base_tree = git(["rev-parse", f"{base}^{{tree}}"], cwd=worktree).stdout.strip()
            if tree == base_tree:
                return {"status": "OUTBOX_INGEST_NOOP", "base_main": base, "accepted": 0, "messages": messages}
            commit = git(
                ["commit-tree", tree, "-p", base, "-m", f"chore: ingest UOS completion outbox batch ({len(candidates)})"],
                cwd=worktree,
            ).stdout.strip()
            push = git(["push", "--porcelain", remote, f"{commit}:{target_ref}"], cwd=root, check=False)
            if push.returncode == 0:
                git(["fetch", "--quiet", remote, branch], cwd=root, check=False)
                return {
                    "status": "OUTBOX_INGESTED",
                    "canonical_commit": commit,
                    "base_main": base,
                    "batch_size": len(candidates),
                    "requests": [item.request_id for item in candidates],
                    "receipts": receipts,
                    "attempt": attempt,
                    "messages": messages,
                }
            if not is_ref_race(push):
                raise CompletionOutboxError("OUTBOX_MAIN_PUSH_FAILED: " + (push.stderr.strip() or push.stdout.strip()))
            if attempt == retries:
                raise CompletionOutboxError("OUTBOX_MAIN_REF_RACE_RETRY_EXHAUSTED")
        finally:
            if added:
                git(["worktree", "remove", "--force", str(worktree)], cwd=root, check=False)
            shutil.rmtree(worktree, ignore_errors=True)
            git(["worktree", "prune"], cwd=root, check=False)
        time.sleep(min(0.05 * attempt + random.random() * 0.08, 0.6))

    raise CompletionOutboxError("unreachable")


def _percentile(values: Iterable[int], q: float) -> int | None:
    seq = sorted(int(value) for value in values)
    if not seq:
        return None
    if len(seq) == 1:
        return seq[0]
    pos = (len(seq) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return seq[lo]
    return round(seq[lo] + (seq[hi] - seq[lo]) * (pos - lo))


def _parse_observation_time(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def status(root: Path, *, remote: str = "origin", branch: str = "main") -> dict[str, Any]:
    """Return read-only queue + historical integration metrics.

    Outbox refs are intentionally retained as audit/recovery evidence. Therefore
    ``remote_refs_total`` is historical staged refs, while ``valid_queue_depth``
    is the current mechanically ingestible queue. Canonical receipts are the
    authoritative count of completed integrations.
    """
    verify_identity(root, remote, branch)
    git(["fetch", "--quiet", remote, branch], cwd=root)
    _fetch_outbox_refs(root, remote)
    base = git(["rev-parse", f"refs/remotes/{remote}/{branch}"], cwd=root).stdout.strip()
    refs = _list_outbox_refs(root, remote)
    valid, messages = _collect(root, base, remote, 128)

    manifests: dict[str, dict[str, Any]] = {}
    for ref_name, commit in refs:
        manifest = _json_at(root, commit, MANIFEST_PATH) or {}
        request_id = str(manifest.get("request_id") or "")
        if request_id:
            manifests[request_id] = manifest

    receipt_names = git(
        ["ls-tree", "-r", "--name-only", base, RECEIPT_ROOT],
        cwd=root,
        check=False,
    ).stdout.splitlines()
    receipts: list[dict[str, Any]] = []
    for rel in receipt_names:
        if not rel.endswith(".json"):
            continue
        item = _json_at(root, base, rel)
        if item and item.get("schema") == "UOS_COMPLETION_OUTBOX_RECEIPT_V1":
            receipts.append(item)

    receipt_ids = {str(item.get("request_id") or "") for item in receipts}
    retained_ingested = sum(1 for request_id in manifests if request_id in receipt_ids)
    invalid_uningested = max(0, len(refs) - len(valid) - retained_ingested)

    batches: dict[str, int] = {}
    waits: list[int] = []
    for item in receipts:
        batch_id = str(item.get("batch_id") or "")
        try:
            batch_size = int(item.get("batch_size") or 0)
        except Exception:
            batch_size = 0
        if batch_id and batch_size > 0:
            batches.setdefault(batch_id, batch_size)
        request_id = str(item.get("request_id") or "")
        manifest = manifests.get(request_id)
        if not manifest:
            continue
        requested = _parse_observation_time(manifest.get("requested_at"))
        ingested = _parse_observation_time(item.get("ingested_at"))
        if requested and ingested:
            waits.append(max(0, round((ingested - requested).total_seconds() * 1000)))

    batch_sizes = list(batches.values())
    return {
        "status": "OUTBOX_STATUS",
        "canonical_main": base,
        "remote_refs_total": len(refs),
        "valid_queue_depth": len(valid),
        "valid_requests": [item.request_id for item in valid],
        "canonical_receipts_total": len(receipts),
        "retained_ingested_refs": retained_ingested,
        "invalid_or_fenced_uningested_refs": invalid_uningested,
        "batch_count": len(batches),
        "batch_size_p50": _percentile(batch_sizes, 0.50),
        "batch_size_p95": _percentile(batch_sizes, 0.95),
        "batch_size_max": max(batch_sizes) if batch_sizes else 0,
        "integration_wait_ms_p50": _percentile(waits, 0.50),
        "integration_wait_ms_p95": _percentile(waits, 0.95),
        "integration_wait_ms_max": max(waits) if waits else 0,
        "skipped_count": len(messages),
        "skipped": messages,
    }


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="UOS mechanical completion Outbox / Integration Lane")
    p.add_argument("--remote", default="origin")
    p.add_argument("--target-branch", default="main")
    sub = p.add_subparsers(dest="command", required=True)
    ingest_p = sub.add_parser("ingest")
    ingest_p.add_argument("--max-batch", type=int, default=16)
    ingest_p.add_argument("--retries", type=int, default=8)
    ingest_p.add_argument("--dry-run", action="store_true")
    sub.add_parser("status")
    return p


def main() -> int:
    args = _parser().parse_args()
    root_proc = git(["rev-parse", "--show-toplevel"], cwd=Path.cwd(), check=False)
    if root_proc.returncode:
        print("UOS_OUTBOX_ERROR: run inside a Git repository", file=sys.stderr)
        return 2
    root = Path(root_proc.stdout.strip()).resolve()
    try:
        if args.command == "status":
            result = status(root, remote=args.remote, branch=args.target_branch)
        else:
            result = ingest(
                root,
                remote=args.remote,
                branch=args.target_branch,
                max_batch=args.max_batch,
                retries=args.retries,
                dry_run=args.dry_run,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (CompletionOutboxError, PublishError, ClaimBrokerError) as exc:
        print(f"UOS_OUTBOX_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
