from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
TOOLS = [
    "uos.py", "claim_broker_v2.py", "canonical_runner.py", "canonical_publish.py",
    "quality_gate.py", "control_extensions.py", "claim_integrity_scan.py",
]


def sh(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode:
        raise AssertionError(f"command failed rc={proc.returncode}: {args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def parse_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            k, v = line.split(":", 1); out[k.strip()] = v.strip()
    return out


def seed_local(root: Path) -> None:
    (root / "tools").mkdir(parents=True)
    for name in TOOLS:
        shutil.copy2(SOURCE / "tools" / name, root / "tools" / name)
    project = root / "orchestration/projects/DEMO"
    project.mkdir(parents=True)
    (project / "PROJECT.yaml").write_text("ProjectID: DEMO\nWorkRoot: projects/DEMO\n", encoding="utf-8")
    fields = [
        "id", "priority", "status", "role", "title", "deps", "inputs", "output",
        "project_id", "phase", "workstream", "exclusive_keys", "size_class",
        "quality_tier", "risk_tier", "wave_id", "batch_hint", "acceptance",
        "compliance_profile", "notes", "min_capability_tier", "context_class",
        "tool_requirements", "context_refs",
    ]
    row = {k: "" for k in fields}
    row.update({
        "id": "TASK_A", "priority": "1", "status": "READY", "role": "WORKER",
        "title": "A", "output": "projects/DEMO/a.txt", "project_id": "DEMO",
        "acceptance": "exists", "min_capability_tier": "1", "context_class": "S",
    })
    with (project / "TASK_CATALOG.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerow(row)
    sh([sys.executable, "tools/uos.py", "--transport", "local", "reconcile"], root)


class ClaimBrokerV2Tests(unittest.TestCase):
    def test_local_claim_uses_broker_v2_and_three_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); seed_local(root)
            proc = sh([sys.executable, "tools/uos.py", "--transport", "local", "claim", "--agent-id", "AG_A", "--task", "TASK_A"], root)
            packet = json.loads(proc.stdout)
            self.assertEqual(packet["ClaimAuthority"], "UOS_CLAIM_BROKER_V2")
            self.assertEqual(packet["ClaimMode"], "CREATE")
            lock = parse_kv(root / "coordination/claims/TASK_A.lock")
            grant = parse_kv(root / packet["GrantPath"])
            request = parse_kv(root / packet["RequestPath"])
            self.assertEqual(lock["ClaimAuthority"], "UOS_CLAIM_BROKER_V2")
            self.assertEqual(grant["ClaimAuthority"], "UOS_CLAIM_BROKER_V2")
            self.assertEqual(request["Decision"], "GRANTED")
            self.assertEqual(request["GrantID"], grant["GrantID"])

    def test_local_complete_fails_closed_on_grant_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); seed_local(root)
            packet = json.loads(sh([sys.executable, "tools/uos.py", "--transport", "local", "claim", "--agent-id", "AG_A", "--task", "TASK_A"], root).stdout)
            grant_path = root / packet["GrantPath"]
            grant_path.write_text(grant_path.read_text(encoding="utf-8").replace(f"LeaseToken: {packet['LeaseToken']}", "LeaseToken: tampered"), encoding="utf-8")
            out = root / "projects/DEMO/a.txt"; out.parent.mkdir(parents=True, exist_ok=True); out.write_text("x\n", encoding="utf-8")
            proc = sh([
                sys.executable, "tools/uos.py", "--transport", "local", "complete",
                "--agent-id", "AG_A", "--task", "TASK_A", "--lease-token", packet["LeaseToken"],
            ], root, check=False)
            self.assertEqual(proc.returncode, 2, (proc.stdout, proc.stderr))
            self.assertIn("Lock/Grant mismatch", proc.stderr)


if __name__ == "__main__":
    unittest.main()
