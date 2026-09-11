# TASK_INV_IMPL_E03_S05 — Location-aware Count Observation and Reconciliation

## Status

`DESIGN_READY_BLOCKED_BY_E02_BALANCE_KERNEL`

## Objective

Evolve the current warehouse-level count workflow into location-aware physical observation while preserving the strong existing principle that approved variance is posted through the inventory service/movement path rather than directly editing a balance cell.

## Existing strength

Current `InventoryCountService` already:

- creates a count session;
- snapshots expected quantity;
- records counted quantity/difference;
- requires later review;
- posts approved difference through inventory adjustment;
- logs the approval/rejection.

This behavior should be preserved and generalized.

## Target evidence model

Suggested additive objects:

```text
inventory_count_observations
  id
  session_id
  location_id
  material_id
  observed_quantity
  scan_source
  observed_by
  observed_at
  remark

inventory_count_variances
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
  adjustment_operation_id
```

Legacy `inventory_count_items` may remain as compatibility/session summary during transition.

## Principle

```text
physical observation != stock mutation
```

Observation is evidence of what the operator saw.

Only an approved reconciliation posts an E02 movement.

## Count scope

Initial supported scopes:

- one location;
- selected locations;
- whole warehouse by enumerating locations.

Do not infer lot/serial details until E07.

## Blind-count option

Session policy may hide expected quantity from the counting operator.

The server still captures the authoritative expected snapshot for later comparison, but the operator response omits it until submit/review.

## Recount

A recount creates a new observation/revision round rather than rewriting the first observation.

Keep:

- first observation;
- recount reason;
- second observation;
- final reviewer decision.

## Adjustment

Approved variance calls E02 movement kernel with a unique business operation such as:

```text
count:<session_id>:<variance_id>:adjust
```

Replay returns original result and never posts twice.

Rejected/no-change variance posts no movement.

## Tests

- observation write leaves balance unchanged;
- expected quantity comes from authoritative E02 projection;
- blind count hides expected quantity from operator-facing result;
- recount preserves original evidence;
- approved variance posts one adjustment movement;
- rejected variance posts none;
- replay of approval posts exactly once;
- location/material mismatch blocked;
- whole-warehouse count does not collapse distinct locations;
- session cannot be silently edited after approval.

## Acceptance

A warehouse can prove what was physically counted, where it was counted, who observed it, how it differed from system stock and which controlled adjustment reconciled the difference.
