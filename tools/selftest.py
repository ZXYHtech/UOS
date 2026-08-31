#!/usr/bin/env python3
"""Run the standalone UOS single-repository and Git-CAS regression suites."""
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
        print("SELFTEST FAIL", file=sys.stderr)
        return proc.returncode
    print("SELFTEST PASS: local lifecycle + multi-clone Git CAS regression suites passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
