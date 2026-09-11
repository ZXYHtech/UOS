# TASK_INV_AUDIT_IMPORT_EXPORT_BACKUP_01 — Import, Export, Backup & Recovery Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `ImportService`, `ExcelImportService`, `BackupService`, storage export/archive paths, relevant APIs and local tests. No GitHub Actions dependency is accepted.

## 1. Executive conclusion

Inventory Lite has materially better data-portability and backup handling than a typical ad-hoc small inventory tool. Imports include preview/validation concepts, inventory imports flow through `InventoryService.adjust_inventory`, and SQLite backup uses the SQLite backup API rather than unsafe raw file copying.

The remaining gap is **operational recovery assurance**. A backup file existing is not equivalent to a tested recovery capability. Automatic backup configuration also does not by itself prove that an independent scheduler is running.

## 2. Positive findings

### Import safety

The source contains typed import templates and preview/validation behavior for multiple domains. Inventory confirmation applies differences through the normal inventory service instead of directly overwriting balances, preserving inventory logs.

This is the correct invariant:

```text
external data -> validate/preview -> canonical service -> business ledger
```

not:

```text
spreadsheet -> direct SQL overwrite
```

### SQLite backup correctness

`BackupService.create_backup()` uses `sqlite3.Connection.backup()` into a new database. This is safer for an active WAL database than copying `inventory.sqlite3` alone while writes are in flight.

### Explicit destructive-restore confirmation

`restore_backup()` requires an explicit confirmation token (`RESTORE`). This is a useful UX guard against accidental restore.

### Backup export and audit

Backup operations can be listed/exported and relevant actions are written to operation logs.

## 3. Main operational gaps

### 3.1 Configured automatic backup is not the same as scheduled backup

`backup_auto_enabled` and retention configuration exist, but static review did not identify a canonical independent scheduler that guarantees backups occur at a defined cadence.

Required design under the project constraint:

```text
python3 -m inventory_app.backup_job
```

invoked by one of:

- systemd timer;
- cron;
- long-running application scheduler/worker.

GitHub Actions must not be the scheduler.

### 3.2 Backup scope must be defined

The database is not the entire system state. Recoverability may require:

- SQLite database;
- original uploaded images;
- derived images if not reproducible or if rebuilding is expensive;
- controlled attachments/resources;
- deployment configuration;
- secrets/configuration kept outside the DB;
- app/version metadata needed to interpret the DB schema.

Define backup classes:

- DB backup
- file/blob backup
- configuration backup
- full recovery bundle

### 3.3 Restore needs compatibility checks

Before overwriting a live system, restore should validate:

- SQLite integrity (`PRAGMA integrity_check`);
- expected application metadata/schema version;
- required tables/migrations;
- source backup timestamp/version;
- sufficient disk space;
- destination service state/maintenance mode.

### 3.4 RPO/RTO are not yet operational contracts

The system needs explicit business targets, for example:

- maximum acceptable data loss window (RPO);
- maximum acceptable restoration time (RTO).

Do not invent values in code. Make them operator-configured operational policy.

### 3.5 Retention is not redundancy

Keeping seven or thirty days of files on the same disk does not protect against disk/server loss. At least one backup copy should be placed outside the primary storage failure domain.

This can be an rsync/SFTP/NAS/object-storage job and must run independently of GitHub.

## 4. Import/export architecture recommendation

Create one durable import/export framework instead of domain-specific one-off handlers.

Every import should have:

1. import type and schema version;
2. source file hash;
3. preview result;
4. row-level errors/warnings;
5. actor;
6. confirmed-at timestamp;
7. idempotency/import-batch key;
8. resulting object IDs;
9. rollback/reversal strategy where meaningful.

For large imports, move execution into a durable background job but keep confirmation explicit.

## 5. Spreadsheet/API data-quality controls

Recommended validations:

- duplicate keys within file;
- duplicate keys against current database;
- unit/quantity type checks;
- unknown warehouse/location/material;
- disabled/obsolete material use;
- BOM cycle introduction;
- invalid parent category;
- invalid lifecycle transition;
- price validity overlap;
- supplier/MPN ambiguity once electronics master data exists.

## 6. Backup design without Actions

Recommended server layout:

```text
inventory-backup.service
  -> python3 -m inventory_app.backup_job --mode scheduled

inventory-backup.timer
  -> invokes service on server cadence

inventory-backup-verify.service
  -> restores latest backup into temporary location
  -> runs integrity/schema/smoke checks
  -> records verification result
```

An alternative cron implementation is acceptable for small deployments.

The important invariant is that source-control availability is irrelevant to backup execution.

## 7. Recovery drill

A production backup is not considered verified until it has passed a restore drill.

Local/server verification should:

1. create controlled fixture data;
2. create backup;
3. mutate live test DB;
4. restore backup into a separate temporary DB;
5. run integrity check;
6. verify key row counts/ledger invariants;
7. start application against restored DB;
8. verify login/read/write smoke paths;
9. record duration and result;
10. delete temporary recovery environment.

Never run a destructive drill on the production DB path.

## 8. Security considerations

Backups may contain:

- user identities;
- customer names/phones/addresses;
- session records;
- order information;
- operational history.

Therefore define:

- file ownership/mode;
- encryption-at-rest for off-host copies where appropriate;
- retention/deletion policy;
- access audit;
- secret separation.

API credentials should preferably be separable from ordinary DB exports or protected with a stronger secret strategy.

## 9. Priorities

### P0

1. establish canonical scheduled backup runner independent of GitHub;
2. add restore-to-temporary verification command;
3. document complete backup scope;
4. add DB integrity/schema compatibility checks before restore;
5. ensure at least one off-host copy path for production.

### P1

1. import-batch/idempotency records;
2. standardized preview/error schema;
3. automated recovery drill record;
4. backup health surfaced in operations dashboard;
5. RPO/RTO configuration/documentation.

### P2

1. incremental/object-storage strategy if data volume grows;
2. signed backup manifest/checksums;
3. point-in-time recovery after PostgreSQL adoption if justified.

## 10. Acceptance signals

All required checks must run locally/server-side:

```text
python3 tools/test_import_safety.py
python3 tools/test_backup_restore.py
python3 tools/test_recovery_drill.py
```

Expected assertions include:

- inventory import creates ledger movement rather than silent balance overwrite;
- corrupt backup is rejected;
- incompatible schema is rejected or explicitly migrated;
- latest backup can be restored into an isolated DB;
- required attachments/config state are accounted for;
- scheduled runner has no GitHub dependency.

## 11. Preliminary maturity

- import preview/validation: 3.5/5
- inventory import ledger safety: 4/5
- DB backup implementation: 4/5
- restore guardrails: 3/5
- automatic scheduling proof: 1.5/5
- off-host redundancy: unverified
- recovery-drill maturity: 1/5
- full-system RPO/RTO discipline: 1/5

## 12. Core recommendation

Preserve the existing SQLite backup API and import-through-service pattern. The next value is not another export button; it is turning backup into an independently scheduled, automatically verified **recovery capability**.