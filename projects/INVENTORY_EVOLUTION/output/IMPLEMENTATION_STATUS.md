# INVENTORY_EVOLUTION — Implementation Status

## Current state

**Phase:** E00 Release Safety / Migration / Recovery Foundation  
**Implementation state:** `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`  
**Do not mark E00 complete yet.**

External implementation repository:

- repository: `ZXYHtech/inventory`
- baseline/current main at start: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`
- implementation branch: `impl/e00-release-safety`
- current implementation head recorded here: `61d486d9c1323d65694e7d7c0f6f3078eaf60045`
- draft PR: `https://github.com/ZXYHtech/inventory/pull/3`

The PR remains intentionally draft because the full repository-local release gate has not yet been executed from a real checkout.

## E00 story implementation coverage

| Story | Code state | Validation state | UOS evidence |
|---|---|---|---|
| E00-S01 schema version + numbered migration runner | Implemented | Awaiting local execution | `TASK_INV_IMPL_E00_S01.md` |
| E00-S02 representative old-DB fixtures | Implemented | Awaiting local execution | `TASK_INV_IMPL_E00_S02.md` |
| E00-S03 integrity + orphan checks | Implemented | Awaiting local execution | `TASK_INV_IMPL_E00_S03.md` |
| E00-S04 local release gate | Implemented + statically hardened | Awaiting local execution | `TASK_INV_IMPL_E00_S04.md` |
| E00-S05 isolated restore verification | Implemented | Awaiting local execution | `TASK_INV_IMPL_E00_S05.md` |
| E00-S06 backup manifest/checksums | Implemented | Awaiting local execution | `TASK_INV_IMPL_E00_S06.md` |
| E00-S07 off-host copy + health + scheduler path | Implemented + statically hardened | Awaiting local execution | `TASK_INV_IMPL_E00_S07.md` |

## Static review completed after initial E00 implementation

A second code-level review was performed against Inventory PR #3 rather than assuming that file presence implied a safe gate.

### Release gate fail-closed hardening

The initial `tools/verify_release.py` filtered required test paths by existence. That meant a damaged/incomplete checkout could theoretically execute fewer required checks and still report success.

Inventory commit `b671f674aa69ac3adb55429fe54f456ab9ea137b` corrects this:

- required Python regression files are no longer silently filtered;
- required E00/core Python files are no longer silently omitted from `py_compile`;
- Bash syntax checks are added for deployment/start scripts when Bash is available;
- existing `tools/test_client_routing.js` is actually executed when Node is available, in addition to JS syntax checks;
- `--require-node` and `--require-bash` allow stricter operator/release environments.

### Backup snapshot collision hardening

The first independent backup-job implementation named snapshots with second-level timestamps. A manual retry or duplicate trigger in the same second could fail safely with `FileExistsError`, but this is unnecessary operational noise.

Inventory commit `61d486d9c1323d65694e7d7c0f6f3078eaf60045` changes names to UTC plus microseconds while preserving the rule that an already-published backup is never overwritten.

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

Migration tests use embedded deterministic fixtures based on actual repository history:

- `3e9eff41196847ad96badffe1705fc6671e68fb0` — early Inventory Lite baseline;
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

For a Linux release environment where shell validation is mandatory:

```bash
python3 tools/verify_release.py --require-bash
```

Node can likewise be made mandatory with `--require-node` when client-routing validation is part of that release profile.

No required correctness logic is unique to GitHub Actions.

### Backup correctness

The old Linux update flow copied the live WAL-mode database file with `cp -a`. E00 replaces this with SQLite Online Backup API snapshots, then restores the snapshot into a temporary database and runs schema/integrity/smoke checks before deployment proceeds.

### Recovery manifest and off-host copy

Recovery manifests record database/artifact/config paths, sizes and SHA-256 checksums. Verified off-host copy can target a mounted NAS/NFS/SMB/sshfs path and re-validates destination files before atomically publishing the bundle.

### Backup scheduling

`tools/run_backup_job.py` is directly executable by an operator, cron or systemd timer. `setup_server.sh` installs a backup service/timer path, but does not enable an operator-unapproved cadence unless `INVENTORY_ENABLE_BACKUP_TIMER=1` is explicitly set.

## Required E00 verification gate

From a real checkout of `impl/e00-release-safety` run:

```bash
python3 tools/verify_release.py
```

The minimum gate must prove:

1. required Python source/test files are present and compile;
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
13. Bash deployment-script syntax when Bash is available/required;
14. JS syntax and client-routing regression when Node is available/required.

Any failure keeps E00 open. Do not proceed to high-risk stock/reservation schema solely because the files exist.

## E01 preparation boundary

E01 implementation remains blocked by E00 completion. Design preparation may continue, but no E01 production code should be merged and no E02 stock schema should start until the E00 local gate passes and PR #3 is reviewed.

After local verification succeeds and PR #3 is reviewed/merged:

```text
E00 COMPLETE
 -> E01 Action Policy + Idempotency + Durable Jobs/Outbox
 -> E11-S01/S02 pricing margin terminology/formula safety
 -> E02 Stock Position + Reservation Kernel
```
