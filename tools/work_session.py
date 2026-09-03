#!/usr/bin/env python3
"""Bounded Work Session control for standalone UOS.

A Work Session is a durable continuation contract, not a scheduler and not
ownership. Each task is still acquired through the normal canonical Claim path.
The session only decides whether another Claim is allowed after the current task
has reached durable canonical completion and passed the visibility/review gate.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from agent_matching import AgentMatchingError, claim_best
    from canonical_publish import PublishError, blob_at, git, publish, verify_identity
    from control_extensions import execution_epoch
except ModuleNotFoundError:
    from tools.agent_matching import AgentMatchingError, claim_best
    from tools.canonical_publish import PublishError, blob_at, git, publish, verify_identity
    from tools.control_extensions import execution_epoch


class WorkSessionError(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    return (dt or utcnow()).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def repo_root() -> Path:
    proc = git(["rev-parse", "--show-toplevel"], cwd=Path.cwd(), check=False)
    if proc.returncode == 0:
        return Path(proc.stdout.strip()).resolve()
    return Path.cwd().resolve()


def require_epoch(root: Path, ack: str) -> None:
    current = execution_epoch(root)
    if current and ack != current:
        raise WorkSessionError(
            f"REBOOT_REQUIRED: current ExecutionEpoch is {current}; run `python tools/uos.py boot` and retry with --ack-execution-epoch {current}"
        )


def _safe_id(value: str, label: str) -> str:
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
    if not value or any(ch not in allowed for ch in value):
        raise WorkSessionError(f"invalid {label}: {value!r}")
    return value


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    try:
        temp.write_text(text, encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _has_remote(root: Path, remote: str) -> bool:
    return git(["rev-parse", "--git-dir"], cwd=root, check=False).returncode == 0 and git(
        ["remote", "get-url", remote], cwd=root, check=False
    ).returncode == 0


def _fetch_head(root: Path, remote: str, branch: str) -> str:
    verify_identity(root, remote, branch)
    git(["fetch", "--quiet", remote, branch], cwd=root)
    return git(["rev-parse", f"refs/remotes/{remote}/{branch}"], cwd=root).stdout.strip()


def _show(root: Path, commit: str, rel: str) -> str | None:
    proc = git(["show", f"{commit}:{rel}"], cwd=root, check=False)
    return proc.stdout if proc.returncode == 0 else None


def _session_rel(agent_id: str, session_id: str) -> str:
    return f"coordination/work_sessions/{agent_id}/{session_id}.json"


def _read_remote_json(root: Path, commit: str, rel: str) -> dict[str, object] | None:
    text = _show(root, commit, rel)
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise WorkSessionError(f"invalid canonical JSON: {rel}") from exc
    if not isinstance(data, dict):
        raise WorkSessionError(f"invalid canonical object: {rel}")
    return data


def _parse_scalar(text: str | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in (text or "").splitlines():
        if ":" not in raw or raw.lstrip().startswith(("#", "-")):
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _quality_enabled(root: Path, commit: str | None) -> bool:
    if commit:
        text = _show(root, commit, ".uos/QUALITY_VISIBILITY_POLICY.yaml")
    else:
        path = root / ".uos/QUALITY_VISIBILITY_POLICY.yaml"
        text = path.read_text(encoding="utf-8") if path.exists() else None
    values = _parse_scalar(text)
    return values.get("Enabled", "false").lower() in {"1", "true", "yes", "on"}


def _canonical_file_exists(root: Path, commit: str | None, rel: str) -> bool:
    if commit:
        return blob_at(root, commit, rel) is not None
    return (root / rel).exists()


def _canonical_json(root: Path, commit: str | None, rel: str) -> dict[str, object] | None:
    if commit:
        return _read_remote_json(root, commit, rel)
    path = root / rel
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def _live_agent_claims(root: Path, commit: str | None, agent_id: str) -> list[str]:
    paths: list[str] = []
    if commit:
        listed = git(
            ["ls-tree", "-r", "--name-only", commit, "coordination/claims"],
            cwd=root,
            check=False,
        ).stdout.splitlines()
        paths = [rel for rel in listed if rel.endswith(".lock")]
    else:
        base = root / "coordination/claims"
        paths = [str(path.relative_to(root)) for path in sorted(base.glob("*.lock"))] if base.exists() else []

    tasks: list[str] = []
    now = utcnow()
    for rel in paths:
        text = _show(root, commit, rel) if commit else (root / rel).read_text(encoding="utf-8")
        lock = _parse_scalar(text)
        if lock.get("AgentID") != agent_id:
            continue
        try:
            if parse_time(lock.get("LeaseExpiresAt", "1970-01-01T00:00:00Z")) <= now:
                continue
        except Exception:
            continue
        task = lock.get("CanonicalID") or Path(rel).stem
        if task:
            tasks.append(task)
    return sorted(set(tasks))


def _read_session(root: Path, agent_id: str, session_id: str, remote: str, branch: str) -> tuple[dict[str, object], str | None, str | None]:
    rel = _session_rel(agent_id, session_id)
    if _has_remote(root, remote):
        commit = _fetch_head(root, remote, branch)
        data = _read_remote_json(root, commit, rel)
        if data is None:
            raise WorkSessionError(f"session not found: {session_id}")
        return data, commit, blob_at(root, commit, rel)
    path = root / rel
    if not path.exists():
        raise WorkSessionError(f"session not found: {session_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise WorkSessionError(f"invalid session: {session_id}")
    return data, None, None


def _write_session_local(root: Path, agent_id: str, session_id: str, data: dict[str, object]) -> str:
    rel = _session_rel(agent_id, session_id)
    _atomic_write(root / rel, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return rel



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


def _mutate_session(
    root: Path,
    *,
    agent_id: str,
    session_id: str,
    remote: str,
    branch: str,
    mutate,
    retries: int = 5,
) -> dict[str, object]:
    if not _has_remote(root, remote):
        data, _commit, _blob = _read_session(root, agent_id, session_id, remote, branch)
        updated = mutate(dict(data))
        _write_session_local(root, agent_id, session_id, updated)
        return updated

    rel = _session_rel(agent_id, session_id)
    for _attempt in range(max(1, retries)):
        data, _commit, old_blob = _read_session(root, agent_id, session_id, remote, branch)
        if not old_blob:
            raise WorkSessionError(f"canonical session blob missing: {session_id}")
        updated = mutate(dict(data))
        _write_session_local(root, agent_id, session_id, updated)
        try:
            publish(
                root,
                paths=[rel],
                deletes=[],
                require_absent=[],
                expect_blobs={rel: old_blob},
                message=f"update work session {session_id}",
                remote=remote,
                branch=branch,
                retries=3,
                allow_replace=True,
            )
            return updated
        except PublishError as exc:
            if "EXPECTED_BLOB_MISMATCH" in str(exc):
                continue
            raise
    raise WorkSessionError("session update lost repeated canonical races")


def start_session(
    root: Path,
    *,
    agent_id: str,
    minutes: int,
    project: str,
    max_tasks: int,
    capability_tier: int,
    tools: str,
    context_class: str,
    roles: str,
    ack_execution_epoch: str,
    remote: str,
    branch: str,
) -> dict[str, object]:
    require_epoch(root, ack_execution_epoch)
    _safe_id(agent_id, "agent id")
    if minutes < 1 or minutes > 1440:
        raise WorkSessionError("minutes must be 1..1440")
    if max_tasks < 1 or max_tasks > 100:
        raise WorkSessionError("max tasks must be 1..100")
    if capability_tier < 1:
        raise WorkSessionError("capability tier must be >= 1")
    context_class = context_class.upper()
    if context_class not in {"XS", "S", "M", "L", "XL"}:
        raise WorkSessionError("context must be one of XS,S,M,L,XL")
    session_id = f"WS_{utcnow().strftime('%Y%m%dT%H%M%SZ')}_{secrets.token_hex(3).upper()}"
    deadline = utcnow() + timedelta(minutes=minutes)
    data: dict[str, object] = {
        "schema": "UOS_WORK_SESSION_V2",
        "session_id": session_id,
        "agent_id": agent_id,
        "state": "ACTIVE",
        "mode": "UNTIL_DEADLINE",
        "created_at": iso(),
        "deadline_at": iso(deadline),
        "project": project,
        "max_tasks": max_tasks,
        "capability": {
            "tier": capability_tier,
            "tools": sorted({x.strip().lower() for x in tools.replace(",", ";").split(";") if x.strip()}),
            "context_class": context_class,
            "roles": sorted({x.strip().upper() for x in roles.replace(",", ";").split(";") if x.strip()}),
        },
        "claimed_tasks": [],
        "completed_tasks": [],
        "current_task": "",
        "stop_reason": "",
        "event_sequence": 0,
        "events": [],
        "last_transition_at": iso(),
        "metrics": {
            "claims_succeeded": 0,
            "tasks_completed": 0,
            "no_match_count": 0,
            "review_block_count": 0,
            "ownership_recovery_count": 0,
            "adopted_claim_count": 0,
            "canonical_ref_races": 0,
            "claim_elapsed_ms_total": 0,
            "claim_elapsed_ms_max": 0,
        },
    }
    rel = _write_session_local(root, agent_id, session_id, data)
    if _has_remote(root, remote):
        verify_identity(root, remote, branch)
        publish(
            root,
            paths=[rel],
            deletes=[],
            require_absent=[rel],
            expect_blobs={},
            message=f"start work session {session_id}",
            remote=remote,
            branch=branch,
            retries=8,
            allow_replace=False,
        )
    return data


def _finish_current_if_possible(
    root: Path,
    *,
    session: dict[str, object],
    commit: str | None,
) -> tuple[str, dict[str, object] | None]:
    task = str(session.get("current_task") or "")
    if not task:
        return "NO_CURRENT", None

    event_rel = f"coordination/quality/events/{task}.json"
    event = _canonical_json(root, commit, event_rel)
    if event and str(event.get("review_status", "")).upper() == "REJECTED":
        return "REWORK_REQUIRED", event

    done_rel = f"coordination/completed/{task}.done"
    if not _canonical_file_exists(root, commit, done_rel):
        return "WORK_CURRENT_TASK", None

    receipt = _canonical_json(root, commit, f"coordination/quality/durability/{task}.json")
    if not receipt or str(receipt.get("status", "")).upper() != "DURABLE_READY":
        return "STOP_DURABILITY_PENDING", receipt

    if _quality_enabled(root, commit):
        if not event:
            return "STOP_QUALITY_EVENT_MISSING", None
        status = str(event.get("review_status", "")).upper()
        if status == "PENDING":
            return "STOP_REVIEW_PENDING", event
        if status == "REJECTED":
            return "REWORK_REQUIRED", event
        if status not in {"ACCEPTED", "AUTO_ACCEPTED"}:
            return "STOP_REVIEW_UNKNOWN", event
    return "CURRENT_COMPLETE", event


def next_step(
    root: Path,
    *,
    agent_id: str,
    session_id: str,
    ack_execution_epoch: str,
    remote: str,
    branch: str,
    lease_minutes: int,
) -> dict[str, object]:
    require_epoch(root, ack_execution_epoch)
    session, commit, _blob = _read_session(root, agent_id, session_id, remote, branch)
    if session.get("agent_id") != agent_id:
        raise WorkSessionError("session owner mismatch")
    state = str(session.get("state") or "")
    if state not in {"ACTIVE", "STOPPING"}:
        return {"status": "SESSION_STOPPED", "session": session}

    capability = session.get("capability") or {}
    if not isinstance(capability, dict):
        raise WorkSessionError("invalid session capability envelope")

    live_claims = _live_agent_claims(root, commit, agent_id)
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
        if len(live_claims) > 1:
            return {
                "status": "RECOVERY_REQUIRED",
                "reason": "MULTIPLE_ACTIVE_CLAIMS_FOR_AGENT",
                "active_claims": live_claims,
                "session": session,
            }
        adopted = live_claims[0]
        def adopt_claim(data: dict[str, object]) -> dict[str, object]:
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
        current = adopted
        if _has_remote(root, remote):
            commit = _fetch_head(root, remote, branch)

    outcome, detail = _finish_current_if_possible(root, session=session, commit=commit)
    if outcome == "REWORK_REQUIRED":
        return {
            "status": "REWORK_REQUIRED",
            "task": session.get("current_task"),
            "review": detail,
            "session": session,
            "instruction": "Correct and re-complete the same rejected task; do not claim unrelated work.",
        }
    if outcome in {"STOP_DURABILITY_PENDING", "STOP_QUALITY_EVENT_MISSING", "STOP_REVIEW_PENDING", "STOP_REVIEW_UNKNOWN"}:
        return {
            "status": outcome,
            "task": session.get("current_task"),
            "detail": detail,
            "session": session,
            "instruction": "Do not claim another task until the current completion is durable and the visibility/review gate is released.",
        }
    if outcome == "WORK_CURRENT_TASK":
        deadline = parse_time(str(session["deadline_at"]))
        return {
            "status": "WORK_CURRENT_TASK",
            "task": session.get("current_task"),
            "stop_after_current": utcnow() >= deadline or state == "STOPPING",
            "session": session,
        }
    if outcome == "CURRENT_COMPLETE":
        finished = str(session.get("current_task") or "")
        def close_current(data: dict[str, object]) -> dict[str, object]:
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
        session = _mutate_session(
            root,
            agent_id=agent_id,
            session_id=session_id,
            remote=remote,
            branch=branch,
            mutate=close_current,
        )
        current = ""

    deadline = parse_time(str(session["deadline_at"]))
    completed_count = len(list(session.get("completed_tasks", [])))
    max_tasks = int(session.get("max_tasks") or 1)
    if state == "STOPPING" or utcnow() >= deadline or completed_count >= max_tasks:
        reason = "OPERATOR_STOP" if state == "STOPPING" else ("DEADLINE_REACHED" if utcnow() >= deadline else "MAX_TASKS_REACHED")
        final_state = "STOPPED" if reason == "OPERATOR_STOP" else "COMPLETED"
        session = _mutate_session(
            root,
            agent_id=agent_id,
            session_id=session_id,
            remote=remote,
            branch=branch,
            mutate=lambda data: {**data, "state": final_state, "stop_reason": reason},
        )
        return {"status": "SESSION_STOPPED", "reason": reason, "session": session}

    proc = claim_best(
        root,
        agent_id=agent_id,
        capability_tier=int(capability.get("tier") or 1),
        tools=";".join(str(x) for x in capability.get("tools", [])),
        context_class=str(capability.get("context_class") or "S"),
        roles=";".join(str(x) for x in capability.get("roles", [])),
        project=str(session.get("project") or ""),
        lease_minutes=lease_minutes,
        ack_execution_epoch=ack_execution_epoch,
        remote=remote,
        branch=branch,
    )
    if proc.returncode != 0:
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

    grant = json.loads(proc.stdout)
    task_id = str(grant.get("CanonicalID") or grant.get("task") or "")
    if not task_id:
        raise WorkSessionError("claim succeeded without task id")

    def record_claim(data: dict[str, object]) -> dict[str, object]:
        return _record_claim_metrics(
            data,
            grant,
            event="CLAIM_GRANTED",
            task=task_id,
        )

    try:
        session = _mutate_session(
            root,
            agent_id=agent_id,
            session_id=session_id,
            remote=remote,
            branch=branch,
            mutate=record_claim,
        )
    except Exception as exc:
        return {
            "status": "CLAIM_GRANTED_SESSION_RECORD_PENDING",
            "grant": grant,
            "session_id": session_id,
            "warning": str(exc),
            "instruction": "Do not claim another task. Re-run session next; it will adopt the canonical live Claim for this Agent.",
        }
    return {"status": "CLAIM_GRANTED", "grant": grant, "session": session}


def stop_session(
    root: Path,
    *,
    agent_id: str,
    session_id: str,
    ack_execution_epoch: str,
    remote: str,
    branch: str,
) -> dict[str, object]:
    require_epoch(root, ack_execution_epoch)
    def stop(data: dict[str, object]) -> dict[str, object]:
        if data.get("agent_id") != agent_id:
            raise WorkSessionError("session owner mismatch")
        if data.get("current_task"):
            data["state"] = "STOPPING"
            data["stop_reason"] = "OPERATOR_STOP_AFTER_CURRENT"
        else:
            data["state"] = "STOPPED"
            data["stop_reason"] = "OPERATOR_STOP"
        return data
    return _mutate_session(
        root,
        agent_id=agent_id,
        session_id=session_id,
        remote=remote,
        branch=branch,
        mutate=stop,
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Bounded UOS work session continuation control.")
    p.add_argument("--remote", default="origin")
    p.add_argument("--target-branch", default="main")
    p.add_argument("--ack-execution-epoch", default="")
    sub = p.add_subparsers(dest="command", required=True)

    item = sub.add_parser("start")
    item.add_argument("--agent-id", required=True)
    item.add_argument("--minutes", type=int, default=30)
    item.add_argument("--project", default="")
    item.add_argument("--max-tasks", type=int, default=10)
    item.add_argument("--capability-tier", type=int, default=1)
    item.add_argument("--tools", default="")
    item.add_argument("--context", default="S")
    item.add_argument("--roles", default="")

    item = sub.add_parser("next")
    item.add_argument("--agent-id", required=True)
    item.add_argument("--session-id", required=True)
    item.add_argument("--lease-minutes", type=int, default=90)

    item = sub.add_parser("status")
    item.add_argument("--agent-id", required=True)
    item.add_argument("--session-id", required=True)

    item = sub.add_parser("stop")
    item.add_argument("--agent-id", required=True)
    item.add_argument("--session-id", required=True)
    return p


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    try:
        if args.command == "start":
            result = start_session(
                root,
                agent_id=args.agent_id,
                minutes=args.minutes,
                project=args.project,
                max_tasks=args.max_tasks,
                capability_tier=args.capability_tier,
                tools=args.tools,
                context_class=args.context,
                roles=args.roles,
                ack_execution_epoch=args.ack_execution_epoch,
                remote=args.remote,
                branch=args.target_branch,
            )
        elif args.command == "next":
            result = next_step(
                root,
                agent_id=args.agent_id,
                session_id=args.session_id,
                ack_execution_epoch=args.ack_execution_epoch,
                remote=args.remote,
                branch=args.target_branch,
                lease_minutes=args.lease_minutes,
            )
        elif args.command == "status":
            result, _commit, _blob = _read_session(root, args.agent_id, args.session_id, args.remote, args.target_branch)
        else:
            result = stop_session(
                root,
                agent_id=args.agent_id,
                session_id=args.session_id,
                ack_execution_epoch=args.ack_execution_epoch,
                remote=args.remote,
                branch=args.target_branch,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        if isinstance(result, dict) and str(result.get("status", "")).startswith("STOP_"):
            return 6 if result.get("status") == "STOP_REVIEW_PENDING" else 4
        if isinstance(result, dict) and result.get("status") in {"OWNERSHIP_LOST", "RECOVERY_REQUIRED"}:
            return 5
        return 0
    except (WorkSessionError, AgentMatchingError, PublishError) as exc:
        print(f"UOS_SESSION_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
