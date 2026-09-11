# TASK_INV_IMPL_E06_S03 — Kitting, Pick and Issue to WO-owned WIP

## Status

`DESIGN_READY_BLOCKED_BY_E06_S02_E03`

## Objective

Turn reserved manufacturing demand into controlled warehouse execution and an auditable material issue into work-order-owned WIP without creating a second stock model.

## Boundary

```text
E06 requirement/reservation = manufacturing demand
E03 pick allocation/scan    = exact warehouse execution
E02 movement ledger         = stock truth
```

Kitting is a view/task grouping only.

## Kit view

For each requirement show:

```text
required quantity
reserved quantity
shortage
suggested/allocated source bin(s)
picked quantity
issued quantity
returned quantity
scrapped quantity
approved substitute status
```

Do not persist a second “kit stock balance”.

## Pick

E03 owns exact-bin allocation and scan evidence.

A WO requirement can be partially picked from one or more bins according to E03 policy.

Picking alone may remain non-stock-changing if it only confirms/allocates physical stock.

## Issue

Issue is a consequential stock transaction.

Conceptual command:

```text
issue_requirement(
  work_order_id,
  requirement_id,
  quantity,
  picked/allocation evidence,
  operation_key
)
```

Transaction:

```text
validate WO active state
validate requirement/reservation/pick
validate actual material/substitution authority
 -> E02 stock movement from warehouse position to WO custody/WIP
 -> consume/convert appropriate reservation
 -> increment requirement issued quantity
 -> audit/correlation receipt
COMMIT together
```

## WO-owned WIP

Issued stock must remain attributable to a specific WO.

Do not model this only as a generic warehouse called `WIP`.

The stock/movement representation must retain:

```text
work_order_id
requirement_id
actual material
quantity
source position
issue operation identity
```

## Partial issue

Allow multiple issue events until the authorized requirement/policy quantity is reached.

Every issue has its own idempotency key/receipt.

## Overissue boundary

Normal issue cannot silently exceed requirement/reservation.

Overissue flows through E06-S04 policy with explicit reason/threshold/authority.

## Start-state interaction

Policy may transition WO from `material_reserved` to `in_progress` on first valid issue or through an explicit start command.

Choose one deterministic policy during implementation and test it; do not let UI clients disagree.

## Tests

- reserved/picked material issues once;
- issue decreases source position and creates WO-owned WIP through E02;
- replay returns original receipt;
- partial issues aggregate correctly;
- two concurrent issue requests cannot exceed reservation/requirement;
- wrong WO/warehouse/bin/material evidence rejected;
- normal issue above authorized quantity rejected;
- requirement issued quantity and E02 movement commit atomically;
- pick task failure does not create issue movement;
- issue history remains immutable after later MBOM changes.

## Acceptance

Warehouse staff can prepare and issue exact reserved material to a manufacturing order with scan/bin evidence, while the common E02 ledger remains the only quantity truth and issued stock remains owned by the WO.
