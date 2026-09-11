# TASK_INV_IMPL_E00_S03 — Migration Integrity + Orphan Checks

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation: `ZXYHtech/inventory#3`, branch `impl/e00-release-safety`, reviewed head `61d486d9c1323d65694e7d7c0f6f3078eaf60045`.

## Implemented evidence

Files:

- `inventory_app/db_integrity.py`
- `tools/check_db_integrity.py`
- `tools/test_db_integrity.py`

Read-only checks include:

- SQLite `PRAGMA integrity_check`;
- declared foreign-key violations via `PRAGMA foreign_key_check`;
- baseline required table/column contract;
- explicit logical orphan queries for historically undeclared relationships such as inventory/material/warehouse, order items, shipments, transfers, BOM, purchasing, platform credentials and aliases.

The gate reports structured issue code, severity, count and message and does not attempt destructive repair.

## Acceptance mapping

- corrupt DB detection: implemented;
- required object/column detection: implemented;
- actionable logical-orphan detection: implemented;
- pre/post migration invocation path: implemented;
- read-only failure behavior: implemented.

## Remaining gate

Run `python3 tools/verify_release.py`; any integrity-test failure keeps E00 open.
