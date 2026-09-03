#!/usr/bin/env python3
"""Apply the tested Phase-6 closeout changes.

This patcher exists so GitHub Actions can validate the kernel candidate before the
runtime files are committed to canonical main. It is intentionally idempotent.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(rel: str, old: str, new: str, marker: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print(f"already patched {rel}")
        return
    if old not in text:
        raise RuntimeError(f"patch anchor not found in {rel}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel}")


def patch_completion_outbox() -> None:
    replace_once(
        "tools/completion_outbox.py",
        "import json\nimport os\n",
        "import json\nimport math\nimport os\n",
        "import math\n",
    )
    old = '''def status(root: Path, *, remote: str = "origin", branch: str = "main") -> dict[str, Any]:\n    verify_identity(root, remote, branch)\n    git(["fetch", "--quiet", remote, branch], cwd=root)\n    _fetch_outbox_refs(root, remote)\n    base = git(["rev-parse", f"refs/remotes/{remote}/{branch}"], cwd=root).stdout.strip()\n    valid, messages = _collect(root, base, remote, 128)\n    return {\n        "status": "OUTBOX_STATUS",\n        "canonical_main": base,\n        "valid_queue_depth": len(valid),\n        "valid_requests": [item.request_id for item in valid],\n        "skipped": messages,\n    }\n'''
    new = '''def _percentile(values: Iterable[int], q: float) -> int | None:\n    seq = sorted(int(value) for value in values)\n    if not seq:\n        return None\n    if len(seq) == 1:\n        return seq[0]\n    pos = (len(seq) - 1) * q\n    lo, hi = math.floor(pos), math.ceil(pos)\n    if lo == hi:\n        return seq[lo]\n    return round(seq[lo] + (seq[hi] - seq[lo]) * (pos - lo))\n\n\ndef _parse_observation_time(value: object) -> datetime | None:\n    try:\n        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))\n    except Exception:\n        return None\n\n\ndef status(root: Path, *, remote: str = "origin", branch: str = "main") -> dict[str, Any]:\n    \"\"\"Return read-only queue + historical integration metrics.\n\n    Outbox refs are intentionally retained as audit/recovery evidence. Therefore\n    ``remote_refs_total`` is historical staged refs, while ``valid_queue_depth``\n    is the current mechanically ingestible queue. Canonical receipts are the\n    authoritative count of completed integrations.\n    \"\"\"\n    verify_identity(root, remote, branch)\n    git(["fetch", "--quiet", remote, branch], cwd=root)\n    _fetch_outbox_refs(root, remote)\n    base = git(["rev-parse", f"refs/remotes/{remote}/{branch}"], cwd=root).stdout.strip()\n    refs = _list_outbox_refs(root, remote)\n    valid, messages = _collect(root, base, remote, 128)\n\n    manifests: dict[str, dict[str, Any]] = {}\n    for ref_name, commit in refs:\n        manifest = _json_at(root, commit, MANIFEST_PATH) or {}\n        request_id = str(manifest.get("request_id") or "")\n        if request_id:\n            manifests[request_id] = manifest\n\n    receipt_names = git(\n        ["ls-tree", "-r", "--name-only", base, RECEIPT_ROOT],\n        cwd=root,\n        check=False,\n    ).stdout.splitlines()\n    receipts: list[dict[str, Any]] = []\n    for rel in receipt_names:\n        if not rel.endswith(".json"):\n            continue\n        item = _json_at(root, base, rel)\n        if item and item.get("schema") == "UOS_COMPLETION_OUTBOX_RECEIPT_V1":\n            receipts.append(item)\n\n    receipt_ids = {str(item.get("request_id") or "") for item in receipts}\n    retained_ingested = sum(1 for request_id in manifests if request_id in receipt_ids)\n    invalid_uningested = max(0, len(refs) - len(valid) - retained_ingested)\n\n    batches: dict[str, int] = {}\n    waits: list[int] = []\n    for item in receipts:\n        batch_id = str(item.get("batch_id") or "")\n        try:\n            batch_size = int(item.get("batch_size") or 0)\n        except Exception:\n            batch_size = 0\n        if batch_id and batch_size > 0:\n            batches.setdefault(batch_id, batch_size)\n        request_id = str(item.get("request_id") or "")\n        manifest = manifests.get(request_id)\n        if not manifest:\n            continue\n        requested = _parse_observation_time(manifest.get("requested_at"))\n        ingested = _parse_observation_time(item.get("ingested_at"))\n        if requested and ingested:\n            waits.append(max(0, round((ingested - requested).total_seconds() * 1000)))\n\n    batch_sizes = list(batches.values())\n    return {\n        "status": "OUTBOX_STATUS",\n        "canonical_main": base,\n        "remote_refs_total": len(refs),\n        "valid_queue_depth": len(valid),\n        "valid_requests": [item.request_id for item in valid],\n        "canonical_receipts_total": len(receipts),\n        "retained_ingested_refs": retained_ingested,\n        "invalid_or_fenced_uningested_refs": invalid_uningested,\n        "batch_count": len(batches),\n        "batch_size_p50": _percentile(batch_sizes, 0.50),\n        "batch_size_p95": _percentile(batch_sizes, 0.95),\n        "batch_size_max": max(batch_sizes) if batch_sizes else 0,\n        "integration_wait_ms_p50": _percentile(waits, 0.50),\n        "integration_wait_ms_p95": _percentile(waits, 0.95),\n        "integration_wait_ms_max": max(waits) if waits else 0,\n        "skipped_count": len(messages),\n        "skipped": messages,\n    }\n'''
    replace_once(
        "tools/completion_outbox.py",
        old,
        new,
        "invalid_or_fenced_uningested_refs",
    )


def patch_work_session() -> None:
    old = '''def _lock_stale(lock: dict[str, str]) -> bool:\n    try:\n        return parse_time(lock.get("LeaseExpiresAt", "1970-01-01T00:00:00Z")) <= utcnow()\n    except Exception:\n        return True\n\n\ndef _record_claim_metrics(\n'''
    new = '''def _lock_stale(lock: dict[str, str]) -> bool:\n    try:\n        return parse_time(lock.get("LeaseExpiresAt", "1970-01-01T00:00:00Z")) <= utcnow()\n    except Exception:\n        return True\n\n\ndef _pending_outbox_for_current(\n    root: Path,\n    *,\n    task: str,\n    agent_id: str,\n    lock: dict[str, str],\n    remote: str,\n) -> dict[str, str] | None:\n    \"\"\"Find only the Outbox ref for the current immutable Grant.\n\n    The exact GrantID in the canonical Lock prevents old Generation refs retained\n    for audit from being mistaken for the current completion candidate.\n    \"\"\"\n    if not remote or not lock:\n        return None\n    project = str(lock.get("ProjectID") or "")\n    grant_id = str(lock.get("GrantID") or "")\n    if not project or not grant_id:\n        return None\n    for value, label in ((project, "project id"), (task, "task id"), (agent_id, "agent id"), (grant_id, "grant id")):\n        _safe_id(value, label)\n    request_id = f"PUB-{grant_id}"\n    _safe_id(request_id, "publish request id")\n    ref_name = f"uos-outbox/{project}/{task}/{agent_id}/{request_id}"\n    proc = git(\n        ["ls-remote", "--heads", remote, f"refs/heads/{ref_name}"],\n        cwd=root,\n        check=False,\n    )\n    if proc.returncode != 0 or not proc.stdout.strip():\n        return None\n    return {\n        "request_id": request_id,\n        "outbox_ref": ref_name,\n        "grant_id": grant_id,\n        "lease_generation": str(lock.get("LeaseGeneration") or ""),\n    }\n\n\ndef _record_claim_metrics(\n'''
    replace_once(
        "tools/work_session.py",
        old,
        new,
        "def _pending_outbox_for_current(",
    )

    old2 = '''    outcome, detail = _finish_current_if_possible(root, session=session, commit=commit)\n    if outcome == "REWORK_REQUIRED":\n'''
    new2 = '''    if current and not _canonical_file_exists(root, commit, f"coordination/completed/{current}.done"):\n        current_lock = _canonical_claim_meta(root, commit, current)\n        pending_outbox = _pending_outbox_for_current(\n            root,\n            task=current,\n            agent_id=agent_id,\n            lock=current_lock,\n            remote=remote if _has_remote(root, remote) else "",\n        )\n        if pending_outbox:\n            deadline = parse_time(str(session["deadline_at"]))\n            return {\n                "status": "WAITING_INTEGRATION",\n                "task": current,\n                "outbox": pending_outbox,\n                "stop_after_current": utcnow() >= deadline or state == "STOPPING",\n                "session": session,\n                "instruction": (\n                    "The current completion is already persisted in the non-canonical Outbox. "\n                    "Do not modify or re-complete this task. Run mechanical `python tools/uos.py outbox ingest` "\n                    "and call session next again only after canonical Done is visible."\n                ),\n            }\n\n    outcome, detail = _finish_current_if_possible(root, session=session, commit=commit)\n    if outcome == "REWORK_REQUIRED":\n'''
    replace_once(
        "tools/work_session.py",
        old2,
        new2,
        '"status": "WAITING_INTEGRATION"',
    )


def patch_observability() -> None:
    old = '''from typing import Any, Iterable\n\n\ndef repo_root() -> Path:\n'''
    new = '''from typing import Any, Iterable\n\ntry:\n    from completion_outbox import status as completion_outbox_status\nexcept ModuleNotFoundError:\n    from tools.completion_outbox import status as completion_outbox_status\n\n\ndef repo_root() -> Path:\n'''
    replace_once(
        "tools/claim_observability.py",
        old,
        new,
        "completion_outbox_status",
    )

    old2 = '''    active_locks = list((root / "coordination/claims").glob("*.lock")) if (root / "coordination/claims").exists() else []\n    request_decisions = Counter(r.get("Decision") or r.get("Status") or "UNKNOWN" for r in requests)\n\n    return {\n'''
    new2 = '''    active_locks = list((root / "coordination/claims").glob("*.lock")) if (root / "coordination/claims").exists() else []\n    request_decisions = Counter(r.get("Decision") or r.get("Status") or "UNKNOWN" for r in requests)\n\n    try:\n        outbox_observation = completion_outbox_status(root)\n    except Exception as exc:\n        outbox_observation = {\n            "status": "OUTBOX_OBSERVABILITY_UNAVAILABLE",\n            "reason": str(exc),\n        }\n\n    return {\n'''
    replace_once(
        "tools/claim_observability.py",
        old2,
        new2,
        "outbox_observation = completion_outbox_status(root)",
    )

    old3 = '''        "work_sessions": {\n            "sessions_total": len(session_docs),\n            "states": dict(sorted(session_states.items())),\n            "claims_succeeded": session_claims,\n            "tasks_completed": session_completions,\n            "no_match_count": no_match,\n            "review_block_count": review_blocks,\n            "ownership_recovery_count": recovered,\n        },\n        "coverage": {\n            "telemetry_note": "CAS latency/retry metrics cover Phase-5 telemetry-enabled Claim wins only.",\n            "no_match_note": "NO_MATCH is counted from Work Session metrics; standalone failed Claims leave no canonical ownership artifact.",\n        },\n'''
    new3 = '''        "work_sessions": {\n            "sessions_total": len(session_docs),\n            "states": dict(sorted(session_states.items())),\n            "claims_succeeded": session_claims,\n            "tasks_completed": session_completions,\n            "no_match_count": no_match,\n            "review_block_count": review_blocks,\n            "ownership_recovery_count": recovered,\n        },\n        "completion_outbox": outbox_observation,\n        "coverage": {\n            "telemetry_note": "CAS latency/retry metrics cover Phase-5 telemetry-enabled Claim wins only.",\n            "no_match_note": "NO_MATCH is counted from Work Session metrics; standalone failed Claims leave no canonical ownership artifact.",\n            "outbox_note": "Outbox refs are non-canonical retained work-plane evidence; only canonical receipts count as integrated completions.",\n        },\n'''
    replace_once(
        "tools/claim_observability.py",
        old3,
        new3,
        '"completion_outbox": outbox_observation',
    )


def patch_observability_workflow() -> None:
    old = '''on:\n  push:\n    branches: [main]\n    paths:\n      - 'coordination/claim_requests/**'\n      - 'coordination/claim_grants/**'\n      - 'coordination/claims/**'\n      - 'coordination/work_sessions/**'\n      - 'coordination/telemetry/claims/**'\n      - 'tools/claim_observability.py'\n      - 'tools/claim_telemetry.py'\n      - 'tools/work_session.py'\n      - '.github/workflows/uos-claim-observability.yml'\n  workflow_dispatch:\n'''
    new = '''on:\n  push:\n    branches: [main]\n    paths:\n      - 'coordination/claim_requests/**'\n      - 'coordination/claim_grants/**'\n      - 'coordination/claims/**'\n      - 'coordination/work_sessions/**'\n      - 'coordination/telemetry/claims/**'\n      - 'coordination/outbox_receipts/**'\n      - 'tools/claim_observability.py'\n      - 'tools/claim_telemetry.py'\n      - 'tools/completion_outbox.py'\n      - 'tools/work_session.py'\n      - '.github/workflows/uos-claim-observability.yml'\n  schedule:\n    - cron: '17 * * * *'\n  workflow_dispatch:\n'''
    replace_once(
        ".github/workflows/uos-claim-observability.yml",
        old,
        new,
        "coordination/outbox_receipts/**",
    )


def main() -> int:
    patch_completion_outbox()
    patch_work_session()
    patch_observability()
    patch_observability_workflow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
