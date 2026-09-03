#!/usr/bin/env python3
"""Apply the exact candidate fixes for the 2026-09-03 full selftest closeout.

Temporary validation helper. It is intentionally idempotent and must be removed
once the tested changes are canonical.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(rel: str, old: str, new: str, marker: str) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print(f"already patched {rel}")
        return
    if old not in text:
        raise SystemExit(f"candidate patch anchor missing: {rel}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel}")


def main() -> int:
    replace_once(
        "tools/work_session.py",
        '''    live_claims = _live_agent_claims(root, commit, agent_id)\n    current = str(session.get("current_task") or "")\n\n    if current:\n        if live_claims and current not in live_claims:\n''',
        '''    live_claims = _live_agent_claims(root, commit, agent_id)\n    current = str(session.get("current_task") or "")\n\n    if current:\n        # A rejected visible result deliberately revokes Done so the same task can\n        # be corrected. Treat that review fact before interpreting a missing Lock\n        # as ownership loss, but never override a conflicting live/reassigned Claim.\n        review = _canonical_json(root, commit, f"coordination/quality/events/{current}.json")\n        if (\n            review\n            and str(review.get("review_status", "")).upper() == "REJECTED"\n            and (not live_claims or current in live_claims)\n        ):\n            review_lock = _canonical_claim_meta(root, commit, current)\n            if not review_lock or review_lock.get("AgentID") == agent_id:\n                return {\n                    "status": "REWORK_REQUIRED",\n                    "task": current,\n                    "review": review,\n                    "session": session,\n                    "instruction": "Correct and re-complete the same rejected task; do not claim unrelated work.",\n                }\n        if live_claims and current not in live_claims:\n''',
        "A rejected visible result deliberately revokes Done",
    )

    replace_once(
        "tests/test_quality_visibility.py",
        '''TOOLS = ["uos.py", "claim_broker_v2.py", "claim_telemetry.py", "completion_outbox.py", "canonical_runner.py", "canonical_publish.py", "quality_gate.py"]\n''',
        '''TOOLS = ["uos.py", "claim_broker_v2.py", "claim_telemetry.py", "completion_outbox.py", "canonical_runner.py", "canonical_publish.py", "quality_gate.py", "control_extensions.py"]\n''',
        '"quality_gate.py", "control_extensions.py"',
    )

    replace_once(
        "tests/test_partial_handoff_git_cas.py",
        '''            self.assertEqual(old_complete.returncode, 2)\n            self.assertIn("FENCED", old_complete.stderr)\n\n            final = successor / "projects/DEMO/final.txt"\n''',
        '''            self.assertEqual(old_complete.returncode, 2)\n            blocked_packet = json.loads(old_complete.stdout)\n            self.assertEqual(blocked_packet["status"], "GRANT_INTEGRITY_BLOCKED")\n            self.assertIn("RequestedAgentID", blocked_packet["mismatch_fields"])\n            self.assertIn("RequestedLeaseToken", blocked_packet["mismatch_fields"])\n\n            final = successor / "projects/DEMO/final.txt"\n''',
        'blocked_packet["status"], "GRANT_INTEGRITY_BLOCKED"',
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
