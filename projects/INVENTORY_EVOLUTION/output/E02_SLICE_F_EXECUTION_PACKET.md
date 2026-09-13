# E02 Slice F Execution Packet — Order / Shipment Reservation Authority Pilot

## Status

`READY_AFTER_E02_SLICE_E`

This packet is the first E02 slice that connects Reservation/ATP to a real customer fulfilment lifecycle.

It must preserve the current order-confirmation/OCR/warehouse-task workflow and move stock-promise authority gradually rather than globally.

## Entry gate

All must be true:

```text
E02-D shadow stock adjustment = zero unexplained divergence
E02-E Reservation/ATP concurrency/lifecycle tests PASS
Migration 9 backup/recovery/integrity coverage PASS
current main full Release Gate PASS
```

Suggested branch family:

```text
impl/e02-order-reservation-fixed-warehouse
impl/e02-order-reservation-open-pool
impl/e02-shipment-reservation-consume
```

Do not force all fulfilment variants into one PR if current workflow differences make review unclear.

Migration:

```text
NONE expected
```

Use Migration 7/8/9 entities. If a durable requirement-snapshot table is genuinely necessary, stop and allocate the next contiguous Migration 10 explicitly; do not hide schema creation inside route code.

## 1. Critical correction to the earlier conceptual design

The current stock deduction side effect occurs in:

```text
ShipmentService.ship(...)
```

not only in:

```text
ShipmentService.complete(...)
```

Current `complete()` behavior may call `ship()` first when the task is still `processing`, then mark Shipment/Order completed.

Therefore the authoritative E02 integration point for **physical issue + reservation consumption** must be the stock-effecting `ship()` command/path.

`complete()` must never create a second reservation consumption or second stock issue.

Target invariant:

```text
ShipmentService.ship
  = physical issue movement + reservation consume + shipped state

ShipmentService.complete
  = completion state transition only
    OR composes ship() once if current legacy UX still permits processing->complete
```

If `complete()` composes `ship()`, both remain inside the same E01 business transaction and the idempotent ship effect is exactly once.

## 2. Current workflow to preserve

Existing architecture already separates:

```text
recognized/manual/platform order candidate
 -> human/authoritative order confirmation
 -> shipment task
 -> warehouse assignment/open pool
 -> accept/processing
 -> scan/logistics
 -> ship (physical stock deduction)
 -> complete
```

Keep these concepts.

Do not reserve stock from probabilistic OCR output.

Current confirmed-order route includes:

```text
POST /api/orders/confirm
 -> require product item validation
 -> OrderService.confirm_order(...)
```

Reservation is triggered only after authoritative demand and a usable warehouse promise scope exist.

## 3. Reservation trigger policy by fulfilment shape

A single `order.confirmed` event is not always enough because current workflows may not yet know the final warehouse.

### Case A — warehouse already authoritative

If the confirmed demand / shipment task has a validated warehouse and the current business flow treats that warehouse assignment as committed:

```text
commit shipment requirement snapshot
 -> reserve warehouse ATP
```

Reservation may happen at shipment-task creation/commit point if that is the earliest point where warehouse identity is authoritative.

### Case B — open-pool / no warehouse yet

Do **not** reserve arbitrary warehouse stock at generic order confirmation.

Current open-pool flow allows a warehouse/operator to accept a pending task later.

Target:

```text
confirmed order
 -> open-pool shipment task (no warehouse reservation yet)
 -> ShipmentService.accept / validated warehouse assignment
 -> reserve ATP in accepted warehouse atomically
```

If selected warehouse cannot satisfy ATP:

```text
accept fails / shortage response
```

or enters an explicitly designed shortage workflow.

Do not silently reserve another warehouse behind the operator's action unless a future allocation policy explicitly owns that decision.

### Case C — reassignment before physical ship

Warehouse reassignment must move promise state safely:

```text
BEGIN IMMEDIATE
 -> validate task still reassignable
 -> reserve/increase target warehouse capacity first or use one atomic move command
 -> release old warehouse remaining reservation
 -> update shipment warehouse
 -> append reservation events/audit
COMMIT
```

Never leave the old reservation stranded.

## 4. Demand / requirement snapshot

Do not make an active reservation depend on a mutable recomputation of order/BOM data.

Before reservation becomes authoritative, freeze the exact fulfilment requirement used to reserve.

Minimum evidence per reserved requirement:

```text
order_id
order_item_id / source line
shipment_task_id
material_id
quantity
warehouse_id at reservation time
source rule / bundle expansion evidence if any
created_at
```

Preferred implementation decision:

- if current `order_items` already represent the exact physical material requirement for this initial path, use their immutable/order snapshot identity directly;
- if fulfilment expands bundles/accessories dynamically and current rows are insufficient, introduce a separate requirement snapshot through an explicit Migration 10.

Do not add Migration 10 merely for architectural symmetry. Characterize current flow first.

## 5. Reservation key

For direct order-item requirement:

```text
order:<order_id>:item:<order_item_id>:shipment:<task_id>:generation:<n>
```

Generation changes only when a legitimate reservation scope/requirement generation changes, e.g. controlled reassignment/rebuild.

Do not use timestamp as the only uniqueness source.

The reservation references the exact order/shipment requirement evidence.

## 6. Initial fulfilment policy

Prefer **full-reservation-only** for the first authoritative customer pilot unless current product behavior already has a well-defined partial-backorder contract.

For a requirement set:

```text
all required lines reserve successfully
 -> task can enter committed/processing state

any required line cannot reserve
 -> transaction rolls back reservations for this attempt
 -> explicit shortage result / task remains uncommitted
```

Do not claim a task is fully allocated when only some lines reserved.

Partial reservation/backorder can be a later reviewed extension.

## 7. Action Policy integration

Reuse E01 policy/idempotency.

Representative actions:

```text
shipment.accept
shipment.reassign
shipment.ship
shipment.complete
shipment.cancel_before_ship
shipment.reverse_issue
```

Server-derived scope remains the current shipment warehouse/task authority.

Do not let request payload warehouse IDs expand permission scope.

The reservation layer does not create a parallel permission system.

## 8. `ShipmentService.accept` / warehouse commitment

For open-pool task acceptance:

```text
BEGIN IMMEDIATE
 -> E01 operation admission
 -> load task/order/requirements
 -> current permission + open-pool acceptance checks
 -> validate selected warehouse scope
 -> calculate ATP under Migration 8/9 truth
 -> reserve all required lines
 -> update task warehouse/assignment/status using existing workflow semantics
 -> reservation events + audit/result receipt
COMMIT
```

If ATP is insufficient, none of the new reservations for this acceptance attempt remain.

Existing `inventory_confirmed` or preview UX must not be treated as authority if server ATP changed before commit; ATP is always recalculated in the write transaction.

## 9. Direct fixed-warehouse shipment task creation

If an existing flow creates a committed shipment task with a warehouse immediately, characterize whether reservation belongs at:

```text
shipment task creation
or
first transition into processing/accepted
```

Choose one authoritative point and test it.

Never create reservation twice on both transitions.

The selected point must have:

- confirmed order demand;
- authoritative warehouse;
- stable requirement identity;
- E01 idempotency key.

## 10. Physical ship transaction — authoritative stock conversion

This is the central Slice F invariant.

Target `shipment.ship` transaction:

```text
BEGIN IMMEDIATE
 -> E01 business-operation admission
 -> load shipment/order/current state
 -> permission + warehouse scope
 -> load exact active reservations for shipment requirements
 -> validate scan/logistics/current ship preconditions
 -> validate reservation remaining quantities
 -> post E02 shipment_issue stock movement(s)
 -> update stock_balances
 -> increment reservation quantity_consumed
 -> append reservation consume event(s)
 -> update shipment status/logistics/shipped_at
 -> update order shipped/platform_sync_status as current semantics require
 -> append existing/compatible audit evidence
 -> E01 result receipt
COMMIT
```

Everything commits or rolls back together.

No external platform API call occurs in this transaction. Remote fulfilment uses E01 Outbox after commit.

## 11. Prevent ATP double subtraction

Explicit regression:

Before shipment:

```text
on_hand = 10
active reservation remaining = 4
ATP = 6
```

After shipping/consuming all 4:

```text
on_hand = 6
reservation remaining = 0
ATP = 6
```

Never calculate:

```text
6 - old reservation 4 = 2
```

The physical issue and promise consumption are two sides of the same committed demand conversion.

## 12. `ShipmentService.complete`

After Slice F:

### If task already `shipped`

`complete()` only changes completion state and audit evidence.

It must not:

- deduct inventory;
- consume reservation again;
- create a second movement.

### If legacy UX permits `processing -> complete`

Retain compatibility by composing the authoritative `ship()` command exactly once, then completing.

The combined request needs one stable E01 operation strategy. Two safe implementation patterns:

1. outer `shipment.complete` operation calls an internal non-separately-idempotent ship subcommand in the same transaction; or
2. a composed operation explicitly records both state effects under one receipt.

Do **not** start a nested independent `BEGIN IMMEDIATE` or second business operation using a new connection.

Characterize current API/test expectations before choosing.

## 13. Cancellation before ship

For a task/order not physically shipped:

```text
cancel committed demand
 -> release all remaining reservations
 -> append release/cancel reservation events
 -> update business state
 -> audit/result receipt
COMMIT
```

Reservation release restores ATP exactly once.

Do not post a physical reversal because no physical issue happened.

## 14. Cancellation after ship

Normal pre-ship cancel is no longer valid.

Use explicit reversal/return/RMA semantics.

Do not merely release a consumed reservation; that would increase promise availability without restoring physical stock.

## 15. Shipment issue reversal

For an allowed current shipment reversal path:

```text
original shipment_issue remains immutable
 -> compensating stock movement restores physical balance
 -> decide reservation policy from business state
```

Possible policy:

- reopen reservation if shipment is returned to a pre-ship committed state and demand still exists;
- leave reservation released/closed if order is cancelled;
- route to RMA later after external/customer fulfilment.

This decision must be explicit per reversal action; do not automatically recreate reservations for every compensating stock movement.

## 16. Response-loss / replay

For `shipment.ship`:

```text
commit movement + balance + reservation consume + state + receipt
 -> HTTP response lost
 -> same key retry
 -> original E01 receipt returned
```

Require:

- one physical movement;
- one reservation consume event per intended effect;
- one stock-balance delta;
- no duplicate shipment ledger/audit side effect.

Same key/different logistics/quantity/effect -> conflict.

## 17. Migration of already-open demand — not yet global cutover

Slice F should pilot new reservations for newly committed/accepted demand on selected controlled paths.

Do not globally manufacture reservations for every pre-existing open order in the same PR.

Provide a read-only migration preview:

```text
open order/shipment
 -> computed requirement
 -> current warehouse
 -> ATP
 -> reservation candidate
 -> shortage/ambiguity classification
```

Global open-state reservation migration remains a later cutover gate (Slice J) after pilot evidence is clean.

If production rollout of Slice F requires selected existing tasks to be brought under reservation authority, make the cohort explicit and reconcile it before enabling enforcement.

## 18. Shadow/authority scope flag

Reservation authority may be enabled by a narrow server-side cohort/scope during pilot, e.g.:

```text
newly accepted shipment tasks after cutover timestamp
```

or another deterministic server-owned condition.

Do not expose an arbitrary client flag such as `use_new_reservation=true`.

Every task should have an unambiguous answer to:

```text
legacy promise semantics
or
E02 reservation-authoritative
```

Mixed hidden behavior is forbidden.

## 19. Existing scan/logistics workflow

Keep current shipment scan logs and logistics requirements.

Reservation does not mean “picked”.

Conceptual distinction:

```text
Reservation = promise against warehouse supply
Scan/pick evidence = operator execution
Movement = physical issue
```

E03 later formalizes bin allocations.

Do not add lot/serial picking in Slice F.

## 20. Platform sync boundary

After local ship commit:

```text
Outbox event owed external fulfilment effect
 -> durable worker
 -> platform API
 -> acknowledgement/retry/reconciliation
```

Remote failure never rolls back valid local shipment stock/reservation truth.

Do not publish E02 ATP to channels yet; that belongs to E09.

## 21. Required focused tests

### Reservation trigger

- OCR/unconfirmed candidate creates no reservation;
- confirmed but open-pool/unassigned demand creates no arbitrary warehouse reservation;
- open-pool accept reserves selected warehouse exactly once;
- fixed-warehouse committed task reserves at exactly one defined transition;
- insufficient ATP blocks commitment without partial hidden reservation.

### Reassignment

- target warehouse ATP validated under transaction;
- old reservation removed/moved exactly once;
- failure to reserve target leaves original assignment/reservation intact.

### Ship

- movement + balance + consume + state commit atomically;
- forced failure after movement insert rolls all effects back;
- response-loss replay creates no duplicate effect;
- ATP double-subtraction regression passes;
- no external network call in transaction.

### Complete

- already-shipped complete creates no stock/reservation effect;
- processing->complete compatibility invokes ship effect once only;
- repeated complete is idempotent/current-state safe according to E01 policy.

### Cancel/reversal

- cancel before ship releases promise exactly once;
- cancel after ship cannot fake stock restoration by reservation release;
- allowed reversal posts compensation and applies explicit reservation policy.

## 22. Expected files

After prior E02/E01 extraction, likely touchpoints:

```text
inventory_app/domains/stock/reservations.py
inventory_app/domains/stock/movement.py
inventory_app/domains/stock/balances.py
inventory_app/domains/stock/atp.py
inventory_app/services.py or extracted shipment domain facade
inventory_app/server.py / route adapter
inventory_app/platform/action_policy.py
tools/test_order_reservation.py
tools/test_shipment_reservation_consume.py
tools/test_shipment_reservation_reversal.py
tools/preview_open_demand_reservations.py
inventory_app/db_integrity.py
inventory_app/recovery_verifier.py
tools/verify_release.py
```

Do not introduce E03/E07 concerns.

## 23. Gate commands

Focused examples:

```bash
python3 tools/test_order_reservation.py
python3 tools/test_shipment_reservation_consume.py
python3 tools/test_shipment_reservation_reversal.py
python3 tools/preview_open_demand_reservations.py --check
python3 tools/reconcile_stock_kernel.py --check
python3 tools/verify_release.py
```

Linux release host:

```bash
python3 tools/verify_release.py --require-bash
```

## 24. PR review checklist

```text
[ ] reservations never originate from raw OCR candidate
[ ] unassigned open-pool order does not reserve arbitrary warehouse
[ ] warehouse assignment is server-authoritative
[ ] one stable requirement snapshot/identity backs each reservation
[ ] ShipmentService.ship is physical issue integration point
[ ] complete cannot double issue/consume
[ ] movement + balance + reservation consume + shipment state are atomic
[ ] pre-ship cancel releases only promise, not physical stock
[ ] post-ship reversal uses compensating movement
[ ] no platform network call in DB transaction
[ ] pilot cohort/authority is explicit server-side
[ ] full Release Gate PASS
```

Any `no` blocks merge.

## 25. Rollback

Once selected real shipment tasks become reservation-authoritative, rollback cannot return to code that ignores their active reservations.

Safe rollback requires either:

- disable creation of new reservation-authoritative tasks while retaining a compatible code path for already authoritative tasks; or
- deploy a prior compatible E02 build that still honors Migration 9 reservations and Migration 7/8 stock truth.

Do not drop reservation rows or switch those tasks to raw legacy availability silently.

## 26. Exit / unlock

Slice F completes when a controlled real fulfilment cohort proves:

```text
committed warehouse demand reserves once
competing demand cannot steal reserved ATP
shipment physical issue consumes reservation atomically
complete cannot double-post
cancel/reversal preserve physical-vs-promise semantics
replay/restart behavior is exact
```

Then unlock:

```text
E02 Slice G — Transfer Integration
```
