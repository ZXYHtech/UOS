# TASK_INV_IMPL_E12_S02 — Reporting Read Models, Historical Snapshots & Drill-down

## Status
`DESIGN_READY_BLOCKED_BY_E12_S01`

## Objective
Serve reliable reporting without turning transactional tables into one-off dashboard queries or creating a second business truth.

## Architecture
Use simple progression:

```text
transactional DB
 -> governed metric queries/views
 -> cached/materialized read models where justified
 -> daily/monthly snapshots for reproducible history where needed
 -> API/UI
```

A separate analytics warehouse is deferred until measured scale/query load requires it.

## Drill-down invariant
Every important aggregate exposes the source records that compose it, e.g. late PO count -> exact POs; quarantine value -> lots/NCRs; negative contribution -> orders/economic events.

## Historical discipline
Use business-event timestamps, not generic `updated_at`, for trend questions. Snapshots retain metric definition/evidence version and source freshness.

## Rules
- read-model lag/freshness is visible;
- cache/snapshot is projection only and can be rebuilt from authoritative sources where contract allows;
- source corrections appear through normal domain adjustments and subsequent snapshots, not direct dashboard-row edits;
- permission scope propagates into read APIs.

## Tests
- aggregate equals drill-down composition;
- stale cache reports freshness state;
- rebuild produces equivalent values from same source/version;
- historical snapshot remains stable after current-state changes.

## Done
Reporting is performant/reproducible without becoming a parallel mutable ERP database.