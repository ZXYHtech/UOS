#!/usr/bin/env python3
"""UOS result-visibility, preview and staged human-review policy.

This module is intentionally domain-neutral. It does not decide whether an
artifact is good; it decides when an Agent must expose a review packet and which
source artifacts require a human-friendly preview companion.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


class QualityGateError(RuntimeError):
    pass


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _scalar_yaml(path: Path) -> dict[str, str]:
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


def load_policy(root: Path) -> dict[str, Any]:
    raw = _scalar_yaml(root / ".uos/QUALITY_VISIBILITY_POLICY.yaml")
    enabled = raw.get("Enabled", "false").lower() in {"1", "true", "yes", "on"}
    return {
        "enabled": enabled,
        "rule_version": raw.get("RuleVersion", "VISIBILITY_V1"),
        "rule_epoch": int(raw.get("RuleEpoch", "1") or "1"),
        "warmup": int(raw.get("Review.WarmupRequired", "3") or "3"),
        "sample_every": int(raw.get("Review.SampleEvery", "5") or "5"),
        "high_risk_always": raw.get("Review.HighRiskAlwaysReview", "true").lower() in {"1", "true", "yes", "on"},
        "block_claims": raw.get("Review.BlockNewClaimsWhilePending", "true").lower() in {"1", "true", "yes", "on"},
        "present_in_conversation": raw.get("Presentation.AgentMustPresentResultInConversation", "true").lower() in {"1", "true", "yes", "on"},
    }


def _safe_rel(value: str) -> str:
    raw = (value or "").strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise QualityGateError(f"repository path escape: {value!r}")
    return str(path)


def preview_path_for(rel: str) -> str | None:
    path = PurePosixPath(_safe_rel(rel))
    suffix = path.suffix.lower()
    if suffix == ".svg":
        return str(path.with_suffix(".png"))
    if suffix in {".html", ".htm"}:
        return str(path.with_suffix(".preview.png"))
    if suffix == ".pdf":
        return str(path.with_suffix(".preview.png"))
    if suffix in {".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx", ".odt", ".ods", ".odp"}:
        return str(path.with_suffix(".preview.pdf"))
    if suffix in {
        ".step", ".stp", ".iges", ".igs", ".dxf", ".dwg", ".aedt", ".aedtz",
        ".kicad_pcb", ".kicad_sch", ".sch", ".brd", ".pcb", ".fcstd", ".f3d",
    }:
        return str(path.with_suffix(".preview.png"))
    return None


def expand_outputs(value: str) -> str:
    items = [_safe_rel(item) for item in (value or "").split(";") if item.strip()]
    out: list[str] = []
    seen: set[str] = set()
    for rel in items:
        if rel not in seen:
            out.append(rel)
            seen.add(rel)
        preview = preview_path_for(rel)
        if preview and preview not in seen:
            out.append(preview)
            seen.add(preview)
    return ";".join(out)


def rewrite_task_publish_args(argv: list[str], root: Path) -> list[str]:
    policy = load_policy(root)
    if not policy["enabled"] or len(argv) < 2 or argv[:2] != ["task", "publish"]:
        return list(argv)
    out = list(argv)
    for index, item in enumerate(out[:-1]):
        if item == "--output":
            out[index + 1] = expand_outputs(out[index + 1])
            return out
    for index, item in enumerate(out):
        if item.startswith("--output="):
            out[index] = "--output=" + expand_outputs(item.split("=", 1)[1])
            return out
    return out


def _task_row(root: Path, task_id: str) -> dict[str, str]:
    base = root / "orchestration/projects"
    for catalog in sorted(base.glob("*/TASK_CATALOG.csv")) if base.exists() else []:
        with catalog.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("id") == task_id:
                    return dict(row)
    raise QualityGateError(f"unknown task: {task_id}")


def completion_paths(root: Path, task_id: str) -> tuple[list[str], list[str]]:
    row = _task_row(root, task_id)
    declared = [_safe_rel(item) for item in (row.get("output") or "").split(";") if item.strip()]
    previews: list[str] = []
    for rel in declared:
        preview = preview_path_for(rel)
        if preview and preview not in previews:
            previews.append(preview)
    all_paths = list(declared)
    for preview in previews:
        if preview not in all_paths:
            all_paths.append(preview)
    return all_paths, previews


def validate_completion_artifacts(root: Path, task_id: str) -> tuple[list[str], list[str]]:
    all_paths, previews = completion_paths(root, task_id)
    missing = [rel for rel in all_paths if not (root / rel).exists() and not (root / rel).is_symlink()]
    if missing:
        raise QualityGateError(
            "PREVIEW_OR_OUTPUT_MISSING: " + ", ".join(missing)
            + ". Source artifacts such as SVG/HTML/PDF/Office/CAD must include their required preview companion."
        )
    return all_paths, previews


def event_path(root: Path, task_id: str) -> Path:
    return root / "coordination/quality/events" / f"{task_id}.json"


def _events(root: Path) -> list[dict[str, Any]]:
    base = root / "coordination/quality/events"
    out: list[dict[str, Any]] = []
    if not base.exists():
        return out
    for path in sorted(base.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data["_path"] = str(path.relative_to(root))
                out.append(data)
        except Exception:
            continue
    return out


def blocking_events(root: Path, project: str = "") -> list[dict[str, Any]]:
    policy = load_policy(root)
    if not policy["enabled"] or not policy["block_claims"]:
        return []
    blocked = []
    for event in _events(root):
        if int(event.get("rule_epoch", -1)) != policy["rule_epoch"]:
            continue
        if str(event.get("review_status", "")).upper() not in {"PENDING", "REJECTED"}:
            continue
        if project and str(event.get("project", "")) != project:
            continue
        blocked.append(event)
    return blocked


def claim_block_packet(root: Path, project: str = "") -> dict[str, Any] | None:
    blocked = blocking_events(root, project)
    if not blocked:
        return None
    return {
        "status": "REVIEW_BLOCKED",
        "message": "New Claim is paused until visible results are reviewed.",
        "pending_reviews": [
            {
                "task": item.get("task"),
                "project": item.get("project"),
                "sequence": item.get("sequence"),
                "outputs": item.get("outputs", []),
                "previews": item.get("previews", []),
                "review_status": item.get("review_status"),
            }
            for item in blocked
        ],
        "operator_instruction": "Present the result and previews in the conversation; do not send the user to GitHub for routine inspection.",
    }


def record_completion(root: Path, task_id: str) -> dict[str, Any] | None:
    policy = load_policy(root)
    if not policy["enabled"]:
        return None
    row = _task_row(root, task_id)
    outputs, previews = validate_completion_artifacts(root, task_id)
    existing = event_path(root, task_id)
    if existing.exists():
        try:
            data = json.loads(existing.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    current_events = [
        event for event in _events(root)
        if int(event.get("rule_epoch", -1)) == policy["rule_epoch"]
    ]
    sequence = len(current_events) + 1
    risk = str(row.get("risk_tier") or "LOW").upper()
    required = sequence <= policy["warmup"]
    reason = "RULE_EPOCH_WARMUP" if required else ""
    if not required and policy["sample_every"] > 0 and sequence % policy["sample_every"] == 0:
        required = True
        reason = "DETERMINISTIC_SAMPLE"
    if policy["high_risk_always"] and risk == "HIGH":
        required = True
        reason = "HIGH_RISK"

    event = {
        "schema": "UOS_QUALITY_EVENT_V1",
        "rule_version": policy["rule_version"],
        "rule_epoch": policy["rule_epoch"],
        "sequence": sequence,
        "task": task_id,
        "project": row.get("project_id", ""),
        "title": row.get("title", ""),
        "risk_tier": risk,
        "outputs": outputs,
        "previews": previews,
        "review_required": required,
        "review_reason": reason or "NOT_SAMPLED",
        "review_status": "PENDING" if required else "AUTO_ACCEPTED",
        "completed_at": iso_now(),
        "presentation": {
            "must_present_in_conversation": bool(policy["present_in_conversation"]),
            "must_include_summary": True,
            "must_render_or_attach_previews": bool(previews),
            "do_not_send_user_to_repository_for_routine_inspection": True,
        },
    }
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return event


def presentation_packet(event: dict[str, Any], original: dict[str, Any] | None = None) -> dict[str, Any]:
    packet: dict[str, Any] = dict(original or {})
    packet["quality_visibility"] = {
        "rule_epoch": event.get("rule_epoch"),
        "sequence": event.get("sequence"),
        "review_required": event.get("review_required"),
        "review_reason": event.get("review_reason"),
        "review_status": event.get("review_status"),
        "outputs": event.get("outputs", []),
        "previews": event.get("previews", []),
        "agent_action": "Summarize the result and show/attach previews directly in the conversation. Do not tell the user to inspect GitHub.",
    }
    if event.get("review_required"):
        packet["quality_visibility"]["next_claims"] = "PAUSED_UNTIL_OPERATOR_REVIEW"
    return packet


def _git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise QualityGateError(proc.stderr.strip() or proc.stdout.strip())
    return proc


def repo_root() -> Path:
    proc = _git(["rev-parse", "--show-toplevel"], Path.cwd(), check=False)
    if proc.returncode == 0:
        return Path(proc.stdout.strip()).resolve()
    return Path.cwd().resolve()


def _review_update(root: Path, task_id: str, decision: str, reviewer: str, feedback: str, remote: str, branch: str) -> dict[str, Any]:
    try:
        from canonical_publish import PublishError, blob_at, publish, verify_identity
    except ModuleNotFoundError:
        from tools.canonical_publish import PublishError, blob_at, publish, verify_identity

    if _git(["rev-parse", "--git-dir"], root, check=False).returncode != 0 or _git(["remote", "get-url", remote], root, check=False).returncode != 0:
        path = event_path(root, task_id)
        if not path.exists():
            raise QualityGateError(f"review event not found: {task_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["review_status"] = decision
        data["reviewed_at"] = iso_now()
        data["reviewed_by"] = reviewer
        if feedback:
            data["feedback"] = feedback
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return data

    try:
        verify_identity(root, remote, branch)
    except PublishError as exc:
        raise QualityGateError(str(exc)) from exc
    _git(["fetch", "--quiet", remote, branch], root)
    base = _git(["rev-parse", f"refs/remotes/{remote}/{branch}"], root).stdout.strip()
    worktree = Path(tempfile.mkdtemp(prefix="uos-quality-review-"))
    added = False
    try:
        add = _git(["worktree", "add", "--detach", "--force", str(worktree), base], root, check=False)
        if add.returncode:
            raise QualityGateError(add.stderr.strip() or add.stdout.strip())
        added = True
        rel = str(event_path(worktree, task_id).relative_to(worktree))
        path = worktree / rel
        if not path.exists():
            raise QualityGateError(f"review event not found: {task_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if str(data.get("review_status", "")).upper() not in {"PENDING", "REJECTED"}:
            raise QualityGateError(f"review is already closed: {task_id} status={data.get('review_status')}")
        expected = blob_at(worktree, base, rel)
        if not expected:
            raise QualityGateError(f"canonical review blob missing: {task_id}")
        data["review_status"] = decision
        data["reviewed_at"] = iso_now()
        data["reviewed_by"] = reviewer
        if feedback:
            data["feedback"] = feedback
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        publish(
            worktree,
            paths=[rel],
            deletes=[],
            require_absent=[],
            expect_blobs={rel: expected},
            message=f"quality review {decision.lower()} {task_id}",
            remote=remote,
            branch=branch,
            allow_replace=True,
        )
        return data
    finally:
        if added:
            _git(["worktree", "remove", "--force", str(worktree)], root, check=False)
        shutil.rmtree(worktree, ignore_errors=True)
        _git(["worktree", "prune"], root, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(prog="quality_gate")
    subs = parser.add_subparsers(dest="command", required=True)
    status = subs.add_parser("status")
    status.add_argument("--project", default="")
    review = subs.add_parser("review")
    review_sub = review.add_subparsers(dest="review_command", required=True)
    for name in ("accept", "reject"):
        item = review_sub.add_parser(name)
        item.add_argument("--task", required=True)
        item.add_argument("--by", default="OPERATOR")
        item.add_argument("--feedback", default="")
        item.add_argument("--remote", default="origin")
        item.add_argument("--target-branch", default="main")
    args = parser.parse_args()
    root = repo_root()
    try:
        if args.command == "status":
            print(json.dumps(claim_block_packet(root, args.project) or {"status": "CLEAR"}, ensure_ascii=False, indent=2))
            return 0
        decision = "ACCEPTED" if args.review_command == "accept" else "REJECTED"
        result = _review_update(root, args.task, decision, args.by, args.feedback, args.remote, args.target_branch)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except QualityGateError as exc:
        print(f"UOS_QUALITY_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
