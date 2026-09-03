#!/usr/bin/env python3
"""Claim one READY TRAVEL_GUIDE_DEPTH task with the standard public-research envelope."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.agent_matching import claim_best, current_epoch  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Claim one book-depth travel task")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--lease-minutes", type=int, default=90)
    args = parser.parse_args()

    epoch = current_epoch(ROOT)
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
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
