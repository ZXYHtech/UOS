# E00 Local Verification Handoff

## Purpose

E00 code is implemented and statically hardened, but must **not** be marked complete until the authoritative repository-local gate runs from a real checkout.

Inventory implementation:

- repo: `ZXYHtech/inventory`
- branch: `impl/e00-release-safety`
- expected reviewed head: `0e0870499f7e8b5e68a308231eae954f106bd5aa`
- PR: `ZXYHtech/inventory#3` (Draft)
- frozen pre-E00 source: `backup/pre-e00-audit-20260911` -> `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`

No GitHub Actions run is required or accepted as the unique correctness path.

## 1. Verify exact checkout

```bash
git fetch origin
git switch impl/e00-release-safety
git pull --ff-only origin impl/e00-release-safety
git rev-parse HEAD
```

Expected head:

```text
0e0870499f7e8b5e68a308231eae954f106bd5aa
```

If the branch intentionally advances, record the newer SHA and verify PR #3 contains it before running the gate.

## 2. Minimum authoritative E00 gate

```bash
python3 tools/verify_release.py
```

Expected result:

```text
RELEASE VERIFICATION: PASS
```

Any non-zero exit/FAIL keeps E00 open.

Linux release profile:

```bash
python3 tools/verify_release.py --require-bash
```

When Node is an agreed release-host dependency:

```bash
python3 tools/verify_release.py --require-bash --require-node
```

Optional stress pass:

```bash
python3 tools/verify_release.py --include-stress
```

## 3. What the gate must prove

At minimum:

1. required E00/core Python files cannot be silently absent;
2. baseline adoption succeeds and rerun is a no-op;
3. real historical fixtures upgrade while preserving representative rows;
4. unknown/tampered/gapped migration state is rejected;
5. forced postflight failure rolls back both test DDL and registry row;
6. SQLite + logical evidence integrity checks behave correctly;
7. cross-warehouse inventory/location mismatch is detected;
8. broken purchase receipt-item ancestry is detected;
9. a DB backup restores into an isolated database and passes smoke reads;
10. manifest/hash tampering is detected;
11. missing/unmarked off-host target is rejected;
12. marked off-host fixture copy is hash-verified;
13. missing declared recovery config fails the backup;
14. successful scheduled-backup fixture contains declared config and release provenance;
15. exact deployed-code snapshot excludes runtime data/cache, records SHA-256/file list and refuses overwrite;
16. code snapshot cannot archive its own output even if the backup directory is under the app tree;
17. setup protects the whole runtime `data/` tree from `rsync --delete`;
18. setup publishes release identity/enables timer only after health;
19. update refuses a missing production DB rather than creating a fresh one;
20. update requires existing `git`/`python3` and does not install them before pre-change evidence;
21. update runs only a narrow compile check before using backup tooling;
22. update captures code + DB + isolated restore + manifest before any apt/pip/code/schema cutover;
23. `PREFLIGHT_ONLY` exits before apt/pip, service stop, rsync or production migration;
24. real cutover stops backup/OCR/Web writers before apt/pip runtime mutation;
25. full target Release Gate runs after target dependencies are prepared and before target code is synced into production;
26. pre-upgrade backup is bound to the old deployed release;
27. backup timer resumes only after post-cutover health;
28. auth/security, core workflow, recognition and warehouse-efficiency regressions remain green;
29. shell/client checks run according to available/required tools.

## 4. Evidence to capture

```bash
git rev-parse HEAD
python3 --version
bash --version | head -1
node --version  # when available/required
python3 tools/verify_release.py --require-bash
```

Retain the complete output or at least:

- tested commit SHA;
- exact command;
- exit code;
- `RELEASE VERIFICATION: PASS`;
- step count/elapsed summary;
- environment versions;
- optional checks intentionally not run.

## 5. Production backup-only preflight

Repository Gate completion and production rollout are separate concerns.

Production safety policy: `PRODUCTION_CHANGE_SAFETY_POLICY.md`.

Before a maintenance window, use:

```bash
INVENTORY_PREFLIGHT_ONLY=1 \
INVENTORY_REPO_BRANCH=<target-branch> \
sudo -E bash deploy/linux/update_server.sh
```

A successful preflight must create/verify:

```text
exact current deployed-code snapshot
+ production SQLite consistent snapshot
+ isolated restore PASS
+ manifest/checksums
+ off-host Recovery Bundle when configured
```

and end with:

```text
PREFLIGHT ONLY: PASS
```

It must not install/update packages, stop Web/OCR, sync target code or mutate the production schema.

Important: production DB backup has **not** already happened merely because this implementation exists. It is proven only by actual server-side output/files.

## 6. Real cutover safety

The real update repeats fresh snapshots immediately before cutover. Only after backup proof does it enter maintenance mode:

```text
stop backup/OCR/Web writers
 -> apt/pip target dependencies
 -> full target Release Gate
 -> rsync target code
 -> numbered migration + postflight
 -> restart + health
```

Any failure after quiescence leaves application writers stopped for explicit repair/restore.

## 7. Optional staging recovery-bundle smoke

Only against staging/copied data:

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

Do not point staging smoke tests at production without explicit operator authorization.

## 8. Completion rule

Only after:

```text
real checkout Release Gate = PASS
AND PR #3 has no unresolved blocker
```

may E00 move to complete and E01 runtime implementation begin.

Production rollout has the additional server-side pre-change backup requirement.

Until then:

```text
E00 = IMPLEMENTED_AWAITING_LOCAL_VERIFICATION
E01 = DESIGN_READY_BLOCKED_BY_E00_GATE
E02 = BLOCKED
```
