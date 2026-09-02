#!/usr/bin/env python3
"""Maintain optional Agent matching requirements for standalone UOS tasks.

The task catalog remains the primary task definition. This sidecar adds only
matching hints that should not affect ownership or write authority.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import secrets
import sys
from pathlib import Path

try:
    from canonical_publish import PublishError, blob_at, git, publish, verify_identity
    from control_extensions import execution_epoch
except ModuleNotFoundError:
    from tools.canonical_publish import PublishError, blob_at, git, publish, verify_identity
    from tools.control_extensions import execution_epoch


FIELDS = ["canonical_id", "min_capability_tier", "context_class", "tool_requirements", "allowed_roles"]


class RequirementError(RuntimeError):
    pass


def repo_root() -> Path:
    proc = git(["rev-parse", "--show-toplevel"], cwd=Path.cwd(), check=False)
    if proc.returncode == 0:
        return Path(proc.stdout.strip()).resolve()
    return Path.cwd().resolve()


def _require_epoch(root: Path, ack: str) -> None:
    current = execution_epoch(root)
    if current and ack != current:
        raise RequirementError(
            f"REBOOT_REQUIRED: current ExecutionEpoch is {current}; run `python tools/uos.py boot` and retry with --ack-execution-epoch {current}"
        )


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _read_csv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text))) if text.strip() else []


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    for row in sorted(rows, key=lambda r: r.get("canonical_id", "")):
        writer.writerow({field: row.get(field, "") for field in FIELDS})
    _atomic_write(path, buffer.getvalue())


def _show(root: Path, commit: str, rel: str) -> str | None:
    proc = git(["show", f"{commit}:{rel}"], cwd=root, check=False)
    return proc.stdout if proc.returncode == 0 else None


def _task_exists(root: Path, commit: str | None, project: str, task: str) -> bool:
    rel = f"orchestration/projects/{project}/TASK_CATALOG.csv"
    if commit:
        text = _show(root, commit, rel)
    else:
        path = root / rel
        text = path.read_text(encoding="utf-8") if path.exists() else None
    if not text:
        return False
    return any(row.get("id") == task for row in csv.DictReader(io.StringIO(text)))


def _has_remote(root: Path, remote: str) -> bool:
    return git(["rev-parse", "--git-dir"], cwd=root, check=False).returncode == 0 and git(
        ["remote", "get-url", remote], cwd=root, check=False
    ).returncode == 0


def set_requirement(
    root: Path,
    *,
    project: str,
    task: str,
    min_capability_tier: int,
    context_class: str,
    tools: str,
    allowed_roles: str,
    ack_execution_epoch: str,
    remote: str,
    branch: str,
    retries: int = 5,
) -> dict[str, str]:
    _require_epoch(root, ack_execution_epoch)
    if min_capability_tier < 1:
        raise RequirementError("min capability tier must be >= 1")
    context_class = (context_class or "S").upper()
    if context_class not in {"XS", "S", "M", "L", "XL"}:
        raise RequirementError("context must be one of XS,S,M,L,XL")
    rel = f"orchestration/projects/{project}/TASK_AGENT_REQUIREMENTS.csv"
    path = root / rel
    new_row = {
        "canonical_id": task,
        "min_capability_tier": str(min_capability_tier),
        "context_class": context_class,
        "tool_requirements": ";".join(sorted({x.strip().lower() for x in tools.replace(",", ";").split(";") if x.strip()})),
        "allowed_roles": ";".join(sorted({x.strip().upper() for x in allowed_roles.replace(",", ";").split(";") if x.strip()})),
    }

    if not _has_remote(root, remote):
        if not _task_exists(root, None, project, task):
            raise RequirementError(f"unknown task: {task}")
        rows = _read_csv(path.read_text(encoding="utf-8") if path.exists() else "")
        rows = [row for row in rows if row.get("canonical_id") != task] + [new_row]
        _write_rows(path, rows)
        return new_row

    verify_identity(root, remote, branch)
    for _attempt in range(max(1, retries)):
        git(["fetch", "--quiet", remote, branch], cwd=root)
        commit = git(["rev-parse", f"refs/remotes/{remote}/{branch}"], cwd=root).stdout.strip()
        if not _task_exists(root, commit, project, task):
            raise RequirementError(f"unknown canonical task: {task}")
        old_text = _show(root, commit, rel) or ""
        rows = _read_csv(old_text)
        rows = [row for row in rows if row.get("canonical_id") != task] + [new_row]
        _write_rows(path, rows)
        old_blob = blob_at(root, commit, rel)
        try:
            publish(
                root,
                paths=[rel],
                deletes=[],
                require_absent=[] if old_blob else [rel],
                expect_blobs={rel: old_blob} if old_blob else {},
                message=f"set Agent requirements for {task}",
                remote=remote,
                branch=branch,
                retries=3,
                allow_replace=bool(old_blob),
            )
            return new_row
        except PublishError as exc:
            if "EXPECTED_BLOB_MISMATCH" in str(exc) or "REQUIRE_ABSENT_FAILED" in str(exc):
                continue
            raise
    raise RequirementError("requirements update lost repeated canonical races")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Set task capability/tool/context matching requirements.")
    p.add_argument("--remote", default="origin")
    p.add_argument("--target-branch", default="main")
    p.add_argument("--ack-execution-epoch", default="")
    sub = p.add_subparsers(dest="command", required=True)
    item = sub.add_parser("set")
    item.add_argument("--project", required=True)
    item.add_argument("--task", required=True)
    item.add_argument("--min-capability", type=int, default=1)
    item.add_argument("--context", default="S")
    item.add_argument("--tools", default="")
    item.add_argument("--allowed-roles", default="")
    return p


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    try:
        if args.command == "set":
            row = set_requirement(
                root,
                project=args.project,
                task=args.task,
                min_capability_tier=args.min_capability,
                context_class=args.context,
                tools=args.tools,
                allowed_roles=args.allowed_roles,
                ack_execution_epoch=args.ack_execution_epoch,
                remote=args.remote,
                branch=args.target_branch,
            )
            print(json.dumps({"status": "UPDATED", "requirement": row}, ensure_ascii=False, indent=2))
            return 0
    except (RequirementError, PublishError) as exc:
        print(f"UOS_REQUIREMENT_ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
