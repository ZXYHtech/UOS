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
    "uos.py", "claim_broker_v2.py", "claim_telemetry.py", "completion_outbox.py",
    "canonical_runner.py",
    "canonical_publish.py",
    "quality_gate.py",
    "control_extensions.py",
    "agent_matching.py",
    "task_requirements.py",
    "work_session.py",
]
EPOCH = "SESSION_TEST_EPOCH"


def sh(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise AssertionError(f"command failed rc={proc.returncode}: {args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(["git", *args], cwd, check=check)


def configure(cwd: Path) -> None:
    git(cwd, "config", "user.name", "UOS Session Test")
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
        f"ExecutionEpoch: {EPOCH}\nCriticalCommandsRequireEpochAck: true\n",
        encoding="utf-8",
    )
    (seed / ".uos/QUALITY_VISIBILITY_POLICY.yaml").write_text(
        "Schema: UOS_QUALITY_VISIBILITY_V1\n"
        "RuleVersion: SESSION_TEST\n"
        "RuleEpoch: 1\n"
        "Enabled: true\n"
        "Review:\n"
        "  WarmupRequired: 3\n"
        "  WarmupMaxConcurrentClaims: 1\n"
        "  SampleEvery: 5\n"
        "  HighRiskAlwaysReview: true\n"
        "  BlockNewClaimsWhilePending: true\n"
        "Presentation:\n"
        "  AgentMustPresentResultInConversation: true\n",
        encoding="utf-8",
    )
    git(seed, "add", ".")
    git(seed, "commit", "-m", "seed session UOS")
    git(td, "init", "--bare", str(remote))
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path) -> None:
    git(path.parent, "clone", str(remote), str(path))
    configure(path)


def uos(cwd: Path, *business: str) -> subprocess.CompletedProcess[str]:
    return sh([sys.executable, "tools/uos.py", "--ack-execution-epoch", EPOCH, *business], cwd)


class WorkSessionGitCasTests(unittest.TestCase):
    def test_session_skips_incompatible_task_and_stops_for_review(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            clone(remote, worker)

            uos(worker, "project", "init", "--project-id", "DEMO", "--title", "Demo")
            uos(
                worker,
                "task", "publish",
                "--project", "DEMO",
                "--task-id", "TASK_HARD",
                "--title", "Hard task",
                "--priority", "1",
                "--min-capability", "4",
                "--context", "L",
                "--output", "projects/DEMO/hard.txt",
                "--acceptance", "hard output exists",
            )
            uos(
                worker,
                "task", "publish",
                "--project", "DEMO",
                "--task-id", "TASK_SAFE",
                "--title", "Safe task",
                "--priority", "2",
                "--min-capability", "2",
                "--context", "M",
                "--output", "projects/DEMO/safe.txt",
                "--acceptance", "safe output exists",
            )
            sh(
                [
                    sys.executable, "tools/task_requirements.py",
                    "--ack-execution-epoch", EPOCH,
                    "set",
                    "--project", "DEMO", "--task", "TASK_HARD",
                    "--min-capability", "4", "--context", "L",
                    "--tools", "python;hfss", "--allowed-roles", "ENGINEER",
                ],
                worker,
            )
            sh(
                [
                    sys.executable, "tools/task_requirements.py",
                    "--ack-execution-epoch", EPOCH,
                    "set",
                    "--project", "DEMO", "--task", "TASK_SAFE",
                    "--min-capability", "2", "--context", "M",
                    "--tools", "python;git", "--allowed-roles", "WORKER",
                ],
                worker,
            )

            started = json.loads(
                sh(
                    [
                        sys.executable, "tools/work_session.py",
                        "--ack-execution-epoch", EPOCH,
                        "start",
                        "--agent-id", "AGENT_1",
                        "--minutes", "30",
                        "--project", "DEMO",
                        "--max-tasks", "2",
                        "--capability-tier", "2",
                        "--tools", "python;git",
                        "--context", "M",
                        "--roles", "WORKER",
                    ],
                    worker,
                ).stdout
            )
            session_id = started["session_id"]

            first = json.loads(
                sh(
                    [
                        sys.executable, "tools/work_session.py",
                        "--ack-execution-epoch", EPOCH,
                        "next",
                        "--agent-id", "AGENT_1",
                        "--session-id", session_id,
                    ],
                    worker,
                ).stdout
            )
            self.assertEqual(first["status"], "CLAIM_GRANTED")
            self.assertEqual(first["grant"]["CanonicalID"], "TASK_SAFE")
            token = first["grant"]["LeaseToken"]

            output = worker / "projects/DEMO/safe.txt"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("safe result\n", encoding="utf-8")
            complete = json.loads(
                uos(
                    worker,
                    "complete",
                    "--agent-id", "AGENT_1",
                    "--task", "TASK_SAFE",
                    "--lease-token", token,
                ).stdout
            )
            self.assertEqual(complete["quality_visibility"]["review_status"], "PENDING")

            blocked = sh(
                [
                    sys.executable, "tools/work_session.py",
                    "--ack-execution-epoch", EPOCH,
                    "next",
                    "--agent-id", "AGENT_1",
                    "--session-id", session_id,
                ],
                worker,
                check=False,
            )
            self.assertEqual(blocked.returncode, 6)
            blocked_json = json.loads(blocked.stdout)
            self.assertEqual(blocked_json["status"], "STOP_REVIEW_PENDING")

            check = td / "check"
            clone(remote, check)
            self.assertFalse((check / "coordination/claims/TASK_HARD.lock").exists())
            self.assertTrue((check / "coordination/completed/TASK_SAFE.done").exists())
            receipt = json.loads((check / "coordination/quality/durability/TASK_SAFE.json").read_text())
            self.assertEqual(receipt["status"], "DURABLE_READY")

            sh(
                [sys.executable, "tools/quality_gate.py", "review", "accept", "--task", "TASK_SAFE", "--by", "OPERATOR"],
                worker,
            )
            no_match = sh(
                [
                    sys.executable, "tools/work_session.py",
                    "--ack-execution-epoch", EPOCH,
                    "next",
                    "--agent-id", "AGENT_1",
                    "--session-id", session_id,
                ],
                worker,
                check=False,
            )
            self.assertEqual(no_match.returncode, 4)
            no_match_json = json.loads(no_match.stdout)
            self.assertEqual(no_match_json["status"], "STOP_NO_MATCH")


if __name__ == "__main__":
    unittest.main()
