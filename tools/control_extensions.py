#!/usr/bin/env python3
"""Small standalone control-plane extensions extracted from proven AI_book UOS lessons.

The module stays domain-neutral and single-repository:
- ExecutionEpoch acknowledgement for stale-agent safety.
- Project WorkRoot output-scope enforcement.
- Deterministic WORK_MARKET derivation.
- Machine-readable artifact durability receipts.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import secrets
from pathlib import Path, PurePosixPath
from typing import Iterable


class ControlExtensionError(RuntimeError):
    pass


CRITICAL_COMMANDS = {"project", "task", "claim", "renew", "complete", "reconcile"}


def _safe_rel(value: str) -> str:
    raw = (value or "").strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ControlExtensionError(f"repository path escape: {value!r}")
    return str(path)


def _parse_scalar(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in raw or raw.lstrip().startswith(("#", "-")):
            continue
        key, value = raw.split(":", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    try:
        temp.write_text(content, encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def execution_epoch(root: Path) -> str:
    return _parse_scalar(root / ".uos/EXECUTION_CONTRACT.yaml").get("ExecutionEpoch", "")


def enforce_execution_epoch(root: Path, command: str, ack: str) -> None:
    epoch = execution_epoch(root)
    if not epoch or command not in CRITICAL_COMMANDS:
        return
    if (ack or "").strip() != epoch:
        raise ControlExtensionError(
            f"REBOOT_REQUIRED: current ExecutionEpoch is {epoch}; run `python tools/uos.py boot` "
            "and retry the critical command with --ack-execution-epoch <CURRENT_EPOCH>"
        )


def project_work_root(root: Path, project_id: str) -> str:
    meta = _parse_scalar(root / "orchestration/projects" / project_id / "PROJECT.yaml")
    work_root = meta.get("WorkRoot") or f"projects/{project_id}"
    return _safe_rel(work_root).rstrip("/")


def validate_project_output_scope(root: Path, project_id: str, output_spec: str) -> None:
    work_root = project_work_root(root, project_id)
    for raw in (output_spec or "").split(";"):
        if not raw.strip():
            continue
        rel = _safe_rel(raw)
        if rel != work_root and not rel.startswith(work_root + "/"):
            raise ControlExtensionError(
                f"PATH_AUTHORITY_DENIED: task in project {project_id} may write only under {work_root}/; got {rel}"
            )


WORK_MARKET_FIELDS = [
    "canonical_id", "project_id", "priority", "role", "title", "workstream",
    "size_class", "min_capability_tier", "context_class", "tool_requirements", "output",
]


def build_work_market(runtime: Path, rows: Iterable[dict[str, str]], states: dict[str, str]) -> None:
    market = [row for row in rows if states.get(row.get("id", "")) == "READY"]
    market.sort(key=lambda row: (int(row.get("priority") or 9999), row.get("id", "")))
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=WORK_MARKET_FIELDS)
    writer.writeheader()
    for row in market:
        writer.writerow(
            {
                "canonical_id": row.get("id", ""),
                "project_id": row.get("project_id", ""),
                "priority": row.get("priority", ""),
                "role": row.get("role", ""),
                "title": row.get("title", ""),
                "workstream": row.get("workstream", ""),
                "size_class": row.get("size_class", ""),
                "min_capability_tier": row.get("min_capability_tier", ""),
                "context_class": row.get("context_class", ""),
                "tool_requirements": row.get("tool_requirements", ""),
                "output": row.get("output", ""),
            }
        )
    _atomic_write(runtime / "WORK_MARKET.csv", buffer.getvalue())


def _digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest_path(path: Path) -> tuple[str, str]:
    if path.is_symlink():
        return "symlink", hashlib.sha256(os.readlink(path).encode("utf-8", errors="surrogateescape")).hexdigest()
    if path.is_file():
        return "file", _digest_file(path)
    if path.is_dir():
        digest = hashlib.sha256()
        for child in sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix()):
            rel = child.relative_to(path).as_posix()
            kind, child_digest = _digest_path(child)
            digest.update(f"{rel}\0{kind}\0{child_digest}\0".encode("utf-8"))
        return "directory", digest.hexdigest()
    return "absent", ""


def write_durability_receipt(root: Path, task_id: str, project_id: str, outputs: list[str]) -> dict[str, object]:
    artifacts: list[dict[str, str]] = []
    missing: list[str] = []
    for raw in outputs:
        rel = _safe_rel(raw)
        path = root / rel
        if not path.exists() and not path.is_symlink():
            missing.append(rel)
            continue
        kind, sha256 = _digest_path(path)
        artifacts.append({"path": rel, "kind": kind, "sha256": sha256})

    payload: dict[str, object] = {
        "schema": "UOS_ARTIFACT_DURABILITY_V1",
        "task": task_id,
        "project": project_id,
        "status": "DURABLE_READY" if not missing else "DURABILITY_INCOMPLETE",
        "binding_mode": "SAME_CANONICAL_TREE_TRANSACTION",
        "artifacts": artifacts,
        "missing": missing,
    }
    target = root / "coordination/quality/durability" / f"{task_id}.json"
    _atomic_write(target, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return payload
