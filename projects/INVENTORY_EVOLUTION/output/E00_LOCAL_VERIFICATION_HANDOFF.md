# E00 Local Verification Handoff

## Purpose

E00 code is implemented and has received multiple static hardening passes, but it must **not** be marked complete until the authoritative repository-local gate runs from a real checkout of the implementation branch.

Inventory implementation:

- repo: `ZXYHtech/inventory`
- branch: `impl/e00-release-safety`
- expected reviewed head at handoff: `322a9d9d65c74e950e37d9f95c17f19510124f7f`
- PR: `ZXYHtech/inventory#3` (Draft)
- audited pre-E00 source frozen at branch `backup/pre-e00-audit-20260911`, commit `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`

No GitHub Actions run is required or accepted as the unique correctness path.

## 1. Verify exact checkout

```bash
git fetch origin
git switch impl/e00-release-safety
git pull --ff-only origin impl/e00-release-safety
git rev-parse HEAD
```

Expected head for this handoff:

```text
322a9d9d65c74e950e37d9f95c17f19510124f7f
```

If the branch intentionally advances, record the newer SHA and verify PR #3 contains the same commits before running the gate.

## 2. Minimum authoritative E00 gate

```bash
python3 tools/verify_release.py
```

Expected terminal result:

```text
RELEASE VERIFICATION: PASS
```

Any non-zero exit or `FAIL` keeps E00 open.

The gate must fail closed if a required Python source/test file is missing.

## 3. Linux release profile

```bash
python3 tools/verify_release.py --require-bash
```

When Node.js is an agreed release-host dependency:

```bash
python3 tools/verify_release.py --require-bash --require-node
```

`--require-bash` makes deployment shell syntax mandatory. `--require-node` makes JavaScript syntax and the existing client-routing regression mandatory.

## 4. Optional stress pass

```bash
python3 tools/verify_release.py --include-stress
```

This supplements but never replaces the deterministic gate.

## 5. What the gate must prove

At minimum:

1. required E00/core Python files compile and cannot be silently absent;
2. current baseline adoption succeeds and repeat run is a no-op;
3. real historical fixtures upgrade while preserving representative business rows;
4. unknown/tampered/gapped migration state is rejected;
5. forced postflight failure rolls back both test DDL and migration registry row;
6. SQLite integrity + expanded logical evidence checks pass on a clean fixture;
7. cross-warehouse inventory/location mismatch is detected;
8. broken purchase receipt-item ancestry is detected;
9. backup restores into an isolated DB and passes migration/integrity/smoke reads;
10. backup manifest/checksum tampering is detected;
11. missing/unmarked off-host destination is rejected;
12. marked off-host fixture copy succeeds and verifies destination hashes;
13. declared recovery-config path missing causes backup failure rather than an incomplete bundle;
14. successful scheduled-backup fixture includes declared config entries and release provenance;
15. pre-change deployed-code snapshot excludes runtime data/cache, records SHA-256/file list and refuses overwrite;
16. pre-change snapshot safely excludes its own output even when the backup directory is configured inside the application tree;
17. deployment safety regression proves `setup_server.sh` protects the entire runtime `data/` tree from `rsync --delete`;
18. deployment safety regression proves setup health-gates release publication and backup timer enablement;
19. deployment safety regression proves update creates the deployed-code snapshot **before** the database snapshot/cutover;
20. deployment safety regression proves update quiesces writers before code/schema cutover and restores timer only after health;
21. pre-upgrade recovery bundle is bound to the old deployed release and captures code snapshot + available deployment config when off-host recovery is configured;
22. existing auth/security, core workflow, recognition and warehouse-efficiency regressions pass;
23. shell/client checks run according to tool availability/strict flags.

## 6. Evidence to capture

```bash
git rev-parse HEAD
python3 --version
bash --version | head -1
node --version  # when available/required
python3 tools/verify_release.py --require-bash
```

Keep the complete gate output or at least:

- exact tested commit SHA;
- exact command;
- exit code;
- `RELEASE VERIFICATION: PASS` summary;
- step count / elapsed summary;
- Python/Bash/Node versions;
- intentionally skipped optional stress checks.

## 7. Production change preflight — mandatory, not optional

Repository tests prove the backup tooling logic, but production cutover has a separate mandatory protection chain documented in:

`PRODUCTION_CHANGE_SAFETY_POLICY.md`

Before production service stop or schema mutation, the update path must produce and verify:

```text
exact current deployed-server code snapshot
+ current production SQLite consistent snapshot
+ isolated DB restore PASS
+ manifest/checksums
+ off-host Recovery Bundle when configured/required
```

The production database has **not** been backed up merely because this code exists. A real production backup is only proven by the files/output produced on the actual server (or an explicitly authorized copy).

## 8. Optional staging recovery-bundle smoke

Only after the deterministic gate and only against a staging/copied DB:

```bash
mkdir -p /mnt/inventory-backup-test
touch /mnt/inventory-backup-test/.inventory-backup-target

cat >/tmp/inventory-staging.conf <<'EOF'
fixture=true
EOF

INVENTORY_BACKUP_CONFIG_PATHS=/tmp/inventory-staging.conf \
python3 tools/run_backup_job.py \
  --database /path/to/staging-copy.sqlite3 \
  --backup-dir /path/to/local-backups \
  --offhost-dir /mnt/inventory-backup-test \
  --source-ref "$(git rev-parse HEAD)" \
  --health-file /path/to/backup-health.json
```

Inspect the generated Manifest and destination bundle to confirm database, configured artifacts/config and `source_ref` are present.

Do not point this smoke test at the production DB without operator approval.

## 9. Completion rule

Only after:

```text
real checkout Release Gate = PASS
AND PR #3 has no unresolved blocker
```

may UOS transition E00 stories to complete and unblock E01 runtime implementation.

Production rollout additionally requires the server-side pre-change backup proof.

Until then:

```text
E00 = IMPLEMENTED_AWAITING_LOCAL_VERIFICATION
E01 = DESIGN_READY_BLOCKED_BY_E00_GATE
E02 = BLOCKED
```
