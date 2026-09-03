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
    "uos.py", "claim_broker_v2.py", "claim_telemetry.py", "canonical_runner.py", "canonical_publish.py",
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
    git(cwd, "config", "user.name", "UOS Request Reclaim Test")
    git(cwd, "config", "user.email", "uos@example.invalid")


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ":" in raw:
            key, value = raw.split(":", 1)
            out[key.strip()] = value.strip()
    return out


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


def bootstrap(worker: Path) -> None:
    uos(worker, "project", "init", "--project-id", "DEMO", "--title", "Demo")
    uos(worker, "task", "publish", "--project", "DEMO", "--task-id", "TASK_A", "--title", "A", "--output", "projects/DEMO/a.txt", "--acceptance", "exists")


class ClaimRequestReclaimTests(unittest.TestCase):
    def test_create_writes_request_grant_lock_in_one_canonical_commit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw); remote = setup_remote(td); a = td / "a"; clone(remote, a); bootstrap(a)
            packet = json.loads(uos(a, "claim", "--agent-id", "AGENT_A", "--task", "TASK_A").stdout)
            self.assertEqual(packet["ClaimMode"], "CREATE")
            self.assertTrue(packet["RequestID"]); self.assertTrue(packet["RequestPath"])
            self.assertTrue(packet["GrantID"]); self.assertTrue(packet["GrantPath"])

            check = td / "check"; clone(remote, check)
            request_path = check / packet["RequestPath"]
            grant_path = check / packet["GrantPath"]
            lock_path = check / "coordination/claims/TASK_A.lock"
            self.assertTrue(request_path.exists()); self.assertTrue(grant_path.exists()); self.assertTrue(lock_path.exists())
            request = parse_kv(request_path); grant = parse_kv(grant_path); lock = parse_kv(lock_path)
            self.assertEqual(request["Schema"], "UOS_CLAIM_REQUEST_V1")
            self.assertEqual(request["Mode"], "CREATE")
            self.assertEqual(request["GrantID"], packet["GrantID"])
            self.assertEqual(grant["RequestPath"], packet["RequestPath"])
            self.assertEqual(grant["ClaimMode"], "CREATE")
            self.assertEqual(lock["RequestPath"], packet["RequestPath"])
            self.assertEqual(lock["ClaimMode"], "CREATE")
            commits = {
                git(check, "log", "-1", "--format=%H", "--", rel).stdout.strip()
                for rel in (packet["RequestPath"], packet["GrantPath"], "coordination/claims/TASK_A.lock")
            }
            self.assertEqual(len(commits), 1, commits)

    def test_stale_lock_reclaim_records_exact_prior_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw); remote = setup_remote(td)
            a, b = td / "a", td / "b"; clone(remote, a); clone(remote, b); bootstrap(a)
            first = json.loads(uos(a, "claim", "--agent-id", "AGENT_A", "--task", "TASK_A").stdout)
            self.assertEqual(first["LeaseGeneration"], 1)

            # Make the canonical active lease stale without changing immutable Request/Grant.
            stale = td / "stale"; clone(remote, stale)
            lock_path = stale / "coordination/claims/TASK_A.lock"
            text = lock_path.read_text(encoding="utf-8")
            lines = []
            for line in text.splitlines():
                if line.startswith("LeaseExpiresAt:"):
                    lines.append("LeaseExpiresAt: 2000-01-01T00:00:00Z")
                else:
                    lines.append(line)
            lock_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            old_blob = git(stale, "hash-object", "coordination/claims/TASK_A.lock").stdout.strip()
            git(stale, "add", "coordination/claims/TASK_A.lock"); git(stale, "commit", "-m", "expire lease"); git(stale, "push", "origin", "main")

            second = json.loads(uos(b, "claim", "--agent-id", "AGENT_B", "--task", "TASK_A").stdout)
            self.assertEqual(second["LeaseGeneration"], 2)
            self.assertEqual(second["ClaimMode"], "RECLAIM")
            check = td / "check"; clone(remote, check)
            lock2 = parse_kv(check / "coordination/claims/TASK_A.lock")
            grant2 = parse_kv(check / second["GrantPath"])
            request2 = parse_kv(check / second["RequestPath"])
            self.assertEqual(lock2["PreviousAgentID"], "AGENT_A")
            self.assertEqual(lock2["PreviousLeaseGeneration"], "1")
            self.assertEqual(lock2["PreviousLeaseToken"], first["LeaseToken"])
            self.assertEqual(lock2["PreviousGrantID"], first["GrantID"])
            self.assertEqual(lock2["PreviousGrantPath"], first["GrantPath"])
            self.assertEqual(lock2["ReclaimedFromLockGitBlobSHA"], old_blob)
            self.assertEqual(grant2["PreviousAgentID"], "AGENT_A")
            self.assertEqual(grant2["PreviousLeaseGeneration"], "1")
            self.assertEqual(grant2["PreviousGrantID"], first["GrantID"])
            self.assertEqual(grant2["ReclaimedFromLockGitBlobSHA"], old_blob)
            self.assertEqual(request2["Mode"], "RECLAIM")
            self.assertEqual(request2["ExpectedPriorLockGitBlobSHA"], old_blob)
            self.assertEqual(request2["ExpectedPriorAgentID"], "AGENT_A")
            self.assertEqual(request2["ExpectedPriorLeaseGeneration"], "1")
            self.assertEqual(request2["ExpectedPriorLeaseToken"], first["LeaseToken"])

            # Old owner is fenced by generation/token change.
            output = a / "projects/DEMO/a.txt"; output.parent.mkdir(parents=True, exist_ok=True); output.write_text("old owner\n", encoding="utf-8")
            fenced = uos(a, "complete", "--agent-id", "AGENT_A", "--task", "TASK_A", "--lease-token", first["LeaseToken"], check=False)
            self.assertNotEqual(fenced.returncode, 0)


if __name__ == "__main__":
    unittest.main()
