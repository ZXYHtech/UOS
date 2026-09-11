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
- reviewed implementation head: `0e0870499f7e8b5e68a308231eae954f106bd5aa`
- PR: `ZXYHtech/inventory#3` (Draft)

Do **not** mark E00 complete until the repository-local Release Gate is executed from a real checkout.
Do **not** claim the production DB has already been backed up; production backup evidence can only be created on the production host or an explicitly authorized copy.

## Mandatory production-change protection

See `PRODUCTION_CHANGE_SAFETY_POLICY.md`.

The current contract is:

```text
frozen pre-audit Git source
 -> confirm production DB exists
 -> require existing git/python3 bootstrap tools
 -> clone target into /tmp only
 -> narrow compile gate for backup/recovery tooling
 -> snapshot exact currently deployed server code
 -> consistent SQLite production snapshot
 -> isolated DB restore verification
 -> manifest/checksums
 -> off-host Recovery Bundle when configured/required
 -> stop backup/OCR/Web writers
 -> only now allow apt/pip runtime changes
 -> full repository Release Gate
 -> rsync target code
 -> numbered migration + integrity postflight
 -> restart + health
```

The frozen Git branch does not replace the exact server-code snapshot because a server can contain manual/local changes not represented in Git.

`INVENTORY_PREFLIGHT_ONLY=1` executes the backup/recovery path and target Release Gate using the currently installed dependencies, then exits before apt/pip, service stop, code sync or production schema migration.

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

## Major E00 hardening

### Release Gate

`tools/verify_release.py` is the authoritative local/server command. Required checks are fail-closed and include:

- Python compile checks;
- migration/integrity/recovery/backup tests;
- pre-change deployed-code snapshot tests;
- deployment-safety regression;
- auth/core/recognition/warehouse regressions;
- Bash syntax when available/required;
- JavaScript syntax/client-routing regression when Node is available/required.

No required correctness logic is unique to GitHub Actions.

### Migration publication safety

Numbered migrations use explicit SQLite `BEGIN IMMEDIATE`. DDL, migration-registry row and postflight integrity belong to one transaction; failure rolls back.

Contracts include:

- contiguous post-baseline versions;
- unknown/tampered history rejection;
- deterministic forced-postflight rollback test.

### Integrity evidence

Read-only integrity checks cover core and operational evidence chains including inventory/location/account, shipment scans/archives, transfer receipts, counts, BOM operations, procurement/receipt/cost ancestry, pricing revisions, attachment derivatives, recognition revisions/corrections and material metadata/resources.

### Exact pre-change server snapshot

`tools/create_prechange_snapshot.py` preserves the actual deployed application tree before production cutover, records SHA-256/file list/release identity, excludes runtime data/cache and refuses overwrite. It also excludes its own output files if a custom backup directory resides under the application tree.

### Missing production DB is fail-closed

`update_server.sh` refuses to continue when the existing production DB is missing. It does not reinterpret missing storage as first deployment or create an empty DB.

### Package changes only after backup proof and writer quiesce

The update path no longer runs `apt`/`pip` before recovery evidence exists. For a real cutover it also stops backup/OCR/Web writers before changing runtime dependencies, preventing the old application from serving requests against a partially updated runtime environment.

If failure occurs after writer quiescence, services remain stopped for explicit repair/restore rather than automatically resuming an unknown mixed state.

### Backup-only production preflight

`INVENTORY_PREFLIGHT_ONLY=1` performs fresh code/DB snapshots, isolated restore, manifest/off-host copy and the target Release Gate on current dependencies, then exits without changing dependencies or production runtime state.

### Disaster-recovery bundle

Off-host destination is fail-closed:

- root must already exist;
- `.inventory-backup-target` must live on the verified mounted filesystem;
- missing/unmarked target fails;
- destination hashes are verified before atomic publish.

Scheduled backups declare recovery config/artifact paths. A declared required config disappearing fails the backup instead of publishing an incomplete bundle.

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

Detailed handoff: `E00_LOCAL_VERIFICATION_HANDOFF.md`.

## E01 is story-ready but blocked

Prepared stories:

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

S01/S02/S03 are now grounded to the current implementation instead of a parallel framework. Pilot business-service bindings are:

```text
transfer.receive  -> TransferService.receive
purchase.receive  -> ProcurementService.receive
shipment.complete -> ShipmentService.complete
```

Proposed additive migration sequence once E00 completes:

```text
Migration 1 = audited E00 baseline adoption
Migration 2 = business_operations
Migration 3 = jobs + job_attempts
Migration 4 = outbox_events
Migration 5 = operation_logs.correlation_id
```

No E01 runtime code should be merged before E00 passes and PR #3 is reviewed/merged.

## Next transition

```text
E00 real-checkout Release Gate PASS
 -> review/merge Inventory PR #3
 -> E01 S01/S02 shared context + action policy
 -> S03 pilot actions
 -> S04 idempotency
 -> S05/S06/S07 durable worker
 -> S08/S09 outbox + correlation
 -> S10 bounded module extraction
 -> only then E02 Stock Position / Reservation Kernel
```
