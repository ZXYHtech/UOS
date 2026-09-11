# Inventory Lite Production Change Safety Policy

## Status

`MANDATORY_FOR_PRODUCTION_CHANGE`

This policy applies before any production change that can alter deployed code, database schema, authoritative business state or recovery configuration.

It is stricter than ordinary source-control rollback because the real server can contain runtime configuration or local changes not represented by Git.

## 1. Non-negotiable rule

No production schema/code cutover may begin until all required pre-change evidence has been captured and verified.

Required evidence:

```text
A. frozen pre-audit source reference
B. exact currently deployed server-code snapshot
C. consistent production database snapshot
D. isolated database restore verification
E. recovery manifest + SHA-256
F. off-host/off-disk verified Recovery Bundle when configured/required
G. exact current and target release identities
```

If any mandatory step fails, the deployment stops before service quiesce/schema mutation.

## 2. Layer A — pre-audit repository version

The code state that existed before E00 implementation is frozen at:

```text
repo: ZXYHtech/inventory
branch: backup/pre-e00-audit-20260911
commit: 78d5cda2527cf24836cd5b82a41f02ca8efdd02c
```

Purpose:

- preserve the audited historical source baseline;
- provide an immutable comparison point while implementation branches evolve;
- prevent later PR changes from erasing the original system state.

This branch does **not** replace a server-side snapshot because a server may contain local/manual deployment changes.

## 3. Layer B — exact deployed-server code snapshot

Immediately before database backup/cutover, `update_server.sh` invokes:

```bash
python3 tools/create_prechange_snapshot.py \
  "$APP_DIR" \
  --output "$BACKUP_DIR/deployed-code-<timestamp>.tar.gz" \
  --metadata "$BACKUP_DIR/deployed-code-<timestamp>.tar.gz.json" \
  --release-ref "$CURRENT_RELEASE_REF"
```

Snapshot contract:

- captures the actual server deployment tree, not just a Git ref;
- excludes runtime `data/`, `.git`, `__pycache__`, `.pyc`;
- records file list, archive size, SHA-256 and current release identity;
- reopens the archive and verifies member list before publishing metadata;
- never overwrites a prior snapshot;
- always excludes its own archive/metadata even if a custom backup directory lives inside the application tree.

## 4. Layer C — production SQLite snapshot

The live database must be copied using SQLite Online Backup API, not `cp` of a WAL-mode database.

Required command path:

```bash
python3 tools/create_safe_backup.py \
  "$APP_DIR/data/inventory.sqlite3" \
  --output "$BACKUP_DIR/inventory-<timestamp>.sqlite3"
```

The source production DB is not modified by the backup operation.

### Missing production DB is a hard stop

`update_server.sh` is an upgrade path, not a first-deployment path.

If this file is absent:

```text
$APP_DIR/data/inventory.sqlite3
```

the script must stop before package/code/schema cutover. It must **not** create a fresh empty database and continue.

Interpret a missing production DB as one of:

- wrong application/data path;
- missing storage mount;
- accidental deletion;
- incomplete recovery;
- operator error.

First deployment belongs to `setup_server.sh`. Recovery requires restoring an explicitly verified backup first.

## 5. Layer D — prove the DB backup can restore

A backup file existing is not enough.

Before cutover:

```bash
python3 tools/verify_backup_restore.py "$BACKUP_FILE"
```

Verification must restore into an isolated temporary DB and prove:

- SQLite integrity;
- baseline/schema validity;
- migration-registry validity;
- logical evidence relationships;
- representative inventory/order/purchase/recognition reads.

Failure blocks cutover.

## 6. Layer E — recovery manifest

The pre-change DB backup receives a manifest containing:

- source release identity of the currently deployed version;
- schema version;
- file size and SHA-256;
- deployed-code archive + archive metadata when a full off-host bundle is built;
- business artifacts such as images when configured;
- deployment configuration that exists on the server.

Important provenance rule:

> A backup made **before** an upgrade belongs to the **old/current deployed release**, never to the new temporary Git clone.

## 7. Layer F — second failure domain

When `INVENTORY_OFFHOST_BACKUP_DIR` is configured, the Recovery Bundle must be copied to a pre-existing target that contains:

```text
.inventory-backup-target
```

This marker must be created on the verified mounted NAS/NFS/SMB/sshfs/off-disk filesystem.

The application must never create the off-host root automatically. If the mount disappears, backup must fail rather than silently writing a fake off-host backup on the primary server.

Destination files are hash-verified before the bundle is atomically published.

## 8. Recovery configuration set

The full Recovery Bundle should include the current files that exist for:

```text
/etc/inventory-lite/backup.env
/etc/systemd/system/inventory-lite.service
/etc/systemd/system/inventory-lite-ocr.service
/etc/systemd/system/inventory-lite-backup.service
/etc/systemd/system/inventory-lite-backup.timer
/etc/nginx/sites-available/inventory-lite.conf
$APP_DIR/.inventory-release-ref
```

Scheduled backups also declare their recovery config set explicitly. A configured required path disappearing is a backup failure, not a silent omission.

## 9. Backup-only production preflight

Before choosing the maintenance window, operators can run the real update path in backup/preflight mode:

```bash
INVENTORY_PREFLIGHT_ONLY=1 \
INVENTORY_REPO_BRANCH=<target-branch> \
sudo -E bash deploy/linux/update_server.sh
```

This mode performs:

```text
target repository Release Gate
 -> current deployed-code snapshot
 -> current production DB consistent snapshot
 -> isolated DB restore verification
 -> manifest/checksum generation
 -> off-host Recovery Bundle when configured
 -> PASS/FAIL
```

and then exits **before**:

```text
stopping Web/OCR
rsyncing target code into APP_DIR
running production schema migration
changing .inventory-release-ref
```

Expected success marker:

```text
PREFLIGHT ONLY: PASS
```

This is the preferred way to prove backup/recovery readiness before the actual maintenance cutover.

A successful preflight does not authorize a later cutover if the production DB/code changes materially between preflight and maintenance time; the real update still creates a fresh pre-change snapshot again immediately before cutover.

## 10. Only after backup proof: maintenance cutover

Required ordering:

```text
Release Gate PASS
 -> exact deployed-code snapshot PASS
 -> SQLite snapshot PASS
 -> isolated restore PASS
 -> manifest/checksum PASS
 -> off-host bundle PASS when configured
 -> remember whether backup timer was active
 -> stop backup timer/service
 -> stop OCR worker
 -> stop Web/API writers
 -> sync new code
 -> numbered migration
 -> post-migration integrity
 -> publish new release identity
 -> start services
 -> /api/health PASS
 -> resume previously-active backup timer
```

If failure occurs after writers have been stopped, Web/OCR remain stopped until an operator explicitly repairs or restores. Do not resume a mixed/unknown state automatically.

## 11. Mandatory evidence retained for every production upgrade

Record:

```text
change timestamp
old/current release SHA
new/target release SHA
pre-change code snapshot path
pre-change code snapshot SHA-256
DB snapshot path
DB snapshot SHA-256
DB schema version
restore verification result
recovery manifest path/checksum
off-host bundle path/checksum when applicable
post-cutover health result
operator/change reference
```

When a backup-only preflight is run, retain its evidence separately from the final cutover backup evidence.

## 12. Production database boundary

Current E00 work in GitHub does **not** mean the live server DB has already been backed up or modified.

The live DB snapshot can only be produced on the server (or from an explicitly authorized copy) when production preflight/update is actually run.

Do not claim a production backup exists until the server-side command output and backup files have been observed.

## 13. E00 completion relationship

This production policy complements, but does not replace, the repository-local E00 gate:

```bash
python3 tools/verify_release.py
```

E00 remains incomplete until the implementation checkout passes that gate. Production rollout additionally requires the pre-change backup sequence in this policy.
