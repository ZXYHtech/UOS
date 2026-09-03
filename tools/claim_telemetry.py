#!/usr/bin/env python3
"""Durable Claim telemetry helpers for UOS canonical transactions.

Telemetry is deliberately not ownership. For a successful Claim candidate the
canonical runner writes one immutable JSON event into the same candidate tree as
the Request/Grant/Lock. If that candidate loses a Git ref race, the whole tree is
discarded and the next attempt recomputes a fresh event. Therefore only the event
attached to the winning canonical Claim is durable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "UOS_CLAIM_TELEMETRY_V1"


def iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _safe_component(value: str) -> str:
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
    out = "".join(ch if ch in allowed else "_" for ch in (value or ""))
    return out[:180] or "UNKNOWN"


def _claim_packet(stdout: str) -> dict[str, Any] | None:
    try:
        value = json.loads(stdout or "{}")
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def record_claim_candidate(
    snapshot: Path,
    *,
    stdout: str,
    cas_attempt: int,
    runner_elapsed_ms_pre_push: int,
    base_commit: str,
) -> str | None:
    """Write telemetry for one successful Claim candidate and return its relpath."""
    packet = _claim_packet(stdout)
    if not packet:
        return None
    task = str(packet.get("CanonicalID") or packet.get("task") or "")
    agent = str(packet.get("AgentID") or "")
    request_id = str(packet.get("RequestID") or "")
    grant_id = str(packet.get("GrantID") or "")
    if not task or not agent or not grant_id:
        return None
    event_id = request_id or grant_id
    rel = (
        f"coordination/telemetry/claims/{_safe_component(agent)}/"
        f"{_safe_component(event_id)}.json"
    )
    path = snapshot / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        # A candidate tree should never have two events for one immutable Grant.
        # Ref-race retries start from a new canonical snapshot/worktree.
        raise RuntimeError(f"claim telemetry already exists: {rel}")
    payload = {
        "schema": SCHEMA,
        "observed_at": iso_ms(),
        "canonical_id": task,
        "project_id": str(packet.get("ProjectID") or ""),
        "agent_id": agent,
        "request_id": request_id,
        "grant_id": grant_id,
        "claim_authority": str(packet.get("ClaimAuthority") or ""),
        "claim_mode": str(packet.get("ClaimMode") or ""),
        "lease_generation": int(packet.get("LeaseGeneration") or 0),
        "cas_attempt": int(cas_attempt),
        "ref_races_before_candidate": max(0, int(cas_attempt) - 1),
        "runner_elapsed_ms_pre_push": max(0, int(runner_elapsed_ms_pre_push)),
        "base_commit": base_commit,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rel


def decorate_claim_result(
    stdout: str,
    *,
    cas_attempt: int,
    runner_elapsed_ms_total: int,
    canonical_commit: str,
    telemetry_path: str | None,
) -> str:
    """Add non-authoritative runtime metadata to the returned Claim JSON."""
    packet = _claim_packet(stdout)
    if not packet:
        return stdout
    packet["canonical_runtime"] = {
        "cas_attempt": int(cas_attempt),
        "ref_races": max(0, int(cas_attempt) - 1),
        "runner_elapsed_ms": max(0, int(runner_elapsed_ms_total)),
        "canonical_commit": canonical_commit,
        "telemetry_path": telemetry_path or "",
    }
    return json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
