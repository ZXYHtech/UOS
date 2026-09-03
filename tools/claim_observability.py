#!/usr/bin/env python3
"""Build a read-only UOS Claim/Work-Session observability report.

The report is derived from durable canonical artifacts. It does not participate
in Claim ownership and never mutates Request/Grant/Lock state.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


def repo_root() -> Path:
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "coordination").exists() or (candidate / ".git").exists():
            return candidate
    return here


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def percentile(values: Iterable[int], q: float) -> int | None:
    seq = sorted(int(x) for x in values)
    if not seq:
        return None
    if len(seq) == 1:
        return seq[0]
    pos = (len(seq) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return seq[lo]
    return round(seq[lo] + (seq[hi] - seq[lo]) * (pos - lo))


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def report(root: Path) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    grants: list[dict[str, str]] = []
    for path in sorted((root / "coordination/claim_grants").glob("*/*.grant")):
        item = parse_kv(path)
        if item:
            grants.append(item)

    requests: list[dict[str, str]] = []
    for path in sorted((root / "coordination/claim_requests").glob("*/*.request")):
        item = parse_kv(path)
        if item:
            requests.append(item)

    telemetry: list[dict[str, Any]] = []
    for path in sorted((root / "coordination/telemetry/claims").glob("*/*.json")):
        item = load_json(path)
        if item and item.get("schema") == "UOS_CLAIM_TELEMETRY_V1":
            telemetry.append(item)

    session_docs: list[dict[str, Any]] = []
    for path in sorted((root / "coordination/work_sessions").glob("*/*.json")):
        item = load_json(path)
        if item:
            session_docs.append(item)

    by_authority = Counter(g.get("ClaimAuthority") or "UNKNOWN" for g in grants)
    by_mode = Counter(g.get("ClaimMode") or "UNKNOWN" for g in grants)
    by_agent = Counter(g.get("AgentID") or "UNKNOWN" for g in grants)
    generations = [int(g.get("LeaseGeneration") or 0) for g in grants if str(g.get("LeaseGeneration") or "").isdigit()]

    last_15 = 0
    last_60 = 0
    per_minute: Counter[str] = Counter()
    for grant in grants:
        dt = parse_time(grant.get("GrantedAt", ""))
        if not dt:
            continue
        if dt >= now - timedelta(minutes=15):
            last_15 += 1
        if dt >= now - timedelta(minutes=60):
            last_60 += 1
        per_minute[dt.strftime("%Y-%m-%dT%H:%MZ")] += 1

    latencies = [int(x.get("runner_elapsed_ms_pre_push") or 0) for x in telemetry]
    attempts = [int(x.get("cas_attempt") or 1) for x in telemetry]
    races = [int(x.get("ref_races_before_candidate") or 0) for x in telemetry]
    contended = sum(1 for x in races if x > 0)

    session_states = Counter(str(s.get("state") or "UNKNOWN") for s in session_docs)
    no_match = 0
    review_blocks = 0
    recovered = 0
    session_claims = 0
    session_completions = 0
    for session in session_docs:
        metrics = session.get("metrics")
        if isinstance(metrics, dict):
            no_match += int(metrics.get("no_match_count") or 0)
            review_blocks += int(metrics.get("review_block_count") or 0)
            recovered += int(metrics.get("ownership_recovery_count") or 0)
            session_claims += int(metrics.get("claims_succeeded") or 0)
            session_completions += int(metrics.get("tasks_completed") or 0)
        else:
            session_claims += len(session.get("claimed_tasks") or []) if isinstance(session.get("claimed_tasks"), list) else 0
            session_completions += len(session.get("completed_tasks") or []) if isinstance(session.get("completed_tasks"), list) else 0

    active_locks = list((root / "coordination/claims").glob("*.lock")) if (root / "coordination/claims").exists() else []
    request_decisions = Counter(r.get("Decision") or r.get("Status") or "UNKNOWN" for r in requests)

    return {
        "schema": "UOS_CLAIM_OBSERVABILITY_V1",
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "ownership": {
            "requests_total": len(requests),
            "grants_total": len(grants),
            "active_locks": len(active_locks),
            "reclaims_total": int(by_mode.get("RECLAIM", 0)),
            "max_lease_generation": max(generations) if generations else 0,
            "by_authority": dict(sorted(by_authority.items())),
            "by_mode": dict(sorted(by_mode.items())),
            "request_decisions": dict(sorted(request_decisions.items())),
            "agents_seen": len(by_agent),
        },
        "throughput": {
            "grants_last_15m": last_15,
            "grants_last_60m": last_60,
            "peak_grants_per_minute": max(per_minute.values()) if per_minute else 0,
            "peak_minute": max(per_minute, key=per_minute.get) if per_minute else None,
        },
        "canonical_cas": {
            "telemetry_samples": len(telemetry),
            "contended_wins": contended,
            "contention_rate": round(contended / len(telemetry), 4) if telemetry else None,
            "cas_attempt_p50": percentile(attempts, 0.50),
            "cas_attempt_p95": percentile(attempts, 0.95),
            "claim_elapsed_ms_pre_push_p50": percentile(latencies, 0.50),
            "claim_elapsed_ms_pre_push_p95": percentile(latencies, 0.95),
            "max_ref_races_before_win": max(races) if races else 0,
        },
        "work_sessions": {
            "sessions_total": len(session_docs),
            "states": dict(sorted(session_states.items())),
            "claims_succeeded": session_claims,
            "tasks_completed": session_completions,
            "no_match_count": no_match,
            "review_block_count": review_blocks,
            "ownership_recovery_count": recovered,
        },
        "coverage": {
            "telemetry_note": "CAS latency/retry metrics cover Phase-5 telemetry-enabled Claim wins only.",
            "no_match_note": "NO_MATCH is counted from Work Session metrics; standalone failed Claims leave no canonical ownership artifact.",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Report UOS Claim Broker / Work Session observability")
    ap.add_argument("--output", default="", help="optional JSON output path relative to repository root")
    ap.add_argument("--assert-broker-v2", action="store_true", help="fail if a new telemetry event uses a non-Broker-V2 authority")
    args = ap.parse_args()
    root = repo_root()
    data = report(root)
    if args.output:
        target = root / args.output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    if args.assert_broker_v2:
        telemetry_dir = root / "coordination/telemetry/claims"
        for path in telemetry_dir.glob("*/*.json") if telemetry_dir.exists() else []:
            item = load_json(path)
            if item and item.get("schema") == "UOS_CLAIM_TELEMETRY_V1" and item.get("claim_authority") != "UOS_CLAIM_BROKER_V2":
                return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
