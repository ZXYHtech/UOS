#!/usr/bin/env python3
"""Run UOS lifecycle commands as latest-canonical Git transactions.

This is the integration layer between the local deterministic `tools/uos.py`
state machine and Git's canonical ref arbitration. Each attempt gets a fresh
snapshot of canonical main, runs the local state machine in an isolated detached
worktree, and publishes the resulting tree with a normal non-force push.

A ref race never reparents stale derived state. The whole UOS command is rerun
from the newer canonical snapshot.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

try:
    from canonical_publish import PublishError, git, is_ref_race, verify_identity
    from quality_gate import (
        QualityGateError,
        claim_block_packet,
        completion_paths,
        event_path,
        load_policy,
        presentation_packet,
        record_completion,
        rewrite_task_publish_args,
    )
except ModuleNotFoundError:
    from tools.canonical_publish import PublishError, git, is_ref_race, verify_identity
    from tools.quality_gate import (
        QualityGateError,
        claim_block_packet,
        completion_paths,
        event_path,
        load_policy,
        presentation_packet,
        record_completion,
        rewrite_task_publish_args,
    )


class CanonicalRunError(RuntimeError):
    pass


def git_repository(root: Path) -> bool:
    proc = git(["rev-parse", "--git-dir"], cwd=root, check=False)
    return proc.returncode == 0


def remote_exists(root: Path, remote: str) -> bool:
    proc = git(["remote", "get-url", remote], cwd=root, check=False)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def resolve_transport(root: Path, requested: str, remote: str, branch: str) -> str:
    """Resolve auto transport without unsafe network-failure fallback."""
    if os.environ.get("UOS_INTERNAL_LOCAL") == "1":
        return "local"
    requested = (requested or "auto").lower()
    if requested not in {"auto", "local", "git-cas"}:
        raise CanonicalRunError(f"unknown transport: {requested}")
    if requested == "local":
        return "local"
    if not git_repository(root):
        if requested == "git-cas":
            raise CanonicalRunError("git-cas transport requires a Git repository")
        return "local"
    if not remote_exists(root, remote):
        if requested == "git-cas":
            raise CanonicalRunError(f"git-cas transport requires remote {remote!r}")
        return "local"
    try:
        verify_identity(root, remote, branch)
    except PublishError as exc:
        raise CanonicalRunError(str(exc)) from exc
    return "git-cas"


def strip_transport_args(argv: list[str]) -> list[str]:
    names = {"--transport", "--remote", "--target-branch", "--cas-retries"}
    out: list[str] = []
    index = 0
    while index < len(argv):
        item = argv[index]
        matched_equals = next((name for name in names if item.startswith(name + "=")), None)
        if matched_equals:
            index += 1
            continue
        if item in names:
            if index + 1 >= len(argv):
                raise CanonicalRunError(f"{item} requires a value")
            index += 2
            continue
        out.append(item)
        index += 1
    return out


def option_value(argv: list[str], name: str) -> str:
    for index, item in enumerate(argv):
        if item == name and index + 1 < len(argv):
            return argv[index + 1]
        if item.startswith(name + "="):
            return item.split("=", 1)[1]
    return ""


def _safe_rel(value: str) -> str:
    raw = (value or "").strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CanonicalRunError(f"repository path escape: {value!r}")
    return str(path)


def _declared_task_outputs(snapshot: Path, task_id: str) -> list[str]:
    base = snapshot / "orchestration/projects"
    if not base.exists():
        raise CanonicalRunError(f"unknown task: {task_id}")
    for catalog in sorted(base.glob("*/TASK_CATALOG.csv")):
        with catalog.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("id") == task_id:
                    return [_safe_rel(item) for item in (row.get("output") or "").split(";") if item.strip()]
    raise CanonicalRunError(f"unknown task: {task_id}")


def _task_outputs(snapshot: Path, task_id: str) -> list[str]:
    if load_policy(snapshot)["enabled"]:
        try:
            paths, _previews = completion_paths(snapshot, task_id)
            return paths
        except QualityGateError as exc:
            raise CanonicalRunError(str(exc)) from exc
    return _declared_task_outputs(snapshot, task_id)


def _tree_digest(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_symlink():
        digest.update(b"L\0" + os.readlink(path).encode("utf-8", errors="surrogateescape"))
        return digest.hexdigest()
    if path.is_file():
        digest.update(b"F\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    if path.is_dir():
        digest.update(b"D\0")
        for child in sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix()):
            rel = child.relative_to(path).as_posix().encode()
            digest.update(rel + b"\0" + _tree_digest(child).encode() + b"\0")
        return digest.hexdigest()
    return "ABSENT"


def _copy_one(source: Path, target: Path, *, allow_replace: bool = False) -> None:
    if target.exists() or target.is_symlink():
        if _tree_digest(source) == _tree_digest(target):
            return
        if not allow_replace:
            raise CanonicalRunError(
                f"TARGET_PATH_CONFLICT: canonical output differs from caller output: {target}"
            )
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        target.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target)


def _review_rejected(snapshot: Path, task_id: str) -> bool:
    path = event_path(snapshot, task_id)
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("review_status", "")).upper() == "REJECTED"
    except Exception:
        return False


def prepare_caller_artifacts(caller_root: Path, snapshot: Path, argv: list[str]) -> None:
    if not argv or argv[0] != "complete":
        return
    task_id = option_value(argv, "--task")
    if not task_id:
        raise CanonicalRunError("complete requires --task")
    allow_replace = _review_rejected(snapshot, task_id)
    for rel in _task_outputs(snapshot, task_id):
        source = caller_root / rel
        if source.exists() or source.is_symlink():
            _copy_one(source, snapshot / rel, allow_replace=allow_replace)


def _canonical_message(argv: list[str]) -> str:
    if not argv:
        return "UOS canonical transaction"
    command = " ".join(argv[:2]) if argv[0] in {"project", "task"} and len(argv) > 1 else argv[0]
    task = option_value(argv, "--task") or option_value(argv, "--task-id")
    project = option_value(argv, "--project") or option_value(argv, "--project-id")
    suffix = task or project
    return f"uos {command}{' ' + suffix if suffix else ''} [canonical]"


def _candidate_from_worktree(snapshot: Path, base: str, message: str) -> str | None:
    status = git(["status", "--porcelain", "--untracked-files=all"], cwd=snapshot).stdout
    if not status.strip():
        return None
    # Fresh canonical worktree: force-add is intentional so declared previews or
    # outputs matched by .gitignore cannot produce a completion fact without the artifact.
    git(["add", "-A", "-f"], cwd=snapshot)
    tree = git(["write-tree"], cwd=snapshot).stdout.strip()
    base_tree = git(["rev-parse", f"{base}^{{tree}}"], cwd=snapshot).stdout.strip()
    if tree == base_tree:
        return None
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "UOS Canonical Runner",
            "GIT_AUTHOR_EMAIL": "uos@example.invalid",
            "GIT_COMMITTER_NAME": "UOS Canonical Runner",
            "GIT_COMMITTER_EMAIL": "uos@example.invalid",
        }
    )
    return git(["commit-tree", tree, "-p", base, "-m", message], cwd=snapshot, env=env).stdout.strip()


def _quality_blocked_proc(local_argv: list[str], snapshot: Path) -> subprocess.CompletedProcess[str] | None:
    if not local_argv or local_argv[0] != "claim":
        return None
    project = option_value(local_argv, "--project")
    task_id = option_value(local_argv, "--task")
    packet = claim_block_packet(snapshot, project, task_id)
    if packet is None:
        return None
    return subprocess.CompletedProcess(
        args=local_argv,
        returncode=6,
        stdout=json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        stderr="",
    )


def _quality_complete_proc(proc: subprocess.CompletedProcess[str], snapshot: Path, local_argv: list[str]) -> subprocess.CompletedProcess[str]:
    if not local_argv or local_argv[0] != "complete" or proc.returncode != 0:
        return proc
    task_id = option_value(local_argv, "--task")
    if not task_id:
        return proc
    try:
        event = record_completion(snapshot, task_id)
    except QualityGateError as exc:
        return subprocess.CompletedProcess(
            args=proc.args,
            returncode=2,
            stdout="",
            stderr=f"UOS_QUALITY_ERROR: {exc}\n",
        )
    if not event:
        return proc
    original: dict[str, object] = {}
    try:
        parsed = json.loads(proc.stdout or "{}")
        if isinstance(parsed, dict):
            original = parsed
    except Exception:
        original = {"status": "DONE", "task": task_id}
    packet = presentation_packet(event, original)
    return subprocess.CompletedProcess(
        args=proc.args,
        returncode=proc.returncode,
        stdout=json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
        stderr=proc.stderr,
    )


def run_canonical(
    caller_root: Path,
    argv: list[str],
    *,
    remote: str = "origin",
    branch: str = "main",
    retries: int = 8,
) -> subprocess.CompletedProcess[str]:
    if retries < 1 or retries > 50:
        raise CanonicalRunError("--cas-retries must be between 1 and 50")
    if not git_repository(caller_root) or not remote_exists(caller_root, remote):
        raise CanonicalRunError("canonical runner requires a Git repository with a configured remote")
    try:
        verify_identity(caller_root, remote, branch)
    except PublishError as exc:
        raise CanonicalRunError(str(exc)) from exc

    base_argv = strip_transport_args(argv)
    target_ref = f"refs/heads/{branch}"
    remote_ref = f"refs/remotes/{remote}/{branch}"
    last_proc: subprocess.CompletedProcess[str] | None = None

    for attempt in range(1, retries + 1):
        fetch = git(["fetch", "--quiet", remote, branch], cwd=caller_root, check=False)
        if fetch.returncode:
            raise CanonicalRunError(
                f"CANONICAL_FETCH_FAILED: {fetch.stderr.strip() or fetch.stdout.strip()}"
            )
        base = git(["rev-parse", remote_ref], cwd=caller_root).stdout.strip()
        worktree = Path(tempfile.mkdtemp(prefix="uos-canonical-worktree-"))
        added = False
        try:
            add = git(["worktree", "add", "--detach", "--force", str(worktree), base], cwd=caller_root, check=False)
            if add.returncode:
                raise CanonicalRunError(
                    f"WORKTREE_CREATE_FAILED: {add.stderr.strip() or add.stdout.strip()}"
                )
            added = True

            local_argv = rewrite_task_publish_args(base_argv, worktree)
            blocked = _quality_blocked_proc(local_argv, worktree)
            if blocked is not None:
                return blocked

            prepare_caller_artifacts(caller_root, worktree, local_argv)

            env = os.environ.copy()
            env["UOS_INTERNAL_LOCAL"] = "1"
            env["UOS_CALLER_ROOT"] = str(caller_root)
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            proc = subprocess.run(
                [sys.executable, str(worktree / "tools/uos.py"), "--transport", "local", *local_argv],
                cwd=worktree,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            proc = _quality_complete_proc(proc, worktree, local_argv)
            last_proc = proc
            if proc.returncode != 0:
                return proc

            candidate = _candidate_from_worktree(worktree, base, _canonical_message(local_argv))
            if candidate is None:
                return proc

            test_delay = float(os.environ.get("UOS_CAS_TEST_DELAY_BEFORE_PUSH", "0") or "0")
            if test_delay > 0:
                time.sleep(test_delay)

            push = git(
                ["push", "--porcelain", remote, f"{candidate}:{target_ref}"],
                cwd=caller_root,
                check=False,
            )
            if push.returncode == 0:
                git(["fetch", "--quiet", remote, branch], cwd=caller_root, check=False)
                return proc
            if not is_ref_race(push):
                raise CanonicalRunError(
                    f"CANONICAL_PUSH_FAILED: {push.stderr.strip() or push.stdout.strip()}"
                )
            if attempt == retries:
                raise CanonicalRunError("CANONICAL_REF_RACE_RETRY_EXHAUSTED")
            time.sleep(random.uniform(0.02, 0.08) * attempt)
        finally:
            if added:
                git(["worktree", "remove", "--force", str(worktree)], cwd=caller_root, check=False)
            shutil.rmtree(worktree, ignore_errors=True)
            git(["worktree", "prune"], cwd=caller_root, check=False)

    if last_proc is not None:
        return last_proc
    raise CanonicalRunError("canonical transaction did not execute")
