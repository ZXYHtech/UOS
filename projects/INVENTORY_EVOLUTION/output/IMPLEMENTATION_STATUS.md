# INVENTORY_EVOLUTION — Implementation Status

## Current state

**Phase:** E00 Release Safety / Migration / Recovery Foundation  
**Implementation state:** `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`  
**Do not mark E00 complete yet.**

External implementation repository:

- repository: `ZXYHtech/inventory`
- baseline/current main at start: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`
- implementation branch: `impl/e00-release-safety`
- current implementation head recorded here: `7e74eab2d49c5701dc530a3701f7836dcec0fe77`
- draft PR: `https://github.com/ZXYHtech/inventory/pull/3`

The PR is intentionally draft because the full private-repository local test suite has not been executed from this orchestration environment.

## E00 story implementation coverage

| Story | Code state | Validation state | Main evidence |
|---|---|---|---|
| E00-S01 schema version + numbered migration runner | Implemented | Awaiting local execution | `inventory_app/schema_migrations.py`, `tools/schema_migrate.py` |
| E00-S02 representative old-DB fixtures | Implemented | Awaiting local execution | `tools/legacy_schema_fixtures.py`, real historical refs `3e9eff4...`, `84d25e9...` |
| E00-S03 integrity + orphan checks | Implemented | Awaiting local execution | `inventory_app/db_integrity.py`, `tools/check_db_integrity.py` |
| E00-S04 local release gate | Implemented | Awaiting local execution | `tools/verify_release.py` |
| E00-S05 isolated restore verification | Implemented | Awaiting local execution | `inventory_app/recovery_verifier.py`, `tools/verify_backup_restore.py` |
| E00-S06 backup manifest/checksums | Implemented | Awaiting local execution | `inventory_app/backup_manifest.py`, `tools/build_backup_manifest.py` |
| E00-S07 off-host copy + health + scheduler path | Implemented | Awaiting local execution | `tools/copy_verified_backup.py`, `tools/run_backup_job.py`, Linux setup/update scripts |

## Key implementation decisions

### Baseline adoption instead of destructive migration-history replay

The historical application used:

```text
SCHEMA_SQL
 -> migrate(conn)
 -> seed
```

E00 preserves that compatibility path for pre-E00 databases, then validates the known current schema before recording:

```text
schema_migrations.version = 1
baseline_current_schema_20260810
source_ref = 78d5cda2527cf24836cd5b82a41f02ca8efdd02c
```

Future structural changes should be numbered immutable migrations rather than indefinitely expanding legacy `migrate(conn)`.

### Real historical fixtures

Migration tests no longer cover only a fresh DB. Embedded deterministic fixture schemas are based on actual repository history:

- `3e9eff41196847ad96badffe1705fc6671e68fb0` — initial Inventory Lite baseline;
- `84d25e9a270eadc869ed01746b46aa1d88d65985` — Stage 5/6 permissions, aliases and BOM era.

Fixture tests preserve representative material, quantity, order and alias records through upgrade.

### Release validation remains local/server-owned

Authoritative entry point:

```bash
python3 tools/verify_release.py
```

Optional stress checks:

```bash
python3 tools/verify_release.py --include-stress
```

No required verification depends on GitHub Actions.

### Backup correctness

The old Linux update flow copied the live WAL-mode database file with `cp -a`. E00 replaces this with SQLite Online Backup API snapshots, then restores the snapshot into a temporary database and runs schema/integrity/smoke checks before deployment proceeds.

### Recovery manifest and off-host copy

Recovery manifests record database/artifact/config paths, sizes and SHA-256 checksums. Verified off-host copy can target a mounted NAS/NFS/SMB/sshfs path and re-validates destination files before publishing the bundle.

### Backup scheduling

`tools/run_backup_job.py` is directly executable by an operator, cron or systemd timer. `setup_server.sh` installs a backup service/timer path, but does not enable an operator-unapproved cadence unless `INVENTORY_ENABLE_BACKUP_TIMER=1` is explicitly set.

## Required E00 verification gate

From a real checkout of `impl/e00-release-safety` run:

```bash
python3 tools/verify_release.py
```

The minimum gate must prove:

1. Python syntax/import compilation;
2. schema baseline adoption and repeat no-op;
3. migration from real historical fixture schemas;
4. rejection of incomplete/unknown/tampered migration state;
5. SQLite integrity and logical-orphan detection;
6. isolated backup restore verification;
7. backup manifest and checksum-tamper detection;
8. independently schedulable backup job with off-host copy fixture;
9. existing auth/security regression;
10. existing core business regression;
11. existing recognition regression;
12. existing warehouse-efficiency regression;
13. JS syntax checks when Node.js is available.

Any failure keeps E00 open. Do not proceed to the high-risk stock/reservation schema solely because the files exist.

## Next state

After local verification succeeds and PR #3 is reviewed/merged:

```text
E00 COMPLETE
 -> E01 Action Policy + Idempotency + Durable Jobs/Outbox
 -> E11-S01/S02 pricing margin terminology/formula safety
 -> E02 Stock Position + Reservation Kernel
```
