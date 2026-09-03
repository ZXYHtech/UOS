#!/usr/bin/env python3
"""Integrate generic Claim Broker V2 into uos.py and canonical_runner.py."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UOS = ROOT / "tools/uos.py"
RUNNER = ROOT / "tools/canonical_runner.py"
MARKER = "broker_claim_exact"


def patch_uos() -> bool:
    text = UOS.read_text(encoding="utf-8")
    if MARKER in text:
        print("uos Broker V2 integration already present")
        return False

    import_anchor = '''except ModuleNotFoundError:\n    from tools.control_extensions import (\n        ControlExtensionError,\n        build_work_market,\n        enforce_execution_epoch,\n        execution_epoch,\n        validate_project_output_scope,\n        write_durability_receipt,\n    )\n'''
    broker_import = '''\ntry:\n    from claim_broker_v2 import (\n        ClaimBrokerError,\n        claim_exact as broker_claim_exact,\n        validate_owned_lock as broker_validate_owned_lock,\n    )\nexcept ModuleNotFoundError:\n    from tools.claim_broker_v2 import (\n        ClaimBrokerError,\n        claim_exact as broker_claim_exact,\n        validate_owned_lock as broker_validate_owned_lock,\n    )\n'''
    if import_anchor not in text:
        raise SystemExit("phase4 uos import anchor not found")
    text = text.replace(import_anchor, import_anchor + broker_import, 1)

    old_claim = '''def command_claim(args: argparse.Namespace) -> int:\n    root = repo_root()\n    safe_id(args.agent_id, "agent id")\n    with RepoMutex(root):\n        row = choose_task(root, args)\n        if not row:\n            print(json.dumps({"status": "NO_MATCH"}))\n            return 4\n        task_id = row["id"]\n        path = claim_path(root, task_id)\n        old = parse_scalar_file(path)\n        generation = 1\n        if old:\n            if not is_stale(old):\n                print(json.dumps({"status": "NO_MATCH", "reason": "ALREADY_CLAIMED", "task": task_id}))\n                return 4\n            generation = int(old.get("LeaseGeneration") or 0) + 1\n            path.unlink(missing_ok=True)\n        token = secrets.token_hex(16)\n        expiry = utcnow() + timedelta(minutes=args.lease_minutes)\n        claim = {\n            "Schema": "UOS_CLAIM_V1",\n            "CanonicalID": task_id,\n            "ProjectID": row.get("project_id", ""),\n            "AgentID": args.agent_id,\n            "LeaseGeneration": generation,\n            "LeaseToken": token,\n            "ClaimedAt": iso(),\n            "LeaseExpiresAt": iso(expiry),\n            "FencingToken": f"{generation}:{token}",\n        }\n        write_kv(path, claim)\n        reconcile(root)\n    claim.update(\n        {\n            "Status": "GRANTED",\n            "Inputs": row.get("inputs", ""),\n            "Output": row.get("output", ""),\n            "Acceptance": row.get("acceptance", ""),\n        }\n    )\n    print(json.dumps(claim, ensure_ascii=False, indent=2))\n    return 0\n'''
    new_claim = '''def command_claim(args: argparse.Namespace) -> int:\n    root = repo_root()\n    safe_id(args.agent_id, "agent id")\n    with RepoMutex(root):\n        row = choose_task(root, args)\n        if not row:\n            print(json.dumps({"status": "NO_MATCH"}))\n            return 4\n        try:\n            claim = broker_claim_exact(\n                root,\n                row,\n                agent_id=args.agent_id,\n                lease_minutes=args.lease_minutes,\n                execution_epoch=execution_epoch(root),\n            )\n        except ClaimBrokerError as exc:\n            raise UOSError(str(exc)) from exc\n        if str(claim.get("status", "")).upper() == "NO_MATCH":\n            print(json.dumps(claim, ensure_ascii=False, indent=2))\n            return 4\n        reconcile(root)\n    print(json.dumps(claim, ensure_ascii=False, indent=2))\n    return 0\n'''
    if old_claim not in text:
        raise SystemExit("phase4 command_claim anchor not found")
    text = text.replace(old_claim, new_claim, 1)

    old_owner = '''def current_owned_lock(root: Path, args: argparse.Namespace) -> tuple[Path, dict[str, str]]:\n    path = claim_path(root, args.task)\n    lock = parse_scalar_file(path)\n    if not lock:\n        raise UOSError("claim not found")\n    if lock.get("AgentID") != args.agent_id:\n        raise UOSError("FENCED: wrong owner")\n    if lock.get("LeaseToken") != args.lease_token:\n        raise UOSError("FENCED: stale lease token")\n    if is_stale(lock):\n        raise UOSError("FENCED: lease expired")\n    return path, lock\n'''
    new_owner = '''def current_owned_lock(root: Path, args: argparse.Namespace) -> tuple[Path, dict[str, str]]:\n    try:\n        return broker_validate_owned_lock(\n            root,\n            task_id=args.task,\n            agent_id=args.agent_id,\n            lease_token=args.lease_token,\n            require_unexpired=True,\n        )\n    except ClaimBrokerError as exc:\n        raise UOSError(str(exc)) from exc\n'''
    if old_owner not in text:
        raise SystemExit("phase4 current_owned_lock anchor not found")
    text = text.replace(old_owner, new_owner, 1)

    UOS.write_text(text, encoding="utf-8")
    print("uos.py integrated with Claim Broker V2")
    return True


def patch_runner() -> bool:
    text = RUNNER.read_text(encoding="utf-8")
    marker = 'if packet.get("GrantPath") and packet.get("RequestPath"):'
    if marker in text:
        print("canonical_runner Broker V2 handoff already present")
        return False
    anchor = '''    if not isinstance(packet, dict):\n        return subprocess.CompletedProcess(proc.args, 2, "", "UOS_GRANT_ERROR: claim response is not an object\\n")\n    task_id = str(packet.get("CanonicalID") or option_value(local_argv, "--task") or "")\n'''
    replacement = '''    if not isinstance(packet, dict):\n        return subprocess.CompletedProcess(proc.args, 2, "", "UOS_GRANT_ERROR: claim response is not an object\\n")\n    # Broker V2 already wrote Request + Grant + Lock inside the local state\n    # mutation. The canonical runner now only publishes that whole tree via CAS.\n    if packet.get("GrantPath") and packet.get("RequestPath"):\n        return proc\n    task_id = str(packet.get("CanonicalID") or option_value(local_argv, "--task") or "")\n'''
    if anchor not in text:
        raise SystemExit("phase4 canonical_runner decorator anchor not found")
    text = text.replace(anchor, replacement, 1)
    RUNNER.write_text(text, encoding="utf-8")
    print("canonical_runner hands Broker V2 ownership through unchanged")
    return True


if __name__ == "__main__":
    patch_uos(); patch_runner()
