from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


matching = load_module("agent_matching_test", ROOT / "tools/agent_matching.py")


class AgentMatchingTests(unittest.TestCase):
    def rows(self):
        return [
            {
                "canonical_id": "TASK_HIGH",
                "project_id": "DEMO",
                "priority": "1",
                "min_capability_tier": "4",
                "context_class": "L",
                "tool_requirements": "python;hfss",
                "allowed_roles": "ENGINEER",
            },
            {
                "canonical_id": "TASK_SAFE",
                "project_id": "DEMO",
                "priority": "2",
                "min_capability_tier": "2",
                "context_class": "M",
                "tool_requirements": "python;git",
                "allowed_roles": "ENGINEER;WORKER",
            },
        ]

    def test_skips_higher_priority_incompatible_task(self) -> None:
        selected, considered = matching.select_compatible(
            self.rows(),
            capability_tier=2,
            tools="python;git",
            context_class="M",
            roles="WORKER",
            project="DEMO",
        )
        self.assertEqual(selected["canonical_id"], "TASK_SAFE")
        self.assertTrue(considered["TASK_HIGH"])
        self.assertEqual(considered["TASK_SAFE"], [])

    def test_missing_tool_is_hard_mismatch(self) -> None:
        selected, considered = matching.select_compatible(
            [self.rows()[1]],
            capability_tier=4,
            tools="python",
            context_class="XL",
            roles="ENGINEER",
        )
        self.assertIsNone(selected)
        self.assertIn("MISSING_TOOLS:git", considered["TASK_SAFE"])

    def test_context_capacity_is_ordered(self) -> None:
        row = dict(self.rows()[1])
        row["tool_requirements"] = ""
        row["allowed_roles"] = ""
        selected, considered = matching.select_compatible(
            [row], capability_tier=5, tools="", context_class="S", roles=""
        )
        self.assertIsNone(selected)
        self.assertIn("CONTEXT<M", considered["TASK_SAFE"])

    def test_sidecar_overrides_market_hints(self) -> None:
        market = [{
            "canonical_id": "TASK_A",
            "project_id": "DEMO",
            "priority": "1",
            "min_capability_tier": "1",
            "context_class": "S",
            "tool_requirements": "",
        }]
        merged = matching.merge_requirements(
            market,
            [{
                "canonical_id": "TASK_A",
                "min_capability_tier": "3",
                "context_class": "L",
                "tool_requirements": "python;cad",
                "allowed_roles": "ENGINEER",
            }],
        )
        self.assertEqual(merged[0]["min_capability_tier"], "3")
        self.assertEqual(merged[0]["tool_requirements"], "python;cad")
        self.assertEqual(merged[0]["allowed_roles"], "ENGINEER")

    def test_exact_incompatible_task_explains_why(self) -> None:
        selected, considered = matching.select_compatible(
            self.rows(),
            capability_tier=1,
            tools="python",
            context_class="S",
            roles="WORKER",
            task="TASK_HIGH",
        )
        self.assertIsNone(selected)
        reasons = considered["TASK_HIGH"]
        self.assertTrue(any(reason.startswith("CAPABILITY_TIER<") for reason in reasons))
        self.assertTrue(any(reason.startswith("MISSING_TOOLS:") for reason in reasons))


if __name__ == "__main__":
    unittest.main()
