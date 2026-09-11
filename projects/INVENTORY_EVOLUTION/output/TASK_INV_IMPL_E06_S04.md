# TASK_INV_IMPL_E06_S04 — Overissue, Return and Scrap

## Status

`DESIGN_READY_BLOCKED_BY_E06_S03`

## Objective

Represent manufacturing material exceptions as distinct, referenced events rather than hiding them inside generic stock adjustments or silently changing planned BOM requirements.

## 1. Event classes

```text
normal issue
controlled overissue
return
material scrap
```

Each has different business meaning and reporting/cost impact.

## 2. Overissue

Legitimate examples:

- feeder/reel setup quantity;
- process loss;
- hand-assembly loss;
- destructive tuning/testing;
- consumable rounding.

Overissue command must capture:

```text
work_order_id
requirement_id
actual material
excess quantity
reason code/text
authority/policy result
actor/time
operation key
```

It does not rewrite `required_quantity`.

Suggested policy:

- configurable absolute/percentage tolerance by material/category/WO class later;
- above threshold requires elevated permission/approval;
- P0 may require explicit `wo.material.overissue` permission for any excess rather than inventing thresholds prematurely.

## 3. Return

Return references WO-issued WIP and moves unused material back through E02.

Rules:

- partial return allowed;
- returned quantity cannot exceed unresolved issued quantity for the actual material/issue context;
- destination stock position validated;
- return exact-once/idempotent;
- later E07 retains lot/serial identity through same operation;
- return is not negative scrap.

## 4. Material scrap

Material scrap records irreversible/controlled disposition from WO custody.

Capture:

```text
requirement / actual material
quantity
reason
actor/time
reference to issue/WIP
quality/NCR reference later E07
```

Scrap must be visible separately for yield/cost variance.

Do not delete or edit original issue.

## 5. Remaining WIP invariant

For each actual material under a WO:

```text
issued
- returned
- scrapped
- explicitly consumed/closed quantity
= unresolved WIP
```

The implementation must define how normal assembly consumption is closed. P0 may close remaining issued quantity to consumption at output/WO closure under an explicit controlled rule if station-level consumption is not tracked.

It must never disappear merely because WO status changes.

## 6. Reversal

Corrections use compensating events:

- overissue reversal where still physically reversible;
- return reversal;
- scrap reversal only under explicit privileged correction policy and never by deleting the scrap event.

E02 movement reversal constraints apply.

## 7. Tests

- normal issue above requirement rejected;
- authorized overissue succeeds and does not change planned requirement;
- reason required;
- return cannot exceed unresolved issued quantity;
- partial return aggregates correctly;
- scrap is distinct from return/consumption;
- replay cannot duplicate return/scrap/overissue;
- reversal posts compensating event without erasing history;
- WIP equation remains consistent after mixed issue/return/scrap events;
- later MBOM changes have no effect on actual execution history.

## Acceptance

Manufacturing exceptions are explainable as explicit actual events, preserving the difference between what the BOM planned and what production really used, returned or lost.
