# E03 Slice E Execution Packet — Location-aware Count Observation

## Status

`READY_AFTER_E03_A_B_AND_E02_BALANCE_AUTHORITY`

## Entry gate

Requires stable E03 locations + typed scan resolver and E02 authoritative balance/adjustment movement for the target warehouse.

Branch:

```text
impl/e03-count-observation
```

Migration:

```text
NEXT_CONTIGUOUS
= inventory_count_observations + inventory_count_variances + indexes
```

Legacy `inventory_count_sessions/items` remain during migration as compatibility/session summary.

## Purpose

Preserve the current good workflow principle:

```text
physical observation
 -> submit/review
 -> approved difference
 -> stock adjustment
```

but make the observation location-aware and immutable.

Critical invariant:

```text
observation != stock mutation
```

## Existing behavior to preserve

Current count flow already has:

- session header;
- warehouse scope;
- snapshot quantity;
- counted quantity/difference;
- pending approval;
- approval/rejection;
- approved correction via inventory adjustment path;
- operation logging.

Do not replace this with an editable balance grid.

## New evidence objects

### inventory_count_observations

```text
id
session_id
round_no
location_id
material_id
observed_quantity
scan_source
observed_by
observed_at
remark
```

### inventory_count_variances

```text
id
session_id
location_id
material_id
expected_quantity
observed_quantity
difference
status
reviewed_by
reviewed_at
review_reason
adjustment_operation_id NULL
```

Suggested variance states:

```text
pending_review
approved
rejected
recount_required
adjusted
```

## Snapshot semantics

At session/round start, capture E02 authoritative expected quantity by location/material.

If stock changes after snapshot but before approval, policy must be explicit:

- preferred safe v1: reviewer sees snapshot time + subsequent movement warning and must recount/rebase before approval;
- never blindly apply old `observed - stale_snapshot` delta to a changed balance.

This closes a risk already identified in E02-I.

## Blind count

Optional session flag:

```text
blind_count = true
```

Server still stores expected snapshot, but operator-facing count workflow does not reveal it until submission/review.

## Recount

Recount appends a new observation round; it never overwrites the first observation.

```text
round 1 observation
 -> reviewer requests recount
 -> round 2 observation
 -> final variance decision
```

## Approved adjustment

Only approval posts E02 movement:

```text
count:<session_id>:variance:<variance_id>:adjust
```

Transaction:

```text
BEGIN IMMEDIATE
 -> idempotency admission
 -> reload variance/session/current balance
 -> verify no unresolved snapshot drift policy violation
 -> post `count_adjustment` movement via E02
 -> store adjustment operation id
 -> mark variance/session review result
 -> audit/receipt
COMMIT
```

Rejected/no-change rows post no movement.

## Scope

Initial scopes:

```text
single location
selected locations
whole warehouse enumerated as distinct locations
```

Whole-warehouse counting must not collapse two bins into one material total.

Unknown legacy/unassigned stock can be counted only through its explicit E02 unassigned position until physically put away/reconciled.

## Scan flow

```text
COUNT TASK
 -> LOCATION
 -> MATERIAL
 -> OBSERVED QUANTITY
 -> SAVE OBSERVATION
```

Resolver performs identity matching only; save observation remains non-mutating.

## Tests

1. observation changes no balance;
2. expected snapshot comes from E02 balance;
3. blind count hides expected value from operator response;
4. two locations for same material remain distinct;
5. wrong warehouse location rejected;
6. duplicate submission with same key does not append duplicate observation unintentionally;
7. recount preserves round 1 evidence;
8. approval posts one E02 count-adjustment movement;
9. approval replay posts no second movement;
10. rejection posts no movement;
11. stock movement after snapshot is detected before adjustment;
12. stale snapshot cannot silently produce destructive delta;
13. approved session cannot be silently edited;
14. full Release Gate passes.

## Rollback

Before new location counts become mandatory, disable new observation creation and keep all evidence. Existing approved E02 movements remain authoritative and are never deleted.

## Stop conditions

Stop if:

- observation API can directly update stock;
- stale snapshot arithmetic can apply without current-balance/recount review;
- whole-warehouse count loses location identity;
- approval can replay movement twice.

## Exit / unlock

Warehouse counting has durable per-location observation/recount/review evidence and all approved corrections use the E02 movement kernel exactly once. Unlocks E03-F cycle-count policies and E03-G guided count UX.