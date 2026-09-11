# TASK_INV_IMPL_E08_S05 — Planner Recommendation Review & Idempotent Conversion

## Status
`DESIGN_READY_BLOCKED_BY_E07_GATE`

## Objective
Keep MRP advisory. A recommendation becomes an executable PO/WO/transfer only through an explicit reviewed E01 business action.

## Recommendation types

```text
BUY
MAKE
TRANSFER
RESCHEDULE_IN
RESCHEDULE_OUT
CANCEL_OR_REDUCE
REVIEW_SUBSTITUTE
```

Lifecycle:

```text
proposed
 -> reviewed
 -> accepted | rejected | superseded
 -> converted where applicable
```

## Required evidence
Each recommendation stores or references:

- material/site;
- action and quantity;
- shortage/release/due dates;
- demand pegging;
- supply counted/excluded;
- planning policy/source;
- MOQ/order multiple rounding;
- MBOM revision where relevant;
- explanation snapshot.

## Conversion safety
- conversion is idempotent through E01 `business_operations`;
- the same accepted recommendation cannot create two POs/WOs/transfers;
- permission and source/AVL validity are revalidated at conversion time;
- stale recommendation may be blocked/superseded when underlying business state changed materially;
- rejected recommendation creates no executable document;
- MRP/AI never directly approves a substitute.

## Tests
Cover duplicate conversion request, stale source, stale demand, rejection, no-approved-source, and exact link from created document back to originating recommendation/run.

## Done
MRP explains and proposes; a human-controlled, idempotent domain action creates the actual operational document.