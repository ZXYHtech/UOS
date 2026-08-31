#!/usr/bin/env python3
"""Standalone UOS latest-canonical Git CAS publisher.

Publishes explicit working-tree paths to one canonical branch without switching
branches and without force. Every retry is rebuilt from the latest remote branch.
This module is repository-agnostic and intentionally contains no AI_book rules.
"""
from __future__ import annotations

import argparse
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable


class PublishError(RuntimeError):
    pass


def git(args: Iterable[str], *, cwd: Path | None = None, env: dict[str, str] | None = None,
        check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, env=env, text=True, input=input_text,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if check and proc.returncode:
        raise PublishError(
            f"git {' '.join(args)} failed ({proc.returncode}): "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc


def root_dir() -> Path:
    proc = git(["rev-parse", "--show-toplevel"])
    return Path(proc.stdout.strip()).resolve()


def normalize_repo_path(root: Path, value: str) -> str:
    raw = Path(value)
    if raw.is_absolute():
        try:
            raw = raw.resolve().relative_to(root)
        except ValueError as exc:
            raise PublishError(f"PATH_ESCAPE: {value}") from exc
    norm = raw.as_posix()
    while norm.startswith("./"):
        norm = norm[2:]
    if not norm or norm == "." or norm == ".git" or norm.startswith(".git/"):
        raise PublishError(f"INVALID_PATH: {value}")
    parts = Path(norm).parts
    if any(part == ".." for part in parts):
        raise PublishError(f"PATH_ESCAPE: {value}")
    return norm


def flatten_simple_yaml(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    stack: list[tuple[int, str]] = []
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, value = raw.strip().split(":", 1)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        prefix = ".".join(item[1] for item in stack)
        full = f"{prefix}.{key}" if prefix else key
        value = value.strip().strip('"').strip("'")
        if value:
            out[full] = value
        else:
            stack.append((indent, key))
    return out


def normalize_locator(value: str) -> str:
    text = (value or "").strip().rstrip("/")
    if text.startswith("git@github.com:"):
        text = "https://github.com/" + text[len("git@github.com:"):]
    if text.startswith("ssh://git@github.com/"):
        text = "https://github.com/" + text[len("ssh://git@github.com/"):]
    if text.endswith(".git"):
        text = text[:-4]
    return text.lower()


def verify_identity(root: Path, remote: str, branch: str) -> None:
    identity_path = root / ".uos/REPOSITORY_IDENTITY.yaml"
    if not identity_path.exists():
        return
    identity = flatten_simple_yaml(identity_path)
    expected_repo = normalize_locator(identity.get("Canonical.Repository", ""))
    expected_branch = (identity.get("Canonical.DefaultBranch") or "main").strip()
    if expected_branch and branch != expected_branch:
        raise PublishError(f"NONCANONICAL_BRANCH: requested={branch} expected={expected_branch}")
    if expected_repo:
        remote_url = git(["remote", "get-url", remote], cwd=root).stdout.strip()
        actual_repo = normalize_locator(remote_url)
        if actual_repo != expected_repo:
            raise PublishError(
                f"NONCANONICAL_TARGET: remote={actual_repo or remote_url} expected={expected_repo}"
            )


def mode_for(path: Path) -> str:
    if path.is_symlink():
        return "120000"
    return "100755" if (path.stat().st_mode & 0o111) else "100644"


def hash_path(root: Path, rel: str) -> tuple[str, str]:
    path = root / rel
    if not path.exists() and not path.is_symlink():
        raise PublishError(f"WORKTREE_PATH_MISSING: {rel}")
    mode = mode_for(path)
    if mode == "120000":
        proc = git(["hash-object", "-w", "--stdin"], cwd=root, input_text=os.readlink(path))
    else:
        proc = git(["hash-object", "-w", "--", rel], cwd=root)
    return mode, proc.stdout.strip()


def blob_at(root: Path, commit: str, rel: str) -> str | None:
    proc = git(["rev-parse", f"{commit}:{rel}"], cwd=root, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def is_ref_race(proc: subprocess.CompletedProcess[str]) -> bool:
    text = f"{proc.stdout}\n{proc.stderr}".lower()
    return any(token in text for token in (
        "non-fast-forward", "fetch first", "[rejected]", "failed to push some refs",
        "cannot lock ref", "stale info", "remote rejected",
    ))


def parse_expected(values: list[str], root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise PublishError("--expect-blob must be PATH=SHA")
        path, sha = value.split("=", 1)
        rel = normalize_repo_path(root, path)
        sha = sha.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
            raise PublishError(f"INVALID_EXPECTED_BLOB: {value}")
        if rel in result and result[rel] != sha:
            raise PublishError(f"DUPLICATE_EXPECTATION: {rel}")
        result[rel] = sha
    return result


def publish(
    root: Path,
    *,
    paths: list[str],
    deletes: list[str],
    require_absent: list[str],
    expect_blobs: dict[str, str],
    message: str,
    remote: str = "origin",
    branch: str = "main",
    retries: int = 8,
    allow_replace: bool = False,
) -> str:
    if retries < 1 or retries > 50:
        raise PublishError("retries must be 1..50")
    verify_identity(root, remote, branch)
    publish_paths = [normalize_repo_path(root, value) for value in paths]
    delete_paths = [normalize_repo_path(root, value) for value in deletes]
    absent_paths = [normalize_repo_path(root, value) for value in require_absent]
    if len(set(publish_paths)) != len(publish_paths):
        raise PublishError("DUPLICATE_PATH")
    if set(publish_paths) & set(delete_paths):
        raise PublishError("PATH_PUBLISH_DELETE_CONFLICT")
    unchecked_deletes = [rel for rel in delete_paths if rel not in expect_blobs]
    if unchecked_deletes:
        raise PublishError(f"DELETE_REQUIRES_EXPECTED_BLOB: {unchecked_deletes}")
    if not publish_paths and not delete_paths:
        raise PublishError("EMPTY_TRANSACTION")

    local_entries = {rel: hash_path(root, rel) for rel in publish_paths}
    remote_ref = f"refs/remotes/{remote}/{branch}"
    target_ref = f"refs/heads/{branch}"

    for attempt in range(1, retries + 1):
        git(["fetch", "--quiet", remote, branch], cwd=root)
        base = git(["rev-parse", remote_ref], cwd=root).stdout.strip()
        base_tree = git(["rev-parse", f"{base}^{{tree}}"], cwd=root).stdout.strip()

        for rel in absent_paths:
            if blob_at(root, base, rel) is not None:
                raise PublishError(f"REQUIRE_ABSENT_FAILED: {rel}")
        for rel, expected in expect_blobs.items():
            actual = blob_at(root, base, rel)
            if actual != expected:
                raise PublishError(
                    f"EXPECTED_BLOB_MISMATCH: {rel} expected={expected} actual={actual or 'ABSENT'}"
                )

        changed = False
        for rel, (_mode, new_blob) in local_entries.items():
            old_blob = blob_at(root, base, rel)
            if old_blob is None or old_blob == new_blob:
                changed = changed or old_blob is None
                continue
            if not allow_replace or rel not in expect_blobs:
                raise PublishError(f"TARGET_PATH_CONFLICT: {rel}")
            changed = True
        for rel in delete_paths:
            if blob_at(root, base, rel) is not None:
                changed = True

        if not changed:
            return base

        with tempfile.NamedTemporaryFile(prefix="uos-index-", delete=True) as index_file:
            env = os.environ.copy()
            env["GIT_INDEX_FILE"] = index_file.name
            git(["read-tree", base_tree], cwd=root, env=env)
            for rel, (mode, blob) in local_entries.items():
                git(["update-index", "--add", "--cacheinfo", mode, blob, rel], cwd=root, env=env)
            for rel in delete_paths:
                git(["update-index", "--force-remove", "--", rel], cwd=root, env=env, check=False)
            tree = git(["write-tree"], cwd=root, env=env).stdout.strip()

        if tree == base_tree:
            return base
        candidate = git(["commit-tree", tree, "-p", base, "-m", message], cwd=root).stdout.strip()
        push = git(["push", "--porcelain", remote, f"{candidate}:{target_ref}"], cwd=root, check=False)
        if push.returncode == 0:
            git(["fetch", "--quiet", remote, branch], cwd=root, check=False)
            return candidate
        if not is_ref_race(push):
            raise PublishError(
                f"PUSH_FAILED: {push.stderr.strip() or push.stdout.strip()}"
            )
        if attempt == retries:
            raise PublishError("CANONICAL_REF_RACE_RETRY_EXHAUSTED")
        time.sleep(random.uniform(0.02, 0.08) * attempt)
    raise PublishError("unreachable")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Publish explicit paths to latest canonical Git branch with non-force CAS semantics.")
    p.add_argument("--path", action="append", default=[])
    p.add_argument("--delete-path", action="append", default=[])
    p.add_argument("--require-absent", action="append", default=[])
    p.add_argument("--expect-blob", action="append", default=[])
    p.add_argument("--message", required=True)
    p.add_argument("--remote", default="origin")
    p.add_argument("--target-branch", default="main")
    p.add_argument("--retries", type=int, default=8)
    p.add_argument("--allow-replace", action="store_true")
    return p


def main() -> int:
    try:
        args = parser().parse_args()
        root = root_dir()
        expected = parse_expected(args.expect_blob, root)
        commit = publish(
            root,
            paths=args.path,
            deletes=args.delete_path,
            require_absent=args.require_absent,
            expect_blobs=expected,
            message=args.message,
            remote=args.remote,
            branch=args.target_branch,
            retries=args.retries,
            allow_replace=args.allow_replace,
        )
        print(commit)
        return 0
    except PublishError as exc:
        print(f"UOS_CAS_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
