#!/usr/bin/env python3
"""Backport persistent Claim Request + reclaim provenance into canonical_runner.

Phase 3 is intentionally compatible with Phase-2 Grants and legacy lock-only
claims. Only new Claims gain a Request anchor and explicit CREATE/RECLAIM chain.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools/canonical_runner.py"
MARKER = "UOS_CLAIM_REQUEST_V1"


def patch() -> bool:
    text = PATH.read_text(encoding="utf-8")
    if MARKER in text:
        print("phase3 request/reclaim patch already present")
        return False

    # Add git-blob helper after _write_grant.
    anchor = '''def _write_grant(path: Path, values: dict[str, object]) -> None:\n    path.parent.mkdir(parents=True, exist_ok=True)\n    if path.exists():\n        raise CanonicalRunError(f"immutable Grant already exists: {path}")\n    path.write_text("".join(f"{key}: {value}\\n" for key, value in values.items()), encoding="utf-8")\n'''
    helper = r'''


def _ownership_git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _write_immutable_request(path: Path, values: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise CanonicalRunError(f"immutable Claim Request already exists: {path}")
    path.write_text("".join(f"{key}: {value}\n" for key, value in values.items()), encoding="utf-8")
'''
    if anchor not in text:
        raise SystemExit("phase3 anchor _write_grant not found")
    text = text.replace(anchor, anchor + helper, 1)

    # Extend decorate signature with prior snapshot ownership.
    old_sig = '''def _decorate_claim_grant(\n    proc: subprocess.CompletedProcess[str],\n    snapshot: Path,\n    local_argv: list[str],\n    execution_ack: str,\n) -> subprocess.CompletedProcess[str]:'''
    new_sig = '''def _decorate_claim_grant(\n    proc: subprocess.CompletedProcess[str],\n    snapshot: Path,\n    local_argv: list[str],\n    execution_ack: str,\n    prior_lock: dict[str, str] | None = None,\n    prior_lock_blob_sha: str = "",\n) -> subprocess.CompletedProcess[str]:'''
    if old_sig not in text:
        raise SystemExit("phase3 decorate signature anchor not found")
    text = text.replace(old_sig, new_sig, 1)

    # Inject Request / mode / reclaim checks immediately after IDs are derived.
    id_anchor = '''    suffix = token[:12]\n    request_id = f"REQ-{task_id}-G{generation}-{suffix}"\n    grant_id = f"GRANT-{task_id}-G{generation}-{suffix}"\n    grant_rel = f"coordination/claim_grants/{agent_id}/{request_id}.grant"\n    grant_path = snapshot / grant_rel\n    claim_rel = f"coordination/claims/{task_id}.lock"\n    done_rel = f"coordination/completed/{task_id}.done"\n    authority = "UOS_CANONICAL_RUNNER_GRANT_V1"\n'''
    id_replacement = '''    suffix = token[:12]\n    request_id = f"REQ-{task_id}-G{generation}-{suffix}"\n    grant_id = f"GRANT-{task_id}-G{generation}-{suffix}"\n    request_rel = f"coordination/claim_requests/{agent_id}/{request_id}.request"\n    request_path = snapshot / request_rel\n    grant_rel = f"coordination/claim_grants/{agent_id}/{request_id}.grant"\n    grant_path = snapshot / grant_rel\n    claim_rel = f"coordination/claims/{task_id}.lock"\n    done_rel = f"coordination/completed/{task_id}.done"\n    authority = "UOS_CANONICAL_RUNNER_GRANT_V1"\n    generation_int = int(generation)\n    claim_mode = "RECLAIM" if generation_int > 1 else "CREATE"\n    previous = prior_lock or {}\n    if claim_mode == "RECLAIM":\n        previous_generation = int(previous.get("LeaseGeneration") or 0)\n        if not previous or previous_generation != generation_int - 1:\n            return subprocess.CompletedProcess(\n                proc.args, 2, "",\n                "UOS_GRANT_ERROR: reclaim generation lacks exact prior canonical lock provenance\\n",\n            )\n        if not prior_lock_blob_sha:\n            return subprocess.CompletedProcess(\n                proc.args, 2, "",\n                "UOS_GRANT_ERROR: reclaim missing prior lock Git blob SHA\\n",\n            )\n\n    request = {\n        "Schema": "UOS_CLAIM_REQUEST_V1",\n        "Status": "PROCESSED",\n        "RequestID": request_id,\n        "AgentID": agent_id,\n        "CanonicalID": task_id,\n        "ProjectID": packet.get("ProjectID", lock.get("ProjectID", "")),\n        "RequestedAt": packet.get("ClaimedAt", lock.get("ClaimedAt", "")),\n        "Mode": claim_mode,\n        "ExecutionEpoch": execution_ack,\n        "LeaseMinutes": option_value(local_argv, "--lease-minutes") or "90",\n        "ExpectedPriorLockGitBlobSHA": prior_lock_blob_sha if claim_mode == "RECLAIM" else "",\n        "ExpectedPriorAgentID": previous.get("AgentID", "") if claim_mode == "RECLAIM" else "",\n        "ExpectedPriorLeaseGeneration": previous.get("LeaseGeneration", "") if claim_mode == "RECLAIM" else "",\n        "ExpectedPriorLeaseToken": previous.get("LeaseToken", "") if claim_mode == "RECLAIM" else "",\n        "Decision": "GRANTED",\n        "GrantID": grant_id,\n        "GrantPath": grant_rel,\n        "ClaimPath": claim_rel,\n    }\n    _write_immutable_request(request_path, request)\n'''
    if id_anchor not in text:
        raise SystemExit("phase3 ID anchor not found")
    text = text.replace(id_anchor, id_replacement, 1)

    # Add request and reclaim provenance fields to grant before writing it.
    grant_anchor = '''        "GrantPath": grant_rel,\n        "ClaimAuthority": authority,\n        "LeaseGeneration": generation,\n'''
    grant_replacement = '''        "GrantPath": grant_rel,\n        "RequestPath": request_rel,\n        "ClaimAuthority": authority,\n        "ClaimMode": claim_mode,\n        "LeaseGeneration": generation,\n'''
    if grant_anchor not in text:
        raise SystemExit("phase3 grant field anchor not found")
    text = text.replace(grant_anchor, grant_replacement, 1)

    ownership_anchor = '''        "OwnershipCheckpoint": f"AgentID={agent_id};Generation={generation};Token={token}",\n    }\n    _write_grant(grant_path, grant)\n'''
    ownership_replacement = '''        "OwnershipCheckpoint": f"AgentID={agent_id};Generation={generation};Token={token}",\n        "PreviousAgentID": previous.get("AgentID", "") if claim_mode == "RECLAIM" else "",\n        "PreviousLeaseGeneration": previous.get("LeaseGeneration", "") if claim_mode == "RECLAIM" else "",\n        "PreviousLeaseToken": previous.get("LeaseToken", "") if claim_mode == "RECLAIM" else "",\n        "PreviousGrantID": previous.get("GrantID", "") if claim_mode == "RECLAIM" else "",\n        "PreviousGrantPath": previous.get("GrantPath", "") if claim_mode == "RECLAIM" else "",\n        "ReclaimedFromLockGitBlobSHA": prior_lock_blob_sha if claim_mode == "RECLAIM" else "",\n    }\n    _write_grant(grant_path, grant)\n'''
    if ownership_anchor not in text:
        raise SystemExit("phase3 ownership anchor not found")
    text = text.replace(ownership_anchor, ownership_replacement, 1)

    # Decorate active lock and response with Request/mode/provenance.
    lock_anchor = '''        "GrantID": grant_id,\n        "GrantPath": grant_rel,\n        "FencingRequired": "YES",\n        "ExecutionEpoch": execution_ack,\n    })\n    packet.update({\n        "GrantID": grant_id,\n        "GrantPath": grant_rel,\n        "ClaimAuthority": authority,\n'''
    lock_replacement = '''        "GrantID": grant_id,\n        "GrantPath": grant_rel,\n        "RequestPath": request_rel,\n        "ClaimMode": claim_mode,\n        "PreviousAgentID": previous.get("AgentID", "") if claim_mode == "RECLAIM" else "",\n        "PreviousLeaseGeneration": previous.get("LeaseGeneration", "") if claim_mode == "RECLAIM" else "",\n        "PreviousLeaseToken": previous.get("LeaseToken", "") if claim_mode == "RECLAIM" else "",\n        "PreviousGrantID": previous.get("GrantID", "") if claim_mode == "RECLAIM" else "",\n        "PreviousGrantPath": previous.get("GrantPath", "") if claim_mode == "RECLAIM" else "",\n        "ReclaimedFromLockGitBlobSHA": prior_lock_blob_sha if claim_mode == "RECLAIM" else "",\n        "FencingRequired": "YES",\n        "ExecutionEpoch": execution_ack,\n    })\n    packet.update({\n        "RequestID": request_id,\n        "RequestPath": request_rel,\n        "ClaimMode": claim_mode,\n        "GrantID": grant_id,\n        "GrantPath": grant_rel,\n        "ClaimAuthority": authority,\n'''
    if lock_anchor not in text:
        raise SystemExit("phase3 lock/response anchor not found")
    text = text.replace(lock_anchor, lock_replacement, 1)

    # Snapshot old ownership before local command mutates/removes a stale lock.
    local_anchor = '''            prepare_caller_artifacts(caller_root, worktree, local_argv)\n\n            env = os.environ.copy()\n'''
    local_replacement = '''            prepare_caller_artifacts(caller_root, worktree, local_argv)\n\n            prior_claim_lock: dict[str, str] | None = None\n            prior_claim_blob_sha = ""\n            if local_argv and local_argv[0] == "claim":\n                prior_task = option_value(local_argv, "--task")\n                if prior_task:\n                    prior_path = worktree / "coordination/claims" / f"{prior_task}.lock"\n                    if prior_path.exists():\n                        prior_claim_lock = _parse_kv(prior_path)\n                        prior_claim_blob_sha = _ownership_git_blob_sha(prior_path)\n\n            env = os.environ.copy()\n'''
    if local_anchor not in text:
        raise SystemExit("phase3 prior ownership anchor not found")
    text = text.replace(local_anchor, local_replacement, 1)

    call_anchor = '''            proc = _decorate_claim_grant(proc, worktree, local_argv, execution_ack)\n'''
    call_replacement = '''            proc = _decorate_claim_grant(\n                proc, worktree, local_argv, execution_ack,\n                prior_lock=prior_claim_lock,\n                prior_lock_blob_sha=prior_claim_blob_sha,\n            )\n'''
    if call_anchor not in text:
        raise SystemExit("phase3 decorator call anchor not found")
    text = text.replace(call_anchor, call_replacement, 1)

    PATH.write_text(text, encoding="utf-8")
    print("phase3 Claim Request + reclaim provenance hooks patched")
    return True


if __name__ == "__main__":
    patch()
