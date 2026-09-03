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
    "uos.py", "claim_broker_v2.py", "claim_telemetry.py",
    "canonical_runner.py",
    "canonical_publish.py",
    "quality_gate.py",
    "control_extensions.py",
]


def sh(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise AssertionError(f"cmd failed {args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(["git", *args], cwd, check=check)


def configure(cwd: Path) -> None:
    git(cwd, "config", "user.name", "UOS Warmup Test")
    git(cwd, "config", "user.email", "uos@example.invalid")


def write_policy(root: Path) -> None:
    path = root / ".uos/QUALITY_VISIBILITY_POLICY.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Schema: UOS_QUALITY_VISIBILITY_V1\n"
        "RuleVersion: TEST\n"
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


class WarmupSerialClaimTests(unittest.TestCase):
    def test_second_task_cannot_start_before_first_result_review(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            seed = td / "seed"
            remote = td / "remote.git"
            seed.mkdir()
            git(seed, "init", "-b", "main")
            configure(seed)
            (seed / "tools").mkdir()
            for name in TOOLS:
                shutil.copy2(SOURCE / "tools" / name, seed / "tools" / name)
            write_policy(seed)
            (seed / "orchestration").mkdir(exist_ok=True)
            (seed / "orchestration/.keep").write_text("\n", encoding="utf-8")
            git(seed, "add", ".")
            git(seed, "commit", "-m", "seed")
            git(td, "init", "--bare", str(remote))
            git(seed, "remote", "add", "origin", str(remote))
            git(seed, "push", "-u", "origin", "main")
            git(remote, "symbolic-ref", "HEAD", "refs/heads/main")

            worker = td / "worker"
            git(td, "clone", str(remote), str(worker))
            configure(worker)

            def uos(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
                return sh([sys.executable, "tools/uos.py", *args], worker, check=check)

            uos("project", "init", "--project-id", "DEMO", "--title", "Demo")
            for task in ("TASK_A", "TASK_B"):
                uos(
                    "task", "publish", "--project", "DEMO", "--task-id", task,
                    "--title", task, "--output", f"projects/DEMO/{task}.md", "--acceptance", "result exists",
                )

            first = json.loads(uos("claim", "--agent-id", "AGENT_A", "--task", "TASK_A").stdout)
            self.assertEqual(first["CanonicalID"], "TASK_A")

            second = uos("claim", "--agent-id", "AGENT_B", "--task", "TASK_B", check=False)
            self.assertEqual(second.returncode, 6)
            packet = json.loads(second.stdout)
            self.assertEqual(packet["status"], "REVIEW_BLOCKED")
            self.assertIn("serialized", packet["message"])


if __name__ == "__main__":
    unittest.main()
