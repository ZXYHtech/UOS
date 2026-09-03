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
]


def sh(args: list[str], cwd: Path, *, check: bool = True, env=None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise AssertionError(f"command failed rc={proc.returncode}: {args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(["git", *args], cwd, check=check)


def configure(cwd: Path) -> None:
    git(cwd, "config", "user.name", "UOS Outbox Test")
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
    git(seed, "commit", "-m", "seed outbox UOS")
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


def bootstrap(worker: Path) -> None:
    uos(worker, "project", "init", "--project-id", "DEMO", "--title", "Demo")
    uos(
        worker,
        "task", "publish",
        "--project", "DEMO",
        "--task-id", "TASK_A",
        "--title", "Task A",
        "--output", "projects/DEMO/a.txt",
        "--acceptance", "output exists",
    )


def force_stage(remote: Path, worker: Path, writer: Path, token: str) -> dict:
    output = worker / "projects/DEMO/a.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("completion candidate\n", encoding="utf-8")

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
    marker.write_text("advance main without touching task\n", encoding="utf-8")
    git(writer, "pull", "--ff-only", "origin", "main")
    git(writer, "add", marker.name)
    git(writer, "commit", "-m", "advance unrelated canonical state")
    git(writer, "push", "origin", "main")
    out, err = proc.communicate(timeout=60)
    if proc.returncode != 7:
        raise AssertionError((proc.returncode, out, err))
    packet = json.loads(out)
    if packet.get("status") != "COMPLETION_STAGED":
        raise AssertionError(packet)
    return packet


class CompletionOutboxFallbackTests(unittest.TestCase):
    def test_ref_race_exhaustion_stages_then_mechanical_ingest_completes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            writer = td / "writer"
            clone(remote, worker)
            bootstrap(worker)
            clone(remote, writer)

            grant = json.loads(uos(worker, "claim", "--agent-id", "AGENT_A", "--project", "DEMO", "--task", "TASK_A").stdout)
            packet = force_stage(remote, worker, writer, grant["LeaseToken"])
            self.assertFalse(packet["canonical_done"])
            self.assertTrue(packet["outbox"]["outbox_ref"].startswith("uos-outbox/DEMO/TASK_A/AGENT_A/"))

            before = td / "before"
            clone(remote, before)
            self.assertFalse((before / "coordination/completed/TASK_A.done").exists())
            self.assertTrue((before / "coordination/claims/TASK_A.lock").exists())
            self.assertFalse((before / "projects/DEMO/a.txt").exists())

            status = json.loads(uos(worker, "outbox", "status").stdout)
            self.assertEqual(status["valid_queue_depth"], 1, status)

            ingested = json.loads(uos(worker, "outbox", "ingest", "--max-batch", "16").stdout)
            self.assertEqual(ingested["status"], "OUTBOX_INGESTED", ingested)
            self.assertEqual(ingested["batch_size"], 1)

            check = td / "check"
            clone(remote, check)
            self.assertEqual((check / "projects/DEMO/a.txt").read_text(encoding="utf-8"), "completion candidate\n")
            self.assertTrue((check / "coordination/completed/TASK_A.done").exists())
            self.assertTrue((check / "coordination/quality/durability/TASK_A.json").exists())
            self.assertFalse((check / "coordination/claims/TASK_A.lock").exists())
            receipt = check / packet["outbox"]["receipt_path"]
            self.assertTrue(receipt.exists())
            receipt_data = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(receipt_data["status"], "INGESTED")

    def test_reclaimed_task_fences_staged_prior_generation_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            writer = td / "writer"
            clone(remote, worker)
            bootstrap(worker)
            clone(remote, writer)

            grant = json.loads(uos(worker, "claim", "--agent-id", "AGENT_A", "--project", "DEMO", "--task", "TASK_A").stdout)
            force_stage(remote, worker, writer, grant["LeaseToken"])

            admin = td / "admin"
            clone(remote, admin)
            lock = admin / "coordination/claims/TASK_A.lock"
            lines = []
            for raw_line in lock.read_text(encoding="utf-8").splitlines():
                lines.append("LeaseExpiresAt: 2000-01-01T00:00:00Z" if raw_line.startswith("LeaseExpiresAt:") else raw_line)
            lock.write_text("\n".join(lines) + "\n", encoding="utf-8")
            git(admin, "add", "coordination/claims/TASK_A.lock")
            git(admin, "commit", "-m", "expire staged owner lease")
            git(admin, "push", "origin", "main")

            contender = td / "contender"
            clone(remote, contender)
            new_grant = json.loads(uos(contender, "claim", "--agent-id", "AGENT_B", "--project", "DEMO", "--task", "TASK_A").stdout)
            self.assertEqual(int(new_grant["LeaseGeneration"]), 2)

            result = json.loads(uos(worker, "outbox", "ingest", "--max-batch", "16").stdout)
            self.assertEqual(result["status"], "OUTBOX_INGEST_NOOP", result)
            self.assertEqual(result["accepted"], 0)
            self.assertTrue(any("OUTBOX_FENCED" in item for item in result.get("messages", [])), result)

            check = td / "check"
            clone(remote, check)
            self.assertFalse((check / "coordination/completed/TASK_A.done").exists())
            current = (check / "coordination/claims/TASK_A.lock").read_text(encoding="utf-8")
            self.assertIn("AgentID: AGENT_B", current)
            self.assertIn("LeaseGeneration: 2", current)

    def test_non_ownership_error_never_creates_outbox_ref(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            clone(remote, worker)
            bootstrap(worker)
            grant = json.loads(uos(worker, "claim", "--agent-id", "AGENT_A", "--project", "DEMO", "--task", "TASK_A").stdout)
            output = worker / "projects/DEMO/a.txt"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("x\n", encoding="utf-8")
            proc = uos(
                worker,
                "--cas-retries", "1",
                "complete",
                "--agent-id", "AGENT_A",
                "--task", "TASK_A",
                "--lease-token", grant["LeaseToken"] + "BAD",
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            refs = git(worker, "ls-remote", "--heads", "origin", "refs/heads/uos-outbox/*", check=False).stdout.strip()
            self.assertEqual(refs, "")


if __name__ == "__main__":
    unittest.main()
