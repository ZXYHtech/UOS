from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]


def load_module():
    path = SOURCE / "tools/claim_observability.py"
    spec = importlib.util.spec_from_file_location("claim_observability", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ClaimObservabilityTests(unittest.TestCase):
    def test_report_combines_grants_cas_and_session_metrics(self) -> None:
        mod = load_module()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            write(
                root / "coordination/claim_requests/A/R.request",
                "Schema: UOS_CLAIM_REQUEST_V1\nStatus: PROCESSED\nDecision: GRANTED\nRequestedAt: " + now + "\n",
            )
            write(
                root / "coordination/claim_grants/A/R.grant",
                "Schema: UOS_CLAIM_GRANT_V1\nStatus: GRANTED\nGrantID: G\nCanonicalID: TASK\n"
                "AgentID: A\nClaimAuthority: UOS_CLAIM_BROKER_V2\nClaimMode: RECLAIM\nLeaseGeneration: 2\nGrantedAt: " + now + "\n",
            )
            write(root / "coordination/claims/TASK.lock", "CanonicalID: TASK\nAgentID: A\n")
            telemetry = {
                "schema": "UOS_CLAIM_TELEMETRY_V1",
                "claim_authority": "UOS_CLAIM_BROKER_V2",
                "cas_attempt": 3,
                "ref_races_before_candidate": 2,
                "runner_elapsed_ms_pre_push": 321,
            }
            write(root / "coordination/telemetry/claims/A/R.json", json.dumps(telemetry))
            session = {
                "schema": "UOS_WORK_SESSION_V2",
                "state": "ACTIVE",
                "metrics": {
                    "claims_succeeded": 3,
                    "tasks_completed": 2,
                    "no_match_count": 1,
                    "review_block_count": 1,
                    "ownership_recovery_count": 1,
                },
            }
            write(root / "coordination/work_sessions/A/S.json", json.dumps(session))

            data = mod.report(root)
            self.assertEqual(data["ownership"]["grants_total"], 1)
            self.assertEqual(data["ownership"]["reclaims_total"], 1)
            self.assertEqual(data["ownership"]["max_lease_generation"], 2)
            self.assertEqual(data["canonical_cas"]["telemetry_samples"], 1)
            self.assertEqual(data["canonical_cas"]["contended_wins"], 1)
            self.assertEqual(data["canonical_cas"]["max_ref_races_before_win"], 2)
            self.assertEqual(data["canonical_cas"]["claim_elapsed_ms_pre_push_p50"], 321)
            self.assertEqual(data["work_sessions"]["ownership_recovery_count"], 1)
            self.assertEqual(data["work_sessions"]["no_match_count"], 1)


if __name__ == "__main__":
    unittest.main()
