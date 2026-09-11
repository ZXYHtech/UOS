# TASK_INV_IMPL_E00_S02 — Representative Old-Database Migration Fixtures

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation is on `ZXYHtech/inventory:impl/e00-release-safety` in PR #3; reviewed head `61d486d9c1323d65694e7d7c0f6f3078eaf60045`.

## Implemented evidence

Files:

- `tools/legacy_schema_fixtures.py`
- `tools/test_schema_migrations.py`

Fixture profiles are derived from real repository history rather than invented toy schemas, including:

- `3e9eff41196847ad96badffe1705fc6671e68fb0` — early Inventory Lite schema;
- `84d25e9a270eadc869ed01746b46aa1d88d65985` — Stage 5/6 permissions / aliases / BOM era.

The tests carry representative business rows through:

```text
historical schema
 -> existing legacy compatibility bootstrap
 -> current audited baseline
 -> immutable migration-registry adoption
```

Preservation assertions cover representative material identity, remarks, inventory quantities, order state and aliases.

## Acceptance mapping

- multiple prior schema eras: implemented;
- deterministic embedded fixtures: implemented;
- row-preservation assertions: implemented;
- upgrade to migration version 1: implemented in test;
- no production database dependency: implemented.

## Remaining gate

`python3 tools/verify_release.py` must execute these fixtures successfully from a real checkout before story completion.
