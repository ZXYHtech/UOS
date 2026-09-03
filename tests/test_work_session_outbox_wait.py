from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
TOOLS = [
    "uos.py",
    "claim_broker_v2.py",
    "claim_telemetry.py",
    "completion_outbox.py",
    "canonical_runner.py",
    "canonical_publish.py",
    "quality_gate.py",
    "control_extensions.py",
    "agent_matching.py",
    "work_session.py",
    "claim_observability.py",
]


def sh(args: list[str], cwd: Path, *, check: bool = True, env=None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise AssertionError(f"command failed rc={proc.returncode}: {args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(["git", *args], cwd, check=check)


def configure(cwd: Path) -> None:
    git(cwd, "config", "user.name", "UOS Session Outbox Test")
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
    git(seed, "commit", "-m", "seed session outbox UOS")
    git(td, "init", "--bare", str(remote))
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path) -> None:
    git(path.parent, "clone", str(remote), str(path))
    configure(path)


def uos(cwd: Path, *args: str, check: bool = True, env=None) -> subprocess.CompletedProcess[str]:
    return sh([sys.executable, "tools/uos.py", *args], cwd, check=check, env=env)


def session(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh([sys.executable, "tools/work_session.py", *args], cwd, check=check)


def bootstrap(worker: Path) -> None:
    uos(worker, "project", "init", "--project-id", "DEMO", "--title", "Demo")
    uos(
        worker,
        "task", "publish",
        "--project", "DEMO",
        "--task-id", "TASK_A",
        "--title", "Task A",
        "--role", "WORKER",
        "--output", "projects/DEMO/a.txt",
        "--acceptance", "output exists",
    )


def force_stage(worker: Path, writer: Path, token: str) -> dict:
    output = worker / "projects/DEMO/a.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("session outbox candidate\n", encoding="utf-8")

    env = os.environ.copy()
    env["UOS_CAS_TEST_DELAY_BEFORE_PUSH"] = "1.2"
    proc = subprocess.Popen(
        [
            sys.executable,
            "tools/uos.py",
            "--cas-retries", "1",
            "complete",
            "--agent-id", "AGENT_A",
            "--task", "TASK_A",
            "--lease-token", token,
        ],
        cwd=worker,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(0.45)
    marker = writer / f"race-{time.time_ns()}.txt"
    marker.write_text("advance unrelated main state\n", encoding="utf-8")
    git(writer, "pull", "--ff-only", "origin", "main")
    git(writer, "add", marker.name)
    git(writer, "commit", "-m", "advance unrelated main state")
    git(writer, "push", "origin", "main")
    out, err = proc.communicate(timeout=60)
    if proc.returncode != 7:
        raise AssertionError((proc.returncode, out, err))
    packet = json.loads(out)
    if packet.get("status") != "COMPLETION_STAGED":
        raise AssertionError(packet)
    return packet


class WorkSessionOutboxWaitTests(unittest.TestCase):
    def test_session_waits_for_exact_current_grant_outbox_then_closes_after_ingest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            writer = td / "writer"
            clone(remote, worker)
            bootstrap(worker)
            clone(remote, writer)

            started = json.loads(
                session(
                    worker,
                    "start",
                    "--agent-id", "AGENT_A",
                    "--minutes", "30",
                    "--project", "DEMO",
                    "--max-tasks", "1",
                    "--capability-tier", "2",
                    "--tools", "git;python",
                    "--context", "M",
                    "--roles", "WORKER",
                ).stdout
            )
            session_id = started["session_id"]
            first = json.loads(
                session(worker, "next", "--agent-id", "AGENT_A", "--session-id", session_id).stdout
            )
            self.assertEqual(first["status"], "CLAIM_GRANTED", first)
            grant = first["grant"]
            self.assertEqual(grant["CanonicalID"], "TASK_A")

            staged = force_stage(worker, writer, grant["LeaseToken"])
            waiting = json.loads(
                session(worker, "next", "--agent-id", "AGENT_A", "--session-id", session_id).stdout
            )
            self.assertEqual(waiting["status"], "WAITING_INTEGRATION", waiting)
            self.assertEqual(waiting["task"], "TASK_A")
            self.assertEqual(waiting["outbox"]["grant_id"], grant["GrantID"])
            self.assertEqual(waiting["outbox"]["outbox_ref"], staged["outbox"]["outbox_ref"])
            self.assertEqual(waiting["session"]["current_task"], "TASK_A")
            self.assertNotIn("TASK_A", waiting["session"]["completed_tasks"])

            queue = json.loads(uos(worker, "outbox", "status").stdout)
            self.assertEqual(queue["remote_refs_total"], 1, queue)
            self.assertEqual(queue["valid_queue_depth"], 1, queue)
            self.assertEqual(queue["canonical_receipts_total"], 0, queue)
            self.assertEqual(queue["batch_count"], 0, queue)

            observation = json.loads(
                sh([sys.executable, "tools/claim_observability.py"], worker).stdout
            )
            self.assertEqual(observation["completion_outbox"]["valid_queue_depth"], 1, observation)
            self.assertEqual(observation["completion_outbox"]["canonical_receipts_total"], 0, observation)

            ingested = json.loads(uos(worker, "outbox", "ingest", "--max-batch", "16").stdout)
            self.assertEqual(ingested["status"], "OUTBOX_INGESTED", ingested)
            self.assertEqual(ingested["batch_size"], 1)

            after_queue = json.loads(uos(worker, "outbox", "status").stdout)
            self.assertEqual(after_queue["remote_refs_total"], 1, after_queue)
            self.assertEqual(after_queue["valid_queue_depth"], 0, after_queue)
            self.assertEqual(after_queue["canonical_receipts_total"], 1, after_queue)
            self.assertEqual(after_queue["retained_ingested_refs"], 1, after_queue)
            self.assertEqual(after_queue["batch_count"], 1, after_queue)
            self.assertEqual(after_queue["batch_size_max"], 1, after_queue)
            self.assertGreaterEqual(after_queue["integration_wait_ms_p50"], 0, after_queue)

            after_observation = json.loads(
                sh([sys.executable, "tools/claim_observability.py"], worker).stdout
            )
            self.assertEqual(after_observation["completion_outbox"]["valid_queue_depth"], 0)
            self.assertEqual(after_observation["completion_outbox"]["canonical_receipts_total"], 1)
            self.assertEqual(after_observation["completion_outbox"]["batch_size_max"], 1)

            final = json.loads(
                session(worker, "next", "--agent-id", "AGENT_A", "--session-id", session_id).stdout
            )
            self.assertEqual(final["status"], "SESSION_STOPPED", final)
            self.assertEqual(final["reason"], "MAX_TASKS_REACHED", final)
            self.assertIn("TASK_A", final["session"]["completed_tasks"])
            self.assertEqual(final["session"]["current_task"], "")

    def test_old_generation_outbox_ref_does_not_trigger_wait_after_reclaim(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            writer = td / "writer"
            clone(remote, worker)
            bootstrap(worker)
            clone(remote, writer)

            started = json.loads(
                session(
                    worker,
                    "start",
                    "--agent-id", "AGENT_A",
                    "--minutes", "30",
                    "--project", "DEMO",
                    "--max-tasks", "1",
                    "--capability-tier", "2",
                    "--tools", "git;python",
                    "--context", "M",
                    "--roles", "WORKER",
                ).stdout
            )
            session_id = started["session_id"]
            first = json.loads(session(worker, "next", "--agent-id", "AGENT_A", "--session-id", session_id).stdout)
            grant1 = first["grant"]
            force_stage(worker, writer, grant1["LeaseToken"])

            admin = td / "admin"
            clone(remote, admin)
            lock = admin / "coordination/claims/TASK_A.lock"
            lines = [
                "LeaseExpiresAt: 2000-01-01T00:00:00Z" if line.startswith("LeaseExpiresAt:") else line
                for line in lock.read_text(encoding="utf-8").splitlines()
            ]
            lock.write_text("\n".join(lines) + "\n", encoding="utf-8")
            git(admin, "add", "coordination/claims/TASK_A.lock")
            git(admin, "commit", "-m", "expire first generation")
            git(admin, "push", "origin", "main")

            recovered = json.loads(
                session(worker, "next", "--agent-id", "AGENT_A", "--session-id", session_id).stdout
            )
            self.assertEqual(recovered["status"], "CURRENT_TASK_RECLAIMED", recovered)
            self.assertEqual(int(recovered["grant"]["LeaseGeneration"]), 2)
            self.assertNotEqual(recovered["grant"]["GrantID"], grant1["GrantID"])

            again = json.loads(
                session(worker, "next", "--agent-id", "AGENT_A", "--session-id", session_id).stdout
            )
            self.assertEqual(again["status"], "WORK_CURRENT_TASK", again)
            self.assertNotEqual(again["status"], "WAITING_INTEGRATION")


if __name__ == "__main__":
    unittest.main()
