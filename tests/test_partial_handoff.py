from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


handoff = load_module("partial_handoff_test", ROOT / "tools/partial_handoff.py")
uos = load_module("uos_handoff_test", ROOT / "tools/uos.py")


def future(minutes: int = 90) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PartialHandoffTests(unittest.TestCase):
    def seed(self, root: Path) -> tuple[str, str]:
        (root / ".uos").mkdir(parents=True)
        (root / ".uos/EXECUTION_CONTRACT.yaml").write_text(
            "Schema: UOS_EXECUTION_CONTRACT_V1\nExecutionEpoch: EPOCH_HANDOFF_1\n",
            encoding="utf-8",
        )
        project = root / "orchestration/projects/DEMO"
        project.mkdir(parents=True)
        (project / "PROJECT.yaml").write_text(
            "Schema: UOS_PROJECT_V1\nProjectID: DEMO\nWorkRoot: projects/DEMO\n",
            encoding="utf-8",
        )
        row = {field: "" for field in uos.TASK_FIELDS}
        row.update(
            {
                "id": "TASK_A",
                "priority": "1",
                "status": "READY",
                "role": "WORKER",
                "title": "Task A",
                "output": "projects/DEMO/final.txt",
                "project_id": "DEMO",
                "acceptance": "final exists",
                "min_capability_tier": "1",
                "context_class": "S",
            }
        )
        uos.write_catalog(project / "TASK_CATALOG.csv", [row])
        token = "TOKEN_OWNER"
        lock = root / "coordination/claims/TASK_A.lock"
        lock.parent.mkdir(parents=True)
        lock.write_text(
            "Schema: UOS_CLAIM_V1\n"
            "CanonicalID: TASK_A\n"
            "ProjectID: DEMO\n"
            "AgentID: AGENT_A\n"
            "LeaseGeneration: 1\n"
            f"LeaseToken: {token}\n"
            f"LeaseExpiresAt: {future()}\n"
            f"FencingToken: 1:{token}\n",
            encoding="utf-8",
        )
        artifact = root / "projects/DEMO/checkpoint.txt"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("partial work\n", encoding="utf-8")
        return token, str(lock)

    def test_partial_checkpoint_does_not_release_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            token, lock_name = self.seed(root)
            before = handoff.parse_scalar_text(Path(lock_name).read_text(encoding="utf-8"))
            result = handoff.create_handoff(
                root,
                agent_id="AGENT_A",
                task_id="TASK_A",
                lease_token=token,
                state="PARTIAL",
                completed="parser implemented",
                artifacts=["projects/DEMO/checkpoint.txt"],
                validation_run="syntax only",
                known_failures="integration not run",
                next_action="run integration test",
                context_refs=["orchestration/projects/DEMO/PROJECT.yaml"],
                ack_execution_epoch="EPOCH_HANDOFF_1",
                remote="origin",
                branch="main",
            )
            after = handoff.parse_scalar_text(Path(lock_name).read_text(encoding="utf-8"))
            self.assertEqual(before["LeaseExpiresAt"], after["LeaseExpiresAt"])
            self.assertEqual(result["state"], "PARTIAL")
            self.assertFalse(result["authority"]["is_completion"])
            self.assertFalse(result["authority"]["transfers_ownership"])
            self.assertFalse((root / "coordination/completed/TASK_A.done").exists())

    def test_handoff_ready_expires_lease_without_done(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            token, lock_name = self.seed(root)
            result = handoff.create_handoff(
                root,
                agent_id="AGENT_A",
                task_id="TASK_A",
                lease_token=token,
                state="HANDOFF_READY",
                completed="checkpoint saved",
                artifacts=["projects/DEMO/checkpoint.txt"],
                validation_run="partial smoke",
                known_failures="final acceptance pending",
                next_action="successor claims TASK_A and revalidates",
                context_refs=[],
                ack_execution_epoch="EPOCH_HANDOFF_1",
                remote="origin",
                branch="main",
            )
            lock = handoff.parse_scalar_text(Path(lock_name).read_text(encoding="utf-8"))
            self.assertTrue(handoff.parse_time(lock["LeaseExpiresAt"]) <= datetime.now(timezone.utc))
            self.assertEqual(lock["HandoffState"], "HANDOFF_READY")
            self.assertEqual(result["release"]["expected_successor_generation"], 2)
            rows, states = uos.effective_states(root)
            self.assertEqual(states["TASK_A"], "READY")
            self.assertFalse((root / "coordination/completed/TASK_A.done").exists())

    def test_wrong_owner_token_and_cross_project_artifact_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            token, _lock_name = self.seed(root)
            with self.assertRaises(handoff.HandoffError):
                handoff.create_handoff(
                    root,
                    agent_id="AGENT_A",
                    task_id="TASK_A",
                    lease_token="WRONG",
                    state="PARTIAL",
                    completed="",
                    artifacts=[],
                    validation_run="",
                    known_failures="",
                    next_action="continue",
                    context_refs=[],
                    ack_execution_epoch="EPOCH_HANDOFF_1",
                    remote="origin",
                    branch="main",
                )
            other = root / "projects/OTHER/leak.txt"
            other.parent.mkdir(parents=True)
            other.write_text("no\n", encoding="utf-8")
            with self.assertRaises(Exception):
                handoff.create_handoff(
                    root,
                    agent_id="AGENT_A",
                    task_id="TASK_A",
                    lease_token=token,
                    state="PARTIAL",
                    completed="",
                    artifacts=["projects/OTHER/leak.txt"],
                    validation_run="",
                    known_failures="",
                    next_action="continue",
                    context_refs=[],
                    ack_execution_epoch="EPOCH_HANDOFF_1",
                    remote="origin",
                    branch="main",
                )

    def test_successor_must_own_claim_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            token, lock_name = self.seed(root)
            handoff.create_handoff(
                root,
                agent_id="AGENT_A",
                task_id="TASK_A",
                lease_token=token,
                state="PARTIAL",
                completed="checkpoint",
                artifacts=[],
                validation_run="",
                known_failures="",
                next_action="continue",
                context_refs=[],
                ack_execution_epoch="EPOCH_HANDOFF_1",
                remote="origin",
                branch="main",
            )
            with self.assertRaises(handoff.HandoffError):
                handoff.read_handoff(
                    root,
                    task_id="TASK_A",
                    agent_id="AGENT_B",
                    lease_token="B_TOKEN",
                    remote="origin",
                    branch="main",
                )


if __name__ == "__main__":
    unittest.main()
