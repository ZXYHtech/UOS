# Inventory Lite Production Change Safety Policy

## Status

`MANDATORY_FOR_PRODUCTION_CHANGE`

This policy applies before any production change that can alter deployed code, runtime dependencies, database schema, authoritative business state or recovery configuration.

## 1. Non-negotiable rule

No production cutover may begin until all required pre-change evidence has been captured and verified.

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

The rule is stricter than “backup before schema migration”:

> No `apt`, `pip`, code sync, service cutover or schema mutation is allowed before the old code + DB recovery evidence exists.

For a real cutover, running Web/OCR/background writers are also stopped **before** `apt`/`pip` changes, so the old production application never runs against a partially updated runtime environment.

## 2. Frozen pre-audit repository version

The code state that existed before E00 implementation is frozen at:

```text
repo: ZXYHtech/inventory
branch: backup/pre-e00-audit-20260911
commit: 78d5cda2527cf24836cd5b82a41f02ca8efdd02c
```

This preserves the audited historical source baseline but does not replace a server-side snapshot because a production server may contain manual/local changes not represented by Git.

## 3. Exact deployed-server code snapshot

Immediately before database backup/cutover, `update_server.sh` creates:

```text
deployed-code-<timestamp>.tar.gz
deployed-code-<timestamp>.tar.gz.json
```

using `tools/create_prechange_snapshot.py`.

Contract:

- capture the actual deployed application tree;
- exclude runtime `data/`, `.git`, `__pycache__`, `.pyc`;
- record file list, size, SHA-256 and current release identity;
- reopen and verify archive members before publishing metadata;
- never overwrite a prior snapshot;
- exclude its own output even if a custom backup directory lives inside the application tree.

## 4. Production SQLite snapshot

The live database must be copied with SQLite Online Backup API, not `cp` of a WAL-mode database:

```bash
python3 tools/create_safe_backup.py \
  "$APP_DIR/data/inventory.sqlite3" \
  --output "$BACKUP_DIR/inventory-<timestamp>.sqlite3"
```

### Missing DB is a hard stop

`update_server.sh` is an upgrade path, not a first-deployment path. If:

```text
$APP_DIR/data/inventory.sqlite3
```

is absent, the update stops before clone/package/code/schema cutover. It must never silently create a fresh empty database.

Possible causes include wrong path, lost mount, accidental deletion or incomplete recovery. First deployment belongs to `setup_server.sh`; recovery requires an explicitly verified backup.

## 5. Prove the DB backup can restore

Before cutover:

```bash
python3 tools/verify_backup_restore.py "$BACKUP_FILE"
```

The verifier restores into an isolated temporary DB and checks SQLite integrity, schema/baseline, migration registry, logical evidence relationships and representative business reads.

A backup file merely existing is not sufficient evidence.

## 6. Recovery manifest and release provenance

The manifest records:

- old/current deployed release identity;
- schema version;
- file size and SHA-256;
- deployed-code archive + metadata when building a full Recovery Bundle;
- business artifacts such as images when configured;
- deployment configuration that actually exists on the server.

A backup taken **before** an upgrade belongs to the **old/current release**, never the new temporary clone HEAD.

## 7. Second failure domain

When `INVENTORY_OFFHOST_BACKUP_DIR` is configured, Recovery Bundle copy requires a pre-existing destination containing:

```text
.inventory-backup-target
```

The marker must live on the verified mounted NAS/NFS/SMB/sshfs/off-disk filesystem. The application never auto-creates the target root. If the mount disappears, backup fails instead of silently writing a fake “off-host” backup on the primary server.

Copied files are checksum-verified before atomic publication.

## 8. Recovery configuration set

The full bundle should capture existing relevant configuration, including:

```text
/etc/inventory-lite/backup.env
/etc/systemd/system/inventory-lite.service
/etc/systemd/system/inventory-lite-ocr.service
/etc/systemd/system/inventory-lite-backup.service
/etc/systemd/system/inventory-lite-backup.timer
/etc/nginx/sites-available/inventory-lite.conf
$APP_DIR/.inventory-release-ref
```

Scheduled backups declare recovery-config paths explicitly. A declared required config disappearing is a backup failure, not a silent omission.

## 9. Bootstrap tools before backup

The production update path requires existing:

```text
git
python3
```

These are bootstrap prerequisites used to fetch and execute the backup/recovery tooling. If either is absent, the script exits.

It deliberately does **not** install them before pre-change evidence is captured, because doing so would violate the “backup before server mutation” rule.

Before target-branch backup tools are allowed to touch production data, the script runs a narrow `py_compile` check over the backup/recovery code using the existing Python runtime.

## 10. Backup-only production preflight

Operators can exercise the real backup path without changing the running system:

```bash
INVENTORY_PREFLIGHT_ONLY=1 \
INVENTORY_REPO_BRANCH=<target-branch> \
sudo -E bash deploy/linux/update_server.sh
```

The mode performs:

```text
clone target to temporary directory
 -> narrow backup-tool compile gate
 -> exact current deployed-code snapshot
 -> current production DB consistent snapshot
 -> isolated restore verification
 -> manifest/checksum generation
 -> off-host Recovery Bundle when configured
 -> run target Release Gate using currently installed dependencies
 -> PASS/FAIL
```

It exits before:

```text
apt/pip dependency changes
stopping Web/OCR/background writers
rsyncing target code into APP_DIR
running production schema migration
changing .inventory-release-ref
```

Expected success marker:

```text
PREFLIGHT ONLY: PASS
```

If the target Release Gate cannot run with currently installed dependencies, the pre-change snapshots still exist, but preflight returns failure. Operators may then plan the real maintenance window; the preflight path itself must not mutate packages to make the test pass.

A successful preflight does not replace the fresh snapshots generated immediately before the real cutover.

## 11. Real maintenance cutover ordering

Required order:

```text
confirm existing production DB
 -> confirm existing git/python3 bootstrap tools
 -> clone target to /tmp only
 -> narrow compile gate for backup/recovery tooling
 -> exact deployed-code snapshot PASS
 -> SQLite snapshot PASS
 -> isolated restore PASS
 -> manifest/checksum PASS
 -> off-host bundle PASS when configured
 -> remember backup-timer state
 -> stop backup timer/service
 -> stop OCR worker
 -> stop Web/API writers
 -> mark deployment quiesced
 -> apt/pip target runtime dependencies
 -> full repository Release Gate PASS
 -> rsync target code
 -> numbered migration + postflight integrity
 -> publish new release identity
 -> restart services
 -> /api/health PASS
 -> resume previously-active backup timer
```

This ordering gives two protections at once:

1. package/code/schema changes never begin before recovery evidence exists;
2. the old application does not keep processing business writes while its runtime dependencies are being changed.

If any failure occurs after writer quiescence, Web/OCR remain stopped until an operator explicitly repairs or restores. Do not auto-resume an unknown mixed state.

## 12. Mandatory evidence for each production upgrade

Retain:

```text
change timestamp
old/current release SHA
new/target release SHA
pre-change code snapshot path + SHA-256
DB snapshot path + SHA-256
DB schema version
restore verification result
recovery manifest path/checksum
off-host bundle path/checksum when applicable
full Release Gate result
post-cutover health result
operator/change reference
```

Preflight evidence and final cutover evidence are separate records.

## 13. Production database boundary

Current E00 work in GitHub does **not** mean the live server DB has already been backed up or modified.

A real production backup exists only after the production host (or an explicitly authorized production copy) has produced the files and successful verification output.

Do not claim otherwise.

## 14. E00 completion relationship

This policy complements, but does not replace, the repository-local E00 gate:

```bash
python3 tools/verify_release.py
```

E00 remains incomplete until the implementation checkout passes that gate. Production rollout additionally requires this server-side pre-change protection chain.
