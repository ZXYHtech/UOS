from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
TOOLS = [
    "uos.py",
    "claim_broker_v2.py",
    "claim_telemetry.py",
    "canonical_runner.py",
    "canonical_publish.py",
    "quality_gate.py",
    "control_extensions.py",
    "agent_matching.py",
    "work_session.py",
]


def sh(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise AssertionError(f"command failed rc={proc.returncode}: {args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(["git", *args], cwd, check=check)


def configure(cwd: Path) -> None:
    git(cwd, "config", "user.name", "UOS Session V2 Test")
    git(cwd, "config", "user.email", "uos@example.invalid")


def setup_remote(td: Path) -> Path:
    seed = td / "seed"
    remote = td / "remote.git"
    seed.mkdir()
    git(seed, "init", "-b", "main")
    configure(seed)
    (seed / "tools").mkdir()
    for name in TOOLS:
        shutil.copy2(SOURCE / "tools" / name, seed / "tools" / name)
    (seed / "orchestration").mkdir()
    (seed / "orchestration/.keep").write_text("\n", encoding="utf-8")
    git(seed, "add", ".")
    git(seed, "commit", "-m", "seed session v2 UOS")
    git(td, "init", "--bare", str(remote))
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path) -> None:
    git(path.parent, "clone", str(remote), str(path))
    configure(path)


def uos(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh([sys.executable, "tools/uos.py", *args], cwd, check=check)


def session(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh([sys.executable, "tools/work_session.py", *args], cwd, check=check)


def publish_two(worker: Path) -> None:
    uos(worker, "project", "init", "--project-id", "DEMO", "--title", "Demo")
    for priority, task in ((1, "TASK_A"), (2, "TASK_B")):
        uos(
            worker,
            "task", "publish",
            "--project", "DEMO",
            "--task-id", task,
            "--title", task,
            "--priority", str(priority),
            "--output", f"projects/DEMO/{task}.txt",
            "--acceptance", "output exists",
        )


def start(worker: Path, agent: str = "AGENT_A") -> dict:
    proc = session(
        worker,
        "start",
        "--agent-id", agent,
        "--minutes", "30",
        "--project", "DEMO",
        "--max-tasks", "2",
        "--capability-tier", "4",
        "--context", "XL",
    )
    return json.loads(proc.stdout)


class WorkSessionV2RecoveryTests(unittest.TestCase):
    def test_completed_current_immediately_continues_to_next_compatible_task(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            clone(remote, worker)
            publish_two(worker)
            started = start(worker)
            sid = started["session_id"]

            first = json.loads(session(worker, "next", "--agent-id", "AGENT_A", "--session-id", sid).stdout)
            self.assertEqual(first["status"], "CLAIM_GRANTED")
            self.assertEqual(first["grant"]["CanonicalID"], "TASK_A")
            token = first["grant"]["LeaseToken"]
            output = worker / "projects/DEMO/TASK_A.txt"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("A\n", encoding="utf-8")
            uos(worker, "complete", "--agent-id", "AGENT_A", "--task", "TASK_A", "--lease-token", token)

            second = json.loads(session(worker, "next", "--agent-id", "AGENT_A", "--session-id", sid).stdout)
            self.assertEqual(second["status"], "CLAIM_GRANTED")
            self.assertEqual(second["grant"]["CanonicalID"], "TASK_B")
            self.assertEqual(second["session"]["completed_tasks"], ["TASK_A"])
            self.assertEqual(second["session"]["metrics"]["tasks_completed"], 1)
            self.assertEqual(second["session"]["metrics"]["claims_succeeded"], 2)

    def test_stale_current_lease_reclaims_exact_same_task_and_returns_new_token(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            clone(remote, worker)
            publish_two(worker)
            started = start(worker)
            sid = started["session_id"]
            first = json.loads(session(worker, "next", "--agent-id", "AGENT_A", "--session-id", sid).stdout)
            self.assertEqual(first["grant"]["CanonicalID"], "TASK_A")
            old_token = first["grant"]["LeaseToken"]

            admin = td / "admin"
            clone(remote, admin)
            lock = admin / "coordination/claims/TASK_A.lock"
            text = lock.read_text(encoding="utf-8")
            lines = []
            for raw_line in text.splitlines():
                if raw_line.startswith("LeaseExpiresAt:"):
                    lines.append("LeaseExpiresAt: 2000-01-01T00:00:00Z")
                else:
                    lines.append(raw_line)
            lock.write_text("\n".join(lines) + "\n", encoding="utf-8")
            git(admin, "add", "coordination/claims/TASK_A.lock")
            git(admin, "commit", "-m", "expire current session lease")
            git(admin, "push", "origin", "main")

            recovered_proc = session(worker, "next", "--agent-id", "AGENT_A", "--session-id", sid, check=False)
            self.assertEqual(recovered_proc.returncode, 0, (recovered_proc.stdout, recovered_proc.stderr))
            recovered = json.loads(recovered_proc.stdout)
            self.assertEqual(recovered["status"], "CURRENT_TASK_RECLAIMED")
            self.assertEqual(recovered["task"], "TASK_A")
            self.assertEqual(recovered["grant"]["CanonicalID"], "TASK_A")
            self.assertEqual(int(recovered["grant"]["LeaseGeneration"]), 2)
            self.assertNotEqual(recovered["grant"]["LeaseToken"], old_token)
            self.assertEqual(recovered["session"]["metrics"]["ownership_recovery_count"], 1)

            check = td / "check"
            clone(remote, check)
            self.assertTrue((check / "coordination/claims/TASK_A.lock").exists())
            self.assertFalse((check / "coordination/claims/TASK_B.lock").exists())


if __name__ == "__main__":
    unittest.main()
