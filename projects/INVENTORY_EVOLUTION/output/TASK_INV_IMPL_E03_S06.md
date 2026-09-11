# TASK_INV_IMPL_E03_S06 — Cycle Count and Simple Warehouse Policies

## Status

`DESIGN_READY_BLOCKED_BY_E03_LOCATION_IDENTITY`

## Objective

Add small, explainable policies for recurring counts, preferred putaway and simple pick ordering without turning Inventory Lite into a generic WMS rules engine.

## Cycle count policy

Suggested additive object:

```text
location_count_policies
  id
  location_id
  interval_days
  enabled
  last_completed_at
  next_due_at
  priority
  remark
```

Initial behavior:

- policy can generate/queue a count task when due;
- task execution uses E03-S05 observation/reconciliation;
- completing a valid count advances `next_due_at`;
- failed/rejected count does not pretend the location was successfully counted.

Scheduler ownership is local/server-side through E01 Durable Jobs or an explicit server task runner. GitHub Actions is not a required scheduler.

## Preferred-bin policy

Suggested simple mapping:

```text
material_preferred_locations
  material_id
  warehouse_id
  location_id
  priority
  enabled
```

Use for deterministic putaway/pick suggestion only.

It does not reserve capacity and does not override E02 stock eligibility.

## Location execution policy

Use explicit flags/fields rather than free-form rules:

```text
putaway_enabled
pick_enabled
count_enabled
pick_sequence
```

Future E07 may add authoritative quality restrictions; E03 must not encode them indirectly through names such as "BAD" or "QC".

## Putaway suggestion order P0

1. explicit valid preferred location;
2. valid location already holding same material when consolidation is desired;
3. enabled storage location;
4. deterministic location-code/order fallback.

No AI required.

## Pick suggestion order P0

1. E02 eligible/reserved stock;
2. explicit preferred location;
3. lower `pick_sequence`;
4. fewer split locations where possible.

No FIFO/FEFO promise is made until authoritative receipt/lot/expiry dimensions exist.

## Safety

- policy suggests; domain command validates;
- disabled location never becomes valid because policy points to it;
- cross-warehouse preferred location rejected;
- policy change affects future suggestions only, not historical executed movements;
- no automatic relocation solely because a policy changed.

## Tests

- due cycle policy creates one count task, not duplicates;
- completion advances next due date;
- failed/rejected count does not advance success evidence incorrectly;
- disabled policy produces no task;
- preferred location suggestion deterministic;
- invalid/cross-warehouse preference rejected;
- pick sequence deterministic;
- changing policy does not mutate stock/history.

## Acceptance

Warehouse operators gain recurring count scheduling and predictable putaway/pick suggestions without introducing opaque optimization logic or another workflow engine.
