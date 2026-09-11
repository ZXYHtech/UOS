# E00 Local Verification Handoff

## Purpose

E00 code is implemented and has received multiple static hardening passes, but it must **not** be marked complete until the authoritative repository-local gate runs from a real checkout of the implementation branch.

Inventory implementation:

- repo: `ZXYHtech/inventory`
- branch: `impl/e00-release-safety`
- expected reviewed head at handoff: `44aea593da47e74f31b120db581a2f5e8442d349`
- PR: `ZXYHtech/inventory#3` (keep Draft until gate passes/review completes)

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
44aea593da47e74f31b120db581a2f5e8442d349
```

If the branch has intentionally advanced, record the newer SHA and verify that PR #3 contains the same commits before running the gate.

## 2. Minimum authoritative E00 gate

```bash
python3 tools/verify_release.py
```

Expected terminal result:

```text
RELEASE VERIFICATION: PASS
```

Any non-zero exit or `FAIL` keeps E00 open.

The gate must execute the required Python regression files rather than silently skipping missing files.

## 3. Linux release-profile gate

On a Linux deployment/release workstation:

```bash
python3 tools/verify_release.py --require-bash
```

This makes deployment/start shell syntax checks mandatory.

If Node.js is part of the release workstation contract, use:

```bash
python3 tools/verify_release.py --require-bash --require-node
```

This additionally requires and executes the existing client-routing regression.

Do not fail E00 merely because a minimal server intentionally lacks Node unless Node is an agreed release-host dependency; the default gate still runs JS/client checks automatically when Node is available.

## 4. Optional stress pass

Not a substitute for the deterministic gate:

```bash
python3 tools/verify_release.py --include-stress
```

Run when OCR/image stress dependencies and machine resources are appropriate.

## 5. What the gate must prove

At minimum:

1. required E00/core Python files compile and cannot be silently absent;
2. current baseline adoption succeeds and repeat run is a no-op;
3. real historical fixture schemas upgrade while preserving representative business rows;
4. unknown/tampered/gapped migration state is rejected;
5. forced postflight failure rolls back test DDL and migration registry row;
6. SQLite integrity + expanded logical evidence checks pass on a clean fixture;
7. cross-warehouse inventory/location mismatch is detected;
8. broken purchase receipt-item ancestry is detected;
9. backup restores into an isolated DB and passes migration/integrity/smoke reads;
10. backup manifest/checksum tampering is detected;
11. missing/unmarked off-host destination is rejected;
12. marked off-host fixture copy succeeds and verifies destination hashes;
13. independent backup job writes correct success/failure health state and release provenance;
14. existing auth/security, core workflow, recognition and warehouse-efficiency regressions pass;
15. shell/client checks run according to tool availability / strict flags.

## 6. Evidence to capture

Record the following in the PR/UOS completion evidence:

```bash
git rev-parse HEAD
python3 --version
bash --version | head -1
node --version  # when available/required
python3 tools/verify_release.py --require-bash
```

Keep the complete gate output or at least:

- exact tested commit SHA;
- command;
- exit code;
- `RELEASE VERIFICATION: PASS` summary;
- step count / elapsed summary;
- environment versions;
- any intentionally skipped optional stress checks.

## 7. Optional staging backup smoke

After the deterministic gate and only against a staging/copied database:

```bash
mkdir -p /mnt/inventory-backup-test
# In production this marker must be created on the verified mounted second failure domain.
touch /mnt/inventory-backup-test/.inventory-backup-target

python3 tools/run_backup_job.py \
  --database /path/to/staging-copy.sqlite3 \
  --backup-dir /path/to/local-backups \
  --offhost-dir /mnt/inventory-backup-test \
  --source-ref "$(git rev-parse HEAD)" \
  --health-file /path/to/backup-health.json
```

Do not use the staging command as permission to point the test at the production DB without operator approval.

## 8. E00 completion rule

Only after:

```text
real checkout gate = PASS
AND PR #3 review has no unresolved blocker
```

may UOS transition E00 stories to completed and unblock E01 runtime implementation.

Until then:

```text
E00 = IMPLEMENTED_AWAITING_LOCAL_VERIFICATION
E01 = DESIGN_READY_IMPLEMENTATION_BLOCKED_BY_E00
E02 = BLOCKED
```
