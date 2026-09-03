from __future__ import annotations

import csv
import importlib.util
import json
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
    git(cwd, "config", "user.name", "UOS Outbox Batch Test")
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
    git(seed, "commit", "-m", "seed outbox batch UOS")
    git(td, "init", "--bare", str(remote))
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path) -> None:
    git(path.parent, "clone", "--quiet", str(remote), str(path))
    configure(path)


def uos(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return sh([sys.executable, "tools/uos.py", *args], cwd)


def load_outbox_module():
    path = SOURCE / "tools/completion_outbox.py"
    spec = importlib.util.spec_from_file_location("completion_outbox_batch_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ":" in raw:
            key, value = raw.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def stage_from_local_complete(module, remote: Path, base: str, task: str, agent: str, token: str, index: int, td: Path) -> dict:
    worker = td / f"stage-{index:02d}"
    clone(remote, worker)
    self_base = git(worker, "rev-parse", "HEAD").stdout.strip()
    if self_base != base:
        raise AssertionError((self_base, base))
    output = worker / f"projects/LOAD/{index:02d}.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f"result-{index:02d}\n", encoding="utf-8")
    lock_rel = f"coordination/claims/{task}.lock"
    lock = parse_kv(worker / lock_rel)
    lock_blob = git(worker, "rev-parse", f"{base}:{lock_rel}").stdout.strip()
    proc = sh(
        [
            sys.executable,
            "tools/uos.py",
            "--transport", "local",
            "complete",
            "--agent-id", agent,
            "--task", task,
            "--lease-token", token,
        ],
        worker,
    )
    packet = json.loads(proc.stdout)
    if packet.get("status") != "DONE":
        raise AssertionError(packet)
    git(worker, "add", "-A")
    git(worker, "commit", "-m", f"local completion candidate {task}")
    candidate = git(worker, "rev-parse", "HEAD").stdout.strip()
    return module.stage_completion_candidate(
        worker,
        candidate_root=worker,
        base=base,
        candidate_commit=candidate,
        task_id=task,
        owner_lock=lock,
        owner_lock_blob_sha=lock_blob,
        remote="origin",
        branch="main",
    )


class CompletionOutboxBatchTests(unittest.TestCase):
    def test_batch_integrates_all_independent_completions_in_one_main_commit(self) -> None:
        scale = int(os.environ.get("UOS_OUTBOX_SCALE", "5"))
        self.assertIn(scale, {2, 5, 10, 30})
        module = load_outbox_module()
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            admin = td / "admin"
            clone(remote, admin)
            uos(admin, "project", "init", "--project-id", "LOAD", "--title", "Load")
            for index in range(scale):
                task = f"TASK_{index:02d}"
                uos(
                    admin,
                    "task", "publish",
                    "--project", "LOAD",
                    "--task-id", task,
                    "--title", task,
                    "--priority", str(index + 1),
                    "--output", f"projects/LOAD/{index:02d}.txt",
                    "--acceptance", "output exists",
                )

            grants: list[tuple[str, str, str]] = []
            for index in range(scale):
                task = f"TASK_{index:02d}"
                agent = f"AGENT_{index:02d}"
                grant = json.loads(
                    uos(admin, "claim", "--agent-id", agent, "--project", "LOAD", "--task", task).stdout
                )
                grants.append((task, agent, grant["LeaseToken"]))

            git(admin, "fetch", "origin", "main")
            base = git(admin, "rev-parse", "origin/main").stdout.strip()
            staged = [
                stage_from_local_complete(module, remote, base, task, agent, token, index, td)
                for index, (task, agent, token) in enumerate(grants)
            ]
            self.assertTrue(all(item["status"] == "COMPLETION_STAGED" for item in staged), staged)

            observer = td / "observer"
            clone(remote, observer)
            before = git(observer, "rev-parse", "origin/main").stdout.strip()
            self.assertEqual(before, base)
            for index in range(scale):
                self.assertFalse((observer / f"coordination/completed/TASK_{index:02d}.done").exists())

            ingested = module.ingest(observer, remote="origin", branch="main", max_batch=scale, retries=8)
            self.assertEqual(ingested["status"], "OUTBOX_INGESTED", ingested)
            self.assertEqual(ingested["batch_size"], scale)
            after = ingested["canonical_commit"]
            count = int(git(observer, "rev-list", "--count", f"{before}..{after}").stdout.strip())
            self.assertEqual(count, 1, ingested)

            check = td / "check"
            clone(remote, check)
            for index in range(scale):
                task = f"TASK_{index:02d}"
                self.assertTrue((check / f"coordination/completed/{task}.done").exists())
                self.assertFalse((check / f"coordination/claims/{task}.lock").exists())
                self.assertEqual(
                    (check / f"projects/LOAD/{index:02d}.txt").read_text(encoding="utf-8"),
                    f"result-{index:02d}\n",
                )
                grant_id = parse_kv(check / f"coordination/claim_grants/AGENT_{index:02d}" / next(
                    p.name for p in (check / f"coordination/claim_grants/AGENT_{index:02d}").glob("*.grant")
                ))["GrantID"]
                receipt = check / f"coordination/outbox_receipts/PUB-{grant_id}.json"
                self.assertTrue(receipt.exists())
            status = json.loads((check / "coordination/runtime/STATUS.json").read_text(encoding="utf-8"))
            self.assertEqual(status["projects"]["LOAD"]["done"], scale)
            self.assertEqual(status["projects"]["LOAD"]["claimed"], 0)


if __name__ == "__main__":
    unittest.main()
