#!/usr/bin/env python3
"""One-shot patcher: add Grant dual-anchor hooks to canonical_runner.py.

This script exists only to make the backport reviewable and reproducible. It is
idempotent and patches small stable anchors in the current standalone runner.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools/canonical_runner.py"
MARKER = "UOS_CANONICAL_RUNNER_GRANT_V1"

HELPERS = r'''

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
    grant_rel = f"coordination/claim_grants/{agent_id}/{request_id}.grant"
    grant_path = snapshot / grant_rel
    claim_rel = f"coordination/claims/{task_id}.lock"
    done_rel = f"coordination/completed/{task_id}.done"
    authority = "UOS_CANONICAL_RUNNER_GRANT_V1"
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
        "ClaimAuthority": authority,
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
    }
    _write_grant(grant_path, grant)
    _update_kv(lock_path, {
        "ClaimAuthority": authority,
        "GrantID": grant_id,
        "GrantPath": grant_rel,
        "FencingRequired": "YES",
        "ExecutionEpoch": execution_ack,
    })
    packet.update({
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
'''


def patch() -> bool:
    text = PATH.read_text(encoding="utf-8")
    if MARKER in text:
        print("phase2 grant patch already present")
        return False

    anchor = '''def _claim_project(snapshot: Path, local_argv: list[str]) -> str:\n    project = option_value(local_argv, "--project")\n    if project:\n        return project\n    return _task_project(snapshot, option_value(local_argv, "--task"))\n'''
    if anchor not in text:
        raise SystemExit("phase2 patch anchor _claim_project not found")
    text = text.replace(anchor, anchor + HELPERS, 1)

    blocked_anchor = '''            blocked = _quality_blocked_proc(local_argv, worktree)\n            if blocked is not None:\n                return blocked\n\n            prepare_caller_artifacts(caller_root, worktree, local_argv)\n'''
    blocked_replacement = '''            blocked = _quality_blocked_proc(local_argv, worktree)\n            if blocked is not None:\n                return blocked\n\n            integrity_block = _grant_integrity_block(worktree, local_argv)\n            if integrity_block is not None:\n                return integrity_block\n\n            prepare_caller_artifacts(caller_root, worktree, local_argv)\n'''
    if blocked_anchor not in text:
        raise SystemExit("phase2 patch anchor quality block not found")
    text = text.replace(blocked_anchor, blocked_replacement, 1)

    proc_anchor = '''            proc = _quality_complete_proc(proc, worktree, local_argv)\n            last_proc = proc\n            if proc.returncode != 0:\n                return proc\n'''
    proc_replacement = '''            proc = _decorate_claim_grant(proc, worktree, local_argv, execution_ack)\n            proc = _quality_complete_proc(proc, worktree, local_argv)\n            last_proc = proc\n            if proc.returncode != 0:\n                return proc\n'''
    if proc_anchor not in text:
        raise SystemExit("phase2 patch anchor subprocess result not found")
    text = text.replace(proc_anchor, proc_replacement, 1)

    PATH.write_text(text, encoding="utf-8")
    print("phase2 claim Grant hooks patched")
    return True


if __name__ == "__main__":
    patch()
