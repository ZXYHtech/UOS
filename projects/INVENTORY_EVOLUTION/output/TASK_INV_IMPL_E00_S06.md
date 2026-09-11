# TASK_INV_IMPL_E00_S06 — Full Backup Manifest + Checksums

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation: `ZXYHtech/inventory#3`, branch `impl/e00-release-safety`, reviewed head `61d486d9c1323d65694e7d7c0f6f3078eaf60045`.

## Implemented evidence

Files:

- `inventory_app/backup_manifest.py`
- `tools/build_backup_manifest.py`
- `tools/test_backup_manifest.py`

Manifest schema records:

- manifest schema/version;
- creation time;
- source release reference when available;
- database schema version;
- entry count / total size;
- role for each entry;
- source path and safe archive path;
- file size;
- SHA-256;
- sensitive-data flag.

Database snapshot is always represented. Additional artifacts/config can be enumerated recursively and hashed. Duplicate/unsafe archive paths are rejected.

Manifest source verification checks existence, size and SHA-256 before an off-host bundle is copied.

## Acceptance mapping

- DB identity/version/checksum: implemented;
- artifact/config inventory: implemented;
- cryptographic checksums: implemented;
- unsafe archive path rejection: implemented;
- tamper-detection tests: implemented.

## Boundary

The manifest describes recovery state; local artifact files remain at their source paths unless an off-host bundle copy is requested. The off-host copy path freezes and verifies the manifest-described files at the destination.

## Remaining gate

Run `python3 tools/verify_release.py` from a real checkout and require the manifest/copy tests to pass.
