from __future__ import annotations

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


session_mod = load_module("work_session_guard_test", ROOT / "tools/work_session.py")


class WorkSessionGuardTests(unittest.TestCase):
    EPOCH = "TEST_EPOCH"
    AGENT = "AGENT_TEST"
    SESSION = "WS_TEST"

    def setup_root(self, root: Path, *, current_task: str = "TASK_A", deadline_offset_minutes: int = 30, max_tasks: int = 3) -> None:
        (root / ".uos").mkdir(parents=True)
        (root / ".uos/EXECUTION_CONTRACT.yaml").write_text(
            f"ExecutionEpoch: {self.EPOCH}\n",
            encoding="utf-8",
        )
        (root / ".uos/QUALITY_VISIBILITY_POLICY.yaml").write_text(
            "Enabled: true\nRuleEpoch: 1\n",
            encoding="utf-8",
        )
        path = root / f"coordination/work_sessions/{self.AGENT}/{self.SESSION}.json"
        path.parent.mkdir(parents=True)
        deadline = datetime.now(timezone.utc) + timedelta(minutes=deadline_offset_minutes)
        data = {
            "schema": "UOS_WORK_SESSION_V1_LITE",
            "session_id": self.SESSION,
            "agent_id": self.AGENT,
            "state": "ACTIVE",
            "mode": "UNTIL_DEADLINE",
            "created_at": "2026-09-02T00:00:00Z",
            "deadline_at": deadline.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "project": "DEMO",
            "max_tasks": max_tasks,
            "capability": {"tier": 3, "tools": ["python", "git"], "context_class": "M", "roles": ["WORKER"]},
            "claimed_tasks": [current_task] if current_task else [],
            "completed_tasks": [],
            "current_task": current_task,
            "stop_reason": "",
        }
        path.write_text(json.dumps(data), encoding="utf-8")

    def write_done_and_receipt(self, root: Path, task: str) -> None:
        done = root / f"coordination/completed/{task}.done"
        done.parent.mkdir(parents=True, exist_ok=True)
        done.write_text("CanonicalID: TASK_A\n", encoding="utf-8")
        receipt = root / f"coordination/quality/durability/{task}.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps({"status": "DURABLE_READY"}), encoding="utf-8")

    def write_event(self, root: Path, task: str, status: str) -> None:
        path = root / f"coordination/quality/events/{task}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"task": task, "review_status": status}), encoding="utf-8")

    def test_pending_review_blocks_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.setup_root(root)
            self.write_done_and_receipt(root, "TASK_A")
            self.write_event(root, "TASK_A", "PENDING")
            result = session_mod.next_step(
                root,
                agent_id=self.AGENT,
                session_id=self.SESSION,
                ack_execution_epoch=self.EPOCH,
                remote="origin",
                branch="main",
                lease_minutes=90,
            )
            self.assertEqual(result["status"], "STOP_REVIEW_PENDING")
            saved = json.loads((root / f"coordination/work_sessions/{self.AGENT}/{self.SESSION}.json").read_text())
            self.assertEqual(saved["current_task"], "TASK_A")

    def test_rejected_review_requires_same_task_rework(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.setup_root(root)
            self.write_event(root, "TASK_A", "REJECTED")
            result = session_mod.next_step(
                root,
                agent_id=self.AGENT,
                session_id=self.SESSION,
                ack_execution_epoch=self.EPOCH,
                remote="origin",
                branch="main",
                lease_minutes=90,
            )
            self.assertEqual(result["status"], "REWORK_REQUIRED")
            self.assertEqual(result["task"], "TASK_A")

    def test_auto_accepted_completion_counts_then_max_tasks_stops(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.setup_root(root, max_tasks=1)
            self.write_done_and_receipt(root, "TASK_A")
            self.write_event(root, "TASK_A", "AUTO_ACCEPTED")
            result = session_mod.next_step(
                root,
                agent_id=self.AGENT,
                session_id=self.SESSION,
                ack_execution_epoch=self.EPOCH,
                remote="origin",
                branch="main",
                lease_minutes=90,
            )
            self.assertEqual(result["status"], "SESSION_STOPPED")
            self.assertEqual(result["reason"], "MAX_TASKS_REACHED")
            self.assertEqual(result["session"]["completed_tasks"], ["TASK_A"])
            self.assertEqual(result["session"]["current_task"], "")

    def test_deadline_does_not_abandon_current_claim(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.setup_root(root, deadline_offset_minutes=-1)
            claim = root / "coordination/claims/TASK_A.lock"
            claim.parent.mkdir(parents=True, exist_ok=True)
            future = datetime.now(timezone.utc) + timedelta(minutes=60)
            claim.write_text(
                "CanonicalID: TASK_A\n"
                f"AgentID: {self.AGENT}\n"
                f"LeaseExpiresAt: {future.replace(microsecond=0).isoformat().replace('+00:00','Z')}\n",
                encoding="utf-8",
            )
            result = session_mod.next_step(
                root,
                agent_id=self.AGENT,
                session_id=self.SESSION,
                ack_execution_epoch=self.EPOCH,
                remote="origin",
                branch="main",
                lease_minutes=90,
            )
            self.assertEqual(result["status"], "WORK_CURRENT_TASK")
            self.assertTrue(result["stop_after_current"])

    def test_missing_durability_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.setup_root(root)
            done = root / "coordination/completed/TASK_A.done"
            done.parent.mkdir(parents=True)
            done.write_text("CanonicalID: TASK_A\n", encoding="utf-8")
            self.write_event(root, "TASK_A", "AUTO_ACCEPTED")
            result = session_mod.next_step(
                root,
                agent_id=self.AGENT,
                session_id=self.SESSION,
                ack_execution_epoch=self.EPOCH,
                remote="origin",
                branch="main",
                lease_minutes=90,
            )
            self.assertEqual(result["status"], "STOP_DURABILITY_PENDING")


if __name__ == "__main__":
    unittest.main()
