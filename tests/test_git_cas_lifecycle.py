from __future__ import annotations

import csv
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
TOOLS = ["uos.py", "canonical_runner.py", "canonical_publish.py", "quality_gate.py", "control_extensions.py"]


def sh(args: list[str], cwd: Path, *, check: bool = True, env=None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=cwd,
        env=env,
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
    git(cwd, "config", "user.name", "UOS Integration Test")
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
    git(seed, "commit", "-m", "seed UOS")
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


def bootstrap_project(worker: Path) -> None:
    uos(
        worker,
        "project",
        "init",
        "--project-id",
        "DEMO",
        "--title",
        "Demo",
        "--goal",
        "Prove canonical lifecycle",
    )


def publish_task(worker: Path, task_id: str, output: str, *, deps: str = "") -> None:
    args = [
        "task",
        "publish",
        "--project",
        "DEMO",
        "--task-id",
        task_id,
        "--title",
        task_id,
        "--output",
        output,
        "--acceptance",
        "output exists",
    ]
    if deps:
        args += ["--deps", deps]
    uos(worker, *args)


class GitCasLifecycleTests(unittest.TestCase):
    def test_auto_transport_unique_claim_and_atomic_complete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            a, b = td / "a", td / "b"
            clone(remote, a)
            clone(remote, b)

            bootstrap_project(a)
            publish_task(a, "TASK_A", "projects/DEMO/result.txt")

            contenders = [
                subprocess.Popen(
                    [sys.executable, "tools/uos.py", "claim", "--agent-id", agent, "--project", "DEMO"],
                    cwd=repo,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                for repo, agent in ((a, "AGENT_A"), (b, "AGENT_B"))
            ]
            results = []
            for proc in contenders:
                out, err = proc.communicate()
                results.append((proc.returncode, out, err, proc))
            winners = [item for item in results if item[0] == 0]
            losers = [item for item in results if item[0] == 4]
            self.assertEqual(len(winners), 1, results)
            self.assertEqual(len(losers), 1, results)

            grant = json.loads(winners[0][1])
            winner_repo = a if grant["AgentID"] == "AGENT_A" else b
            output = winner_repo / "projects/DEMO/result.txt"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("canonical result\n", encoding="utf-8")
            uos(
                winner_repo,
                "complete",
                "--agent-id",
                grant["AgentID"],
                "--task",
                "TASK_A",
                "--lease-token",
                grant["LeaseToken"],
            )

            check = td / "check"
            clone(remote, check)
            self.assertEqual((check / "projects/DEMO/result.txt").read_text(), "canonical result\n")
            self.assertTrue((check / "coordination/completed/TASK_A.done").exists())
            self.assertTrue((check / "coordination/quality/durability/TASK_A.json").exists())
            self.assertFalse((check / "coordination/claims/TASK_A.lock").exists())
            status = json.loads((check / "coordination/runtime/STATUS.json").read_text())
            self.assertEqual(status["projects"]["DEMO"]["done"], 1)

    def test_concurrent_task_publish_replays_from_latest_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            admin = td / "admin"
            clone(remote, admin)
            bootstrap_project(admin)

            a, b = td / "a", td / "b"
            clone(remote, a)
            clone(remote, b)
            commands = [
                (a, "TASK_A", "projects/DEMO/a.txt"),
                (b, "TASK_B", "projects/DEMO/b.txt"),
            ]
            procs = [
                subprocess.Popen(
                    [
                        sys.executable,
                        "tools/uos.py",
                        "task",
                        "publish",
                        "--project",
                        "DEMO",
                        "--task-id",
                        task,
                        "--title",
                        task,
                        "--output",
                        output,
                        "--acceptance",
                        "output exists",
                    ],
                    cwd=repo,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                for repo, task, output in commands
            ]
            results = [proc.communicate() + (proc.returncode,) for proc in procs]
            self.assertTrue(all(result[2] == 0 for result in results), results)

            check = td / "check"
            clone(remote, check)
            with (check / "orchestration/projects/DEMO/TASK_CATALOG.csv").open(newline="", encoding="utf-8") as handle:
                ids = {row["id"] for row in csv.DictReader(handle)}
            self.assertEqual(ids, {"TASK_A", "TASK_B"})

    def test_reconcile_ref_race_recomputes_from_new_canonical_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            admin = td / "admin"
            clone(remote, admin)
            bootstrap_project(admin)
            publish_task(admin, "TASK_A", "projects/DEMO/a.txt")

            status_worker, writer = td / "status", td / "writer"
            clone(remote, status_worker)
            clone(remote, writer)

            env = os.environ.copy()
            env["UOS_CAS_TEST_DELAY_BEFORE_PUSH"] = "0.8"
            proc = subprocess.Popen(
                [sys.executable, "tools/uos.py", "status", "--project", "DEMO"],
                cwd=status_worker,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(0.2)

            git(writer, "pull", "--ff-only", "origin", "main")
            catalog = writer / "orchestration/projects/DEMO/TASK_CATALOG.csv"
            with catalog.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
                fields = list(rows[0].keys())
            new_row = dict(rows[0])
            new_row.update(
                {
                    "id": "TASK_B",
                    "title": "TASK_B",
                    "output": "projects/DEMO/b.txt",
                    "priority": "2",
                }
            )
            rows.append(new_row)
            with catalog.open("w", newline="", encoding="utf-8") as handle:
                writer_obj = csv.DictWriter(handle, fieldnames=fields)
                writer_obj.writeheader()
                writer_obj.writerows(rows)
            git(writer, "add", str(catalog.relative_to(writer)))
            git(writer, "commit", "-m", "advance canonical catalog without reconcile")
            git(writer, "push", "origin", "main")

            out, err = proc.communicate()
            self.assertEqual(proc.returncode, 0, (out, err))

            check = td / "check"
            clone(remote, check)
            status = json.loads((check / "coordination/runtime/STATUS.json").read_text())
            self.assertEqual(status["projects"]["DEMO"]["total"], 2)
            with (check / "coordination/runtime/TASK_STATUS.csv").open(newline="", encoding="utf-8") as handle:
                ids = {row["id"] for row in csv.DictReader(handle)}
            self.assertEqual(ids, {"TASK_A", "TASK_B"})
            with (check / "coordination/runtime/WORK_MARKET.csv").open(newline="", encoding="utf-8") as handle:
                market_ids = {row["canonical_id"] for row in csv.DictReader(handle)}
            self.assertEqual(market_ids, {"TASK_A", "TASK_B"})

    def test_repeated_status_is_canonical_noop_when_state_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            clone(remote, worker)
            bootstrap_project(worker)
            publish_task(worker, "TASK_A", "projects/DEMO/a.txt")
            uos(worker, "status", "--project", "DEMO")
            git(worker, "fetch", "origin", "main")
            first = git(worker, "rev-parse", "origin/main").stdout.strip()
            uos(worker, "status", "--project", "DEMO")
            git(worker, "fetch", "origin", "main")
            second = git(worker, "rev-parse", "origin/main").stdout.strip()
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
