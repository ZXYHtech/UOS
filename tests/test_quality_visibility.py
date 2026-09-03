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
TOOLS = ["uos.py", "claim_broker_v2.py", "claim_telemetry.py", "completion_outbox.py", "canonical_runner.py", "canonical_publish.py", "quality_gate.py"]
sys.path.insert(0, str(SOURCE / "tools"))

from quality_gate import (  # noqa: E402
    QualityGateError,
    claim_block_packet,
    event_path,
    expand_outputs,
    record_completion,
)


def sh(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise AssertionError(f"cmd failed {args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(["git", *args], cwd, check=check)


def configure(cwd: Path) -> None:
    git(cwd, "config", "user.name", "UOS Quality Test")
    git(cwd, "config", "user.email", "uos@example.invalid")


def write_policy(root: Path) -> None:
    path = root / ".uos/QUALITY_VISIBILITY_POLICY.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Schema: UOS_QUALITY_VISIBILITY_V1\n"
        "RuleVersion: TEST_VISIBILITY\n"
        "RuleEpoch: 1\n"
        "Enabled: true\n"
        "Review:\n"
        "  WarmupRequired: 3\n"
        "  SampleEvery: 5\n"
        "  HighRiskAlwaysReview: true\n"
        "  BlockNewClaimsWhilePending: true\n"
        "Presentation:\n"
        "  AgentMustPresentResultInConversation: true\n",
        encoding="utf-8",
    )


def write_catalog(root: Path, rows: list[dict[str, str]]) -> None:
    path = root / "orchestration/projects/DEMO/TASK_CATALOG.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "project_id", "title", "risk_tier", "output"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class QualityVisibilityUnitTests(unittest.TestCase):
    def test_preview_expansion(self) -> None:
        self.assertEqual(expand_outputs("art/figure.svg"), "art/figure.svg;art/figure.png")
        self.assertEqual(expand_outputs("web/index.html"), "web/index.html;web/index.preview.png")
        self.assertEqual(expand_outputs("deck/demo.pptx"), "deck/demo.pptx;deck/demo.preview.pdf")

    def test_first_three_then_deterministic_sample(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_policy(root)
            rows = []
            for index in range(1, 6):
                task = f"TASK_{index}"
                output = f"projects/DEMO/{index}.md"
                rows.append({"id": task, "project_id": "DEMO", "title": task, "risk_tier": "LOW", "output": output})
                path = root / output
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"result {index}\n", encoding="utf-8")
            write_catalog(root, rows)
            events = [record_completion(root, f"TASK_{index}") for index in range(1, 6)]
            self.assertEqual([event["review_required"] for event in events], [True, True, True, False, True])
            self.assertEqual(events[4]["review_reason"], "DETERMINISTIC_SAMPLE")

    def test_svg_completion_requires_png_preview(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_policy(root)
            write_catalog(root, [{"id": "TASK_SVG", "project_id": "DEMO", "title": "svg", "risk_tier": "LOW", "output": "projects/DEMO/a.svg"}])
            svg = root / "projects/DEMO/a.svg"
            svg.parent.mkdir(parents=True, exist_ok=True)
            svg.write_text("<svg/>\n", encoding="utf-8")
            with self.assertRaises(QualityGateError) as ctx:
                record_completion(root, "TASK_SVG")
            self.assertIn("a.png", str(ctx.exception))

    def test_rejected_task_can_reclaim_itself_but_blocks_other_work(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_policy(root)
            path = event_path(root, "TASK_BAD")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({
                "rule_epoch": 1,
                "task": "TASK_BAD",
                "project": "DEMO",
                "review_status": "REJECTED",
                "outputs": [],
                "previews": [],
            }), encoding="utf-8")
            self.assertIsNone(claim_block_packet(root, "DEMO", "TASK_BAD"))
            self.assertEqual(claim_block_packet(root, "DEMO", "TASK_OTHER")["status"], "REVIEW_BLOCKED")


class QualityVisibilityGitIntegrationTests(unittest.TestCase):
    def setup_remote(self, td: Path) -> Path:
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
        git(seed, "commit", "-m", "seed quality UOS")
        git(td, "init", "--bare", str(remote))
        git(seed, "remote", "add", "origin", str(remote))
        git(seed, "push", "-u", "origin", "main")
        git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
        return remote

    def uos(self, cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return sh([sys.executable, "tools/uos.py", *args], cwd, check=check)

    def test_preview_gate_review_pause_and_accept(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = self.setup_remote(td)
            worker = td / "worker"
            git(td, "clone", str(remote), str(worker))
            configure(worker)

            self.uos(worker, "project", "init", "--project-id", "DEMO", "--title", "Demo")
            self.uos(
                worker, "task", "publish", "--project", "DEMO", "--task-id", "TASK_SVG",
                "--title", "Make SVG", "--output", "projects/DEMO/figure.svg", "--acceptance", "figure visible",
            )
            self.uos(
                worker, "task", "publish", "--project", "DEMO", "--task-id", "TASK_NEXT",
                "--title", "Next", "--output", "projects/DEMO/next.md", "--acceptance", "next exists",
            )

            git(worker, "fetch", "origin", "main")
            catalog_text = git(worker, "show", "origin/main:orchestration/projects/DEMO/TASK_CATALOG.csv").stdout
            self.assertIn("projects/DEMO/figure.svg;projects/DEMO/figure.png", catalog_text)

            claim = json.loads(self.uos(worker, "claim", "--agent-id", "AGENT_A", "--task", "TASK_SVG").stdout)
            svg = worker / "projects/DEMO/figure.svg"
            svg.parent.mkdir(parents=True, exist_ok=True)
            svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>\n", encoding="utf-8")

            missing_preview = self.uos(
                worker, "complete", "--agent-id", "AGENT_A", "--task", "TASK_SVG",
                "--lease-token", claim["LeaseToken"], check=False,
            )
            self.assertEqual(missing_preview.returncode, 2)
            self.assertIn("figure.png", missing_preview.stderr)

            (worker / "projects/DEMO/figure.png").write_bytes(b"PNG preview fixture\n")
            completed = self.uos(
                worker, "complete", "--agent-id", "AGENT_A", "--task", "TASK_SVG",
                "--lease-token", claim["LeaseToken"],
            )
            packet = json.loads(completed.stdout)
            self.assertTrue(packet["quality_visibility"]["review_required"])
            self.assertEqual(packet["quality_visibility"]["review_status"], "PENDING")
            self.assertIn("projects/DEMO/figure.png", packet["quality_visibility"]["previews"])

            blocked = self.uos(worker, "claim", "--agent-id", "AGENT_B", "--task", "TASK_NEXT", check=False)
            self.assertEqual(blocked.returncode, 6)
            self.assertIn("REVIEW_BLOCKED", blocked.stdout)

            accepted = sh(
                [sys.executable, "tools/quality_gate.py", "review", "accept", "--task", "TASK_SVG", "--by", "TEST_OPERATOR"],
                worker,
            )
            self.assertIn("ACCEPTED", accepted.stdout)
            next_claim = self.uos(worker, "claim", "--agent-id", "AGENT_B", "--task", "TASK_NEXT")
            self.assertEqual(json.loads(next_claim.stdout)["CanonicalID"], "TASK_NEXT")


if __name__ == "__main__":
    unittest.main()
