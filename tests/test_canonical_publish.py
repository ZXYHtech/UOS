from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PUB = Path(__file__).resolve().parents[1] / "tools/canonical_publish.py"


def sh(args, cwd: Path, check=True):
    proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise AssertionError(f"cmd failed {args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def git(cwd: Path, *args, check=True):
    return sh(["git", *args], cwd, check=check)


def configure(cwd: Path):
    git(cwd, "config", "user.name", "UOS Test")
    git(cwd, "config", "user.email", "uos@example.invalid")


def setup_remote(td: Path):
    seed = td / "seed"
    remote = td / "remote.git"
    seed.mkdir()
    git(seed, "init", "-b", "main")
    configure(seed)
    (seed / "README.md").write_text("seed\n")
    git(seed, "add", ".")
    git(seed, "commit", "-m", "seed")
    git(td, "init", "--bare", str(remote))
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
    return remote


def clone(remote: Path, path: Path):
    git(path.parent, "clone", str(remote), str(path))
    configure(path)


def run_pub(cwd: Path, *args, check=True):
    return sh([sys.executable, str(PUB), *args], cwd, check=check)


class CanonicalPublishTests(unittest.TestCase):
    def test_disjoint_concurrent_publish_retries_and_preserves_both(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            a, b = td / "a", td / "b"
            clone(remote, a)
            clone(remote, b)
            (a / "a.txt").write_text("A\n")
            (b / "b.txt").write_text("B\n")
            pa = subprocess.Popen(
                [sys.executable, str(PUB), "--path", "a.txt", "--message", "A"],
                cwd=a, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            pb = subprocess.Popen(
                [sys.executable, str(PUB), "--path", "b.txt", "--message", "B"],
                cwd=b, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            oa, ea = pa.communicate()
            ob, eb = pb.communicate()
            self.assertEqual(pa.returncode, 0, (oa, ea))
            self.assertEqual(pb.returncode, 0, (ob, eb))
            check = td / "check"
            clone(remote, check)
            self.assertEqual((check / "a.txt").read_text(), "A\n")
            self.assertEqual((check / "b.txt").read_text(), "B\n")

    def test_claim_create_if_absent_has_one_winner(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            a, b = td / "a", td / "b"
            clone(remote, a)
            clone(remote, b)
            rel = "coordination/claims/TASK_X.lock"
            for repo, agent in ((a, "A"), (b, "B")):
                path = repo / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"AgentID: {agent}\nLeaseToken: {agent}\n")
            procs = [
                subprocess.Popen(
                    [sys.executable, str(PUB), "--path", rel, "--require-absent", rel, "--message", "claim"],
                    cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                for repo in (a, b)
            ]
            results = []
            for proc in procs:
                out, err = proc.communicate()
                results.append((proc.returncode, out, err))
            self.assertEqual(sum(rc == 0 for rc, _, _ in results), 1, results)
            self.assertEqual(sum("REQUIRE_ABSENT_FAILED" in err for _, _, err in results), 1, results)

    def test_completion_publishes_output_done_and_deletes_claim_atomically(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            clone(remote, worker)
            claim = "coordination/claims/TASK_X.lock"
            claim_path = worker / claim
            claim_path.parent.mkdir(parents=True, exist_ok=True)
            claim_path.write_text("AgentID: A\nLeaseToken: t1\n")
            run_pub(worker, "--path", claim, "--require-absent", claim, "--message", "claim")
            git(worker, "fetch", "origin", "main")
            expected = git(worker, "rev-parse", f"origin/main:{claim}").stdout.strip()
            output = "projects/P/out.txt"
            done = "coordination/completed/TASK_X.done"
            (worker / output).parent.mkdir(parents=True, exist_ok=True)
            (worker / output).write_text("ok\n")
            (worker / done).parent.mkdir(parents=True, exist_ok=True)
            (worker / done).write_text("Result: PASS\n")
            run_pub(
                worker,
                "--path", output,
                "--path", done,
                "--delete-path", claim,
                "--expect-blob", f"{claim}={expected}",
                "--message", "complete",
            )
            check = td / "check"
            clone(remote, check)
            self.assertTrue((check / output).exists())
            self.assertTrue((check / done).exists())
            self.assertFalse((check / claim).exists())

    def test_expected_blob_fences_stale_replacement(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            a, b = td / "a", td / "b"
            clone(remote, a)
            clone(remote, b)
            rel = "coordination/claims/TASK_X.lock"
            path = a / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("v1\n")
            run_pub(a, "--path", rel, "--require-absent", rel, "--message", "claim")
            git(a, "fetch", "origin", "main")
            stale = git(a, "rev-parse", f"origin/main:{rel}").stdout.strip()
            git(b, "fetch", "origin", "main")
            git(b, "checkout", "-B", "main", "origin/main")
            replacement = b / rel
            replacement.parent.mkdir(parents=True, exist_ok=True)
            replacement.write_text("v2\n")
            current = git(b, "rev-parse", f"origin/main:{rel}").stdout.strip()
            run_pub(
                b, "--path", rel, "--expect-blob", f"{rel}={current}",
                "--allow-replace", "--message", "renew",
            )
            path.write_text("v3-stale\n")
            failed = run_pub(
                a, "--path", rel, "--expect-blob", f"{rel}={stale}",
                "--allow-replace", "--message", "stale", check=False,
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("EXPECTED_BLOB_MISMATCH", failed.stderr)

    def test_same_path_conflict_does_not_clobber(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            a, b = td / "a", td / "b"
            clone(remote, a)
            clone(remote, b)
            (a / "same.txt").write_text("A\n")
            run_pub(a, "--path", "same.txt", "--message", "A")
            (b / "same.txt").write_text("B\n")
            failed = run_pub(b, "--path", "same.txt", "--message", "B", check=False)
            self.assertEqual(failed.returncode, 2)
            self.assertIn("TARGET_PATH_CONFLICT", failed.stderr)

    def test_delete_requires_expected_blob(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            clone(remote, worker)
            failed = run_pub(
                worker,
                "--delete-path", "README.md",
                "--message", "unsafe delete",
                check=False,
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("DELETE_REQUIRES_EXPECTED_BLOB", failed.stderr)

    def test_repository_identity_rejects_wrong_remote(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            remote = setup_remote(td)
            worker = td / "worker"
            clone(remote, worker)
            anchor = worker / ".uos/REPOSITORY_IDENTITY.yaml"
            anchor.parent.mkdir(parents=True, exist_ok=True)
            anchor.write_text(
                "Canonical:\n"
                "  Repository: https://github.com/example/not-this-repo\n"
                "  DefaultBranch: main\n"
            )
            (worker / "x.txt").write_text("x\n")
            failed = run_pub(worker, "--path", "x.txt", "--message", "wrong target", check=False)
            self.assertEqual(failed.returncode, 2)
            self.assertIn("NONCANONICAL_TARGET", failed.stderr)


if __name__ == "__main__":
    unittest.main()
