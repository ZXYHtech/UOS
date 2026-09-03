#!/usr/bin/env python3
"""Integrate UOS completion Outbox fallback and CLI entrypoint.

Applied and tested in CI before publishing kernel changes back to canonical main.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"phase6 patch anchor missing: {label}")
    return text.replace(old, new, 1)


def patch_canonical_runner() -> None:
    path = ROOT / "tools/canonical_runner.py"
    text = path.read_text(encoding="utf-8")

    if "from completion_outbox import CompletionOutboxError, stage_completion_candidate" not in text:
        anchor = (
            "try:\n"
            "    from claim_telemetry import decorate_claim_result, record_claim_candidate\n"
            "except ModuleNotFoundError:\n"
            "    from tools.claim_telemetry import decorate_claim_result, record_claim_candidate\n"
        )
        block = anchor + (
            "\ntry:\n"
            "    from completion_outbox import CompletionOutboxError, stage_completion_candidate\n"
            "except ModuleNotFoundError:\n"
            "    from tools.completion_outbox import CompletionOutboxError, stage_completion_candidate\n"
        )
        text = replace_once(text, anchor, block, "completion outbox import")

    ownership_anchor = (
        "            prior_claim_lock: dict[str, str] | None = None\n"
        "            prior_claim_blob_sha = \"\"\n"
        "            if local_argv and local_argv[0] == \"claim\":\n"
    )
    if "completion_owner_lock" not in text:
        ownership_block = (
            "            completion_owner_lock: dict[str, str] | None = None\n"
            "            completion_owner_lock_blob_sha = \"\"\n"
            "            if local_argv and local_argv[0] == \"complete\":\n"
            "                completion_task = option_value(local_argv, \"--task\")\n"
            "                if completion_task:\n"
            "                    completion_lock_path = worktree / \"coordination/claims\" / f\"{completion_task}.lock\"\n"
            "                    if completion_lock_path.exists():\n"
            "                        completion_owner_lock = _parse_kv(completion_lock_path)\n"
            "                        completion_owner_lock_blob_sha = _ownership_git_blob_sha(completion_lock_path)\n"
            "\n"
            + ownership_anchor
        )
        text = replace_once(text, ownership_anchor, ownership_block, "completion ownership snapshot")

    exhaustion_anchor = (
        "            if attempt == retries:\n"
        "                raise CanonicalRunError(\"CANONICAL_REF_RACE_RETRY_EXHAUSTED\")\n"
    )
    if "COMPLETION_STAGED" not in text:
        exhaustion_block = (
            "            if attempt == retries:\n"
            "                if local_argv and local_argv[0] == \"complete\" and completion_owner_lock:\n"
            "                    task_id = option_value(local_argv, \"--task\")\n"
            "                    if not task_id:\n"
            "                        raise CanonicalRunError(\"complete fallback lost task id\")\n"
            "                    try:\n"
            "                        staged = stage_completion_candidate(\n"
            "                            caller_root,\n"
            "                            candidate_root=worktree,\n"
            "                            base=base,\n"
            "                            candidate_commit=candidate,\n"
            "                            task_id=task_id,\n"
            "                            owner_lock=completion_owner_lock,\n"
            "                            owner_lock_blob_sha=completion_owner_lock_blob_sha,\n"
            "                            remote=remote,\n"
            "                            branch=branch,\n"
            "                        )\n"
            "                    except CompletionOutboxError as exc:\n"
            "                        raise CanonicalRunError(f\"COMPLETION_OUTBOX_STAGE_FAILED: {exc}\") from exc\n"
            "                    original: object = proc.stdout.strip()\n"
            "                    try:\n"
            "                        original = json.loads(proc.stdout)\n"
            "                    except Exception:\n"
            "                        pass\n"
            "                    packet = {\n"
            "                        \"status\": \"COMPLETION_STAGED\",\n"
            "                        \"task\": task_id,\n"
            "                        \"canonical_done\": False,\n"
            "                        \"reason\": \"DIRECT_MAIN_REF_RACE_RETRY_EXHAUSTED\",\n"
            "                        \"outbox\": staged,\n"
            "                        \"completion_candidate\": original,\n"
            "                        \"instruction\": \"Do not treat the task as Done and do not claim unrelated next work until the outbox candidate is canonically ingested. Run `python tools/uos.py outbox ingest` or wait for another Agent to perform mechanical ingest.\",\n"
            "                    }\n"
            "                    return subprocess.CompletedProcess(\n"
            "                        args=proc.args,\n"
            "                        returncode=7,\n"
            "                        stdout=json.dumps(packet, ensure_ascii=False, indent=2) + \"\\n\",\n"
            "                        stderr=proc.stderr,\n"
            "                    )\n"
            "                raise CanonicalRunError(\"CANONICAL_REF_RACE_RETRY_EXHAUSTED\")\n"
        )
        text = replace_once(text, exhaustion_anchor, exhaustion_block, "completion outbox fallback")

    path.write_text(text, encoding="utf-8")
    print("patched tools/canonical_runner.py")


def patch_uos() -> None:
    path = ROOT / "tools/uos.py"
    text = path.read_text(encoding="utf-8")

    reconcile_anchor = (
        "def command_reconcile(_args: argparse.Namespace) -> int:\n"
        "    root = repo_root()\n"
        "    with RepoMutex(root):\n"
        "        payload = reconcile(root)\n"
        "    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))\n"
        "    return 0\n"
    )
    if "def command_outbox_ingest" not in text:
        block = reconcile_anchor + r'''


def command_outbox_status(args: argparse.Namespace) -> int:
    root = repo_root()
    try:
        from completion_outbox import status as outbox_status
    except ModuleNotFoundError:
        from tools.completion_outbox import status as outbox_status
    payload = outbox_status(root, remote=args.remote, branch=args.target_branch)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def command_outbox_ingest(args: argparse.Namespace) -> int:
    root = repo_root()
    # Ingest can complete tasks and delete canonical locks, so it carries the
    # same stale-agent ExecutionEpoch requirement as `complete`.
    try:
        enforce_execution_epoch(root, "complete", args.ack_execution_epoch)
    except ControlExtensionError as exc:
        raise UOSError(str(exc)) from exc
    try:
        from completion_outbox import ingest as outbox_ingest
    except ModuleNotFoundError:
        from tools.completion_outbox import ingest as outbox_ingest
    payload = outbox_ingest(
        root,
        remote=args.remote,
        branch=args.target_branch,
        max_batch=args.max_batch,
        retries=args.ingest_retries,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0
'''
        text = replace_once(text, reconcile_anchor, block, "uos outbox commands")

    parser_anchor = (
        "    item = subs.add_parser(\"complete\")\n"
        "    item.add_argument(\"--agent-id\", required=True)\n"
        "    item.add_argument(\"--task\", required=True)\n"
        "    item.add_argument(\"--lease-token\", required=True)\n"
        "    item.add_argument(\"--result\", default=\"PASS\")\n"
        "    item.add_argument(\"--allow-missing-output\", action=\"store_true\")\n"
        "    item.set_defaults(func=command_complete)\n"
        "    return parser\n"
    )
    if 'subs.add_parser("outbox")' not in text:
        parser_block = (
            "    item = subs.add_parser(\"complete\")\n"
            "    item.add_argument(\"--agent-id\", required=True)\n"
            "    item.add_argument(\"--task\", required=True)\n"
            "    item.add_argument(\"--lease-token\", required=True)\n"
            "    item.add_argument(\"--result\", default=\"PASS\")\n"
            "    item.add_argument(\"--allow-missing-output\", action=\"store_true\")\n"
            "    item.set_defaults(func=command_complete)\n"
            "\n"
            "    outbox = subs.add_parser(\"outbox\")\n"
            "    outbox_subs = outbox.add_subparsers(dest=\"outbox_command\", required=True)\n"
            "    item = outbox_subs.add_parser(\"status\")\n"
            "    item.set_defaults(func=command_outbox_status)\n"
            "    item = outbox_subs.add_parser(\"ingest\")\n"
            "    item.add_argument(\"--max-batch\", type=int, default=16)\n"
            "    item.add_argument(\"--ingest-retries\", type=int, default=8)\n"
            "    item.add_argument(\"--dry-run\", action=\"store_true\")\n"
            "    item.set_defaults(func=command_outbox_ingest)\n"
            "    return parser\n"
        )
        text = replace_once(text, parser_anchor, parser_block, "uos outbox parser")

    transport_anchor = (
        "        try:\n"
        "            from canonical_runner import resolve_transport, run_canonical\n"
        "        except ModuleNotFoundError:\n"
        "            from tools.canonical_runner import resolve_transport, run_canonical\n"
        "\n"
        "        mode = resolve_transport(root, args.transport, args.remote, args.target_branch)\n"
    )
    if 'if args.command == "outbox":' not in text:
        transport_block = (
            "        if args.command == \"outbox\":\n"
            "            return args.func(args)\n"
            "\n"
            + transport_anchor
        )
        text = replace_once(text, transport_anchor, transport_block, "outbox direct dispatch")

    path.write_text(text, encoding="utf-8")
    print("patched tools/uos.py")


def patch_test_fixtures() -> None:
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        if '"canonical_runner.py"' not in text or "TOOLS" not in text or '"completion_outbox.py"' in text:
            continue
        original = text
        if '    "claim_telemetry.py",\n' in text:
            text = text.replace(
                '    "claim_telemetry.py",\n',
                '    "claim_telemetry.py",\n    "completion_outbox.py",\n',
                1,
            )
        elif '"claim_telemetry.py",' in text:
            text = text.replace('"claim_telemetry.py",', '"claim_telemetry.py", "completion_outbox.py",', 1)
        elif '    "claim_broker_v2.py",\n' in text:
            text = text.replace(
                '    "claim_broker_v2.py",\n',
                '    "claim_broker_v2.py",\n    "completion_outbox.py",\n',
                1,
            )
        elif '"claim_broker_v2.py",' in text:
            text = text.replace('"claim_broker_v2.py",', '"claim_broker_v2.py", "completion_outbox.py",', 1)
        else:
            raise SystemExit(f"unable to add completion_outbox fixture dependency: {path.relative_to(ROOT)}")
        if text != original:
            path.write_text(text, encoding="utf-8")
            print("patched", path.relative_to(ROOT))


def main() -> None:
    patch_canonical_runner()
    patch_uos()
    patch_test_fixtures()


if __name__ == "__main__":
    main()
