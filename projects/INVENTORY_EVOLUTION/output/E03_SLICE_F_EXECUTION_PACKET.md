# E03 Slice F Execution Packet — Cycle Count + Simple Warehouse Policies

## Status

`READY_AFTER_E03_A_E_AND_E01_JOBS`

## Entry gate

Requires stable locations, location-aware count workflow and E01 Durable Jobs/server-local scheduling.

Branch:

```text
impl/e03-warehouse-policy
```

Migration:

```text
NEXT_CONTIGUOUS
= location_count_policies + material_preferred_locations + indexes
```

Location execution flags/pick sequence may already exist from E03-A; do not duplicate columns/tables.

## Purpose

Add a small deterministic warehouse policy layer for:

- recurring cycle count scheduling;
- preferred putaway locations;
- preferred pick locations / ordering;
- simple execution flags.

This is not a generic WMS rules engine and not AI slotting.

## Cycle count policy

```text
location_count_policies
  id
  location_id
  interval_days
  priority
  enabled
  last_completed_at
  next_due_at
  created_by
  updated_at
  remark
```

Scheduled evaluation runs through E01 Durable Jobs/systemd-owned worker.

Due evaluation creates or queues exactly one count task for an applicable due cycle.

A successful reviewed count advances `last_completed_at/next_due_at`.

A failed/rejected/abandoned session must not pretend the location was successfully counted.

## Preferred location policy

```text
material_preferred_locations
  id
  material_id
  warehouse_id
  location_id
  usage_type: putaway | pick | both
  priority
  enabled
  created_at
  updated_at
```

Rules:

- location must belong to same warehouse;
- disabled/archived/non-applicable location rejected;
- preference suggests future execution only;
- changing preference never moves existing stock;
- preference cannot override E02 stock eligibility/reservation;
- no FIFO/FEFO claim without E07 lot/expiry truth.

## Putaway suggestion P0

Deterministic order:

1. explicit valid preferred putaway location;
2. valid location already holding same material when consolidation policy allows;
3. enabled STORAGE location with putaway enabled;
4. deterministic `location_code` fallback.

No automatic movement occurs from suggestion.

## Pick suggestion P0

Deterministic order:

1. E02 eligible/reserved stock only;
2. valid preferred pick location;
3. lower `pick_sequence`;
4. fewer split locations where possible;
5. stable location-code tie-break.

Suggestion always returns reasoning fields so operator/reviewer can see why a bin was selected.

## Scheduler / dedupe

Cycle evaluation idempotency key concept:

```text
cycle-count:<location_id>:<due_date_or_policy_generation>
```

Repeated worker runs must not create duplicate active count tasks for the same policy period.

No required scheduler depends on GitHub Actions.

## Tests

1. due policy creates one count task;
2. repeated scheduler run does not duplicate it;
3. successful reviewed count advances next due;
4. rejected/failed count does not record false completion;
5. disabled policy produces no task;
6. cross-warehouse preference rejected;
7. archived/disabled location cannot be preferred for execution;
8. putaway suggestion deterministic;
9. pick suggestion deterministic;
10. preference change moves no stock and rewrites no historical task;
11. worker restart/retry preserves idempotency;
12. no GitHub Actions dependency;
13. full Release Gate passes.

## Rollback

Disable policies and scheduled job generation. Existing task/count/history remains. No stock rollback required because policy only suggests/schedules and ordinary E03/E02 commands perform execution.

## Stop conditions

Stop if:

- policy starts directly mutating stock;
- scheduler creates duplicate count tasks;
- policy needs arbitrary SQL/Python expressions;
- pick/putaway suggestions bypass location enabled flags or E02 eligibility.

## Exit / unlock

Warehouse gets predictable recurring counts and simple deterministic putaway/pick suggestions without introducing opaque optimization or a second execution authority.