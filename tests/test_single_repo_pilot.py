#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UOS = REPO / "tools/uos.py"
FIELDS = [
    "id", "priority", "status", "role", "title", "deps", "inputs", "output",
    "project_id", "phase", "workstream", "exclusive_keys", "size_class",
    "quality_tier", "risk_tier", "wave_id", "batch_hint", "acceptance",
    "compliance_profile", "notes", "min_capability_tier", "context_class",
    "tool_requirements", "context_refs",
]


def run(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(UOS), *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"command failed rc={proc.returncode}: {args}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc


def write_project(root: Path, project_id: str = "DEMO") -> Path:
    directory = root / "orchestration/projects" / project_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "PROJECT.yaml").write_text(
        "Schema: UOS_PROJECT_V1\n"
        f"ProjectID: {project_id}\n"
        "Title: Demo\n"
        "State: ACTIVE\n"
        f"IntentVersion: {project_id}_INTENT_V1\n"
        "RepositoryMode: SAME_REPOSITORY\n"
        f"WorkRoot: projects/{project_id}\n"
        "Goal: Test project\n",
        encoding="utf-8",
    )
    return directory


def write_tasks(directory: Path, rows: list[dict[str, str]]) -> None:
    with (directory / "TASK_CATALOG.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            payload = {key: "" for key in FIELDS}
            payload.update(row)
            writer.writerow(payload)


class SingleRepoPilotTests(unittest.TestCase):
    def test_lifecycle_releases_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = write_project(root)
            write_tasks(
                project,
                [
                    {
                        "id": "TASK_A",
                        "priority": "1",
                        "status": "READY",
                        "role": "ARCHITECT",
                        "title": "Spec",
                        "output": "projects/DEMO/SPEC.md",
                        "project_id": "DEMO",
                        "acceptance": "write spec",
                    },
                    {
                        "id": "TASK_B",
                        "priority": "2",
                        "status": "BLOCKED",
                        "role": "WORKER",
                        "title": "Build",
                        "deps": "TASK_A",
                        "inputs": "projects/DEMO/SPEC.md",
                        "output": "projects/DEMO/index.html",
                        "project_id": "DEMO",
                        "acceptance": "build",
                    },
                ],
            )
            status = json.loads(run(root, "status", "--project", "DEMO").stdout)
            self.assertEqual(status["projects"]["DEMO"]["ready"], 1)
            self.assertEqual(status["projects"]["DEMO"]["blocked"], 1)

            grant = json.loads(run(root, "claim", "--agent-id", "AGENT_A", "--project", "DEMO").stdout)
            self.assertEqual(grant["CanonicalID"], "TASK_A")
            token = grant["LeaseToken"]
            output = root / "projects/DEMO/SPEC.md"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("spec\n", encoding="utf-8")
            run(root, "complete", "--agent-id", "AGENT_A", "--task", "TASK_A", "--lease-token", token)

            status = json.loads(run(root, "status", "--project", "DEMO").stdout)
            self.assertEqual(status["projects"]["DEMO"]["done"], 1)
            self.assertEqual(status["projects"]["DEMO"]["ready"], 1)
            next_grant = json.loads(run(root, "claim", "--agent-id", "AGENT_B", "--project", "DEMO").stdout)
            self.assertEqual(next_grant["CanonicalID"], "TASK_B")

    def test_project_and_task_publish_do_not_create_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "orchestration").mkdir()
            run(root, "project", "init", "--project-id", "NEWPROJ", "--title", "New Project")
            run(
                root,
                "task",
                "publish",
                "--project",
                "NEWPROJ",
                "--task-id",
                "TASK_NEW_01",
                "--title",
                "First task",
                "--output",
                "projects/NEWPROJ/result.txt",
                "--acceptance",
                "result exists",
            )
            self.assertTrue((root / "orchestration/projects/NEWPROJ/PROJECT.yaml").exists())
            self.assertTrue((root / "orchestration/projects/NEWPROJ/TASK_CATALOG.csv").exists())
            self.assertFalse((root / "coordination/claims/TASK_NEW_01.lock").exists())
            self.assertFalse((root / "coordination/completed/TASK_NEW_01.done").exists())
            status = json.loads(run(root, "status", "--project", "NEWPROJ").stdout)
            self.assertEqual(status["projects"]["NEWPROJ"]["ready"], 1)

    def test_concurrent_task_publish_preserves_both_rows(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "orchestration").mkdir()
            run(root, "project", "init", "--project-id", "PUB", "--title", "Publish race")
            base = [sys.executable, str(UOS), "task", "publish", "--project", "PUB"]
            procs = [
                subprocess.Popen(
                    base + [
                        "--task-id", f"TASK_PUB_{i}",
                        "--title", f"Task {i}",
                        "--output", f"projects/PUB/out{i}.txt",
                        "--acceptance", "exists",
                    ],
                    cwd=root,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                for i in range(2)
            ]
            results = [proc.communicate() + (proc.returncode,) for proc in procs]
            self.assertEqual([item[2] for item in results], [0, 0], results)
            rows = list(csv.DictReader((root / "orchestration/projects/PUB/TASK_CATALOG.csv").open(encoding="utf-8")))
            self.assertEqual({row["id"] for row in rows}, {"TASK_PUB_0", "TASK_PUB_1"})

    def test_publish_rejects_paths_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "orchestration").mkdir()
            run(root, "project", "init", "--project-id", "SAFE", "--title", "Safe paths")
            escaped = run(
                root,
                "task",
                "publish",
                "--project", "SAFE",
                "--task-id", "TASK_ESCAPE",
                "--title", "Escape",
                "--output", "../outside.txt",
                "--acceptance", "must reject",
                check=False,
            )
            self.assertEqual(escaped.returncode, 2)
            self.assertIn("must stay inside repository", escaped.stderr)
            rows = list(csv.DictReader((root / "orchestration/projects/SAFE/TASK_CATALOG.csv").open(encoding="utf-8")))
            self.assertEqual(rows, [])

    def test_ten_contenders_create_one_owner(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = write_project(root)
            write_tasks(
                project,
                [{
                    "id": "TASK_ONLY",
                    "priority": "1",
                    "status": "READY",
                    "role": "WORKER",
                    "title": "Only task",
                    "output": "projects/DEMO/out.txt",
                    "project_id": "DEMO",
                    "acceptance": "write out",
                }],
            )
            procs = [
                subprocess.Popen(
                    [sys.executable, str(UOS), "claim", "--agent-id", f"AGENT_{i}", "--project", "DEMO"],
                    cwd=root,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                for i in range(10)
            ]
            results = [proc.communicate() + (proc.returncode,) for proc in procs]
            winners = [item for item in results if item[2] == 0 and '"Status": "GRANTED"' in item[0]]
            self.assertEqual(len(winners), 1, results)
            locks = list((root / "coordination/claims").glob("*.lock"))
            self.assertEqual(len(locks), 1)

    def test_expired_owner_is_fenced_after_reclaim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = write_project(root)
            write_tasks(
                project,
                [{
                    "id": "TASK_FENCE",
                    "priority": "1",
                    "status": "READY",
                    "role": "WORKER",
                    "title": "Fence",
                    "output": "projects/DEMO/out.txt",
                    "project_id": "DEMO",
                    "acceptance": "write out",
                }],
            )
            first = json.loads(run(root, "claim", "--agent-id", "OLD", "--task", "TASK_FENCE").stdout)
            old_token = first["LeaseToken"]
            lock = root / "coordination/claims/TASK_FENCE.lock"
            text = lock.read_text(encoding="utf-8")
            lines = []
            for line in text.splitlines():
                if line.startswith("LeaseExpiresAt:"):
                    line = "LeaseExpiresAt: 2000-01-01T00:00:00Z"
                lines.append(line)
            lock.write_text("\n".join(lines) + "\n", encoding="utf-8")

            second = json.loads(run(root, "claim", "--agent-id", "NEW", "--task", "TASK_FENCE").stdout)
            self.assertEqual(int(second["LeaseGeneration"]), 2)
            self.assertNotEqual(second["LeaseToken"], old_token)

            stale = run(
                root,
                "renew",
                "--agent-id",
                "OLD",
                "--task",
                "TASK_FENCE",
                "--lease-token",
                old_token,
                check=False,
            )
            self.assertEqual(stale.returncode, 2)
            self.assertIn("FENCED", stale.stderr)


if __name__ == "__main__":
    unittest.main()
