# E01 Slice C Execution Packet — Consequential Pilot Actions

## Status

`READY_TO_START_ONLY_AFTER_E01_SLICE_B_MERGE`

This slice proves Action Policy + durable business-operation idempotency against real existing workflows **without changing E02 stock semantics**.

Do not migrate all pilots at once. Treat them as C1/C2/C3 merge/review gates.

## 1. Entry gate

All must be true:

```text
E00 PASS + merged
E01 Slice A merged
E01 Slice B merged
Migration 2 business_operations active
full Release Gate PASS on current main
```

Suggested branch strategy:

```text
impl/e01-pilot-transfer-receive
impl/e01-pilot-purchase-receive
impl/e01-pilot-shipment-complete
```

Prefer three small PRs. If one combined review branch is temporarily used, retain separate commits/gates and do not merge later pilots before earlier evidence is accepted.

# 2. Existing authoritative behavior to preserve

## C1 — `transfer.receive`

Current API/security behavior:

```text
permission = transfer.process
scope = transfer.to_warehouse_id for receive/receive-exception/resume-receive
service = TransferService.receive(conn, tid, uid, data)
```

Current service accepts states:

```text
in_transit
shipped
pending_receive
exception   (only valid receive-exception context)
```

Current receive behavior includes:

- optional partial receipt by material code;
- reject negative receipt;
- reject receipt above remaining quantity;
- require reason when receipt remains short;
- verify or reconstruct expected `transfer_out` movement before inbound receipt;
- post `transfer_in` through existing `InventoryService.adjust_inventory`;
- update `transfer_items.received_quantity`;
- write `transfer_receipt_events`;
- update transfer status/exception fields;
- write exactly one authoritative `operation_logs` receive record.

Current route normally returns `{id: tid}` because `TransferService.receive(...)` itself does not need to return a new API shape.

**Do not change any of the above business semantics in C1.**

## C2 — `purchase.receive`

Current API/security behavior:

```text
permission = purchase.manage
scope = purchase_order.warehouse_id
service = ProcurementService.receive(conn, order_id, data, uid)
```

Current service accepts:

```text
approved
part_received
```

Current receive behavior includes:

- require submitted item quantities;
- reject negative/over-remaining quantities;
- create `purchase_receipts`;
- create `purchase_receipt_items`;
- allocate freight/other amount into landed cost;
- append `material_purchase_prices`;
- increment PO-line `received_quantity`;
- post stock through current `InventoryService.adjust_inventory`;
- transition PO to `part_received` or `completed`;
- write `purchase.receive` audit;
- return `{receipt_id, receipt_no, status}`.

**Do not refactor landed-cost or procurement accounting while adding idempotency.**

## C3 — `shipment.complete`

Current API/security behavior:

```text
permission = shipment.process
scope = shipment_task.warehouse_id
warehouse_operator additionally cannot operate a task assigned to another user
service = ShipmentService.complete(conn, task_id, uid)
```

Current service behavior is intentionally two-stage:

```text
if task.status == processing:
  ShipmentService.ship(... no_logistics ...)
    -> deduct inventory
    -> mark shipment/order shipped
    -> write shipment.ship audit

then require status == shipped
 -> mark shipment completed
 -> mark order completed
 -> write shipment.complete audit
```

This means C3 is replay-sensitive even though `complete()` has no meaningful request body: completing from `processing` can trigger the stock deduction via `ship()`.

**Do not split or redesign this state machine in E01.** E02 later changes stock authority.

# 3. Common Action Policy order

Every pilot must preserve:

```text
RequestContext
 -> authoritative target load
 -> existing permission check
 -> object-derived warehouse scope
 -> existing special actor/assignment rule
 -> existing domain state/precondition
 -> normalized fingerprint
 -> atomic-local idempotency transaction
 -> existing service using SAME conn
 -> existing audit/business evidence
 -> succeeded receipt
COMMIT
```

Rejected permission/scope/state requests must never create a successful business operation or call the mutation service.

# 4. C1 Transfer Receive

## Policy

```text
action_code = transfer.receive
permission = transfer.process
target_loader = transfer_order(id)
scope = target.to_warehouse_id
idempotency = required
audit = service_owned_audit
```

## Fingerprint

Canonical effect payload should include:

```text
transfer_order_id
normalized receipt lines:
  material_code
  received_quantity
exception_type
reason
```

Sort receipt lines by canonical material code if line order has no business meaning.

Do not include correlation ID or client retry timestamp.

## Receipt

Preserve current public response. Stored idempotency receipt can remain small:

```json
{
  "target_type": "transfer_order",
  "target_id": 123
}
```

Optionally include stable resulting status/latest receipt-event ID only if obtained without changing API semantics.

## Required replay assertions

For full and partial receive:

- duplicate same key posts inbound stock once;
- `received_quantity` increments once;
- one receive/partial-receive event is created;
- one receive audit record is created;
- same key/different quantities conflicts;
- response-loss retry returns compatible `{id}` response;
- wrong destination-warehouse user cannot create operation/movement.

## Important partial-receive case

A partial receipt followed by a legitimate second receipt is **not a replay**. It must use a new operation key/fingerprint and post only the remaining quantity.

Do not globally dedupe on transfer ID alone.

# 5. C2 Purchase Receive

## Policy

```text
action_code = purchase.receive
permission = purchase.manage
target_loader = purchase_order(id)
scope = target.warehouse_id
idempotency = required
audit = service_owned_audit
```

## Fingerprint

Include:

```text
purchase_order_id
sorted receipt lines:
  purchase_order_item_id
  quantity
remark (because it is persisted on receipt)
```

Do not fingerprint generated `receipt_no`; it does not exist before execution.

## Receipt

Reuse current service return exactly:

```json
{
  "receipt_id": 123,
  "receipt_no": "PR...",
  "status": "part_received|completed"
}
```

This is an ideal persisted result receipt for response-loss replay.

## Required replay assertions

Same-key retry must not duplicate:

- `purchase_receipts`;
- `purchase_receipt_items`;
- purchase-price history rows;
- landed-cost allocation;
- line received quantity;
- stock movement;
- purchase audit.

Same key + changed quantity/remark must conflict.

A legitimate later partial receipt uses a new operation key.

# 6. C3 Shipment Complete

## Policy

```text
action_code = shipment.complete
permission = shipment.process
target_loader = shipment_task(id)
scope = target.warehouse_id
special_actor_rule = existing warehouse_operator assigned-user restriction
idempotency = required
audit = service_owned_audit
```

## Fingerprint

There is effectively no business payload beyond the command/target:

```text
action_code
shipment_task_id
```

Do not include current task status in the fingerprint; status is authoritative mutable state checked by the service/policy precondition, not client intent.

## Receipt

Preserve existing API response:

```json
{"id": task_id}
```

## Required two-state tests

### Starting from `processing`

First call:

```text
ship/no-logistics stock deduction
+ shipment.ship audit
+ shipment/order shipped state
+ completion state
+ shipment.complete audit
```

Retry same key:

- no second deduction;
- no second ship audit;
- no second complete audit;
- same compatible response.

### Starting from `shipped`

First call only completes state; retry still executes no service mutation.

## Assignment/scope assertions

- wrong warehouse denied before operation execution;
- warehouse operator assigned to another user denied;
- admin/unrestricted behavior remains identical to existing helpers.

# 7. Transaction rule

Each pilot uses one caller-owned SQLite connection.

Do not open a second connection inside the idempotency wrapper for:

```text
service mutation
business_operation success
operation_logs
inventory_logs
receipt/event rows
```

They must share one commit boundary.

External platform synchronization is not part of this transaction. Existing local `platform_sync_status` behavior can remain; later E01 Outbox/E09 own durable external delivery.

# 8. Existing audit is authoritative

Use:

```text
audit_mode = service_owned_audit
```

The wrapper must not add a second `operation_logs` row merely because it executed a policy.

`business_operations` is command/replay evidence, not a duplicate human audit log.

# 9. Required tests per pilot

Every C1/C2/C3 PR runs:

```text
existing happy-path workflow test
existing invalid-state test
permission test
wrong-scope test
same-key replay
same-key/different-fingerprint conflict
concurrent same-key attempt
injected failure before commit
lost-response replay
audit-count assertion
business-row-count assertion
stock-delta assertion where applicable
full tools/verify_release.py
```

Do not accept a test that only proves HTTP duplicate suppression; verify the underlying stock/receipt/event rows.

# 10. Stop conditions

Stop a pilot rather than broadening scope if any of the following appears:

- service commits internally in a way that breaks one atomic transaction;
- current state semantics are ambiguous under replay;
- existing audit cannot be kept exactly once;
- implementing idempotency would require E02 stock model changes;
- external network side effects occur inside the local transaction;
- API compatibility would require a broad frontend rewrite.

Record the incompatibility and resolve it as a separate prerequisite.

# 11. Merge order

```text
C1 transfer.receive PASS + merge
 -> branch C2 from new main
C2 purchase.receive PASS + merge
 -> branch C3 from new main
C3 shipment.complete PASS + merge
```

Do not stack all three on the old main.

# 12. Exit / unlock

Slice C is complete when all three pilots prove business-exactly-once behavior without changing stock semantics or existing authorization/state behavior.

Then unlock:

```text
E01 Slice D — Durable Jobs / Lease / Worker / Retry / Dead-letter
```

Stock redesign remains blocked until E01 and E11 early gates complete.
