from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
TOOLS = [
    "uos.py",
    "canonical_runner.py",
    "canonical_publish.py",
    "quality_gate.py",
    "control_extensions.py",
    "agent_matching.py",
    "high_contention_claim.py",
]
TASK_FIELDS = [
    "id", "priority", "status", "role", "title", "deps", "inputs", "output",
    "project_id", "phase", "workstream", "exclusive_keys", "size_class",
    "quality_tier", "risk_tier", "wave_id", "batch_hint", "acceptance",
    "compliance_profile", "notes", "min_capability_tier", "context_class",
    "tool_requirements", "context_refs",
]


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
    git(cwd, "config", "user.name", "UOS Contention Test")
    git(cwd, "config", "user.email", "uos@example.invalid")


def setup_remote(td: Path, count: int) -> Path:
    seed = td / "seed"
    remote = td / "remote.git"
    seed.mkdir()
    git(seed, "init", "-b", "main")
    configure(seed)
    (seed / "tools").mkdir()
    for name in TOOLS:
        shutil.copy2(SOURCE / "tools" / name, seed / "tools" / name)

    project = seed / "orchestration/projects/LOAD"
    project.mkdir(parents=True)
    (project / "PROJECT.yaml").write_text(
        "Schema: UOS_PROJECT_V1\n"
        "ProjectID: LOAD\n"
        "Title: Load Test\n"
        "State: ACTIVE\n"
        "RepositoryMode: SAME_REPOSITORY\n"
        "WorkRoot: projects/LOAD\n",
        encoding="utf-8",
    )
    with (project / "TASK_CATALOG.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TASK_FIELDS)
        writer.writeheader()
        for index in range(count):
            row = {field: "" for field in TASK_FIELDS}
            row.update(
                {
                    "id": f"TASK_{index:02d}",
                    "priority": str(index + 1),
                    "status": "READY",
                    "role": "WORKER",
                    "title": f"Task {index:02d}",
                    "output": f"projects/LOAD/{index:02d}.txt",
                    "project_id": "LOAD",
                    "phase": "RESEARCH",
                    "workstream": f"lane_{index:02d}",
                    "exclusive_keys": f"LOAD:{index:02d}",
                    "size_class": "S",
                    "quality_tier": "STANDARD",
                    "risk_tier": "LOW",
                    "acceptance": "claim only",
                    "compliance_profile": "SOFTWARE_V1",
                    "min_capability_tier": "1",
                    "context_class": "S",
                }
            )
            writer.writerow(row)

    sh([sys.executable, "tools/uos.py", "--transport", "local", "reconcile"], seed)
    git(seed, "add", ".")
    git(seed, "commit", "-m", f"seed {count} READY tasks")
    git(td, "init", "--bare", str(remote))
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path) -> None:
    git(path.parent, "clone", "--quiet", str(remote), str(path))
    configure(path)


class HighContentionClaimTests(unittest.TestCase):
    def test_distinct_exact_tasks_all_claim_under_contention(self) -> None:
        scale = int(os.environ.get("UOS_CONTENTION_SCALE", "5"))
        self.assertIn(scale, {5, 10, 30})
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td, scale)
            workers: list[Path] = []
            for index in range(scale):
                worker = td / f"worker-{index:02d}"
                clone(remote, worker)
                workers.append(worker)

            env = os.environ.copy()
            # Keep production semantics (bounded jitter) while making local CI fast.
            env["UOS_EXACT_CLAIM_JITTER_MS"] = "1800"
            procs = []
            for index, worker in enumerate(workers):
                procs.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            "tools/high_contention_claim.py",
                            "--agent-id", f"AGENT_{index:02d}",
                            "--task", f"TASK_{index:02d}",
                            "--project", "LOAD",
                            "--capability-tier", "4",
                            "--tools", "web;python",
                            "--context", "XL",
                            "--cas-retries", "30",
                            "--outer-attempts", "6",
                        ],
                        cwd=worker,
                        env=env,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                )

            results = []
            for proc in procs:
                out, err = proc.communicate(timeout=180)
                results.append((proc.returncode, out, err))
            failures = [item for item in results if item[0] != 0]
            self.assertEqual(failures, [], results)

            check = td / "check"
            clone(remote, check)
            locks = sorted((check / "coordination/claims").glob("TASK_*.lock"))
            self.assertEqual(len(locks), scale)
            owners = set()
            for path in locks:
                meta = {}
                for raw_line in path.read_text(encoding="utf-8").splitlines():
                    if ":" in raw_line:
                        key, value = raw_line.split(":", 1)
                        meta[key.strip()] = value.strip()
                owners.add(meta.get("AgentID"))
                self.assertTrue(meta.get("LeaseToken"))
                self.assertTrue(meta.get("LeaseGeneration"))
            self.assertEqual(len(owners), scale)


if __name__ == "__main__":
    unittest.main()
