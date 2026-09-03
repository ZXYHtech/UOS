#!/usr/bin/env python3
"""Run standalone UOS syntax and full discovered regression coverage."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if shutil.which("git") is None:
        print("SELFTEST FAIL: git is required", file=sys.stderr)
        return 2

    compile_proc = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "tools", "tests"],
        cwd=ROOT,
    )
    if compile_proc.returncode:
        print("SELFTEST FAIL: Python compile check failed", file=sys.stderr)
        return compile_proc.returncode

    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
        "-v",
    ]
    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode:
        print("SELFTEST FAIL: regression suite failed", file=sys.stderr)
        return proc.returncode

    print(
        "SELFTEST PASS: syntax + lifecycle + latest-main CAS + Broker V2 Request/Grant/Lock + "
        "reclaim/fencing + high-contention Claim + quality visibility + capability matching + "
        "Work Session V2 + Partial Handoff + Completion Outbox/batch Integration + observability passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
