#!/usr/bin/env python3
"""Claim one READY TRAVEL_GUIDE_DEPTH task with the standard public-research envelope.

This helper intentionally adds a small randomized startup delay and retries only
transient canonical Git/CAS races. Multiple Agents may claim different tasks at
the same time, but every Claim still publishes coordination state to the same
canonical branch, so a short burst can otherwise make one Agent lose the ref
race even when its task is still READY.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.agent_matching import claim_best, current_epoch  # noqa: E402


TRANSIENT_MARKERS = (
    "CANONICAL_REF_RACE_RETRY_EXHAUSTED",
    "COMPATIBLE_TASKS_LOST_CANONICAL_RACES",
    "REF_RACE",
    "NON_FAST_FORWARD",
    "STALE_INFO",
)


def _is_transient(proc) -> bool:
    text = f"{proc.stdout or ''}\n{proc.stderr or ''}".upper()
    return any(marker in text for marker in TRANSIENT_MARKERS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Claim one book-depth travel task")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--lease-minutes", type=int, default=90)
    parser.add_argument("--claim-attempts", type=int, default=8)
    args = parser.parse_args()

    attempts = max(1, min(args.claim_attempts, 20))
    epoch = current_epoch(ROOT)

    # Desynchronise Agents launched from near-identical prompts at the same time.
    if attempts > 1:
        time.sleep(random.uniform(0.05, 0.55))

    last = None
    for attempt in range(1, attempts + 1):
        proc = claim_best(
            ROOT,
            agent_id=args.agent_id,
            capability_tier=4,
            tools="web;python",
            context_class="XL",
            project="TRAVEL_GUIDE_DEPTH",
            task=args.task,
            lease_minutes=args.lease_minutes,
            ack_execution_epoch=epoch,
        )
        last = proc
        if proc.returncode == 0:
            if proc.stdout:
                print(proc.stdout, end="")
            if proc.stderr:
                print(proc.stderr, end="", file=sys.stderr)
            return 0

        if not _is_transient(proc) or attempt >= attempts:
            break

        # Exponential-ish backoff with jitter; keep it short for interactive Agents.
        ceiling = min(4.0, 0.30 * (2 ** (attempt - 1)))
        time.sleep(random.uniform(0.15, ceiling))

    assert last is not None
    if last.stdout:
        print(last.stdout, end="")
    if last.stderr:
        print(last.stderr, end="", file=sys.stderr)
    return last.returncode


if __name__ == "__main__":
    raise SystemExit(main())
