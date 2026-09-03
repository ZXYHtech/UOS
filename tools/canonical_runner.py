#!/usr/bin/env python3
"""Run UOS lifecycle commands as latest-canonical Git transactions.

This is the integration layer between the local deterministic `tools/uos.py`
state machine and Git's canonical ref arbitration. Each attempt gets a fresh
snapshot of canonical main, runs the local state machine in an isolated detached
worktree, and publishes the resulting tree with a normal non-force push.

A ref race never reparents stale derived state. The whole UOS command is rerun
from the newer canonical snapshot.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

try:
    from canonical_publish import PublishError, git, is_ref_race, verify_identity
    from quality_gate import (
        QualityGateError,
        claim_block_packet,
        completion_paths,
        event_path,
        load_policy,
        presentation_packet,
        project_operator_warmup_satisfied,
        record_completion,
        rewrite_task_publish_args,
    )
except ModuleNotFoundError:
    from tools.canonical_publish import PublishError, git, is_ref_race, verify_identity
    from tools.quality_gate import (
        QualityGateError,
        claim_block_packet,
        completion_paths,
        event_path,
        load_policy,
        presentation_packet,
        project_operator_warmup_satisfied,
        record_completion,
        rewrite_task_publish_args,
    )


class CanonicalRunError(RuntimeError):
    pass


def git_repository(root: Path) -> bool:
    proc = git(["rev-parse", "--git-dir"], cwd=root, check=False)
    return proc.returncode == 0


def remote_exists(root: Path, remote: str) -> bool:
    proc = git(["remote", "get-url", remote], cwd=root, check=False)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def resolve_transport(root: Path, requested: str, remote: str, branch: str) -> str:
    """Resolve auto transport without unsafe network-failure fallback."""
    if os.environ.get("UOS_INTERNAL_LOCAL") == "1":
        return "local"
    requested = (requested or "auto").lower()
    if requested not in {"auto", "local", "git-cas"}:
        raise CanonicalRunError(f"unknown transport: {requested}")
    if requested == "local":
        return "local"
    if not git_repository(root):
        if requested == "git-cas":
            raise CanonicalRunError("git-cas transport requires a Git repository")
        return "local"
    if not remote_exists(root, remote):
        if requested == "git-cas":
            raise CanonicalRunError(f"git-cas transport requires remote {remote!r}")
        return "local"
    try:
        verify_identity(root, remote, branch)
    except PublishError as exc:
        raise CanonicalRunError(str(exc)) from exc
    return "git-cas"


def strip_transport_args(argv: list[str]) -> list[str]:
    names = {"--transport", "--remote", "--target-branch", "--cas-retries"}
    out: list[str] = []
    index = 0
    while index < len(argv):
        item = argv[index]
        matched_equals = next((name for name in names if item.startswith(name + "=")), None)
        if matched_equals:
            index += 1
            continue
        if item in names:
            if index + 1 >= len(argv):
                raise CanonicalRunError(f"{item} requires a value")
            index += 2
            continue
        out.append(item)
        index += 1
    return out


def extract_execution_ack(argv: list[str]) -> tuple[str, list[str]]:
    """Remove the global Epoch ack while preserving the business command shape.

    Quality/preview helpers intentionally receive argv beginning with
    `task`, `claim`, `complete`, etc. The ack is reinserted only when the
    isolated local state machine is invoked.
    """
    out: list[str] = []
    ack = ""
    index = 0
    while index < len(argv):
        item = argv[index]
        if item == "--ack-execution-epoch":
            if index + 1 >= len(argv):
                raise CanonicalRunError("--ack-execution-epoch requires a value")
            ack = argv[index + 1]
            index += 2
            continue
        if item.startswith("--ack-execution-epoch="):
            ack = item.split("=", 1)[1]
            index += 1
            continue
        out.append(item)
        index += 1
    return ack, out


def option_value(argv: list[str], name: str) -> str:
    for index, item in enumerate(argv):
        if item == name and index + 1 < len(argv):
            return argv[index + 1]
        if item.startswith(name + "="):
            return item.split("=", 1)[1]
    return ""


def _safe_rel(value: str) -> str:
    raw = (value or "").strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CanonicalRunError(f"repository path escape: {value!r}")
    return str(path)


def _declared_task_outputs(snapshot: Path, task_id: str) -> list[str]:
    base = snapshot / "orchestration/projects"
    if not base.exists():
        raise CanonicalRunError(f"unknown task: {task_id}")
    for catalog in sorted(base.glob("*/TASK_CATALOG.csv")):
        with catalog.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("id") == task_id:
                    return [_safe_rel(item) for item in (row.get("output") or "").split(";") if item.strip()]
    raise CanonicalRunError(f"unknown task: {task_id}")


def _task_project(snapshot: Path, task_id: str) -> str:
    if not task_id:
        return ""
    base = snapshot / "orchestration/projects"
    if not base.exists():
        return ""
    for catalog in sorted(base.glob("*/TASK_CATALOG.csv")):
        with catalog.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("id") == task_id:
                    return str(row.get("project_id") or "")
    return ""


def _claim_project(snapshot: Path, local_argv: list[str]) -> str:
    project = option_value(local_argv, "--project")
    if project:
        return project
    return _task_project(snapshot, option_value(local_argv, "--task"))


def _parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip().strip('"')
    return out


def _update_kv(path: Path, updates: dict[str, object]) -> None:
    if not path.exists():
        raise CanonicalRunError(f"ownership file missing: {path}")
    pending = {str(k): str(v) for k, v in updates.items()}
    output: list[str] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in raw or raw.lstrip().startswith("#"):
            output.append(raw)
            continue
        key, _value = raw.split(":", 1)
        name = key.strip()
        if name in pending:
            output.append(f"{name}: {pending.pop(name)}")
        else:
            output.append(raw)
    output.extend(f"{key}: {value}" for key, value in pending.items())
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def _write_grant(path: Path, values: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise CanonicalRunError(f"immutable Grant already exists: {path}")
    path.write_text("".join(f"{key}: {value}\n" for key, value in values.items()), encoding="utf-8")



def _ownership_git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _write_immutable_request(path: Path, values: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise CanonicalRunError(f"immutable Claim Request already exists: {path}")
    path.write_text("".join(f"{key}: {value}\n" for key, value in values.items()), encoding="utf-8")


def _grant_integrity_block(snapshot: Path, local_argv: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Fail closed for new Grant-backed renew/complete; allow legacy locks."""
    if not local_argv or local_argv[0] not in {"renew", "complete"}:
        return None
    task_id = option_value(local_argv, "--task")
    if not task_id:
        return None
    lock_path = snapshot / "coordination/claims" / f"{task_id}.lock"
    lock = _parse_kv(lock_path)
    if not lock:
        return None  # normal local lifecycle code will emit the canonical error
    grant_rel = (lock.get("GrantPath") or "").strip()
    if not grant_rel:
        return None  # LEGACY_LOCK_ONLY compatibility for in-flight pre-Phase-2 claims
    try:
        grant_rel = _safe_rel(grant_rel)
    except CanonicalRunError as exc:
        packet = {"status": "GRANT_INTEGRITY_BLOCKED", "task": task_id, "reason": str(exc)}
        return subprocess.CompletedProcess(local_argv, 2, json.dumps(packet, ensure_ascii=False, indent=2) + "\n", "")
    if not grant_rel.startswith("coordination/claim_grants/"):
        packet = {"status": "GRANT_INTEGRITY_BLOCKED", "task": task_id, "reason": "GrantPath outside claim_grants"}
        return subprocess.CompletedProcess(local_argv, 2, json.dumps(packet, ensure_ascii=False, indent=2) + "\n", "")
    grant_path = snapshot / grant_rel
    grant = _parse_kv(grant_path)
    checks = {
        "CanonicalID": (lock.get("CanonicalID", ""), grant.get("CanonicalID", "")),
        "AgentID": (lock.get("AgentID", ""), grant.get("AgentID", "")),
        "LeaseGeneration": (lock.get("LeaseGeneration", ""), grant.get("LeaseGeneration", "")),
        "LeaseToken": (lock.get("LeaseToken", ""), grant.get("LeaseToken", "")),
        "GrantID": (lock.get("GrantID", ""), grant.get("GrantID", "")),
    }
    requested_agent = option_value(local_argv, "--agent-id")
    requested_token = option_value(local_argv, "--lease-token")
    if requested_agent:
        checks["RequestedAgentID"] = (requested_agent, grant.get("AgentID", ""))
    if requested_token:
        checks["RequestedLeaseToken"] = (requested_token, grant.get("LeaseToken", ""))
    bad = [name for name, pair in checks.items() if not pair[1] or pair[0] != pair[1]]
    if bad:
        packet = {
            "status": "GRANT_INTEGRITY_BLOCKED",
            "task": task_id,
            "grant_path": grant_rel,
            "reason": "lock/grant/request mismatch",
            "mismatch_fields": bad,
        }
        return subprocess.CompletedProcess(local_argv, 2, json.dumps(packet, ensure_ascii=False, indent=2) + "\n", "")
    return None


def _decorate_claim_grant(
    proc: subprocess.CompletedProcess[str],
    snapshot: Path,
    local_argv: list[str],
    execution_ack: str,
    prior_lock: dict[str, str] | None = None,
    prior_lock_blob_sha: str = "",
) -> subprocess.CompletedProcess[str]:
    """Create immutable Grant and decorate Lock in the same canonical Claim tree."""
    if not local_argv or local_argv[0] != "claim" or proc.returncode != 0:
        return proc
    try:
        packet = json.loads(proc.stdout or "{}")
    except Exception as exc:
        return subprocess.CompletedProcess(proc.args, 2, "", f"UOS_GRANT_ERROR: invalid claim response: {exc}\n")
    if not isinstance(packet, dict):
        return subprocess.CompletedProcess(proc.args, 2, "", "UOS_GRANT_ERROR: claim response is not an object\n")
    # Broker V2 already wrote Request + Grant + Lock inside the local state
    # mutation. The canonical runner now only publishes that whole tree via CAS.
    if packet.get("GrantPath") and packet.get("RequestPath"):
        return proc
    task_id = str(packet.get("CanonicalID") or option_value(local_argv, "--task") or "")
    agent_id = str(packet.get("AgentID") or option_value(local_argv, "--agent-id") or "")
    generation = str(packet.get("LeaseGeneration") or "")
    token = str(packet.get("LeaseToken") or "")
    if not task_id or not agent_id or not generation or not token:
        return subprocess.CompletedProcess(proc.args, 2, "", "UOS_GRANT_ERROR: incomplete ownership fields\n")
    lock_path = snapshot / "coordination/claims" / f"{task_id}.lock"
    lock = _parse_kv(lock_path)
    if (
        lock.get("AgentID") != agent_id
        or lock.get("LeaseGeneration") != generation
        or lock.get("LeaseToken") != token
    ):
        return subprocess.CompletedProcess(proc.args, 2, "", "UOS_GRANT_ERROR: canonical lock differs from claim response\n")

    suffix = token[:12]
    request_id = f"REQ-{task_id}-G{generation}-{suffix}"
    grant_id = f"GRANT-{task_id}-G{generation}-{suffix}"
    request_rel = f"coordination/claim_requests/{agent_id}/{request_id}.request"
    request_path = snapshot / request_rel
    grant_rel = f"coordination/claim_grants/{agent_id}/{request_id}.grant"
    grant_path = snapshot / grant_rel
    claim_rel = f"coordination/claims/{task_id}.lock"
    done_rel = f"coordination/completed/{task_id}.done"
    authority = "UOS_CANONICAL_RUNNER_GRANT_V1"
    generation_int = int(generation)
    claim_mode = "RECLAIM" if generation_int > 1 else "CREATE"
    previous = prior_lock or {}
    if claim_mode == "RECLAIM":
        previous_generation = int(previous.get("LeaseGeneration") or 0)
        if not previous or previous_generation != generation_int - 1:
            return subprocess.CompletedProcess(
                proc.args, 2, "",
                "UOS_GRANT_ERROR: reclaim generation lacks exact prior canonical lock provenance\n",
            )
        if not prior_lock_blob_sha:
            return subprocess.CompletedProcess(
                proc.args, 2, "",
                "UOS_GRANT_ERROR: reclaim missing prior lock Git blob SHA\n",
            )

    request = {
        "Schema": "UOS_CLAIM_REQUEST_V1",
        "Status": "PROCESSED",
        "RequestID": request_id,
        "AgentID": agent_id,
        "CanonicalID": task_id,
        "ProjectID": packet.get("ProjectID", lock.get("ProjectID", "")),
        "RequestedAt": packet.get("ClaimedAt", lock.get("ClaimedAt", "")),
        "Mode": claim_mode,
        "ExecutionEpoch": execution_ack,
        "LeaseMinutes": option_value(local_argv, "--lease-minutes") or "90",
        "ExpectedPriorLockGitBlobSHA": prior_lock_blob_sha if claim_mode == "RECLAIM" else "",
        "ExpectedPriorAgentID": previous.get("AgentID", "") if claim_mode == "RECLAIM" else "",
        "ExpectedPriorLeaseGeneration": previous.get("LeaseGeneration", "") if claim_mode == "RECLAIM" else "",
        "ExpectedPriorLeaseToken": previous.get("LeaseToken", "") if claim_mode == "RECLAIM" else "",
        "Decision": "GRANTED",
        "GrantID": grant_id,
        "GrantPath": grant_rel,
        "ClaimPath": claim_rel,
    }
    _write_immutable_request(request_path, request)
    grant = {
        "Schema": "UOS_CLAIM_GRANT_V1",
        "Status": "GRANTED",
        "RequestID": request_id,
        "GrantID": grant_id,
        "CanonicalID": task_id,
        "ProjectID": packet.get("ProjectID", lock.get("ProjectID", "")),
        "AgentID": agent_id,
        "GrantedAt": packet.get("ClaimedAt", lock.get("ClaimedAt", "")),
        "ClaimPath": claim_rel,
        "DonePath": done_rel,
        "GrantPath": grant_rel,
        "RequestPath": request_rel,
        "ClaimAuthority": authority,
        "ClaimMode": claim_mode,
        "LeaseGeneration": generation,
        "LeaseToken": token,
        "LeaseExpiresAt": packet.get("LeaseExpiresAt", lock.get("LeaseExpiresAt", "")),
        "FencingToken": packet.get("FencingToken", lock.get("FencingToken", "")),
        "ExecutionEpoch": execution_ack,
        "Inputs": packet.get("Inputs", ""),
        "Output": packet.get("Output", ""),
        "Acceptance": packet.get("Acceptance", ""),
        "Ownership": "ACTIVE_CANONICAL_CLAIM_WITH_IMMUTABLE_GRANT",
        "OwnershipCheckpoint": f"AgentID={agent_id};Generation={generation};Token={token}",
        "PreviousAgentID": previous.get("AgentID", "") if claim_mode == "RECLAIM" else "",
        "PreviousLeaseGeneration": previous.get("LeaseGeneration", "") if claim_mode == "RECLAIM" else "",
        "PreviousLeaseToken": previous.get("LeaseToken", "") if claim_mode == "RECLAIM" else "",
        "PreviousGrantID": previous.get("GrantID", "") if claim_mode == "RECLAIM" else "",
        "PreviousGrantPath": previous.get("GrantPath", "") if claim_mode == "RECLAIM" else "",
        "ReclaimedFromLockGitBlobSHA": prior_lock_blob_sha if claim_mode == "RECLAIM" else "",
    }
    _write_grant(grant_path, grant)
    _update_kv(lock_path, {
        "ClaimAuthority": authority,
        "GrantID": grant_id,
        "GrantPath": grant_rel,
        "RequestPath": request_rel,
        "ClaimMode": claim_mode,
        "PreviousAgentID": previous.get("AgentID", "") if claim_mode == "RECLAIM" else "",
        "PreviousLeaseGeneration": previous.get("LeaseGeneration", "") if claim_mode == "RECLAIM" else "",
        "PreviousLeaseToken": previous.get("LeaseToken", "") if claim_mode == "RECLAIM" else "",
        "PreviousGrantID": previous.get("GrantID", "") if claim_mode == "RECLAIM" else "",
        "PreviousGrantPath": previous.get("GrantPath", "") if claim_mode == "RECLAIM" else "",
        "ReclaimedFromLockGitBlobSHA": prior_lock_blob_sha if claim_mode == "RECLAIM" else "",
        "FencingRequired": "YES",
        "ExecutionEpoch": execution_ack,
    })
    packet.update({
        "RequestID": request_id,
        "RequestPath": request_rel,
        "ClaimMode": claim_mode,
        "GrantID": grant_id,
        "GrantPath": grant_rel,
        "ClaimAuthority": authority,
        "OwnershipCheckpoint": grant["OwnershipCheckpoint"],
    })
    return subprocess.CompletedProcess(
        args=proc.args,
        returncode=0,
        stdout=json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        stderr=proc.stderr,
    )


def _task_outputs(snapshot: Path, task_id: str) -> list[str]:
    if load_policy(snapshot)["enabled"]:
        try:
            paths, _previews = completion_paths(snapshot, task_id)
            return paths
        except QualityGateError as exc:
            raise CanonicalRunError(str(exc)) from exc
    return _declared_task_outputs(snapshot, task_id)


def _tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(b"L\0" + os.readlink(path).encode("utf-8", errors="surrogateescape"))
        return digest.hexdigest()
    if path.is_file():
        digest.update(b"F\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    if path.is_dir():
        digest.update(b"D\0")
        for child in sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix()):
            rel = child.relative_to(path).as_posix().encode()
            digest.update(rel + b"\0" + _tree_digest(child).encode() + b"\0")
        return digest.hexdigest()
    return "ABSENT"


def _copy_one(source: Path, target: Path, *, allow_replace: bool = False) -> None:
    if target.exists() or target.is_symlink():
        if _tree_digest(source) == _tree_digest(target):
            return
        if not allow_replace:
            raise CanonicalRunError(
                f"TARGET_PATH_CONFLICT: canonical output differs from caller output: {target}"
            )
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        target.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target)


def _review_rejected(snapshot: Path, task_id: str) -> bool:
    path = event_path(snapshot, task_id)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("review_status", "")).upper() == "REJECTED"
    except Exception:
        return False


def prepare_caller_artifacts(caller_root: Path, snapshot: Path, argv: list[str]) -> None:
    if not argv or argv[0] != "complete":
        return
    task_id = option_value(argv, "--task")
    if not task_id:
        raise CanonicalRunError("complete requires --task")
    allow_replace = _review_rejected(snapshot, task_id)
    for rel in _task_outputs(snapshot, task_id):
        source = caller_root / rel
        if source.exists() or source.is_symlink():
            _copy_one(source, snapshot / rel, allow_replace=allow_replace)


def _canonical_message(argv: list[str]) -> str:
    if not argv:
        return "UOS canonical transaction"
    command = " ".join(argv[:2]) if argv[0] in {"project", "task"} and len(argv) > 1 else argv[0]
    task = option_value(argv, "--task") or option_value(argv, "--task-id")
    project = option_value(argv, "--project") or option_value(argv, "--project-id")
    suffix = task or project
    return f"uos {command}{' ' + suffix if suffix else ''} [canonical]"


def _candidate_from_worktree(snapshot: Path, base: str, message: str) -> str | None:
    status = git(["status", "--porcelain", "--untracked-files=all"], cwd=snapshot).stdout
    if not status.strip():
        return None
    git(["add", "-A", "-f"], cwd=snapshot)
    tree = git(["write-tree"], cwd=snapshot).stdout.strip()
    base_tree = git(["rev-parse", f"{base}^{{tree}}"], cwd=snapshot).stdout.strip()
    if tree == base_tree:
        return None
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "UOS Canonical Runner",
            "GIT_AUTHOR_EMAIL": "uos@example.invalid",
            "GIT_COMMITTER_NAME": "UOS Canonical Runner",
            "GIT_COMMITTER_EMAIL": "uos@example.invalid",
        }
    )
    return git(["commit-tree", tree, "-p", base, "-m", message], cwd=snapshot, env=env).stdout.strip()


def _policy_int(snapshot: Path, key: str, default: int) -> int:
    path = snapshot / ".uos/QUALITY_VISIBILITY_POLICY.yaml"
    if not path.exists():
        return default
    prefix = key + ":"
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw.strip()
        if stripped.startswith(prefix):
            try:
                return int(stripped.split(":", 1)[1].strip())
            except ValueError:
                return default
    return default


def _epoch_events(snapshot: Path, epoch: int) -> list[dict[str, object]]:
    base = snapshot / "coordination/quality/events"
    out: list[dict[str, object]] = []
    if not base.exists():
        return out
    for path in sorted(base.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and int(data.get("rule_epoch", -1)) == epoch:
                out.append(data)
        except Exception:
            continue
    return out


def _warmup_serial_block(snapshot: Path, local_argv: list[str]) -> subprocess.CompletedProcess[str] | None:
    if not local_argv or local_argv[0] != "claim":
        return None
    policy = load_policy(snapshot)
    if not policy["enabled"] or policy["warmup"] <= 0:
        return None
    project = _claim_project(snapshot, local_argv)
    if project_operator_warmup_satisfied(snapshot, project):
        return None
    events = _epoch_events(snapshot, int(policy["rule_epoch"]))
    accepted = [
        item for item in events
        if int(item.get("sequence", 999999)) <= int(policy["warmup"])
        and str(item.get("review_status", "")).upper() == "ACCEPTED"
    ]
    if len(accepted) >= int(policy["warmup"]):
        return None

    max_claims = max(1, _policy_int(snapshot, "WarmupMaxConcurrentClaims", 1))
    claim_dir = snapshot / "coordination/claims"
    active_claims = sorted(claim_dir.glob("*.lock")) if claim_dir.exists() else []
    task_id = option_value(local_argv, "--task")
    if len(active_claims) < max_claims:
        return None
    if task_id and any(path.stem == task_id for path in active_claims):
        # Explicit same-task claim is allowed to reach the normal Lease/Fencing
        # logic, which is needed for stale reclaim and rejected-task correction.
        return None
    packet = {
        "status": "REVIEW_BLOCKED",
        "message": "RuleEpoch warmup is serialized: wait for the current task result to be shown and confirmed before starting another task.",
        "rule_epoch": policy["rule_epoch"],
        "warmup_required": policy["warmup"],
        "warmup_accepted": len(accepted),
        "active_claims": [path.stem for path in active_claims],
        "operator_instruction": "Show the current result in the conversation and obtain operator confirmation before the next new Claim.",
    }
    return subprocess.CompletedProcess(
        args=local_argv,
        returncode=6,
        stdout=json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        stderr="",
    )


def _quality_blocked_proc(local_argv: list[str], snapshot: Path) -> subprocess.CompletedProcess[str] | None:
    if not local_argv or local_argv[0] != "claim":
        return None
    project = _claim_project(snapshot, local_argv)
    task_id = option_value(local_argv, "--task")
    packet = claim_block_packet(snapshot, project, task_id)
    if packet is not None:
        return subprocess.CompletedProcess(
            args=local_argv,
            returncode=6,
            stdout=json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
            stderr="",
        )
    return _warmup_serial_block(snapshot, local_argv)


def _quality_complete_proc(proc: subprocess.CompletedProcess[str], snapshot: Path, local_argv: list[str]) -> subprocess.CompletedProcess[str]:
    if not local_argv or local_argv[0] != "complete" or proc.returncode != 0:
        return proc
    task_id = option_value(local_argv, "--task")
    if not task_id:
        return proc
    try:
        event = record_completion(snapshot, task_id)
    except QualityGateError as exc:
        return subprocess.CompletedProcess(
            args=proc.args,
            returncode=2,
            stdout="",
            stderr=f"UOS_QUALITY_ERROR: {exc}\n",
        )
    if not event:
        return proc
    original: dict[str, object] = {}
    try:
        parsed = json.loads(proc.stdout or "{}")
        if isinstance(parsed, dict):
            original = parsed
    except Exception:
        original = {"status": "DONE", "task": task_id}
    packet = presentation_packet(event, original)
    return subprocess.CompletedProcess(
        args=proc.args,
        returncode=proc.returncode,
        stdout=json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        stderr=proc.stderr,
    )


def run_canonical(
    caller_root: Path,
    argv: list[str],
    *,
    remote: str = "origin",
    branch: str = "main",
    retries: int = 8,
) -> subprocess.CompletedProcess[str]:
    if retries < 1 or retries > 50:
        raise CanonicalRunError("--cas-retries must be between 1 and 50")
    if not git_repository(caller_root) or not remote_exists(caller_root, remote):
        raise CanonicalRunError("canonical runner requires a Git repository with a configured remote")
    try:
        verify_identity(caller_root, remote, branch)
    except PublishError as exc:
        raise CanonicalRunError(str(exc)) from exc

    stripped_argv = strip_transport_args(argv)
    execution_ack, base_argv = extract_execution_ack(stripped_argv)
    target_ref = f"refs/heads/{branch}"
    remote_ref = f"refs/remotes/{remote}/{branch}"
    last_proc: subprocess.CompletedProcess[str] | None = None

    for attempt in range(1, retries + 1):
        fetch = git(["fetch", "--quiet", remote, branch], cwd=caller_root, check=False)
        if fetch.returncode:
            raise CanonicalRunError(
                f"CANONICAL_FETCH_FAILED: {fetch.stderr.strip() or fetch.stdout.strip()}"
            )
        base = git(["rev-parse", remote_ref], cwd=caller_root).stdout.strip()
        worktree = Path(tempfile.mkdtemp(prefix="uos-canonical-worktree-"))
        added = False
        try:
            add = git(["worktree", "add", "--detach", "--force", str(worktree), base], cwd=caller_root, check=False)
            if add.returncode:
                raise CanonicalRunError(
                    f"WORKTREE_CREATE_FAILED: {add.stderr.strip() or add.stdout.strip()}"
                )
            added = True

            local_argv = rewrite_task_publish_args(base_argv, worktree)
            blocked = _quality_blocked_proc(local_argv, worktree)
            if blocked is not None:
                return blocked

            integrity_block = _grant_integrity_block(worktree, local_argv)
            if integrity_block is not None:
                return integrity_block

            prepare_caller_artifacts(caller_root, worktree, local_argv)

            prior_claim_lock: dict[str, str] | None = None
            prior_claim_blob_sha = ""
            if local_argv and local_argv[0] == "claim":
                prior_task = option_value(local_argv, "--task")
                if prior_task:
                    prior_path = worktree / "coordination/claims" / f"{prior_task}.lock"
                    if prior_path.exists():
                        prior_claim_lock = _parse_kv(prior_path)
                        prior_claim_blob_sha = _ownership_git_blob_sha(prior_path)

            env = os.environ.copy()
            env["UOS_INTERNAL_LOCAL"] = "1"
            env["UOS_CALLER_ROOT"] = str(caller_root)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            local_globals = ["--transport", "local"]
            if execution_ack:
                local_globals.extend(["--ack-execution-epoch", execution_ack])
            proc = subprocess.run(
                [sys.executable, str(worktree / "tools/uos.py"), *local_globals, *local_argv],
                cwd=worktree,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            proc = _decorate_claim_grant(
                proc, worktree, local_argv, execution_ack,
                prior_lock=prior_claim_lock,
                prior_lock_blob_sha=prior_claim_blob_sha,
            )
            proc = _quality_complete_proc(proc, worktree, local_argv)
            last_proc = proc
            if proc.returncode != 0:
                return proc

            candidate = _candidate_from_worktree(worktree, base, _canonical_message(local_argv))
            if candidate is None:
                return proc

            test_delay = float(os.environ.get("UOS_CAS_TEST_DELAY_BEFORE_PUSH", "0") or "0")
            if test_delay > 0:
                time.sleep(test_delay)

            push = git(
                ["push", "--porcelain", remote, f"{candidate}:{target_ref}"],
                cwd=caller_root,
                check=False,
            )
            if push.returncode == 0:
                git(["fetch", "--quiet", remote, branch], cwd=caller_root, check=False)
                return proc
            if not is_ref_race(push):
                raise CanonicalRunError(
                    f"CANONICAL_PUSH_FAILED: {push.stderr.strip() or push.stdout.strip()}"
                )
            if attempt == retries:
                raise CanonicalRunError("CANONICAL_REF_RACE_RETRY_EXHAUSTED")
            time.sleep(random.uniform(0.02, 0.08) * attempt)
        finally:
            if added:
                git(["worktree", "remove", "--force", str(worktree)], cwd=caller_root, check=False)
            shutil.rmtree(worktree, ignore_errors=True)
            git(["worktree", "prune"], cwd=caller_root, check=False)

    if last_proc is not None:
        return last_proc
    raise CanonicalRunError("canonical transaction did not execute")
