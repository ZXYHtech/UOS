#!/usr/bin/env python3
"""Run standalone UOS syntax, lifecycle, CAS, visibility and continuation regressions."""
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
        "SELFTEST PASS: syntax + local lifecycle + low-level CAS + integrated multi-clone lifecycle + quality visibility + upstream delta + capability matching + bounded work session passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
