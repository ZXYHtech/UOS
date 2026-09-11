# TASK_INV_IMPL_E00_S01 — Schema Version + Numbered Immutable Migration Runner

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation:

- repo: `ZXYHtech/inventory`
- branch: `impl/e00-release-safety`
- PR: `ZXYHtech/inventory#3`
- reviewed implementation head: `61d486d9c1323d65694e7d7c0f6f3078eaf60045`

## Implemented contract

E00 adopts the audited `2026-08-10` runtime schema as migration version `1` instead of replaying historical DDL destructively.

Flow:

```text
legacy SCHEMA_SQL + migrate(conn)
 -> validate known baseline contract
 -> schema_migrations(version=1)
 -> future numbered immutable migrations
```

Evidence:

- `inventory_app/schema_migrations.py`
- `tools/schema_migrate.py`
- baseline source ref `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`

Implemented safeguards:

- baseline validation before stamping;
- migration name/checksum immutability verification;
- unknown future migration version rejection;
- repeat execution is a no-op when state already matches;
- future migration versions must be monotonic.

## Acceptance mapping

- non-destructive current-baseline adoption: implemented;
- `schema_migrations` version record: implemented;
- rerun no-op: test implemented;
- tampered/unknown migration record rejection: test implemented;
- local/server executable path: `python3 tools/schema_migrate.py`.

## Remaining gate

Run from a real checkout:

```bash
python3 tools/verify_release.py
```

Do not mark this story complete until the migration tests pass in that gate.
