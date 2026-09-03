from __future__ import annotations

import csv
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
TOOLS = [
    "uos.py", "canonical_runner.py", "canonical_publish.py",
    "quality_gate.py", "control_extensions.py", "claim_integrity_scan.py",
]


def sh(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise AssertionError(f"command failed rc={proc.returncode}: {args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh(["git", *args], cwd, check=check)


def configure(cwd: Path) -> None:
    git(cwd, "config", "user.name", "UOS Grant Test")
    git(cwd, "config", "user.email", "uos@example.invalid")


def setup_remote(td: Path) -> Path:
    seed, remote = td / "seed", td / "remote.git"
    seed.mkdir(); git(seed, "init", "-b", "main"); configure(seed)
    (seed / "tools").mkdir()
    for name in TOOLS:
        shutil.copy2(SOURCE / "tools" / name, seed / "tools" / name)
    (seed / "orchestration").mkdir(); (seed / "orchestration/.keep").write_text("\n", encoding="utf-8")
    git(seed, "add", "."); git(seed, "commit", "-m", "seed")
    git(td, "init", "--bare", str(remote)); git(seed, "remote", "add", "origin", str(remote)); git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path) -> None:
    git(path.parent, "clone", str(remote), str(path)); configure(path)


def uos(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return sh([sys.executable, "tools/uos.py", *args], cwd, check=check)


class ClaimGrantIntegrationTests(unittest.TestCase):
    def test_claim_commits_lock_and_immutable_grant_together_and_complete_retains_grant(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw); remote = setup_remote(td); worker = td / "worker"; clone(remote, worker)
            uos(worker, "project", "init", "--project-id", "DEMO", "--title", "Demo")
            uos(worker, "task", "publish", "--project", "DEMO", "--task-id", "TASK_A", "--title", "A", "--output", "projects/DEMO/result.txt", "--acceptance", "exists")
            claim = uos(worker, "claim", "--agent-id", "AGENT_A", "--task", "TASK_A")
            grant = json.loads(claim.stdout)
            self.assertTrue(grant.get("GrantID"), grant)
            self.assertTrue(grant.get("GrantPath"), grant)

            check = td / "check"; clone(remote, check)
            lock_path = check / "coordination/claims/TASK_A.lock"
            grant_path = check / grant["GrantPath"]
            self.assertTrue(lock_path.exists()); self.assertTrue(grant_path.exists())
            lock = lock_path.read_text(encoding="utf-8")
            self.assertIn(f"GrantID: {grant['GrantID']}", lock)
            self.assertIn(f"GrantPath: {grant['GrantPath']}", lock)
            lock_commit = git(check, "log", "-1", "--format=%H", "--", "coordination/claims/TASK_A.lock").stdout.strip()
            grant_commit = git(check, "log", "-1", "--format=%H", "--", grant["GrantPath"]).stdout.strip()
            self.assertEqual(lock_commit, grant_commit)

            output = worker / "projects/DEMO/result.txt"; output.parent.mkdir(parents=True, exist_ok=True); output.write_text("ok\n", encoding="utf-8")
            uos(worker, "complete", "--agent-id", "AGENT_A", "--task", "TASK_A", "--lease-token", grant["LeaseToken"])
            final = td / "final"; clone(remote, final)
            self.assertFalse((final / "coordination/claims/TASK_A.lock").exists())
            self.assertTrue((final / grant["GrantPath"]).exists())
            self.assertTrue((final / "coordination/completed/TASK_A.done").exists())
            scan = sh([sys.executable, "tools/claim_integrity_scan.py", "--fail-on-violation"], final)
            self.assertIn("violations_seen=0", scan.stdout)
            with (final / "coordination/runtime/CLAIM_INTEGRITY.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(any(row["canonical_id"] == "TASK_A" and row["integrity_status"] == "DONE" for row in rows), rows)

    def test_tampered_grant_blocks_complete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw); remote = setup_remote(td); worker = td / "worker"; clone(remote, worker)
            uos(worker, "project", "init", "--project-id", "DEMO", "--title", "Demo")
            uos(worker, "task", "publish", "--project", "DEMO", "--task-id", "TASK_A", "--title", "A", "--output", "projects/DEMO/result.txt", "--acceptance", "exists")
            claim = json.loads(uos(worker, "claim", "--agent-id", "AGENT_A", "--task", "TASK_A").stdout)
            attacker = td / "attacker"; clone(remote, attacker)
            gp = attacker / claim["GrantPath"]
            gp.write_text(gp.read_text(encoding="utf-8").replace(f"LeaseToken: {claim['LeaseToken']}", "LeaseToken: TAMPERED"), encoding="utf-8")
            git(attacker, "add", claim["GrantPath"]); git(attacker, "commit", "-m", "tamper grant"); git(attacker, "push", "origin", "main")
            output = worker / "projects/DEMO/result.txt"; output.parent.mkdir(parents=True, exist_ok=True); output.write_text("should not complete\n", encoding="utf-8")
            proc = uos(worker, "complete", "--agent-id", "AGENT_A", "--task", "TASK_A", "--lease-token", claim["LeaseToken"], check=False)
            self.assertEqual(proc.returncode, 2, (proc.stdout, proc.stderr))
            self.assertIn("GRANT_INTEGRITY_BLOCKED", proc.stdout + proc.stderr)


class ScannerCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("claim_integrity_scan_test", SOURCE / "tools/claim_integrity_scan.py")
        assert spec and spec.loader
        cls.scanmod = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.scanmod)

    def test_legacy_lock_is_accepted_during_phase2_migration(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); lock = root / "coordination/claims/TASK_LEGACY.lock"; lock.parent.mkdir(parents=True)
            expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
            lock.write_text("Schema: UOS_CLAIM_V1\nCanonicalID: TASK_LEGACY\nAgentID: AGENT_OLD\nLeaseGeneration: 1\nLeaseToken: oldtoken\nLeaseExpiresAt: " + expiry + "\n", encoding="utf-8")
            rows, violations, repaired = self.scanmod.scan(root)
            self.assertEqual(violations, 0); self.assertEqual(repaired, 0)
            self.assertEqual(rows[0]["integrity_status"], "LEGACY_ACTIVE")


if __name__ == "__main__":
    unittest.main()
