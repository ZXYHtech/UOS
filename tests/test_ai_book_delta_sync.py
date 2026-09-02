from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
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


ext = load_module("control_extensions_test", ROOT / "tools/control_extensions.py")
uos = load_module("uos_delta_test", ROOT / "tools/uos.py")


class AiBookDeltaSyncTests(unittest.TestCase):
    def test_execution_epoch_blocks_stale_critical_command(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".uos").mkdir()
            (root / ".uos/EXECUTION_CONTRACT.yaml").write_text(
                "Schema: UOS_EXECUTION_CONTRACT_V1\nExecutionEpoch: EPOCH_TEST_1\n",
                encoding="utf-8",
            )
            ext.enforce_execution_epoch(root, "boot", "")
            with self.assertRaises(ext.ControlExtensionError):
                ext.enforce_execution_epoch(root, "claim", "STALE")
            ext.enforce_execution_epoch(root, "claim", "EPOCH_TEST_1")

    def test_project_work_root_denies_cross_project_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = root / "orchestration/projects/ALPHA"
            project.mkdir(parents=True)
            (project / "PROJECT.yaml").write_text(
                "ProjectID: ALPHA\nWorkRoot: projects/ALPHA\n",
                encoding="utf-8",
            )
            ext.validate_project_output_scope(root, "ALPHA", "projects/ALPHA/result.md")
            with self.assertRaises(ext.ControlExtensionError):
                ext.validate_project_output_scope(root, "ALPHA", "projects/BETA/result.md")

    def test_reconcile_builds_ready_only_work_market(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = root / "orchestration/projects/DEMO"
            project.mkdir(parents=True)
            (project / "PROJECT.yaml").write_text(
                "ProjectID: DEMO\nWorkRoot: projects/DEMO\n",
                encoding="utf-8",
            )
            rows = []
            for task_id, priority, deps in (("TASK_A", "1", ""), ("TASK_B", "2", "TASK_A")):
                row = {field: "" for field in uos.TASK_FIELDS}
                row.update(
                    {
                        "id": task_id,
                        "priority": priority,
                        "status": "READY" if not deps else "BLOCKED",
                        "role": "WORKER",
                        "title": task_id,
                        "deps": deps,
                        "output": f"projects/DEMO/{task_id}.txt",
                        "project_id": "DEMO",
                        "workstream": "general",
                        "size_class": "S",
                        "min_capability_tier": "1",
                        "context_class": "S",
                    }
                )
                rows.append(row)
            uos.write_catalog(project / "TASK_CATALOG.csv", rows)
            uos.reconcile(root)
            with (root / "coordination/runtime/WORK_MARKET.csv").open(newline="", encoding="utf-8") as handle:
                market = list(csv.DictReader(handle))
            self.assertEqual([row["canonical_id"] for row in market], ["TASK_A"])

    def test_durability_receipt_binds_path_and_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "projects/DEMO/result.bin"
            output.parent.mkdir(parents=True)
            output.write_bytes(b"durable artifact\x00\x01")
            receipt = ext.write_durability_receipt(
                root,
                "TASK_DEMO",
                "DEMO",
                ["projects/DEMO/result.bin"],
            )
            self.assertEqual(receipt["status"], "DURABLE_READY")
            self.assertEqual(
                receipt["artifacts"][0]["sha256"],
                hashlib.sha256(b"durable artifact\x00\x01").hexdigest(),
            )
            saved = json.loads(
                (root / "coordination/quality/durability/TASK_DEMO.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved["binding_mode"], "SAME_CANONICAL_TREE_TRANSACTION")


if __name__ == "__main__":
    unittest.main()
