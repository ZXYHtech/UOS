#!/usr/bin/env python3
"""Provider-neutral UOS Claim Broker V2.

The broker owns exact-task CREATE/RECLAIM semantics and writes the three
ownership anchors:
  Claim Request (immutable) -> Grant (immutable) -> active Lock.

Git serialization is deliberately outside this module. In git-cas transport the
broker runs inside a latest-canonical isolated transaction; a ref race discards
the whole ownership decision and reruns from newer canonical state. In local
transport RepoMutex provides same-worktree serialization.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Dict


class ClaimBrokerError(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    return (dt or utcnow()).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_kv(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip().strip('"')
    return out


def safe_rel(value: str) -> str:
    raw = (value or "").strip().replace("\\", "/")
    p = PurePosixPath(raw)
    if not raw or p.is_absolute() or any(part in {"", ".", ".."} for part in p.parts):
        raise ClaimBrokerError(f"unsafe repository path: {value!r}")
    return str(p)


def parse_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise ClaimBrokerError(f"invalid lease timestamp: {value!r}") from exc


def is_stale(meta: Dict[str, str]) -> bool:
    try:
        return parse_time(meta.get("LeaseExpiresAt", "")) <= utcnow()
    except ClaimBrokerError:
        return True


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def write_immutable(path: Path, values: Dict[str, object], label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ClaimBrokerError(f"immutable {label} already exists: {path}")
    path.write_text("".join(f"{key}: {value}\n" for key, value in values.items()), encoding="utf-8")


def write_lock(path: Path, values: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{key}: {value}\n" for key, value in values.items()), encoding="utf-8")


def claim_exact(
    root: Path,
    row: Dict[str, str],
    *,
    agent_id: str,
    lease_minutes: int,
    execution_epoch: str = "",
) -> Dict[str, object]:
    """Create or reclaim exact task ownership from the current canonical snapshot."""
    task_id = str(row.get("id") or "")
    if not task_id:
        raise ClaimBrokerError("task row has no id")
    if lease_minutes < 1:
        raise ClaimBrokerError("lease_minutes must be >= 1")

    lock_path = root / "coordination/claims" / f"{task_id}.lock"
    done_path = root / "coordination/completed" / f"{task_id}.done"
    if done_path.exists():
        return {"status": "NO_MATCH", "reason": "ALREADY_DONE", "task": task_id}

    previous = parse_kv(lock_path)
    prior_blob_sha = git_blob_sha(lock_path) if lock_path.exists() else ""
    generation = 1
    if previous:
        if not is_stale(previous):
            return {
                "status": "NO_MATCH",
                "reason": "ALREADY_CLAIMED",
                "task": task_id,
                "owner": previous.get("AgentID", ""),
                "lease_generation": previous.get("LeaseGeneration", ""),
            }
        generation = int(previous.get("LeaseGeneration") or 0) + 1
        if generation <= 1:
            raise ClaimBrokerError("invalid predecessor LeaseGeneration")

    mode = "RECLAIM" if generation > 1 else "CREATE"
    token = secrets.token_hex(16)
    now = iso()
    expiry = iso(utcnow() + timedelta(minutes=lease_minutes))
    suffix = token[:12]
    request_id = f"REQ-{task_id}-G{generation}-{suffix}"
    grant_id = f"GRANT-{task_id}-G{generation}-{suffix}"
    request_rel = f"coordination/claim_requests/{agent_id}/{request_id}.request"
    grant_rel = f"coordination/claim_grants/{agent_id}/{request_id}.grant"
    claim_rel = f"coordination/claims/{task_id}.lock"
    done_rel = f"coordination/completed/{task_id}.done"
    authority = "UOS_CLAIM_BROKER_V2"
    fencing = f"{generation}:{token}"

    if mode == "RECLAIM":
        prior_generation = int(previous.get("LeaseGeneration") or 0)
        if prior_generation != generation - 1 or not prior_blob_sha:
            raise ClaimBrokerError("reclaim lacks exact predecessor provenance")

    request: Dict[str, object] = {
        "Schema": "UOS_CLAIM_REQUEST_V1",
        "Status": "PROCESSED",
        "RequestID": request_id,
        "AgentID": agent_id,
        "CanonicalID": task_id,
        "ProjectID": row.get("project_id", ""),
        "RequestedAt": now,
        "Mode": mode,
        "ExecutionEpoch": execution_epoch,
        "LeaseMinutes": lease_minutes,
        "ExpectedPriorLockGitBlobSHA": prior_blob_sha if mode == "RECLAIM" else "",
        "ExpectedPriorAgentID": previous.get("AgentID", "") if mode == "RECLAIM" else "",
        "ExpectedPriorLeaseGeneration": previous.get("LeaseGeneration", "") if mode == "RECLAIM" else "",
        "ExpectedPriorLeaseToken": previous.get("LeaseToken", "") if mode == "RECLAIM" else "",
        "Decision": "GRANTED",
        "GrantID": grant_id,
        "GrantPath": grant_rel,
        "ClaimPath": claim_rel,
    }
    grant: Dict[str, object] = {
        "Schema": "UOS_CLAIM_GRANT_V1",
        "Status": "GRANTED",
        "RequestID": request_id,
        "GrantID": grant_id,
        "CanonicalID": task_id,
        "ProjectID": row.get("project_id", ""),
        "AgentID": agent_id,
        "GrantedAt": now,
        "ClaimPath": claim_rel,
        "DonePath": done_rel,
        "GrantPath": grant_rel,
        "RequestPath": request_rel,
        "ClaimAuthority": authority,
        "ClaimMode": mode,
        "LeaseGeneration": generation,
        "LeaseToken": token,
        "LeaseExpiresAt": expiry,
        "FencingToken": fencing,
        "ExecutionEpoch": execution_epoch,
        "Inputs": row.get("inputs", ""),
        "Output": row.get("output", ""),
        "Acceptance": row.get("acceptance", ""),
        "Ownership": "ACTIVE_CANONICAL_CLAIM_WITH_IMMUTABLE_REQUEST_AND_GRANT",
        "OwnershipCheckpoint": f"AgentID={agent_id};Generation={generation};Token={token}",
        "PreviousAgentID": previous.get("AgentID", "") if mode == "RECLAIM" else "",
        "PreviousLeaseGeneration": previous.get("LeaseGeneration", "") if mode == "RECLAIM" else "",
        "PreviousLeaseToken": previous.get("LeaseToken", "") if mode == "RECLAIM" else "",
        "PreviousGrantID": previous.get("GrantID", "") if mode == "RECLAIM" else "",
        "PreviousGrantPath": previous.get("GrantPath", "") if mode == "RECLAIM" else "",
        "ReclaimedFromLockGitBlobSHA": prior_blob_sha if mode == "RECLAIM" else "",
    }
    lock: Dict[str, object] = {
        "Schema": "UOS_CLAIM_V1",
        "CanonicalID": task_id,
        "ProjectID": row.get("project_id", ""),
        "AgentID": agent_id,
        "LeaseGeneration": generation,
        "LeaseToken": token,
        "ClaimedAt": now,
        "LeaseExpiresAt": expiry,
        "FencingToken": fencing,
        "ClaimAuthority": authority,
        "RequestPath": request_rel,
        "GrantID": grant_id,
        "GrantPath": grant_rel,
        "ClaimMode": mode,
        "PreviousAgentID": previous.get("AgentID", "") if mode == "RECLAIM" else "",
        "PreviousLeaseGeneration": previous.get("LeaseGeneration", "") if mode == "RECLAIM" else "",
        "PreviousLeaseToken": previous.get("LeaseToken", "") if mode == "RECLAIM" else "",
        "PreviousGrantID": previous.get("GrantID", "") if mode == "RECLAIM" else "",
        "PreviousGrantPath": previous.get("GrantPath", "") if mode == "RECLAIM" else "",
        "ReclaimedFromLockGitBlobSHA": prior_blob_sha if mode == "RECLAIM" else "",
        "FencingRequired": "YES",
        "ExecutionEpoch": execution_epoch,
    }

    # Immutable decision records first, active pointer last. A remote git-cas
    # transaction publishes all three atomically; local-mode crash residue is
    # detectable by claim_integrity_scan.
    write_immutable(root / request_rel, request, "Claim Request")
    write_immutable(root / grant_rel, grant, "Grant")
    write_lock(lock_path, lock)

    packet: Dict[str, object] = dict(lock)
    packet.update({
        "Status": "GRANTED",
        "RequestID": request_id,
        "RequestPath": request_rel,
        "GrantID": grant_id,
        "GrantPath": grant_rel,
        "ClaimMode": mode,
        "Inputs": row.get("inputs", ""),
        "Output": row.get("output", ""),
        "Acceptance": row.get("acceptance", ""),
        "OwnershipCheckpoint": grant["OwnershipCheckpoint"],
    })
    return packet


def validate_owned_lock(
    root: Path,
    *,
    task_id: str,
    agent_id: str,
    lease_token: str,
    require_unexpired: bool = True,
) -> tuple[Path, Dict[str, str]]:
    """Validate current owner plus optional Request/Grant anchors."""
    lock_path = root / "coordination/claims" / f"{task_id}.lock"
    lock = parse_kv(lock_path)
    if not lock:
        raise ClaimBrokerError("claim not found")
    if lock.get("AgentID") != agent_id:
        raise ClaimBrokerError("FENCED: wrong owner")
    if lock.get("LeaseToken") != lease_token:
        raise ClaimBrokerError("FENCED: stale lease token")
    if require_unexpired and is_stale(lock):
        raise ClaimBrokerError("FENCED: lease expired")

    grant_rel = (lock.get("GrantPath") or "").strip()
    if not grant_rel:
        # Legacy pre-Phase-2 ownership remains valid during migration.
        return lock_path, lock
    grant_rel = safe_rel(grant_rel)
    if not grant_rel.startswith("coordination/claim_grants/"):
        raise ClaimBrokerError("FENCED: invalid GrantPath")
    grant = parse_kv(root / grant_rel)
    checks = {
        "CanonicalID": (lock.get("CanonicalID", ""), grant.get("CanonicalID", "")),
        "AgentID": (lock.get("AgentID", ""), grant.get("AgentID", "")),
        "LeaseGeneration": (lock.get("LeaseGeneration", ""), grant.get("LeaseGeneration", "")),
        "LeaseToken": (lock.get("LeaseToken", ""), grant.get("LeaseToken", "")),
        "GrantID": (lock.get("GrantID", ""), grant.get("GrantID", "")),
    }
    bad = [name for name, pair in checks.items() if not pair[1] or pair[0] != pair[1]]
    if bad:
        raise ClaimBrokerError("FENCED: Lock/Grant mismatch: " + ",".join(bad))

    request_rel = (lock.get("RequestPath") or grant.get("RequestPath") or "").strip()
    if request_rel:
        request_rel = safe_rel(request_rel)
        if not request_rel.startswith("coordination/claim_requests/"):
            raise ClaimBrokerError("FENCED: invalid RequestPath")
        request = parse_kv(root / request_rel)
        req_checks = {
            "CanonicalID": (request.get("CanonicalID", ""), lock.get("CanonicalID", "")),
            "AgentID": (request.get("AgentID", ""), lock.get("AgentID", "")),
            "GrantID": (request.get("GrantID", ""), lock.get("GrantID", "")),
            "GrantPath": (request.get("GrantPath", ""), grant_rel),
        }
        req_bad = [name for name, pair in req_checks.items() if not pair[1] or pair[0] != pair[1]]
        if req_bad:
            raise ClaimBrokerError("FENCED: Request/Grant/Lock mismatch: " + ",".join(req_bad))
    return lock_path, lock
