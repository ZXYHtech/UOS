from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
TOOLS = [
    "uos.py", "claim_broker_v2.py",
    "canonical_runner.py",
    "canonical_publish.py",
    "quality_gate.py",
    "control_extensions.py",
    "agent_matching.py",
    "work_session.py",
    "partial_handoff.py",
    "handoff_takeover.py",
]
EPOCH = "EPOCH_HANDOFF_GIT_1"


def sh(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode:
        raise AssertionError(
            f"command failed rc={proc.returncode}: {args}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(["git", *args], cwd, check=check)


def configure(cwd: Path) -> None:
    git(cwd, "config", "user.name", "UOS Handoff Test")
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
    (seed / ".uos").mkdir()
    (seed / ".uos/EXECUTION_CONTRACT.yaml").write_text(
        "Schema: UOS_EXECUTION_CONTRACT_V1\n"
        f"ExecutionEpoch: {EPOCH}\n"
        "CriticalCommandsRequireEpochAck: true\n",
        encoding="utf-8",
    )
    git(seed, "add", ".")
    git(seed, "commit", "-m", "seed handoff UOS")
    git(td, "init", "--bare", str(remote))
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path) -> None:
    git(path.parent, "clone", str(remote), str(path))
    configure(path)


def uos(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(
        [sys.executable, "tools/uos.py", "--ack-execution-epoch", EPOCH, *args],
        cwd,
        check=check,
    )


def session(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(
        [sys.executable, "tools/work_session.py", "--ack-execution-epoch", EPOCH, *args],
        cwd,
        check=check,
    )


def handoff(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(
        [sys.executable, "tools/partial_handoff.py", "--ack-execution-epoch", EPOCH, *args],
        cwd,
        check=check,
    )


def takeover(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(
        [sys.executable, "tools/handoff_takeover.py", "--ack-execution-epoch", EPOCH, *args],
        cwd,
        check=check,
    )


def parse_scalar(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ":" in raw and not raw.lstrip().startswith(("#", "-")):
            key, value = raw.split(":", 1)
            out[key.strip()] = value.strip()
    return out


class PartialHandoffGitCasTests(unittest.TestCase):
    def test_handoff_ready_preserves_checkpoint_and_successor_reclaims_generation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            owner = td / "owner"
            successor = td / "successor"
            clone(remote, owner)
            clone(remote, successor)

            uos(owner, "project", "init", "--project-id", "DEMO", "--title", "Demo")
            uos(
                owner,
                "task",
                "publish",
                "--project",
                "DEMO",
                "--task-id",
                "TASK_A",
                "--title",
                "Task A",
                "--output",
                "projects/DEMO/final.txt",
                "--acceptance",
                "final exists",
            )

            started = json.loads(
                session(
                    owner,
                    "start",
                    "--agent-id",
                    "AGENT_A",
                    "--minutes",
                    "30",
                    "--project",
                    "DEMO",
                    "--max-tasks",
                    "3",
                    "--capability-tier",
                    "1",
                    "--context",
                    "S",
                ).stdout
            )
            session_id = started["session_id"]
            step = json.loads(
                session(
                    owner,
                    "next",
                    "--agent-id",
                    "AGENT_A",
                    "--session-id",
                    session_id,
                ).stdout
            )
            self.assertEqual(step["status"], "CLAIM_GRANTED")
            grant_a = step["grant"]
            self.assertEqual(grant_a["CanonicalID"], "TASK_A")
            self.assertEqual(int(grant_a["LeaseGeneration"]), 1)

            checkpoint = owner / "projects/DEMO/checkpoint.txt"
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.write_text("safe partial state\n", encoding="utf-8")

            hand = json.loads(
                handoff(
                    owner,
                    "create",
                    "--agent-id",
                    "AGENT_A",
                    "--task",
                    "TASK_A",
                    "--lease-token",
                    grant_a["LeaseToken"],
                    "--state",
                    "HANDOFF_READY",
                    "--completed",
                    "parsed inputs and saved checkpoint",
                    "--artifact",
                    "projects/DEMO/checkpoint.txt",
                    "--validation-run",
                    "partial smoke",
                    "--known-failures",
                    "final output not generated",
                    "--next-action",
                    "restore checkpoint then finish final output",
                    "--context-ref",
                    "orchestration/projects/DEMO/PROJECT.yaml",
                ).stdout
            )
            self.assertEqual(hand["state"], "HANDOFF_READY")
            self.assertFalse(hand["authority"]["transfers_ownership"])
            self.assertEqual(hand["release"]["expected_successor_generation"], 2)
            self.assertEqual(hand["derived_state_refresh"]["status"], "REFRESHED")
            checkpoint_rel = hand["artifacts"][0]["checkpoint_path"]
            self.assertEqual(hand["artifacts"][0]["source_path"], "projects/DEMO/checkpoint.txt")
            self.assertTrue(checkpoint_rel.startswith("coordination/handoff_artifacts/TASK_A/"))

            inspect = td / "inspect"
            clone(remote, inspect)
            self.assertTrue((inspect / "coordination/handoffs/TASK_A.handoff").exists())
            self.assertFalse((inspect / "projects/DEMO/checkpoint.txt").exists())
            self.assertEqual(
                (inspect / checkpoint_rel).read_text(encoding="utf-8"),
                "safe partial state\n",
            )
            self.assertFalse((inspect / "coordination/completed/TASK_A.done").exists())
            lock_a = parse_scalar(inspect / "coordination/claims/TASK_A.lock")
            expires = datetime.fromisoformat(lock_a["LeaseExpiresAt"].replace("Z", "+00:00"))
            self.assertLessEqual(expires, datetime.now(timezone.utc))
            self.assertEqual(lock_a["HandoffState"], "HANDOFF_READY")
            session_state = json.loads(
                (inspect / f"coordination/work_sessions/AGENT_A/{session_id}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(session_state["state"], "STOPPED")
            self.assertEqual(session_state["stop_reason"], "HANDOFF_READY")
            market = (inspect / "coordination/runtime/WORK_MARKET.csv").read_text(encoding="utf-8")
            self.assertIn("TASK_A", market)

            old_renew = uos(
                owner,
                "renew",
                "--agent-id",
                "AGENT_A",
                "--task",
                "TASK_A",
                "--lease-token",
                grant_a["LeaseToken"],
                check=False,
            )
            self.assertEqual(old_renew.returncode, 2)
            self.assertIn("FENCED", old_renew.stderr)

            take = json.loads(
                takeover(
                    successor,
                    "--agent-id",
                    "AGENT_B",
                    "--task",
                    "TASK_A",
                ).stdout
            )
            self.assertEqual(take["status"], "CLAIM_GRANTED_WITH_HANDOFF")
            grant_b = take["grant"]
            read = take["handoff"]
            self.assertEqual(int(grant_b["LeaseGeneration"]), 2)
            self.assertNotEqual(grant_b["LeaseToken"], grant_a["LeaseToken"])
            self.assertTrue(read["successor"]["ownership_verified"])
            self.assertTrue(read["successor"]["generation_advanced"])
            self.assertEqual(read["artifacts"][0]["checkpoint_path"], checkpoint_rel)
            self.assertIn("UNVERIFIED_PARTIAL_WORK", read["warning"])

            old_complete = uos(
                owner,
                "complete",
                "--agent-id",
                "AGENT_A",
                "--task",
                "TASK_A",
                "--lease-token",
                grant_a["LeaseToken"],
                check=False,
            )
            self.assertEqual(old_complete.returncode, 2)
            self.assertIn("FENCED", old_complete.stderr)

            final = successor / "projects/DEMO/final.txt"
            final.parent.mkdir(parents=True, exist_ok=True)
            final.write_text("successor completed after revalidation\n", encoding="utf-8")
            uos(
                successor,
                "complete",
                "--agent-id",
                "AGENT_B",
                "--task",
                "TASK_A",
                "--lease-token",
                grant_b["LeaseToken"],
            )

            check = td / "check"
            clone(remote, check)
            self.assertTrue((check / "coordination/completed/TASK_A.done").exists())
            self.assertFalse((check / "coordination/claims/TASK_A.lock").exists())
            self.assertTrue((check / "coordination/handoffs/TASK_A.handoff").exists())
            self.assertTrue((check / checkpoint_rel).exists())
            self.assertEqual(
                (check / "projects/DEMO/final.txt").read_text(encoding="utf-8"),
                "successor completed after revalidation\n",
            )


if __name__ == "__main__":
    unittest.main()
