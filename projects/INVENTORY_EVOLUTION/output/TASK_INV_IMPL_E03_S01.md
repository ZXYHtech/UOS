# TASK_INV_IMPL_E03_S01 — Stable Warehouse Location Identity

## Status

`DESIGN_READY_BLOCKED_BY_E02_STOCK_IDENTITY`

## Objective

Make `warehouse_locations` a stable operational identity suitable for bin-level stock execution while preserving current zone/shelf/box compatibility and warehouse layout UI.

## Current evidence

Today `warehouse_locations` is identified by:

```text
warehouse_id + zone_name + shelf_code + box_no
```

and `warehouse_layout_items` can visually represent locations. E02 is expected to make location part of canonical stock identity.

## Target

Add/normalize concepts such as:

```text
location_code
location_type
parent_location_id
scan_code
pick_sequence
putaway_enabled
pick_enabled
count_enabled
```

Initial location types:

```text
receiving
storage
dispatch_staging
virtual
```

Do not add quality-state meaning here; quarantine/accepted/rejected belong to E07 stock/quality state rather than being inferred solely from a bin name.

## Migration

Do not assign migration number until E02 merges.

Migration requirements:

- preserve legacy location IDs;
- generate proposed `location_code` deterministically;
- preflight duplicate/conflict report before UNIQUE enforcement;
- never silently merge locations;
- preserve layout links by location ID;
- invalid warehouse/location relationships fail preflight.

## Canonical identity rules

- `location_code` unique within warehouse;
- identity is independent from display title/layout x/y coordinates;
- changing zone/shelf display metadata does not silently change historical movement references;
- disabled location remains queryable historically but cannot receive new execution unless a specific transition allows it;
- a task may only use locations belonging to its warehouse.

## Tests

- deterministic migration from existing zone/shelf/box fixtures;
- duplicate generated code is reported, not overwritten;
- layout changes do not change location identity;
- cross-warehouse location use rejected;
- disabled/non-pickable/non-putaway location policy enforced;
- E02 stock-position identity references canonical location ID.

## Acceptance

Every active physical stock bin has one stable operational location identity suitable for scan, movement, count and pick allocation.
