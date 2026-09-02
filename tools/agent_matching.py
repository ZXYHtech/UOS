#!/usr/bin/env python3
"""Capability-aware task selection for standalone UOS.

This is a thin discovery/claim adapter, not a second ownership system. It reads the
latest canonical READY work market, filters by an Agent capability envelope, then
claims the selected task through the normal ``tools/uos.py claim`` path. Canonical
Claim/Lease/Fencing and the quality visibility gate therefore remain authoritative.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

try:
    from canonical_publish import PublishError, git, verify_identity
    from control_extensions import execution_epoch
except ModuleNotFoundError:
    from tools.canonical_publish import PublishError, git, verify_identity
    from tools.control_extensions import execution_epoch


class AgentMatchingError(RuntimeError):
    pass


CONTEXT_RANK = {"XS": 1, "S": 2, "M": 3, "L": 4, "XL": 5}
REQUIREMENT_FIELDS = [
    "canonical_id", "min_capability_tier", "context_class", "tool_requirements", "allowed_roles"
]


def repo_root() -> Path:
    proc = git(["rev-parse", "--show-toplevel"], cwd=Path.cwd(), check=False)
    if proc.returncode == 0:
        return Path(proc.stdout.strip()).resolve()
    return Path.cwd().resolve()


def _tokens(value: str | Iterable[str]) -> set[str]:
    if isinstance(value, str):
        raw = value.replace(",", ";").split(";")
    else:
        raw = list(value)
    return {str(item).strip().lower() for item in raw if str(item).strip()}


def _roles(value: str | Iterable[str]) -> set[str]:
    return {item.upper() for item in _tokens(value)}


def _context_rank(value: str, *, default: int = 0) -> int:
    text = (value or "").strip().upper()
    if not text:
        return default
    return CONTEXT_RANK.get(text, 999 if text == "ANY" else -1)


def match_reasons(
    row: dict[str, str],
    *,
    capability_tier: int,
    tools: set[str],
    context_class: str,
    roles: set[str],
) -> list[str]:
    reasons: list[str] = []
    try:
        required_tier = int(row.get("min_capability_tier") or 1)
    except ValueError:
        required_tier = 1
    if capability_tier < required_tier:
        reasons.append(f"CAPABILITY_TIER<{required_tier}")

    required_tools = _tokens(row.get("tool_requirements") or "")
    missing_tools = sorted(required_tools - tools)
    if missing_tools:
        reasons.append("MISSING_TOOLS:" + ",".join(missing_tools))

    required_context = _context_rank(row.get("context_class") or "", default=0)
    agent_context = _context_rank(context_class, default=0)
    if required_context < 0:
        reasons.append(f"UNKNOWN_TASK_CONTEXT:{row.get('context_class')}")
    elif required_context and agent_context < required_context:
        reasons.append(f"CONTEXT<{(row.get('context_class') or '').upper()}")

    allowed_roles = _roles(row.get("allowed_roles") or "")
    if allowed_roles and not (allowed_roles & roles):
        reasons.append("ROLE_NOT_ALLOWED:" + ",".join(sorted(allowed_roles)))
    return reasons


def merge_requirements(rows: list[dict[str, str]], requirement_rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    overrides = {row.get("canonical_id", ""): row for row in requirement_rows if row.get("canonical_id")}
    out: list[dict[str, str]] = []
    for source in rows:
        row = dict(source)
        override = overrides.get(row.get("canonical_id", ""), {})
        for key in ("min_capability_tier", "context_class", "tool_requirements", "allowed_roles"):
            if override.get(key, "").strip():
                row[key] = override[key].strip()
        out.append(row)
    return out


def select_compatible(
    rows: list[dict[str, str]],
    *,
    capability_tier: int,
    tools: str = "",
    context_class: str = "S",
    roles: str = "",
    project: str = "",
    task: str = "",
    exclude: set[str] | None = None,
) -> tuple[dict[str, str] | None, dict[str, list[str]]]:
    tool_set = _tokens(tools)
    role_set = _roles(roles)
    excluded = exclude or set()
    considered: dict[str, list[str]] = {}
    candidates: list[dict[str, str]] = []
    for row in rows:
        task_id = row.get("canonical_id", "")
        if not task_id or task_id in excluded:
            continue
        if project and row.get("project_id") != project:
            continue
        if task and task_id != task:
            continue
        reasons = match_reasons(
            row,
            capability_tier=capability_tier,
            tools=tool_set,
            context_class=context_class,
            roles=role_set,
        )
        considered[task_id] = reasons
        if not reasons:
            candidates.append(row)
    candidates.sort(key=lambda row: (int(row.get("priority") or 9999), row.get("canonical_id", "")))
    return (candidates[0] if candidates else None), considered


def _is_git(root: Path) -> bool:
    return git(["rev-parse", "--git-dir"], cwd=root, check=False).returncode == 0


def _has_remote(root: Path, remote: str) -> bool:
    return _is_git(root) and git(["remote", "get-url", remote], cwd=root, check=False).returncode == 0


def _refresh_market(root: Path, *, remote: str, branch: str, project: str) -> None:
    args = [sys.executable, str(root / "tools/uos.py"), "--remote", remote, "--target-branch", branch, "status"]
    if project:
        args.extend(["--project", project])
    proc = subprocess.run(args, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise AgentMatchingError(proc.stderr.strip() or proc.stdout.strip() or "failed to refresh work market")


def _show(root: Path, commit: str, rel: str) -> str | None:
    proc = git(["show", f"{commit}:{rel}"], cwd=root, check=False)
    return proc.stdout if proc.returncode == 0 else None


def _read_csv(text: str | None) -> list[dict[str, str]]:
    if not text:
        return []
    return list(csv.DictReader(io.StringIO(text)))


def _latest_rows(root: Path, *, remote: str, branch: str, project: str) -> list[dict[str, str]]:
    if not _has_remote(root, remote):
        market = root / "coordination/runtime/WORK_MARKET.csv"
        rows = _read_csv(market.read_text(encoding="utf-8") if market.exists() else "")
        reqs: list[dict[str, str]] = []
        base = root / "orchestration/projects"
        if base.exists():
            for path in sorted(base.glob("*/TASK_AGENT_REQUIREMENTS.csv")):
                reqs.extend(_read_csv(path.read_text(encoding="utf-8")))
        return merge_requirements(rows, reqs)

    verify_identity(root, remote, branch)
    _refresh_market(root, remote=remote, branch=branch, project=project)
    git(["fetch", "--quiet", remote, branch], cwd=root)
    commit = git(["rev-parse", f"refs/remotes/{remote}/{branch}"], cwd=root).stdout.strip()
    rows = _read_csv(_show(root, commit, "coordination/runtime/WORK_MARKET.csv"))

    names = git(
        ["ls-tree", "-r", "--name-only", commit, "orchestration/projects"],
        cwd=root,
        check=False,
    ).stdout.splitlines()
    reqs: list[dict[str, str]] = []
    for rel in names:
        if rel.endswith("/TASK_AGENT_REQUIREMENTS.csv"):
            reqs.extend(_read_csv(_show(root, commit, rel)))
    return merge_requirements(rows, reqs)


def current_epoch(root: Path) -> str:
    return execution_epoch(root)


def claim_best(
    root: Path,
    *,
    agent_id: str,
    capability_tier: int,
    tools: str = "",
    context_class: str = "S",
    roles: str = "",
    project: str = "",
    task: str = "",
    lease_minutes: int = 90,
    ack_execution_epoch: str = "",
    remote: str = "origin",
    branch: str = "main",
    attempts: int = 4,
) -> subprocess.CompletedProcess[str]:
    if capability_tier < 1:
        raise AgentMatchingError("capability tier must be >= 1")
    excluded: set[str] = set()
    last_considered: dict[str, list[str]] = {}
    for _attempt in range(max(1, attempts)):
        rows = _latest_rows(root, remote=remote, branch=branch, project=project)
        selected, considered = select_compatible(
            rows,
            capability_tier=capability_tier,
            tools=tools,
            context_class=context_class,
            roles=roles,
            project=project,
            task=task,
            exclude=excluded,
        )
        last_considered = considered
        if selected is None:
            payload = {
                "status": "NO_MATCH",
                "reason": "NO_COMPATIBLE_READY_TASK",
                "project": project or None,
                "task": task or None,
                "agent_envelope": {
                    "capability_tier": capability_tier,
                    "tools": sorted(_tokens(tools)),
                    "context_class": context_class,
                    "roles": sorted(_roles(roles)),
                },
                "considered": considered,
            }
            return subprocess.CompletedProcess(args=[], returncode=4, stdout=json.dumps(payload, ensure_ascii=False, indent=2) + "\n", stderr="")

        task_id = selected["canonical_id"]
        cmd = [
            sys.executable,
            str(root / "tools/uos.py"),
            "--remote", remote,
            "--target-branch", branch,
        ]
        if ack_execution_epoch:
            cmd.extend(["--ack-execution-epoch", ack_execution_epoch])
        cmd.extend([
            "claim",
            "--agent-id", agent_id,
            "--task", task_id,
            "--lease-minutes", str(lease_minutes),
        ])
        if project:
            cmd.extend(["--project", project])
        proc = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode == 0:
            try:
                grant = json.loads(proc.stdout)
                if isinstance(grant, dict):
                    grant["matching"] = {
                        "capability_tier": capability_tier,
                        "tools": sorted(_tokens(tools)),
                        "context_class": context_class,
                        "roles": sorted(_roles(roles)),
                        "selected_task": task_id,
                    }
                    proc = subprocess.CompletedProcess(
                        args=proc.args,
                        returncode=0,
                        stdout=json.dumps(grant, ensure_ascii=False, indent=2) + "\n",
                        stderr=proc.stderr,
                    )
            except Exception:
                pass
            return proc
        if proc.returncode in {4} and not task:
            excluded.add(task_id)
            continue
        return proc

    payload = {
        "status": "NO_MATCH",
        "reason": "COMPATIBLE_TASKS_LOST_CANONICAL_RACES",
        "considered": last_considered,
    }
    return subprocess.CompletedProcess(args=[], returncode=4, stdout=json.dumps(payload, ensure_ascii=False, indent=2) + "\n", stderr="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Select/claim READY UOS work using an Agent capability envelope.")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--target-branch", default="main")
    parser.add_argument("--ack-execution-epoch", default="")
    sub = parser.add_subparsers(dest="command", required=True)

    def envelope(p: argparse.ArgumentParser, *, require_agent: bool) -> None:
        if require_agent:
            p.add_argument("--agent-id", required=True)
        p.add_argument("--capability-tier", type=int, default=1)
        p.add_argument("--tools", default="")
        p.add_argument("--context", default="S")
        p.add_argument("--roles", default="")
        p.add_argument("--project", default="")
        p.add_argument("--task", default="")

    item = sub.add_parser("select")
    envelope(item, require_agent=False)
    item = sub.add_parser("claim")
    envelope(item, require_agent=True)
    item.add_argument("--lease-minutes", type=int, default=90)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = repo_root()
    try:
        if args.command == "select":
            rows = _latest_rows(root, remote=args.remote, branch=args.target_branch, project=args.project)
            selected, considered = select_compatible(
                rows,
                capability_tier=args.capability_tier,
                tools=args.tools,
                context_class=args.context,
                roles=args.roles,
                project=args.project,
                task=args.task,
            )
            print(json.dumps({"status": "MATCH" if selected else "NO_MATCH", "selected": selected, "considered": considered}, ensure_ascii=False, indent=2))
            return 0 if selected else 4
        proc = claim_best(
            root,
            agent_id=args.agent_id,
            capability_tier=args.capability_tier,
            tools=args.tools,
            context_class=args.context,
            roles=args.roles,
            project=args.project,
            task=args.task,
            lease_minutes=args.lease_minutes,
            ack_execution_epoch=args.ack_execution_epoch,
            remote=args.remote,
            branch=args.target_branch,
        )
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)
        return proc.returncode
    except (AgentMatchingError, PublishError) as exc:
        print(f"UOS_MATCH_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
