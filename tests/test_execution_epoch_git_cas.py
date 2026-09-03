from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
TOOLS = ["uos.py", "claim_broker_v2.py", "claim_telemetry.py", "canonical_runner.py", "canonical_publish.py", "quality_gate.py", "control_extensions.py"]
EPOCH = "EPOCH_INTEGRATION_1"


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
    git(cwd, "config", "user.name", "UOS Epoch Integration Test")
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
    (seed / ".uos/QUALITY_VISIBILITY_POLICY.yaml").write_text(
        "Schema: UOS_QUALITY_VISIBILITY_V1\n"
        "RuleVersion: TEST_VISIBILITY_V1\n"
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
    git(seed, "commit", "-m", "seed epoch-gated UOS")
    git(td, "init", "--bare", str(remote))
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path) -> None:
    git(path.parent, "clone", str(remote), str(path))
    configure(path)


def uos(cwd: Path, *business_args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(
        [
            sys.executable,
            "tools/uos.py",
            "--ack-execution-epoch",
            EPOCH,
            *business_args,
        ],
        cwd,
        check=check,
    )


class ExecutionEpochGitCasTests(unittest.TestCase):
    def test_epoch_ack_preserves_svg_preview_and_durability_gates(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            clone(remote, worker)

            stale = sh(
                [sys.executable, "tools/uos.py", "claim", "--agent-id", "AGENT_STALE", "--project", "DEMO"],
                worker,
                check=False,
            )
            self.assertEqual(stale.returncode, 2)
            self.assertIn("REBOOT_REQUIRED", stale.stderr)

            uos(worker, "project", "init", "--project-id", "DEMO", "--title", "Demo")
            uos(
                worker,
                "task",
                "publish",
                "--project",
                "DEMO",
                "--task-id",
                "TASK_SVG",
                "--title",
                "SVG artifact",
                "--output",
                "projects/DEMO/figure.svg",
                "--acceptance",
                "SVG and PNG preview exist",
            )

            inspect = td / "inspect-publish"
            clone(remote, inspect)
            catalog = inspect / "orchestration/projects/DEMO/TASK_CATALOG.csv"
            with catalog.open(newline="", encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            outputs = set(row["output"].split(";"))
            self.assertEqual(outputs, {"projects/DEMO/figure.svg", "projects/DEMO/figure.png"})

            claim = json.loads(
                uos(worker, "claim", "--agent-id", "AGENT_1", "--project", "DEMO").stdout
            )
            artifact_dir = worker / "projects/DEMO"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            (artifact_dir / "figure.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>\n',
                encoding="utf-8",
            )
            (artifact_dir / "figure.png").write_bytes(b"PNG-PREVIEW-TEST")

            complete = json.loads(
                uos(
                    worker,
                    "complete",
                    "--agent-id",
                    "AGENT_1",
                    "--task",
                    "TASK_SVG",
                    "--lease-token",
                    claim["LeaseToken"],
                ).stdout
            )
            self.assertTrue(complete["quality_visibility"]["review_required"])
            self.assertEqual(complete["quality_visibility"]["review_status"], "PENDING")

            check = td / "check"
            clone(remote, check)
            self.assertTrue((check / "projects/DEMO/figure.svg").exists())
            self.assertTrue((check / "projects/DEMO/figure.png").exists())
            receipt = json.loads(
                (check / "coordination/quality/durability/TASK_SVG.json").read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["status"], "DURABLE_READY")
            self.assertEqual(
                {item["path"] for item in receipt["artifacts"]},
                {"projects/DEMO/figure.svg", "projects/DEMO/figure.png"},
            )
            event = json.loads(
                (check / "coordination/quality/events/TASK_SVG.json").read_text(encoding="utf-8")
            )
            self.assertEqual(event["review_status"], "PENDING")
            self.assertTrue((check / "coordination/completed/TASK_SVG.done").exists())
            self.assertFalse((check / "coordination/claims/TASK_SVG.lock").exists())


if __name__ == "__main__":
    unittest.main()
