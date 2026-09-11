# TASK_INV_IMPL_E00_S06 — Full Backup Manifest + Checksums

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation: `ZXYHtech/inventory#3`, branch `impl/e00-release-safety`, reviewed head `7a8e0adcc0bf4f8fddba4688802ef2486f18f56c`.

## Implemented evidence

Files:

- `inventory_app/backup_manifest.py`
- `tools/build_backup_manifest.py`
- `tools/run_backup_job.py`
- `tools/test_backup_manifest.py`
- `tools/test_backup_job.py`
- `deploy/linux/setup_server.sh`
- `deploy/linux/update_server.sh`

Manifest records:

- manifest schema/version;
- creation time;
- deployed application release identity (`source_ref`) when known;
- database schema version;
- entry count / total size;
- entry role, source path and safe archive path;
- file size;
- SHA-256;
- sensitive-data flag.

Database snapshot is always represented. Artifacts/config are recursively enumerated and hashed. Duplicate/unsafe archive paths are rejected.

## Release provenance hardening

Deployment persists `.inventory-release-ref`; scheduled backup reads it when explicit/environment release identity is absent.

Pre-upgrade backup is explicitly bound to the **currently deployed** release, not the new clone HEAD.

## Recovery configuration hardening

Scheduled backup supports strict declared roots:

```text
INVENTORY_BACKUP_ARTIFACT_PATHS
INVENTORY_BACKUP_CONFIG_PATHS
```

A declared path going missing fails the job instead of silently producing an incomplete recovery package.

Installed Linux backup service declares the baseline recovery-config set:

- `/etc/inventory-lite/backup.env`;
- Web service unit;
- OCR service unit;
- backup service unit;
- backup timer;
- Nginx site config.

Pre-upgrade off-host bundle captures corresponding current-deployment config files that actually exist, preserving compatibility with older installs.

Config archive roots use deterministic ordinals so equal basenames from different directories cannot collide.

## Acceptance mapping

- DB identity/version/checksum: implemented;
- deployed release provenance: implemented;
- artifact/config inventory: implemented;
- strict declared config presence: implemented;
- cryptographic checksums: implemented;
- unsafe/duplicate archive-path rejection: implemented;
- source tamper detection: implemented;
- destination copy checksum verification: implemented;
- scheduled-backup E2E test proves declared config is present in Manifest and off-host bundle: implemented.

## Boundary

A local Manifest references local artifact/config sources. The verified off-host copy freezes those files into the second failure-domain bundle. Configuration may contain sensitive data and must inherit appropriate destination permissions/storage controls.

## Remaining gate

Run from a real checkout:

```bash
python3 tools/verify_release.py
```

S06 is not complete until manifest/backup-job/deployment-safety tests pass in that authoritative gate.
