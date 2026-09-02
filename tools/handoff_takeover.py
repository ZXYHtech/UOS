#!/usr/bin/env python3
"""Claim a handoff task through normal UOS ownership, then read recovery context.

This helper never creates ownership itself. It delegates the Claim to `uos.py` and
only reads the handoff after the new canonical Claim succeeds.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

try:
    from canonical_publish import git
    from control_extensions import execution_epoch
    from partial_handoff import HandoffError, read_handoff
except ModuleNotFoundError:
    from tools.canonical_publish import git
    from tools.control_extensions import execution_epoch
    from tools.partial_handoff import HandoffError, read_handoff


class TakeoverError(RuntimeError):
    pass


def repo_root() -> Path:
    proc = git(["rev-parse", "--show-toplevel"], cwd=Path.cwd(), check=False)
    if proc.returncode == 0:
        return Path(proc.stdout.strip()).resolve()
    return Path.cwd().resolve()


def require_epoch(root: Path, ack: str) -> None:
    current = execution_epoch(root)
    if current and ack != current:
        raise TakeoverError(
            f"REBOOT_REQUIRED: current ExecutionEpoch is {current}; run `python tools/uos.py boot` "
            f"and retry with --ack-execution-epoch {current}"
        )


def takeover(
    root: Path,
    *,
    agent_id: str,
    task_id: str,
    lease_minutes: int,
    ack: str,
    remote: str,
    branch: str,
) -> tuple[int, dict[str, object]]:
    require_epoch(root, ack)
    command = [
        sys.executable,
        str(root / "tools/uos.py"),
        "--remote",
        remote,
        "--target-branch",
        branch,
    ]
    if ack:
        command.extend(["--ack-execution-epoch", ack])
    command.extend(
        [
            "claim",
            "--agent-id",
            agent_id,
            "--task",
            task_id,
            "--lease-minutes",
            str(lease_minutes),
        ]
    )
    proc = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        detail: object = proc.stdout.strip() or proc.stderr.strip()
        try:
            detail = json.loads(proc.stdout)
        except Exception:
            pass
        return proc.returncode, {
            "status": "CLAIM_FAILED",
            "detail": detail,
        }

    try:
        grant = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise TakeoverError("uos.py claim succeeded but returned invalid JSON") from exc
    token = str(grant.get("LeaseToken") or "")
    if not token:
        raise TakeoverError("uos.py claim succeeded without LeaseToken")

    try:
        handoff = read_handoff(
            root,
            task_id=task_id,
            agent_id=agent_id,
            lease_token=token,
            remote=remote,
            branch=branch,
        )
        return 0, {
            "status": "CLAIM_GRANTED_WITH_HANDOFF",
            "grant": grant,
            "handoff": handoff,
            "instruction": "Restore/inspect checkpoint artifacts and re-run the original task Acceptance before completion.",
        }
    except HandoffError as exc:
        # Ownership already exists. Never encourage the caller to repeat Claim.
        return 0, {
            "status": "CLAIM_GRANTED_HANDOFF_READ_PENDING",
            "grant": grant,
            "warning": str(exc),
            "instruction": "Do not claim again. Re-run partial_handoff.py read with this LeaseToken after connectivity/state is available.",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normal UOS Claim followed by verified partial handoff read.")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--target-branch", default="main")
    parser.add_argument("--ack-execution-epoch", default="")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--lease-minutes", type=int, default=90)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    try:
        code, result = takeover(
            root,
            agent_id=args.agent_id,
            task_id=args.task,
            lease_minutes=args.lease_minutes,
            ack=args.ack_execution_epoch,
            remote=args.remote,
            branch=args.target_branch,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return code
    except TakeoverError as exc:
        print(f"UOS_HANDOFF_TAKEOVER_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
