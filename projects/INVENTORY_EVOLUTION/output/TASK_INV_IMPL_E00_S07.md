# TASK_INV_IMPL_E00_S07 — Off-host Backup Copy + Health + Scheduler Path

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation: `ZXYHtech/inventory#3`, branch `impl/e00-release-safety`, reviewed head `61d486d9c1323d65694e7d7c0f6f3078eaf60045`.

## Implemented evidence

Files:

- `inventory_app/backup_manifest.py`
- `inventory_app/backup_runtime.py`
- `tools/copy_verified_backup.py`
- `tools/run_backup_job.py`
- `tools/test_backup_job.py`
- `deploy/linux/setup_server.sh`
- `deploy/linux/update_server.sh`

Operational flow:

```text
consistent DB snapshot
 -> isolated recovery verification
 -> recovery manifest / checksums
 -> optional mounted off-host/off-disk bundle copy
 -> destination checksum verification
 -> atomic publish of bundle
 -> backup-health JSON
 -> prune old local verified snapshots only after success
```

Scheduler ownership is local/server-side. `setup_server.sh` installs a systemd oneshot service and timer, but intentionally does not enable an operator-unapproved cadence unless `INVENTORY_ENABLE_BACKUP_TIMER=1` is explicit.

Supported off-host target is a mounted path (NAS/NFS/SMB/sshfs etc.); the application does not embed remote credentials or shell transports.

## Static review hardening

Follow-up review identified a harmless but avoidable filename collision if two backup jobs start in the same second. Inventory commit `61d486d9c1323d65694e7d7c0f6f3078eaf60045` changes snapshot names to UTC + microseconds while retaining the rule that an existing backup is never overwritten.

## Acceptance mapping

- direct operator/systemd/cron execution: implemented;
- off-host copy hook: implemented;
- destination verification: implemented;
- health success/failure record: implemented;
- retention only after successful backup pipeline: implemented;
- no GitHub scheduler dependency: implemented;
- operator-controlled schedule: implemented.

## Remaining operator decisions / gate

Before production enablement, define RPO/RTO, retention and the actual off-host destination/failure domain. Then run:

```bash
python3 tools/verify_release.py
python3 tools/run_backup_job.py --database /path/to/inventory.sqlite3 --offhost-dir /mounted/backup/path
```

E00-S07 is not complete until the deterministic local test passes; production off-host destination policy remains an operator configuration decision rather than a guessed default.
