# TASK_INV_IMPL_E06_S05 — Partial Completion and Finished Output Receipt

## Status

`DESIGN_READY_BLOCKED_BY_E06_S03_E02`

## Objective

Allow one work order to create finished output through multiple exact-once receipts while preserving the frozen product/revision/MBOM identity and leaving a clean seam for E07 quality/test release.

## Output event

Suggested object or durable evidence projection:

```text
work_order_output_receipts
  id
  work_order_id
  receipt_no
  product_material_id
  product_revision_id
  quantity
  destination_warehouse_id
  destination_location_id
  status
  movement_operation_id
  created_by/at
  reversed_by/at
  reversal_operation_id
```

Lot/serial identities are added by E07 and are not fabricated now.

## Completion command

```text
complete_output(
  work_order_id,
  quantity,
  destination,
  operation_key
)
```

Validation:

- WO is active and allows completion;
- output product/revision comes from frozen WO, not client override;
- quantity positive;
- cumulative accepted output does not exceed planned/policy quantity unless authorized exception exists;
- destination valid;
- required material/WIP policy satisfied;
- E01 idempotency key valid.

Transaction:

```text
validate
 -> post E02 output receipt movement
 -> create immutable WO output receipt evidence
 -> update completed quantity
 -> update WO state to partially_completed/completed as appropriate
 -> audit/correlation receipt
COMMIT atomically
```

## Partial completion

Example:

```text
planned 20
receipt 8  -> completed 8, status partially_completed
receipt 7  -> completed 15
receipt 5  -> completed 20, eligible for completed/closure checks
```

A WO may remain active after a partial receipt.

## Completion vs closure

`completed_quantity == planned_quantity` is necessary but may not be sufficient for final closure.

Before closure validate:

- no unexplained WIP;
- no unresolved cancellation/disposition;
- required quality/test gate when E07 policy exists;
- all mandatory execution evidence complete.

Keep `production output complete` and `administratively closed` distinguishable if implementation needs it.

## Quality seam

Before E07, do not invent test PASS/FAIL.

Design output receipt so E07 can later attach:

```text
finished lot/serial
quality state
RF/electrical test runs
release decision
```

When quality policy becomes authoritative, finished output can enter pending-release/non-saleable state until E07 release.

## Output reversal

If a completion was posted incorrectly, use an explicit reversal linked to original receipt/movement.

Do not delete output receipt.

Reversal cannot exceed unreversed output and must update WO completed quantity consistently.

## Tests

- partial receipts aggregate correctly;
- receipt exact-once under retry;
- product/revision cannot be client-swapped;
- cumulative over-completion blocked without authority;
- movement + receipt + completed quantity atomic;
- reversal is compensating and bounded;
- future product/MBOM revision does not alter historical output identity;
- reaching planned qty does not bypass unresolved WIP/quality closure checks.

## Acceptance

Production can receive actual finished quantities incrementally against a frozen WO configuration, with exact stock/audit evidence and a forward-compatible quality/serial seam.
