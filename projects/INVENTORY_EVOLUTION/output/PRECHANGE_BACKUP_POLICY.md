# INVENTORY_EVOLUTION — Pre-change Backup Policy

## Status

`MANDATORY_PRODUCTION_GATE`

This policy applies before any production Inventory Lite code/schema cutover.
It is not optional documentation.

## Required protection layers

### 1. Audit-start source freeze

The source version that existed before the E00 audit must remain permanently addressable.

Current frozen reference:

- repository: `ZXYHtech/inventory`
- backup branch: `backup/pre-e00-audit-20260911`
- pinned commit: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`

This protects the repository baseline independently of later implementation branches/PRs.

### 2. Actual deployed-server code snapshot

Git history is not sufficient because a server may contain local/manual changes.
Before a production update, create and verify a snapshot of the **actual current deployed application tree**.

Implementation path on `impl/e00-release-safety`:

```bash
python3 tools/create_prechange_snapshot.py \
  /opt/inventory-lite \
  --output /opt/inventory-lite/data/backups/deployed-code-<timestamp>.tar.gz \
  --release-ref <current-release-ref>
```

The snapshot excludes runtime `data/`, `.git` and caches, and writes:

- compressed archive;
- SHA-256;
- file inventory;
- deployed release reference;
- metadata JSON.

Existing snapshots are never overwritten.

### 3. Production SQLite database snapshot

Before any service stop, rsync or schema migration:

```text
live DB
 -> SQLite Online Backup API snapshot
 -> isolated temporary restore
 -> integrity/schema/smoke verification
 -> recovery manifest
```

A copied file without successful isolated restore verification is **not** considered a valid pre-change database backup.

### 4. Recovery bundle when off-host backup is configured

The off-host bundle should contain/checksum:

- pre-change database snapshot;
- actual deployed-code snapshot + metadata;
- images/business artifacts when present;
- release reference;
- backup.env;
- web/OCR/backup systemd units and timer;
- Nginx site configuration;
- other explicitly declared recovery configuration.

Off-host destination must pre-exist and contain `.inventory-backup-target`. Missing mount/marker is a hard failure.

## Production cutover order

```text
Release Gate PASS
 -> freeze actual deployed code
 -> snapshot production DB
 -> restore-verify DB snapshot
 -> build/check recovery manifest
 -> verified off-host copy when configured
 -> only then stop writers/timers
 -> sync code
 -> run numbered migration
 -> postflight integrity
 -> start services
 -> health check
 -> resume backup timer
```

If any step before cutover fails, production remains unchanged.

If a failure occurs after services have been quiesced, fail closed: do not resume an unknown mixed-version state. Use the pre-change code snapshot and verified DB backup for recovery/repair.

## Current boundary

The current ChatGPT/GitHub work is modifying only the implementation branch/Draft PR. It has not directly changed the production server database.

The production database backup cannot be claimed as already executed until a real server run produces the backup/restore evidence. Therefore:

```text
repository baseline backup = PRESENT
production deployed-code/DB backup = REQUIRED BEFORE FIRST REAL SERVER CUTOVER
```
