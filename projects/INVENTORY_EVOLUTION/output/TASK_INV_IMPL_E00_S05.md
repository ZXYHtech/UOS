# TASK_INV_IMPL_E00_S05 — Isolated Backup Restore Verification

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation: `ZXYHtech/inventory#3`, branch `impl/e00-release-safety`, reviewed head `61d486d9c1323d65694e7d7c0f6f3078eaf60045`.

## Implemented evidence

Files:

- `inventory_app/backup_runtime.py`
- `inventory_app/recovery_verifier.py`
- `tools/create_safe_backup.py`
- `tools/verify_backup_restore.py`
- `tools/test_backup_restore_verification.py`

Recovery verification behavior:

```text
live SQLite WAL database
 -> SQLite Online Backup API snapshot
 -> open backup read-only
 -> restore into isolated temporary SQLite DB
 -> integrity / baseline checks
 -> migration-registry verification/adoption
 -> post-checks
 -> representative read/join smoke checks
```

The verification path does not overwrite the source backup or live production database.

## Acceptance mapping

- WAL-safe snapshot creation: implemented;
- isolated restore: implemented;
- integrity/schema checks: implemented;
- representative application read smoke checks: implemented;
- source backup remains unchanged: implemented;
- deterministic repository-local tests: implemented.

## Remaining gate

`python3 tools/verify_release.py` must pass the backup/restore suite from a real checkout before completion.
