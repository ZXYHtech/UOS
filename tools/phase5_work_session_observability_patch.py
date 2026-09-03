#!/usr/bin/env python3
"""Integrate Phase-5 Work Session V2 and winning-CAS telemetry.

This migration is intentionally mechanical and idempotent. It patches the tested
kernel files in CI, runs regressions, and only then lets the workflow publish the
result back to main.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"phase5 patch anchor missing: {label}")
    return text.replace(old, new, 1)


def patch_canonical_runner() -> None:
    path = ROOT / "tools/canonical_runner.py"
    text = path.read_text(encoding="utf-8")

    if "from claim_telemetry import decorate_claim_result, record_claim_candidate" not in text:
        anchor = "\n\nclass CanonicalRunError(RuntimeError):\n"
        block = (
            "\n\ntry:\n"
            "    from claim_telemetry import decorate_claim_result, record_claim_candidate\n"
            "except ModuleNotFoundError:\n"
            "    from tools.claim_telemetry import decorate_claim_result, record_claim_candidate\n"
            "\n\nclass CanonicalRunError(RuntimeError):\n"
        )
        text = replace_once(text, anchor, block, "canonical telemetry import")

    text = replace_once(
        text,
        "    last_proc: subprocess.CompletedProcess[str] | None = None\n\n    for attempt in range(1, retries + 1):\n",
        "    last_proc: subprocess.CompletedProcess[str] | None = None\n    runner_started = time.perf_counter()\n\n    for attempt in range(1, retries + 1):\n",
        "canonical runner timer",
    )

    candidate_anchor = "            candidate = _candidate_from_worktree(worktree, base, _canonical_message(local_argv))\n"
    if "record_claim_candidate(" not in text:
        candidate_block = (
            "            telemetry_path: str | None = None\n"
            "            if local_argv and local_argv[0] == \"claim\":\n"
            "                try:\n"
            "                    telemetry_path = record_claim_candidate(\n"
            "                        worktree,\n"
            "                        stdout=proc.stdout,\n"
            "                        cas_attempt=attempt,\n"
            "                        runner_elapsed_ms_pre_push=round((time.perf_counter() - runner_started) * 1000),\n"
            "                        base_commit=base,\n"
            "                    )\n"
            "                except Exception as exc:\n"
            "                    raise CanonicalRunError(f\"CLAIM_TELEMETRY_ERROR: {exc}\") from exc\n"
            "\n"
            "            candidate = _candidate_from_worktree(worktree, base, _canonical_message(local_argv))\n"
        )
        text = replace_once(text, candidate_anchor, candidate_block, "candidate telemetry")

    success_anchor = (
        "            if push.returncode == 0:\n"
        "                git([\"fetch\", \"--quiet\", remote, branch], cwd=caller_root, check=False)\n"
        "                return proc\n"
    )
    if "runner_elapsed_ms_total" not in text:
        success_block = (
            "            if push.returncode == 0:\n"
            "                git([\"fetch\", \"--quiet\", remote, branch], cwd=caller_root, check=False)\n"
            "                if local_argv and local_argv[0] == \"claim\":\n"
            "                    runtime_stdout = decorate_claim_result(\n"
            "                        proc.stdout,\n"
            "                        cas_attempt=attempt,\n"
            "                        runner_elapsed_ms_total=round((time.perf_counter() - runner_started) * 1000),\n"
            "                        canonical_commit=candidate,\n"
            "                        telemetry_path=telemetry_path,\n"
            "                    )\n"
            "                    proc = subprocess.CompletedProcess(\n"
            "                        args=proc.args, returncode=proc.returncode, stdout=runtime_stdout, stderr=proc.stderr\n"
            "                    )\n"
            "                return proc\n"
        )
        text = replace_once(text, success_anchor, success_block, "claim runtime result")

    path.write_text(text, encoding="utf-8")
    print("patched tools/canonical_runner.py")


def patch_work_session() -> None:
    path = ROOT / "tools/work_session.py"
    text = path.read_text(encoding="utf-8")

    if "import time\n" not in text:
        text = replace_once(text, "import sys\n", "import sys\nimport time\n", "work session time import")

    helper_anchor = "\n\ndef _mutate_session(\n"
    if "def _session_transition(" not in text:
        helpers = r'''


def _session_transition(
    data: dict[str, object],
    event: str,
    *,
    task: str = "",
    increments: dict[str, int] | None = None,
    detail: dict[str, object] | None = None,
) -> dict[str, object]:
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}
    metrics = dict(metrics)
    for key, amount in (increments or {}).items():
        metrics[key] = int(metrics.get(key) or 0) + int(amount)
    data["metrics"] = metrics
    sequence = int(data.get("event_sequence") or 0) + 1
    entry: dict[str, object] = {
        "sequence": sequence,
        "at": iso(),
        "event": event,
        "task": task,
    }
    if detail:
        entry["detail"] = detail
    events = list(data.get("events", [])) if isinstance(data.get("events"), list) else []
    events.append(entry)
    data["events"] = events[-100:]
    data["event_sequence"] = sequence
    data["last_transition_at"] = entry["at"]
    return data


def _canonical_claim_meta(root: Path, commit: str | None, task: str) -> dict[str, str]:
    rel = f"coordination/claims/{task}.lock"
    if commit:
        return _parse_scalar(_show(root, commit, rel))
    path = root / rel
    return _parse_scalar(path.read_text(encoding="utf-8") if path.exists() else None)


def _lock_stale(lock: dict[str, str]) -> bool:
    try:
        return parse_time(lock.get("LeaseExpiresAt", "1970-01-01T00:00:00Z")) <= utcnow()
    except Exception:
        return True


def _record_claim_metrics(
    data: dict[str, object],
    grant: dict[str, object],
    *,
    event: str,
    task: str,
    ownership_recovery: bool = False,
) -> dict[str, object]:
    claimed = list(data.get("claimed_tasks", [])) if isinstance(data.get("claimed_tasks"), list) else []
    if task and task not in claimed:
        claimed.append(task)
    data["claimed_tasks"] = claimed
    data["current_task"] = task

    runtime = grant.get("canonical_runtime")
    runtime = runtime if isinstance(runtime, dict) else {}
    elapsed = int(runtime.get("runner_elapsed_ms") or 0)
    ref_races = int(runtime.get("ref_races") or 0)
    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}
    metrics = dict(metrics)
    metrics["claims_succeeded"] = int(metrics.get("claims_succeeded") or 0) + 1
    metrics["canonical_ref_races"] = int(metrics.get("canonical_ref_races") or 0) + ref_races
    metrics["claim_elapsed_ms_total"] = int(metrics.get("claim_elapsed_ms_total") or 0) + elapsed
    metrics["claim_elapsed_ms_max"] = max(int(metrics.get("claim_elapsed_ms_max") or 0), elapsed)
    if ownership_recovery:
        metrics["ownership_recovery_count"] = int(metrics.get("ownership_recovery_count") or 0) + 1
    data["metrics"] = metrics
    return _session_transition(
        data,
        event,
        task=task,
        detail={
            "lease_generation": int(grant.get("LeaseGeneration") or 0),
            "claim_mode": str(grant.get("ClaimMode") or ""),
            "canonical_ref_races": ref_races,
            "claim_elapsed_ms": elapsed,
        },
    )
'''
        text = replace_once(text, helper_anchor, helpers + helper_anchor, "work session helpers")

    text = text.replace('"schema": "UOS_WORK_SESSION_V1_LITE",', '"schema": "UOS_WORK_SESSION_V2",', 1)
    if '"event_sequence": 0,' not in text:
        data_anchor = (
            '        "claimed_tasks": [],\n'
            '        "completed_tasks": [],\n'
            '        "current_task": "",\n'
            '        "stop_reason": "",\n'
        )
        data_block = (
            '        "claimed_tasks": [],\n'
            '        "completed_tasks": [],\n'
            '        "current_task": "",\n'
            '        "stop_reason": "",\n'
            '        "event_sequence": 0,\n'
            '        "events": [],\n'
            '        "last_transition_at": iso(),\n'
            '        "metrics": {\n'
            '            "claims_succeeded": 0,\n'
            '            "tasks_completed": 0,\n'
            '            "no_match_count": 0,\n'
            '            "review_block_count": 0,\n'
            '            "ownership_recovery_count": 0,\n'
            '            "adopted_claim_count": 0,\n'
            '            "canonical_ref_races": 0,\n'
            '            "claim_elapsed_ms_total": 0,\n'
            '            "claim_elapsed_ms_max": 0,\n'
            '        },\n'
        )
        text = replace_once(text, data_anchor, data_block, "session v2 initial metrics")

    capability_block = (
        '    capability = session.get("capability") or {}\n'
        '    if not isinstance(capability, dict):\n'
        '        raise WorkSessionError("invalid session capability envelope")\n'
    )
    # Move capability validation before any ownership-recovery Claim attempt.
    if text.count(capability_block) == 1:
        text = text.replace(capability_block, "", 1)
        state_anchor = (
            '    if state not in {"ACTIVE", "STOPPING"}:\n'
            '        return {"status": "SESSION_STOPPED", "session": session}\n\n'
        )
        text = replace_once(text, state_anchor, state_anchor + capability_block + "\n", "early capability envelope")

    recovery_anchor = (
        '    live_claims = _live_agent_claims(root, commit, agent_id)\n'
        '    current = str(session.get("current_task") or "")\n'
        '    if not current and live_claims:\n'
    )
    if '"CURRENT_TASK_RECLAIMED"' not in text:
        recovery_block = r'''    live_claims = _live_agent_claims(root, commit, agent_id)
    current = str(session.get("current_task") or "")

    if current:
        if live_claims and current not in live_claims:
            return {
                "status": "RECOVERY_REQUIRED",
                "reason": "SESSION_CURRENT_DIFFERS_FROM_LIVE_AGENT_CLAIM",
                "task": current,
                "active_claims": live_claims,
                "session": session,
                "instruction": "Do not continue work or claim another task until ownership is reconciled.",
            }
        if not live_claims and not _canonical_file_exists(root, commit, f"coordination/completed/{current}.done"):
            lock = _canonical_claim_meta(root, commit, current)
            if not lock:
                return {
                    "status": "OWNERSHIP_LOST",
                    "reason": "CURRENT_CLAIM_LOCK_MISSING",
                    "task": current,
                    "session": session,
                    "instruction": "Do not continue the task. Run Claim Integrity recovery before doing more work.",
                }
            if lock.get("AgentID") != agent_id:
                return {
                    "status": "OWNERSHIP_LOST",
                    "reason": "CURRENT_TASK_REASSIGNED",
                    "task": current,
                    "canonical_owner": lock.get("AgentID"),
                    "session": session,
                    "instruction": "Stop work on this task; another Agent owns the canonical Lease.",
                }
            if not _lock_stale(lock):
                return {
                    "status": "RECOVERY_REQUIRED",
                    "reason": "LIVE_CLAIM_NOT_DISCOVERABLE",
                    "task": current,
                    "session": session,
                }

            recovery_started = time.perf_counter()
            recovered = claim_best(
                root,
                agent_id=agent_id,
                capability_tier=int(capability.get("tier") or 1),
                tools=";".join(str(x) for x in capability.get("tools", [])),
                context_class=str(capability.get("context_class") or "S"),
                roles=";".join(str(x) for x in capability.get("roles", [])),
                project=str(session.get("project") or ""),
                task=current,
                lease_minutes=lease_minutes,
                ack_execution_epoch=ack_execution_epoch,
                remote=remote,
                branch=branch,
                attempts=2,
            )
            if recovered.returncode != 0:
                detail_obj: object = recovered.stdout.strip() or recovered.stderr.strip()
                try:
                    detail_obj = json.loads(recovered.stdout)
                except Exception:
                    pass
                return {
                    "status": "OWNERSHIP_LOST",
                    "reason": "EXACT_CURRENT_RECLAIM_FAILED",
                    "task": current,
                    "detail": detail_obj,
                    "session": session,
                    "instruction": "Do not claim unrelated work from this session until the current task is reconciled.",
                }
            grant = json.loads(recovered.stdout)
            if not isinstance(grant, dict) or str(grant.get("CanonicalID") or "") != current:
                raise WorkSessionError("exact current-task recovery returned a different task")
            runtime = grant.get("canonical_runtime")
            if not isinstance(runtime, dict):
                runtime = {}
            if not runtime.get("runner_elapsed_ms"):
                runtime["runner_elapsed_ms"] = round((time.perf_counter() - recovery_started) * 1000)
                grant["canonical_runtime"] = runtime

            session = _mutate_session(
                root,
                agent_id=agent_id,
                session_id=session_id,
                remote=remote,
                branch=branch,
                mutate=lambda data: _record_claim_metrics(
                    data,
                    grant,
                    event="CURRENT_TASK_RECLAIMED",
                    task=current,
                    ownership_recovery=True,
                ),
            )
            return {
                "status": "CURRENT_TASK_RECLAIMED",
                "task": current,
                "grant": grant,
                "session": session,
                "instruction": "Continue only the same current task using the new LeaseToken.",
            }

    if not current and live_claims:
'''
        text = replace_once(text, recovery_anchor, recovery_block, "session exact-task recovery")

    adoption_old = r'''        session = _mutate_session(
            root,
            agent_id=agent_id,
            session_id=session_id,
            remote=remote,
            branch=branch,
            mutate=lambda data: {**data, "current_task": adopted, "claimed_tasks": list(dict.fromkeys([*list(data.get("claimed_tasks", [])), adopted]))},
        )
'''
    if adoption_old in text:
        adoption_new = r'''        def adopt_claim(data: dict[str, object]) -> dict[str, object]:
            claimed = list(data.get("claimed_tasks", [])) if isinstance(data.get("claimed_tasks"), list) else []
            if adopted not in claimed:
                claimed.append(adopted)
            data["claimed_tasks"] = claimed
            data["current_task"] = adopted
            return _session_transition(
                data,
                "ADOPTED_CANONICAL_CLAIM",
                task=adopted,
                increments={"adopted_claim_count": 1, "ownership_recovery_count": 1},
            )
        session = _mutate_session(
            root,
            agent_id=agent_id,
            session_id=session_id,
            remote=remote,
            branch=branch,
            mutate=adopt_claim,
        )
'''
        text = text.replace(adoption_old, adoption_new, 1)

    close_old = r'''        def close_current(data: dict[str, object]) -> dict[str, object]:
            completed = list(data.get("completed_tasks", []))
            if finished and finished not in completed:
                completed.append(finished)
            data["completed_tasks"] = completed
            data["current_task"] = ""
            return data
'''
    if close_old in text:
        close_new = r'''        def close_current(data: dict[str, object]) -> dict[str, object]:
            completed = list(data.get("completed_tasks", [])) if isinstance(data.get("completed_tasks"), list) else []
            increment = 0
            if finished and finished not in completed:
                completed.append(finished)
                increment = 1
            data["completed_tasks"] = completed
            data["current_task"] = ""
            return _session_transition(
                data,
                "CURRENT_TASK_DURABLY_COMPLETE",
                task=finished,
                increments={"tasks_completed": increment},
            )
'''
        text = text.replace(close_old, close_new, 1)

    failure_old = r'''    if proc.returncode != 0:
        detail_obj: object = proc.stdout.strip() or proc.stderr.strip()
        try:
            detail_obj = json.loads(proc.stdout)
        except Exception:
            pass
        status = "STOP_REVIEW_PENDING" if proc.returncode == 6 else "STOP_NO_MATCH"
        return {"status": status, "detail": detail_obj, "session": session}
'''
    if failure_old in text:
        failure_new = r'''    if proc.returncode != 0:
        detail_obj: object = proc.stdout.strip() or proc.stderr.strip()
        try:
            detail_obj = json.loads(proc.stdout)
        except Exception:
            pass
        status = "STOP_REVIEW_PENDING" if proc.returncode == 6 else "STOP_NO_MATCH"
        metric_key = "review_block_count" if status == "STOP_REVIEW_PENDING" else "no_match_count"
        session = _mutate_session(
            root,
            agent_id=agent_id,
            session_id=session_id,
            remote=remote,
            branch=branch,
            mutate=lambda data: _session_transition(
                data,
                status,
                increments={metric_key: 1},
            ),
        )
        return {"status": status, "detail": detail_obj, "session": session}
'''
        text = text.replace(failure_old, failure_new, 1)

    record_old = r'''    def record_claim(data: dict[str, object]) -> dict[str, object]:
        claimed = list(data.get("claimed_tasks", []))
        if task_id not in claimed:
            claimed.append(task_id)
        data["claimed_tasks"] = claimed
        data["current_task"] = task_id
        return data
'''
    if record_old in text:
        record_new = r'''    def record_claim(data: dict[str, object]) -> dict[str, object]:
        return _record_claim_metrics(
            data,
            grant,
            event="CLAIM_GRANTED",
            task=task_id,
        )
'''
        text = text.replace(record_old, record_new, 1)

    return_anchor = (
        '        if isinstance(result, dict) and str(result.get("status", "")).startswith("STOP_"):\n'
        '            return 6 if result.get("status") == "STOP_REVIEW_PENDING" else 4\n'
        '        return 0\n'
    )
    if 'result.get("status") in {"OWNERSHIP_LOST", "RECOVERY_REQUIRED"}' not in text:
        return_block = (
            '        if isinstance(result, dict) and str(result.get("status", "")).startswith("STOP_"):\n'
            '            return 6 if result.get("status") == "STOP_REVIEW_PENDING" else 4\n'
            '        if isinstance(result, dict) and result.get("status") in {"OWNERSHIP_LOST", "RECOVERY_REQUIRED"}:\n'
            '            return 5\n'
            '        return 0\n'
        )
        text = replace_once(text, return_anchor, return_block, "session recovery exit code")

    path.write_text(text, encoding="utf-8")
    print("patched tools/work_session.py")


def patch_test_fixtures() -> None:
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        if '"canonical_runner.py"' not in text or "TOOLS" not in text or '"claim_telemetry.py"' in text:
            continue
        original = text
        if '    "claim_broker_v2.py",\n' in text:
            text = text.replace(
                '    "claim_broker_v2.py",\n',
                '    "claim_broker_v2.py",\n    "claim_telemetry.py",\n',
                1,
            )
        elif '"claim_broker_v2.py",' in text:
            text = text.replace('"claim_broker_v2.py",', '"claim_broker_v2.py", "claim_telemetry.py",', 1)
        elif '    "uos.py",\n' in text:
            text = text.replace('    "uos.py",\n', '    "uos.py",\n    "claim_telemetry.py",\n', 1)
        elif 'TOOLS = ["uos.py", ' in text:
            text = text.replace('TOOLS = ["uos.py", ', 'TOOLS = ["uos.py", "claim_telemetry.py", ', 1)
        else:
            raise SystemExit(f"unable to add claim_telemetry.py fixture dependency: {path.relative_to(ROOT)}")
        if text != original:
            path.write_text(text, encoding="utf-8")
            print("patched", path.relative_to(ROOT))


def main() -> None:
    patch_canonical_runner()
    patch_work_session()
    patch_test_fixtures()


if __name__ == "__main__":
    main()
