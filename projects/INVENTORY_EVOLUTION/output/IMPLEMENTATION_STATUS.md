# INVENTORY_EVOLUTION — Implementation Status

## Current state

**Phase:** E00 Release Safety / Migration / Recovery Foundation  
**Implementation state:** `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`  
**E01 state:** `DESIGN_READY_BLOCKED_BY_E00_GATE`  
**E02 state:** `BLOCKED`

External implementation:

- repo: `ZXYHtech/inventory`
- audited pre-E00 baseline/main: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`
- frozen pre-audit branch: `backup/pre-e00-audit-20260911`
- implementation branch: `impl/e00-release-safety`
- reviewed implementation head: `322a9d9d65c74e950e37d9f95c17f19510124f7f`
- PR: `ZXYHtech/inventory#3` (Draft)

Do **not** mark E00 complete until the repository-local Release Gate is executed from a real checkout.
Do **not** perform a production code/schema cutover until the pre-change server code + database backup policy has passed on the production host.

## Mandatory production-change protection

See:

`PRODUCTION_CHANGE_SAFETY_POLICY.md`

The required pre-change chain is:

```text
frozen pre-audit Git source
 -> repository Release Gate
 -> snapshot exact currently-deployed server code
 -> consistent SQLite production snapshot
 -> isolated database restore verification
 -> manifest/checksums
 -> off-host Recovery Bundle when configured/required
 -> only then quiesce writers and cut over code/schema
```

The frozen Git branch is not considered a substitute for the server-code snapshot: a real server can contain local configuration or manual changes that are not present in Git.

`update_server.sh` now creates a verified `deployed-code-<timestamp>.tar.gz` plus metadata before the database snapshot or any service stop. The snapshot excludes runtime `data/` but captures the actual deployed application tree and SHA-256/file manifest. It also fences its own output files if a custom backup directory is configured inside the application tree.

The production SQLite backup still uses SQLite Online Backup API and must pass an isolated recovery drill before cutover.

## E00 story coverage

| Story | Code | Runtime validation | Evidence |
|---|---|---|---|
| E00-S01 migration registry/baseline adoption | Implemented | Awaiting real checkout | `TASK_INV_IMPL_E00_S01.md` |
| E00-S02 historical DB fixtures | Implemented | Awaiting real checkout | `TASK_INV_IMPL_E00_S02.md` |
| E00-S03 integrity/orphan checks | Implemented + expanded | Awaiting real checkout | `TASK_INV_IMPL_E00_S03.md` |
| E00-S04 authoritative Release Gate | Implemented + fail-closed | Awaiting real checkout | `TASK_INV_IMPL_E00_S04.md` |
| E00-S05 isolated restore verification | Implemented + transaction-aligned | Awaiting real checkout | `TASK_INV_IMPL_E00_S05.md` |
| E00-S06 recovery manifest/checksums/config | Implemented + expanded | Awaiting real checkout | `TASK_INV_IMPL_E00_S06.md` |
| E00-S07 off-host copy/health/scheduler | Implemented + fail-closed | Awaiting real checkout | `TASK_INV_IMPL_E00_S07.md` |

## Major E00 hardening completed after first implementation

### Release Gate

`tools/verify_release.py` is the authoritative local/server command. Required tests/files are not silently skipped. It now includes:

- Python compile checks;
- migration/integrity/recovery/backup tests;
- deployed-code pre-change snapshot tests;
- deployment-safety regression;
- existing auth/core/recognition/warehouse regressions;
- Bash syntax when available/required;
- JavaScript syntax and existing client-routing regression when Node is available/required.

No required correctness logic is unique to GitHub Actions.

### Migration publication safety

Numbered migrations use explicit SQLite `BEGIN IMMEDIATE` semantics. DDL, migration-registry row and postflight integrity belong to one transaction. Failure rolls back.

Additional contracts:

- migration versions must be contiguous after baseline version 1;
- unknown/tampered migration history is rejected;
- deterministic test injects Migration 2, forces postflight failure and requires both test DDL and registry row to disappear.

### Integrity evidence

Read-only integrity checks extend into operational evidence including:

- inventory account/location validity and cross-warehouse location mismatch;
- inventory logs;
- shipment scan/archive chains;
- transfer receipt events;
- inventory counts;
- project BOM / BOM operations;
- purchase order/item/receipt/landed-cost ancestry;
- pricing revisions/rules;
- attachment derivative and recognition revision/correction chains;
- material metadata/resources.

### Release / upgrade cutover

`update_server.sh` treats code + schema cutover as a maintenance transaction:

```text
new code Release Gate
 -> exact currently deployed code snapshot
 -> consistent pre-upgrade DB backup
 -> isolated recovery verification + manifest/off-host copy
 -> stop backup timer/service + OCR + Web writers
 -> rsync code
 -> numbered migration + integrity postflight
 -> persist new release identity
 -> restart
 -> health check
 -> restore previously-active backup timer
```

If failure occurs after writer quiescence, services remain stopped instead of continuing in an unknown mixed version.

Pre-upgrade backup Manifest records the **currently deployed** release, not the new clone HEAD. When off-host recovery is configured, the bundle also includes the pre-change deployed-code archive and its metadata.

### Fresh/repair deployment safety

`setup_server.sh` may be re-run without allowing `rsync --delete` to own `data/`. The entire runtime `data/` tree is excluded, protecting DB, images, generated artifacts, backup files and health records.

A setup is not published as successful until `/api/health` passes. Release identity and backup-timer enablement occur only after health succeeds.

### Release provenance

Deployment persists `.inventory-release-ref`; scheduled backups retain application release identity even though `.git` is deliberately absent from the deployed directory.

### Disaster-recovery bundle

Off-host destination is fail-closed:

- root must already exist;
- production/scheduled copy requires `.inventory-backup-target` on the verified mounted filesystem;
- missing/unmarked target fails and writes failed health;
- destination hashes are verified before atomic publish.

Backup names use UTC microseconds and existing snapshots are never overwritten.

Scheduled backups support strict declared recovery paths through:

```text
INVENTORY_BACKUP_ARTIFACT_PATHS
INVENTORY_BACKUP_CONFIG_PATHS
```

The installed backup service declares the baseline recovery configuration set:

- `/etc/inventory-lite/backup.env`;
- Web/OCR/Backup systemd units;
- backup timer;
- Nginx site configuration.

A declared config path going missing makes the backup fail instead of silently publishing an incomplete recovery bundle. Pre-upgrade off-host backup captures corresponding configuration that actually exists on the old deployment.

## Required E00 gate

From a real checkout of the implementation branch:

```bash
python3 tools/verify_release.py
```

Linux strict profile:

```bash
python3 tools/verify_release.py --require-bash
```

When Node is an agreed release-host dependency:

```bash
python3 tools/verify_release.py --require-bash --require-node
```

Any failure keeps E00 open.

Detailed handoff:

`E00_LOCAL_VERIFICATION_HANDOFF.md`

## E01 is story-ready

The master E01 design remains:

`TASK_INV_IMPL_E01.md`

Story contracts are independently prepared:

```text
TASK_INV_IMPL_E01_S01.md  Shared API/domain primitives
TASK_INV_IMPL_E01_S02.md  Action Policy registry
TASK_INV_IMPL_E01_S03.md  Pilot high-risk routes
TASK_INV_IMPL_E01_S04.md  Business operation / idempotency
TASK_INV_IMPL_E01_S05.md  Durable jobs
TASK_INV_IMPL_E01_S06.md  Worker CLI/service
TASK_INV_IMPL_E01_S07.md  Retry / dead-letter
TASK_INV_IMPL_E01_S08.md  Transactional outbox
TASK_INV_IMPL_E01_S09.md  Correlation propagation
TASK_INV_IMPL_E01_S10.md  Modular-monolith extraction
```

Proposed additive migration sequence once E00 is complete:

```text
Migration 1 = audited E00 baseline adoption
Migration 2 = business_operations
Migration 3 = jobs + job_attempts
Migration 4 = outbox_events
Migration 5 = operation_logs.correlation_id
```

No E01 production code should be merged before the E00 gate passes and PR #3 is reviewed/merged.

## Next transition

```text
E00 real-checkout Release Gate PASS
 -> review/merge Inventory PR #3
 -> start E01-S01/S02
 -> E01-S03 pilot routes
 -> E01-S04 idempotency
 -> E01-S05/S06/S07 durable worker
 -> E01-S08/S09 outbox + correlation
 -> E01-S10 bounded module extraction
 -> only then advance toward E02 Stock Position / Reservation Kernel
```
