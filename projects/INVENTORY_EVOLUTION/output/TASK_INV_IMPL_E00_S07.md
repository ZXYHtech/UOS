# TASK_INV_IMPL_E00_S07 — Off-host Backup Copy + Health + Scheduler Path

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation: `ZXYHtech/inventory#3`, branch `impl/e00-release-safety`, reviewed head `16ae9ebc74782cd62819323c8d162ceddc7a29a5`.

## Implemented evidence

Files:

- `inventory_app/backup_manifest.py`
- `inventory_app/backup_runtime.py`
- `tools/copy_verified_backup.py`
- `tools/run_backup_job.py`
- `tools/test_backup_manifest.py`
- `tools/test_backup_job.py`
- `deploy/linux/setup_server.sh`
- `deploy/linux/update_server.sh`

Operational flow:

```text
consistent DB snapshot
 -> isolated recovery verification
 -> recovery manifest / checksums
 -> optional mounted off-host/off-disk bundle copy
 -> verify destination mount marker
 -> destination checksum verification
 -> atomic publish of bundle
 -> backup-health JSON
 -> prune old local verified snapshots only after success
```

Scheduler ownership is local/server-side. `setup_server.sh` installs a systemd oneshot service and timer, but intentionally does not enable an operator-unapproved cadence unless `INVENTORY_ENABLE_BACKUP_TIMER=1` is explicit.

Supported off-host target is a mounted path (NAS/NFS/SMB/sshfs etc.); the application does not embed remote credentials or shell transports.

## Static review hardening

### Same-second snapshot collision

Follow-up review identified a harmless but avoidable filename collision if two backup jobs start in the same second. Inventory commit `61d486d9c1323d65694e7d7c0f6f3078eaf60045` changes snapshot names to UTC + microseconds while retaining the rule that an existing backup is never overwritten.

### False off-host success when a mount disappears

A more serious review finding was that the first off-host copy implementation would auto-create the destination root. If a configured NAS/NFS/SMB/sshfs mount disappeared, the primary server could create the same local mount-point directory and then report a copy as if it had crossed a failure domain.

This is now fail-closed:

- the off-host root must already exist; code never creates it;
- production/scheduled off-host copy requires `.inventory-backup-target`;
- the marker must be created **on the verified mounted target filesystem**;
- if the mount disappears and therefore the marker disappears, backup fails and records failed health instead of silently writing locally;
- direct copy CLI requires the marker by default; an explicit `--allow-unmarked-destination` escape hatch exists only for controlled local/test use;
- deterministic tests prove missing destination and existing-but-unmarked destination are rejected;
- `setup_server.sh` runs one backup/recovery iteration before enabling the timer, so a configured invalid off-host target blocks timer enablement.

Relevant Inventory commits include `f545c14e3ba5af9fcbb48baf1435dc423792a3ad` through `16ae9ebc74782cd62819323c8d162ceddc7a29a5`.

## Acceptance mapping

- direct operator/systemd/cron execution: implemented;
- off-host copy hook: implemented;
- destination must pre-exist: implemented;
- fail-closed mount marker: implemented;
- destination checksum verification: implemented;
- health success/failure record: implemented;
- retention only after successful backup pipeline: implemented;
- first-run verification before timer enablement: implemented;
- no GitHub scheduler dependency: implemented;
- operator-controlled schedule: implemented.

## Remaining operator decisions / gate

Before production enablement, define RPO/RTO, retention and the actual off-host destination/failure domain. After mounting and verifying the remote filesystem, create its marker as the application user, for example:

```bash
sudo -u inventory touch /mnt/inventory-backup/.inventory-backup-target
```

Then run:

```bash
python3 tools/verify_release.py
python3 tools/run_backup_job.py \
  --database /path/to/inventory.sqlite3 \
  --offhost-dir /mnt/inventory-backup
```

E00-S07 is not complete until the deterministic local release gate passes; production off-host destination policy remains an operator configuration decision rather than a guessed default.
