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
    git(cwd, "config", "user.name", "UOS Telemetry Test")
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
    git(seed, "commit", "-m", "seed telemetry UOS")
    git(td, "init", "--bare", str(remote))
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path) -> None:
    git(path.parent, "clone", str(remote), str(path))
    configure(path)


def uos(cwd: Path, *args: str, env=None) -> subprocess.CompletedProcess[str]:
    return sh([sys.executable, "tools/uos.py", *args], cwd, env=env)


class ClaimTelemetryGitCasTests(unittest.TestCase):
    def test_winning_claim_records_retry_and_runtime_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            admin = td / "admin"
            clone(remote, admin)
            uos(admin, "project", "init", "--project-id", "DEMO", "--title", "Demo")
            uos(
                admin,
                "task", "publish",
                "--project", "DEMO",
                "--task-id", "TASK_A",
                "--title", "Task A",
                "--output", "projects/DEMO/a.txt",
                "--acceptance", "output exists",
            )

            worker, writer = td / "worker", td / "writer"
            clone(remote, worker)
            clone(remote, writer)

            env = os.environ.copy()
            env["UOS_CAS_TEST_DELAY_BEFORE_PUSH"] = "1.5"
            proc = subprocess.Popen(
                [sys.executable, "tools/uos.py", "claim", "--agent-id", "AGENT_A", "--project", "DEMO", "--task", "TASK_A"],
                cwd=worker,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(0.6)
            marker = writer / "race-marker.txt"
            marker.write_text("advance canonical ref\n", encoding="utf-8")
            git(writer, "add", "race-marker.txt")
            git(writer, "commit", "-m", "advance canonical during claim candidate")
            git(writer, "push", "origin", "main")

            out, err = proc.communicate(timeout=60)
            self.assertEqual(proc.returncode, 0, (out, err))
            grant = json.loads(out)
            runtime = grant.get("canonical_runtime") or {}
            self.assertGreaterEqual(int(runtime.get("cas_attempt") or 0), 2, grant)
            self.assertGreaterEqual(int(runtime.get("ref_races") or 0), 1, grant)
            self.assertGreater(int(runtime.get("runner_elapsed_ms") or 0), 0, grant)
            self.assertTrue(runtime.get("canonical_commit"), grant)
            telemetry_rel = str(runtime.get("telemetry_path") or "")
            self.assertTrue(telemetry_rel, grant)

            check = td / "check"
            clone(remote, check)
            event = json.loads((check / telemetry_rel).read_text(encoding="utf-8"))
            self.assertEqual(event["schema"], "UOS_CLAIM_TELEMETRY_V1")
            self.assertEqual(event["canonical_id"], "TASK_A")
            self.assertEqual(event["agent_id"], "AGENT_A")
            self.assertEqual(event["claim_authority"], "UOS_CLAIM_BROKER_V2")
            self.assertGreaterEqual(int(event["cas_attempt"]), 2)
            self.assertGreaterEqual(int(event["ref_races_before_candidate"]), 1)


if __name__ == "__main__":
    unittest.main()
