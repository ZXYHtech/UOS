from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


requirements = load_module("task_requirements_test", ROOT / "tools/task_requirements.py")


class TaskRequirementTests(unittest.TestCase):
    def setup_root(self, root: Path) -> None:
        (root / ".uos").mkdir()
        (root / ".uos/EXECUTION_CONTRACT.yaml").write_text("ExecutionEpoch: E1\n", encoding="utf-8")
        project = root / "orchestration/projects/DEMO"
        project.mkdir(parents=True)
        (project / "TASK_CATALOG.csv").write_text(
            "id,priority,status,role,title,deps,inputs,output,project_id,phase,workstream,exclusive_keys,size_class,quality_tier,risk_tier,wave_id,batch_hint,acceptance,compliance_profile,notes,min_capability_tier,context_class,tool_requirements,context_refs\n"
            "TASK_A,1,READY,WORKER,Task A,,,projects/DEMO/a.txt,DEMO,BUILD,general,,S,STANDARD,LOW,,,ok,SOFTWARE_V1,,1,S,,\n",
            encoding="utf-8",
        )

    def test_local_set_writes_normalized_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.setup_root(root)
            row = requirements.set_requirement(
                root,
                project="DEMO",
                task="TASK_A",
                min_capability_tier=3,
                context_class="L",
                tools="HFSS; python;hfss",
                allowed_roles="Engineer,worker",
                ack_execution_epoch="E1",
                remote="origin",
                branch="main",
            )
            self.assertEqual(row["tool_requirements"], "hfss;python")
            self.assertEqual(row["allowed_roles"], "ENGINEER;WORKER")
            with (root / "orchestration/projects/DEMO/TASK_AGENT_REQUIREMENTS.csv").open(newline="", encoding="utf-8") as handle:
                saved = next(csv.DictReader(handle))
            self.assertEqual(saved["min_capability_tier"], "3")
            self.assertEqual(saved["context_class"], "L")

    def test_stale_epoch_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.setup_root(root)
            with self.assertRaises(requirements.RequirementError):
                requirements.set_requirement(
                    root,
                    project="DEMO",
                    task="TASK_A",
                    min_capability_tier=1,
                    context_class="S",
                    tools="",
                    allowed_roles="",
                    ack_execution_epoch="OLD",
                    remote="origin",
                    branch="main",
                )
            self.assertFalse((root / "orchestration/projects/DEMO/TASK_AGENT_REQUIREMENTS.csv").exists())


if __name__ == "__main__":
    unittest.main()
