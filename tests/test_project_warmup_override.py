from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from tools.canonical_runner import _warmup_serial_block
from tools.quality_gate import project_operator_warmup_satisfied, record_completion


HEADER = [
    "id", "priority", "status", "role", "title", "deps", "inputs", "output",
    "project_id", "phase", "workstream", "exclusive_keys", "size_class",
    "quality_tier", "risk_tier", "wave_id", "batch_hint", "acceptance",
    "compliance_profile", "notes", "min_capability_tier", "context_class",
    "tool_requirements", "context_refs",
]


def write_policy(root: Path) -> None:
    path = root / ".uos/QUALITY_VISIBILITY_POLICY.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Schema: UOS_QUALITY_VISIBILITY_V1\n"
        "RuleVersion: TEST\n"
        "RuleEpoch: 7\n"
        "Enabled: true\n"
        "Review:\n"
        "  WarmupRequired: 3\n"
        "  WarmupMaxConcurrentClaims: 1\n"
        "  SampleEvery: 5\n"
        "  HighRiskAlwaysReview: true\n"
        "  BlockNewClaimsWhilePending: true\n"
        "Presentation:\n"
        "  AgentMustPresentResultInConversation: true\n",
        encoding="utf-8",
    )


def write_project(root: Path, project: str, *, satisfied: bool) -> None:
    path = root / "orchestration/projects" / project / "PROJECT.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    extra = (
        "OperatorReviewPolicy: ONE_CONFIRMATION_THEN_CONTINUE\n"
        "OperatorWarmupRequired: 1\n"
        f"OperatorWarmupStatus: {'SATISFIED' if satisfied else 'PENDING'}\n"
        "PostWarmupMode: PARALLEL_ALLOWED_WITH_SAMPLING_AND_HIGH_RISK_REVIEW\n"
    )
    path.write_text(f"Schema: UOS_PROJECT_V1\nProjectID: {project}\n" + extra, encoding="utf-8")


def write_catalog(root: Path, project: str, rows: list[dict[str, str]]) -> None:
    path = root / "orchestration/projects" / project / "TASK_CATALOG.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()
        for row in rows:
            item = {key: "" for key in HEADER}
            item.update(row)
            writer.writerow(item)


class ProjectWarmupOverrideTests(unittest.TestCase):
    def test_satisfied_project_bypasses_serial_warmup_but_keeps_sampling_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_policy(root)
            write_project(root, "TRAVEL_GUIDE_DEPTH", satisfied=True)
            output = "projects/TRAVEL_GUIDE/research/book/test.md"
            write_catalog(
                root,
                "TRAVEL_GUIDE_DEPTH",
                [{
                    "id": "TASK_DEPTH_01",
                    "project_id": "TRAVEL_GUIDE_DEPTH",
                    "output": output,
                    "risk_tier": "LOW",
                }],
            )
            claim_dir = root / "coordination/claims"
            claim_dir.mkdir(parents=True, exist_ok=True)
            (claim_dir / "OTHER_TASK.lock").write_text("LeaseExpiresAt: 2999-01-01T00:00:00+00:00\n", encoding="utf-8")

            self.assertTrue(project_operator_warmup_satisfied(root, "TRAVEL_GUIDE_DEPTH"))
            blocked = _warmup_serial_block(
                root,
                ["claim", "--agent-id", "AGENT_B", "--project", "TRAVEL_GUIDE_DEPTH", "--task", "TASK_DEPTH_01"],
            )
            self.assertIsNone(blocked)

            target = root / output
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("result\n", encoding="utf-8")
            event = record_completion(root, "TASK_DEPTH_01")
            assert event is not None
            self.assertTrue(event["project_warmup_override_satisfied"])
            self.assertEqual(event["review_status"], "AUTO_ACCEPTED")
            self.assertEqual(event["review_reason"], "NOT_SAMPLED")

    def test_unsatisfied_project_still_uses_global_warmup(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_policy(root)
            write_project(root, "OTHER", satisfied=False)
            output = "projects/OTHER/result.md"
            write_catalog(
                root,
                "OTHER",
                [{
                    "id": "TASK_OTHER_01",
                    "project_id": "OTHER",
                    "output": output,
                    "risk_tier": "LOW",
                }],
            )
            target = root / output
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("result\n", encoding="utf-8")
            event = record_completion(root, "TASK_OTHER_01")
            assert event is not None
            self.assertFalse(event["project_warmup_override_satisfied"])
            self.assertEqual(event["review_status"], "PENDING")
            self.assertEqual(event["review_reason"], "RULE_EPOCH_WARMUP")


if __name__ == "__main__":
    unittest.main()
