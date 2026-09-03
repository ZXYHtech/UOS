#!/usr/bin/env python3
"""Claim one READY TRAVEL_GUIDE_DEPTH task with the standard public-research envelope.

This project helper is intentionally thin. High-contention behavior now lives in
the generic Kernel ingress ``tools/high_contention_claim.py`` so TRAVEL_GUIDE does
not maintain a second Claim/Lease/Fencing implementation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.control_extensions import execution_epoch  # noqa: E402
from tools.high_contention_claim import claim_exact  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Claim one book-depth travel task")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--lease-minutes", type=int, default=90)
    parser.add_argument("--cas-retries", type=int, default=20)
    parser.add_argument("--outer-attempts", type=int, default=4)
    args = parser.parse_args()

    proc = claim_exact(
        ROOT,
        agent_id=args.agent_id,
        task=args.task,
        capability_tier=4,
        tools="web;python",
        context_class="XL",
        project="TRAVEL_GUIDE_DEPTH",
        lease_minutes=args.lease_minutes,
        ack_execution_epoch=execution_epoch(ROOT),
        jitter_ms=3000,
        cas_retries=args.cas_retries,
        outer_attempts=args.outer_attempts,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
