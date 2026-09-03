#!/usr/bin/env python3
"""AI_book-style high-contention ingress for exact UOS task claims.

This is a generic Kernel ingress, not a project-specific ownership system.
It preserves ``tools/uos.py`` as the canonical Claim/Lease/Fencing authority while
adding the production contention behavior already proven in AI_book:

1. bounded random startup jitter for explicit Task claims;
2. read-only fetch of latest canonical Work Market / requirements;
3. read-only latest canonical Lock preflight;
4. active owner => local NO_MATCH with zero canonical write;
5. compatible READY task => normal latest-canonical UOS CAS transaction;
6. transient ref-race exhaustion => bounded outer retry from fresh canonical state.

The important invariant is unchanged: ownership exists only after ``tools/uos.py``
returns GRANTED and the matching canonical lock exists. This module never creates
locks, done files, or alternative ownership records itself.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from agent_matching import merge_requirements, select_compatible
    from canonical_publish import PublishError, git, verify_identity
    from control_extensions import execution_epoch
except ModuleNotFoundError:
    from tools.agent_matching import merge_requirements, select_compatible
    from tools.canonical_publish import PublishError, git, verify_identity
    from tools.control_extensions import execution_epoch


class HighContentionClaimError(RuntimeError):
    pass


TRANSIENT_MARKERS = (
    "CANONICAL_REF_RACE_RETRY_EXHAUSTED",
    "CANONICAL_PUSH_FAILED",
    "NON_FAST_FORWARD",
    "STALE_INFO",
    "REF_RACE",
)


def _read_csv(text: str | None) -> list[dict[str, str]]:
    if not text:
        return []
    return list(csv.DictReader(io.StringIO(text)))


def _show(root: Path, commit: str, rel: str) -> str | None:
    proc = git(["show", f"{commit}:{rel}"], cwd=root, check=False)
    return proc.stdout if proc.returncode == 0 else None


def _parse_kv_text(text: str | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in (text or "").splitlines():
        if not raw or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip().strip('"')
    return out


def _lock_is_stale(meta: dict[str, str]) -> bool:
    value = (meta.get("LeaseExpiresAt") or "").strip()
    if not value:
        return True
    try:
        expiry = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry <= datetime.now(timezone.utc)
    except Exception:
        return True


def _latest_commit(root: Path, remote: str, branch: str) -> str:
    try:
        verify_identity(root, remote, branch)
    except PublishError as exc:
        raise HighContentionClaimError(str(exc)) from exc
    fetch = git(["fetch", "--quiet", remote, branch], cwd=root, check=False)
    if fetch.returncode:
        raise HighContentionClaimError(
            f"CANONICAL_FETCH_FAILED: {fetch.stderr.strip() or fetch.stdout.strip()}"
        )
    return git(["rev-parse", f"refs/remotes/{remote}/{branch}"], cwd=root).stdout.strip()


def _latest_market_rows(root: Path, commit: str) -> list[dict[str, str]]:
    rows = _read_csv(_show(root, commit, "coordination/runtime/WORK_MARKET.csv"))
    names = git(
        ["ls-tree", "-r", "--name-only", commit, "orchestration/projects"],
        cwd=root,
        check=False,
    ).stdout.splitlines()
    reqs: list[dict[str, str]] = []
    for rel in names:
        if rel.endswith("/TASK_AGENT_REQUIREMENTS.csv"):
            reqs.extend(_read_csv(_show(root, commit, rel)))
    return merge_requirements(rows, reqs)


def _no_match(
    *,
    task: str,
    agent_id: str,
    reason: str,
    considered: dict[str, list[str]] | None = None,
) -> subprocess.CompletedProcess[str]:
    payload: dict[str, object] = {
        "status": "NO_MATCH",
        "reason": reason,
        "task": task,
        "agent_id": agent_id,
        "ownership": "NONE",
        "canonical_write": "NONE",
    }
    if considered is not None:
        payload["considered"] = considered
    return subprocess.CompletedProcess(
        args=[],
        returncode=4,
        stdout=json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        stderr="",
    )


def exact_preflight(
    root: Path,
    *,
    remote: str,
    branch: str,
    task: str,
    agent_id: str,
    capability_tier: int,
    tools: str,
    context_class: str,
    roles: str,
    project: str,
    jitter_ms: int,
) -> subprocess.CompletedProcess[str] | None:
    """Return local NO_MATCH or None when the exact task may enter canonical CAS."""
    if jitter_ms > 0:
        time.sleep(random.random() * min(jitter_ms, 5000) / 1000.0)

    commit = _latest_commit(root, remote, branch)
    lock = _parse_kv_text(_show(root, commit, f"coordination/claims/{task}.lock"))
    if lock and not _lock_is_stale(lock):
        return _no_match(
            task=task,
            agent_id=agent_id,
            reason="CANONICAL_CLAIM_ALREADY_EXISTS",
        )

    rows = _latest_market_rows(root, commit)
    selected, considered = select_compatible(
        rows,
        capability_tier=capability_tier,
        tools=tools,
        context_class=context_class,
        roles=roles,
        project=project,
        task=task,
    )
    if selected is None:
        return _no_match(
            task=task,
            agent_id=agent_id,
            reason="NO_COMPATIBLE_READY_TASK",
            considered=considered,
        )
    return None


def _is_transient(proc: subprocess.CompletedProcess[str]) -> bool:
    text = f"{proc.stdout or ''}\n{proc.stderr or ''}".upper()
    return any(marker in text for marker in TRANSIENT_MARKERS)


def claim_exact(
    root: Path,
    *,
    agent_id: str,
    task: str,
    capability_tier: int,
    tools: str,
    context_class: str,
    roles: str = "",
    project: str = "",
    lease_minutes: int = 90,
    ack_execution_epoch: str = "",
    remote: str = "origin",
    branch: str = "main",
    jitter_ms: int = 3000,
    cas_retries: int = 20,
    outer_attempts: int = 4,
) -> subprocess.CompletedProcess[str]:
    if not task:
        raise HighContentionClaimError("exact task is required")
    if capability_tier < 1:
        raise HighContentionClaimError("capability tier must be >= 1")
    attempts = max(1, min(outer_attempts, 10))
    cas_retries = max(1, min(cas_retries, 50))
    last: subprocess.CompletedProcess[str] | None = None

    for attempt in range(1, attempts + 1):
        preflight = exact_preflight(
            root,
            remote=remote,
            branch=branch,
            task=task,
            agent_id=agent_id,
            capability_tier=capability_tier,
            tools=tools,
            context_class=context_class,
            roles=roles,
            project=project,
            jitter_ms=jitter_ms if attempt == 1 else min(1000, jitter_ms),
        )
        if preflight is not None:
            return preflight

        cmd = [
            sys.executable,
            str(root / "tools/uos.py"),
            "--remote", remote,
            "--target-branch", branch,
            "--cas-retries", str(cas_retries),
        ]
        if ack_execution_epoch:
            cmd.extend(["--ack-execution-epoch", ack_execution_epoch])
        cmd.extend([
            "claim",
            "--agent-id", agent_id,
            "--task", task,
            "--lease-minutes", str(lease_minutes),
        ])
        if project:
            cmd.extend(["--project", project])
        proc = subprocess.run(
            cmd,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        last = proc
        if proc.returncode == 0:
            try:
                payload = json.loads(proc.stdout)
                if isinstance(payload, dict):
                    payload["contention_ingress"] = {
                        "mode": "EXACT_TASK_PREFLIGHT_V1",
                        "capability_tier": capability_tier,
                        "tools": sorted(x for x in tools.replace(",", ";").split(";") if x),
                        "context_class": context_class,
                        "project": project or None,
                        "cas_retries": cas_retries,
                    }
                    proc = subprocess.CompletedProcess(
                        args=proc.args,
                        returncode=0,
                        stdout=json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                        stderr=proc.stderr,
                    )
            except Exception:
                pass
            return proc
        if not _is_transient(proc) or attempt >= attempts:
            return proc
        time.sleep(random.uniform(0.15, min(2.5, 0.35 * (2 ** (attempt - 1)))))

    assert last is not None
    return last


def repo_root() -> Path:
    proc = git(["rev-parse", "--show-toplevel"], cwd=Path.cwd(), check=False)
    if proc.returncode:
        raise HighContentionClaimError("run inside a UOS Git working clone")
    return Path(proc.stdout.strip()).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="High-contention exact UOS Claim ingress")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--project", default="")
    parser.add_argument("--capability-tier", type=int, default=1)
    parser.add_argument("--tools", default="")
    parser.add_argument("--context", default="S")
    parser.add_argument("--roles", default="")
    parser.add_argument("--lease-minutes", type=int, default=90)
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--target-branch", default="main")
    parser.add_argument("--ack-execution-epoch", default="")
    parser.add_argument(
        "--jitter-ms",
        type=int,
        default=int(os.environ.get("UOS_EXACT_CLAIM_JITTER_MS", "3000")),
    )
    parser.add_argument(
        "--cas-retries",
        type=int,
        default=int(os.environ.get("UOS_HIGH_CONTENTION_CAS_RETRIES", "20")),
    )
    parser.add_argument("--outer-attempts", type=int, default=4)
    args = parser.parse_args()

    root = repo_root()
    ack = args.ack_execution_epoch or execution_epoch(root)
    try:
        proc = claim_exact(
            root,
            agent_id=args.agent_id,
            task=args.task,
            capability_tier=args.capability_tier,
            tools=args.tools,
            context_class=args.context,
            roles=args.roles,
            project=args.project,
            lease_minutes=args.lease_minutes,
            ack_execution_epoch=ack,
            remote=args.remote,
            branch=args.target_branch,
            jitter_ms=max(0, args.jitter_ms),
            cas_retries=args.cas_retries,
            outer_attempts=args.outer_attempts,
        )
    except HighContentionClaimError as exc:
        print(f"UOS_HIGH_CONTENTION_ERROR: {exc}", file=sys.stderr)
        return 2
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
