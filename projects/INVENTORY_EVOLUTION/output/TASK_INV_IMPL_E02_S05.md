# TASK_INV_IMPL_E02_S05 — Order / Shipment Reservation Integration

## Status

`DESIGN_READY_BLOCKED_BY_E02_S04`

## Objective

Connect confirmed order demand and shipment execution to the new reservation/ATP kernel without rewriting the mature order-ingest/OCR/shipment-task workflows.

## Current flow to preserve

The current system already separates:

```text
order
 -> shipment task
 -> warehouse/stock validation
 -> scan/logistics workflow
 -> shipment completion
 -> stock deduction
```

That separation is valuable and remains.

E02 adds the missing promise layer:

```text
order confirmed
 -> reserve warehouse stock
 -> shipment task consumes reservation
 -> physical issue movement posts
```

## Reservation trigger

Do not reserve on probabilistic OCR recognition output.

Reservation begins only after the business reaches an authoritative confirmed order/demand state.

The exact trigger must preserve current human-confirmation controls for image/OCR orders.

## Reservation identity

Suggested reservation key per authoritative demand line:

```text
order:<order_id>:line:<order_item_id>:material:<material_id>:generation:<n>
```

If fulfilment BOM/accessory expansion creates multiple material requirements, each requirement gets deterministic line identity linked back to the originating order/shipment requirement snapshot.

## Requirement snapshot

Do not recalculate historical shipment demand from a mutable BOM after reservation.

When an order/shipment requirement becomes committed, persist the exact material requirement snapshot used for reservation, including:

```text
source order line
material
required quantity
source/BOM/accessory evidence
calculation/version timestamp
```

Later controlled BOM domains may improve this; E02 only needs enough to prevent current mutable definitions from silently changing an open reservation.

## Warehouse allocation

Reservation may begin at:

1. explicitly selected warehouse; or
2. policy-selected warehouse after ATP evaluation.

Warehouse assignment must be server-derived/validated from authoritative allowed scope, not trusted from arbitrary client payload.

If a shipment task is reassigned:

```text
release/move old warehouse reservation
+ create/move new warehouse reservation
one idempotent business transaction where possible
```

Do not leave hidden reservation behind in the old warehouse.

## Shortage behavior

If total required quantity cannot be reserved:

```text
confirmed demand
 -> partial reservation / backorder state (only if business policy allows)
OR
 -> reservation failure / operator shortage queue
```

Do not silently report fully allocated when ATP is insufficient.

The first implementation may choose full-reservation-only if that is safer than introducing partial fulfilment immediately.

## Shipment completion

Current shipment completion stock deduction becomes:

```text
load shipment task + authoritative reservation(s)
 -> validate state/scope
 -> verify picked/scanned evidence required by current flow
 -> post shipment_issue movement
 -> consume matching reservation quantity
 -> update shipment/order state
 -> audit/result receipt
COMMIT
```

Stock issue and reservation consumption must be atomic.

## Reversal

Shipment reversal uses:

```text
compensating stock movement
+ reservation restoration/reopen only when business state requires it
```

Do not blindly recreate promise stock after every reversal; cancellation/refund/re-ship semantics determine whether reservation should be active again.

The reversal operation must link to the original shipment movement and remain idempotent.

## Existing shipment scan evidence

Keep current scan logs.

E02 may add links from scan/requirement evidence to reservation/material requirement but must not attempt the full bin/lot/serial picking model; E03/E07 own that.

## API/action policy pilots

The existing E01 pilot around `ShipmentService.complete` becomes the natural integration point.

Expected Action Policy shape:

```text
shipment.complete
  permission = shipment.process
  scope = shipment warehouse derived from task
  state = valid completion state
  idempotency = required
  stock effect = consume reservation + post issue movement
```

Do not add a second stock-deduct path beside the new stock domain.

## Order cancellation

Before physical shipment:

```text
cancel authoritative demand
 -> release remaining reservation
```

After physical issue/shipment:

```text
normal cancel is insufficient
 -> return/reversal/RMA business path required
```

Do not use reservation release to undo already-posted physical stock.

## Platform synchronization

Local reservation/shipment transaction must not call marketplace APIs inline.

After local commit, use E01 Outbox for required platform synchronization.

Remote sync failure does not roll back a valid local stock issue; it creates retry/reconciliation evidence.

## Migration of current open orders

At activation:

1. identify current authoritative open/confirmed demand;
2. calculate material requirements deterministically;
3. attempt reservations in a controlled migration/reconciliation run;
4. classify shortages/ambiguities;
5. require operator review for unresolved cases;
6. do not mark reservation mode authoritative until open-demand migration is reconciled.

No fabricated historical reservation timestamp is required; record migration-created reservations honestly.

## Tests

- OCR/unconfirmed order does not reserve stock;
- confirmed order creates expected reservation once;
- duplicate confirm/retry does not duplicate reservation;
- two orders competing for limited ATP cannot both fully reserve;
- shipment reassignment releases/moves reservation correctly;
- completion consumes reservation + posts physical movement exactly once;
- simulated response loss then retry returns original completion receipt;
- completion failure rolls back both stock movement and reservation consumption;
- cancel-before-ship releases reservation;
- reversal posts compensation without deleting original stock movement;
- remote platform sync failure leaves local stock/reservation truth intact;
- migrated open orders reconcile or appear on explicit shortage/review report;
- full Release Gate passes.

## Rollback

Before order reservation is authoritative, disable the pilot and retain evidence.

After activation, rollback code must still honor active reservations; returning to a release that only checks raw `quantity_available` is unsafe.

## Acceptance

S05 is complete when a confirmed order can no longer promise the same free stock to another demand, and shipment completion atomically converts that promise into a posted physical issue exactly once.

## Dependencies

E02-S04 plus E01 Action Policy/Idempotency/Outbox.

## Non-goals

- no multi-package redesign;
- no advanced partial shipment unless explicitly chosen;
- no bin allocation;
- no lot/serial fulfilment;
- no RMA workflow.