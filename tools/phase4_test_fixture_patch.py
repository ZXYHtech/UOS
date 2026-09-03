#!/usr/bin/env python3
"""Add claim_broker_v2.py to isolated Git-CAS test tool fixtures."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "tests/test_git_cas_lifecycle.py",
    "tests/test_execution_epoch_git_cas.py",
    "tests/test_high_contention_claim.py",
    "tests/test_quality_visibility.py",
    "tests/test_quality_warmup_serial.py",
    "tests/test_partial_handoff_git_cas.py",
    "tests/test_work_session_git_cas.py",
    "tests/test_claim_grant_integrity.py",
    "tests/test_claim_request_reclaim.py",
]

for rel in FILES:
    path = ROOT / rel
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    if '"claim_broker_v2.py"' in text:
        continue
    # Multi-line lists: insert after uos.py. Single-line lists: insert after uos.py token.
    if '    "uos.py",\n' in text:
        text = text.replace('    "uos.py",\n', '    "uos.py",\n    "claim_broker_v2.py",\n', 1)
    elif 'TOOLS = ["uos.py", ' in text:
        text = text.replace('TOOLS = ["uos.py", ', 'TOOLS = ["uos.py", "claim_broker_v2.py", ', 1)
    else:
        raise SystemExit(f"TOOLS fixture anchor not found in {rel}")
    path.write_text(text, encoding="utf-8")
    print("patched", rel)
