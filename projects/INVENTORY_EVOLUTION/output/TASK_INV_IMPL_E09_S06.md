# TASK_INV_IMPL_E09_S06 — Cancellation / Refund / Return Conflict Policy

## Status
`DESIGN_READY_BLOCKED_BY_E01_E02_GATES`

## Objective
Normalize remote cancellation/refund events without treating every case as "delete order" or "put stock back".

## Cancellation by local state

```text
before reservation -> cancel canonical order
reserved -> cancel + release E02 reservation
picking -> stop/reconcile warehouse task and picked stock
shipped -> create after-sales exception; do not reverse shipment blindly
```

## Refund vs return
Keep distinct lifecycles:

```text
financial refund request/approval/payment
```

and

```text
physical return request/in-transit/received/inspection/disposition
```

They may be linked but neither implies the other automatically.

Physical return is later delegated to E10 RMA/return domain. E09 records normalized platform event and link.

## Safety rules
- remote refund does not directly increase stock;
- remote cancellation after shipment never deletes shipment or serial trace;
- reservation release is idempotent;
- picked-but-not-shipped stock must be explicitly reconciled before becoming ATP again;
- ambiguous platform state becomes exception/manual review.

## Tests
Cover cancellation in unreserved/reserved/picking/shipped states, refund-without-return, duplicate cancellation event, and remote return event linked to one internal after-sales case.

## Done
Every remote cancellation/refund produces a state-aware internal action or exception rather than destructive reset semantics.