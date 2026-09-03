#!/usr/bin/env python3
"""Scan UOS Claim/Grant/Done ownership integrity.

Phase-2 compatibility rules:
- legacy active locks without GrantPath remain valid and are reported as LEGACY_ACTIVE;
- new grant-backed locks must match immutable Grant owner/generation/token/GrantID;
- completed tasks may retain immutable Grants but must not retain an active lock;
- stale leases are RECLAIMABLE, not automatically corrupt;
- safe repair is intentionally narrow: remove a lock only when the task is already
  complete, or restore a missing generation-1 lock from a non-stale Grant.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Dict, List


def repo_root() -> Path:
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "coordination").exists() or (candidate / ".git").exists():
            return candidate
    raise SystemExit("run inside a UOS repository")


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
        return ""
    return str(p)


def intv(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def parse_time(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def stale(meta: Dict[str, str]) -> bool:
    dt = parse_time(meta.get("LeaseExpiresAt", ""))
    return dt is None or dt <= datetime.now(timezone.utc)


def grant_files(root: Path) -> List[Path]:
    base = root / "coordination/claim_grants"
    return sorted(base.glob("*/*.grant")) if base.exists() else []


def expected_lock_from_grant(grant: Dict[str, str]) -> Dict[str, str]:
    return {
        "Schema": "UOS_CLAIM_V1",
        "CanonicalID": grant.get("CanonicalID", ""),
        "ProjectID": grant.get("ProjectID", ""),
        "AgentID": grant.get("AgentID", ""),
        "LeaseGeneration": grant.get("LeaseGeneration", "1"),
        "LeaseToken": grant.get("LeaseToken", ""),
        "ClaimedAt": grant.get("GrantedAt", ""),
        "LeaseExpiresAt": grant.get("LeaseExpiresAt", ""),
        "FencingToken": grant.get("FencingToken", ""),
        "ClaimAuthority": grant.get("ClaimAuthority", "UOS_CANONICAL_RUNNER_GRANT_V1"),
        "GrantID": grant.get("GrantID", ""),
        "GrantPath": grant.get("GrantPath", ""),
        "FencingRequired": "YES",
    }


def write_kv(path: Path, values: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{k}: {v}\n" for k, v in values.items()), encoding="utf-8")


def scan(root: Path, *, repair_safe: bool = False) -> tuple[List[Dict[str, str]], int, int]:
    claims = root / "coordination/claims"
    done = root / "coordination/completed"
    grants = grant_files(root)
    grant_by_path = {p.relative_to(root).as_posix(): parse_kv(p) for p in grants}
    grants_by_task: Dict[str, List[tuple[Path, Dict[str, str]]]] = {}
    for p in grants:
        g = parse_kv(p)
        cid = g.get("CanonicalID", "")
        if cid:
            grants_by_task.setdefault(cid, []).append((p, g))

    rows: List[Dict[str, str]] = []
    violations = repaired = 0
    lock_paths = sorted(claims.glob("*.lock")) if claims.exists() else []
    seen_grants: set[str] = set()

    for lock_path in lock_paths:
        lock = parse_kv(lock_path)
        cid = lock.get("CanonicalID") or lock_path.stem
        done_path = done / f"{cid}.done"
        status = "PASS"
        reason = "grant-backed lock matches immutable Grant"
        repaired_flag = "NO"
        grant_rel = safe_rel(lock.get("GrantPath", ""))
        grant_id = lock.get("GrantID", "")

        if done_path.exists():
            status, reason = "VIOLATION", "completed task still has active claim lock"
            violations += 1
            if repair_safe:
                lock_path.unlink(missing_ok=True)
                status, reason, repaired_flag = "REPAIRED", "removed claim lock for already-completed task", "YES"
                repaired += 1
        elif not grant_rel:
            status, reason = ("LEGACY_STALE" if stale(lock) else "LEGACY_ACTIVE"), "legacy lock has no GrantPath; accepted for backward compatibility"
        else:
            seen_grants.add(grant_rel)
            grant = grant_by_path.get(grant_rel)
            if not grant:
                status, reason = "VIOLATION", "GrantPath referenced by lock does not exist"
                violations += 1
            else:
                checks = {
                    "CanonicalID": (lock.get("CanonicalID", ""), grant.get("CanonicalID", "")),
                    "AgentID": (lock.get("AgentID", ""), grant.get("AgentID", "")),
                    "LeaseGeneration": (lock.get("LeaseGeneration", ""), grant.get("LeaseGeneration", "")),
                    "LeaseToken": (lock.get("LeaseToken", ""), grant.get("LeaseToken", "")),
                    "GrantID": (grant_id, grant.get("GrantID", "")),
                }
                bad = [k for k, pair in checks.items() if pair[0] != pair[1]]
                if bad:
                    status, reason = "VIOLATION", "lock/grant mismatch: " + ",".join(bad)
                    violations += 1
                elif stale(lock):
                    status, reason = "RECLAIMABLE", "grant-backed lease is stale and may be fenced by a higher generation"

        rows.append({
            "canonical_id": cid,
            "agent_id": lock.get("AgentID", ""),
            "lease_generation": lock.get("LeaseGeneration", ""),
            "grant_id": grant_id,
            "grant_path": grant_rel,
            "claim_path": lock_path.relative_to(root).as_posix(),
            "integrity_status": status,
            "repaired": repaired_flag,
            "reason": reason,
        })

    # Grants without their referenced/current lock: completed/superseded are valid,
    # otherwise an unfinished latest grant is an orphan ownership anchor.
    for cid, items in sorted(grants_by_task.items()):
        items.sort(key=lambda item: intv(item[1].get("LeaseGeneration", "0"), 0))
        latest_gen = max(intv(g.get("LeaseGeneration", "0"), 0) for _p, g in items)
        for grant_path, grant in items:
            rel = grant_path.relative_to(root).as_posix()
            if rel in seen_grants:
                continue
            gen = intv(grant.get("LeaseGeneration", "0"), 0)
            done_path = done / f"{cid}.done"
            lock_path = claims / f"{cid}.lock"
            status = "DONE" if done_path.exists() else ("SUPERSEDED" if gen < latest_gen else "VIOLATION")
            reason = (
                "completion exists; immutable Grant retained as ownership history"
                if status == "DONE" else
                "older Grant superseded by a higher lease generation"
                if status == "SUPERSEDED" else
                "unfinished latest Grant has no matching canonical lock"
            )
            repaired_flag = "NO"
            if status == "VIOLATION":
                violations += 1
                if repair_safe and gen == 1 and not stale(grant) and not lock_path.exists():
                    expected = expected_lock_from_grant(grant)
                    if expected.get("LeaseToken") and expected.get("GrantID") and expected.get("LeaseExpiresAt"):
                        write_kv(lock_path, expected)
                        status, reason, repaired_flag = "REPAIRED", "restored missing generation-1 lock from non-stale immutable Grant", "YES"
                        repaired += 1
            rows.append({
                "canonical_id": cid,
                "agent_id": grant.get("AgentID", ""),
                "lease_generation": grant.get("LeaseGeneration", ""),
                "grant_id": grant.get("GrantID", ""),
                "grant_path": rel,
                "claim_path": lock_path.relative_to(root).as_posix(),
                "integrity_status": status,
                "repaired": repaired_flag,
                "reason": reason,
            })

    return rows, violations, repaired


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan UOS Claim/Grant/Done ownership integrity")
    ap.add_argument("--repair-safe", action="store_true", help="apply only bounded non-destructive ownership repairs")
    ap.add_argument("--fail-on-violation", action="store_true")
    args = ap.parse_args()
    root = repo_root()
    rows, violations, repaired = scan(root, repair_safe=args.repair_safe)
    out = root / "coordination/runtime/CLAIM_INTEGRITY.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["canonical_id", "agent_id", "lease_generation", "grant_id", "grant_path", "claim_path", "integrity_status", "repaired", "reason"]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    print(f"claim integrity: rows={len(rows)} violations_seen={violations} repaired={repaired} output={out.relative_to(root)}")
    return 2 if args.fail_on_violation and violations > repaired else 0


if __name__ == "__main__":
    raise SystemExit(main())
