# TASK_INV_AUDIT_ORDER_FULFILLMENT_01 — Order Allocation, Picking, Shipping & Completion Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed order normalization/duplicate detection, recognition confirmation, shipment service, inventory validation/deduction, scan logs, platform sync state and current workflow tests/docs. No GitHub Actions status is used as evidence.

## 1. Executive conclusion

Order fulfilment is another relatively mature Inventory Lite domain. The product has a real chain from order ingestion/recognition through human confirmation, shipment-task execution, logistics/scan operations and stock deduction.

The largest structural gap is **allocation/reservation**. Current code can determine whether a warehouse has enough stock and blocks negative stock at the final mutation point, but no first-class durable reservation tied to an order line was found. This means the system protects physical quantity better than it protects promise/commitment quantity.

For low-volume operator-controlled use this can be acceptable. For automated multi-channel e-commerce, it creates a risk of multiple open orders all being told that the same unreserved stock is available.

## 2. Order ingestion foundation

The services define normalized order adapters for at least:

- website API;
- Taobao API;
- Pinduoduo API;
- manual order;
- image-recognition order.

All normalize toward a shared order shape including platform/account/order number, receiver/address, items and source metadata.

This adapter concept is strategically correct. Future channels should implement the same contract rather than add platform-specific logic throughout the order domain.

## 3. Recognition-to-order confirmation

The current OCR path has strong human-control concepts:

- recognition task;
- structured result;
- validation issues;
- manual confirmation requirement;
- duplicate detection;
- correction/revision records;
- formal order creation only after confirmation.

The source checks candidate duplicates before order creation and can surface suspected duplicates for manual review.

This is particularly valuable because OCR is probabilistic while inventory mutation must be deterministic.

## 4. Duplicate-order protection

The order schema has a uniqueness rule around platform/order number, while service logic also performs broader duplicate/similarity checks.

This layered approach is useful:

```text
schema exact identity
+ service semantic/similarity detection
+ human override for ambiguous cases
```

For API-driven synchronization, a stronger future contract is still needed:

```text
channel + shop account + external order id + external line id + sync event id
```

because a platform can contain multiple shops/accounts and updates/retries to the same order should not be interpreted as new business events.

## 5. Shipment task lifecycle

`shipment_tasks` separates operational fulfilment from the commercial order. Fields include:

- order;
- warehouse;
- creator/assignee;
- status;
- logistics company/number;
- accepted/shipped/completed timestamps.

Shipment operations include:

- open-pool or assigned handling;
- accept/transfer;
- stock validation;
- scan evidence;
- logistics confirmation;
- inventory deduction;
- reversal support in later workflows;
- archive evidence for completed tasks.

This separation is a strong architectural choice and should survive future refactoring.

## 6. Stock validation and fulfilment BOM/accessory expansion

Shipment availability logic expands required material beyond only the sales line. Current source can derive fulfilment requirements from associated BOM/accessory lines and aggregate required quantities per material/warehouse.

This is useful for kits/modules where one sold SKU requires multiple stock items.

However, because no controlled BOM revision/effectivity model exists, the fulfilment requirement is only as strong as the current BOM/accessory definition. Future manufacturing/sales-kit semantics should distinguish:

- sales bundle explosion;
- manufacturing BOM;
- optional accessories;
- packaging material;
- service/spare parts.

## 7. Reservation/allocation gap

No first-class order reservation entity was found in the pinned model.

Current pattern is closer to:

```text
order/task -> calculate required stock -> show enough/not enough -> later deduct on fulfilment
```

rather than:

```text
order -> reserve stock -> allocate warehouse/bin -> pick -> consume reservation -> ship
```

### Business impact

Possible oversubscription:

```text
5 available
A needs 4
B needs 4
both are open before either finishes
```

Both workflows may initially see sufficient stock. Final negative-stock prevention can cause the later completion to fail, but customer/order promise quality is already degraded.

### Recommended lifecycle

```text
Order confirmed
 -> reservation created
 -> warehouse allocation
 -> bin allocation
 -> pick task
 -> picked
 -> packed
 -> shipped
 -> reservation consumed / movement posted
```

Cancellation/reassignment must release or move the reservation.

## 8. Picking and scan model

`shipment_scan_logs` is a strong foundation. It records task/material/scanned code/quantity/match/operator/time.

For a true WMS flow it should expand to prove:

- source location;
- lot/serial if applicable;
- expected quantity;
- actual picked quantity;
- scan sequence;
- exception reason;
- pack/carton association later.

The system should not merely scan “the right product”; it should prove “the right product from the right controlled stock identity.”

## 9. Shipment idempotency/retry risk

Current shipment stock movements are linked by `reference_type='shipment_task'` and task ID, and later code can reconstruct actual inventory changes and reversals from ledger history.

That is a good audit foundation.

However, the global inventory mutation primitive does not itself enforce a unique business operation key. Therefore shipment completion/ship requests must be locally tested under:

- double-click;
- network timeout after commit;
- concurrent two-client execution;
- retry after application restart;
- reversal then re-ship.

A status check may prevent many ordinary repeats, but database-enforced operation identity is safer than relying on timing and status alone.

### Recommended identity

```text
shipment:<task_id>:stock-deduct:<generation>
```

or one operation key per task/material movement, protected by UNIQUE constraint.

## 10. Platform synchronization boundary

Orders have `platform_sync_status`, and shipment code can mark external-channel orders as needing manual/platform synchronization after shipping.

This is a useful explicit state rather than assuming remote sync succeeded.

Future connector design should use a durable sync outbox:

```text
local business commit
 -> outbox event
 -> independent worker
 -> remote API
 -> acknowledgement/cursor
 -> reconciliation
 -> retry/dead-letter
```

The remote platform must never participate in the same database transaction as the local stock change.

The worker should run via server process/systemd and must not depend on GitHub Actions.

## 11. Order state and commercial exceptions

Future order model should distinguish:

- confirmed;
- reserved;
- partially allocated;
- backordered;
- picking;
- partially shipped;
- shipped;
- cancelled before fulfilment;
- cancelled after fulfilment requiring return/reversal;
- refund pending/completed;
- aftersales/RMA.

Do not overload shipment status and order status into one state machine.

## 12. Multi-package / partial shipment gap

The current shipment task model appears centered on one task with logistics company/number fields. For growing e-commerce, future scenarios include:

- one order split across warehouses;
- partial shipment;
- multiple parcels for one shipment/order;
- replacement shipment;
- package-level carrier tracking;
- pack material/weight/dimensions.

Recommended future aggregate:

```text
shipment
shipment_lines
packages
package_lines
carrier_events
```

Only introduce this when real order volume/use cases justify it.

## 13. Cancellation/reversal principle

Existing shipment-reversal logic reconstructs unreversed stock deductions from ledger history and can restore inventory through compensating movement rather than deleting the original movement.

That is the correct accounting/audit principle:

`reverse with a new event, do not erase history`.

Reuse this pattern for future:

- returns;
- RMA replacement;
- production issue reversal;
- purchase return;
- quality disposition.

## 14. Electronics-company fulfilment extensions

For serialised RF modules/instruments, shipping should eventually capture:

```text
order line
 -> exact finished-goods serial
 -> product revision
 -> firmware revision
 -> test report/result
 -> shipment/package
 -> customer
```

Then aftersales can traverse:

`customer -> order -> shipped serial -> production batch -> component lots -> test history -> RMA`.

This is currently not available because serial genealogy is not modeled.

## 15. Automation opportunities

Independent of Actions:

- auto-reserve confirmed orders by policy;
- shortage/backorder alerts;
- suggested warehouse allocation;
- batch-wave picking;
- pick-path ordering after bin model exists;
- automatic shipment sync outbox;
- logistics tracking worker;
- stuck-task SLA reminders;
- anomaly detection between order/task/ledger/platform state.

All automated writes should be durable, idempotent and visible to the operator.

## 16. Local/server verification — no Actions

Recommended direct tests:

```bash
python3 tools/test_order_fulfilment.py
python3 tools/test_shipment_idempotency.py
python3 tools/test_order_reservation.py
python3 tools/test_platform_sync_outbox.py
```

Required scenarios:

- duplicate external order replay;
- OCR exact/similar duplicate handling;
- two orders competing for insufficient aggregate stock;
- warehouse reassignment releases/recreates reservation correctly;
- double shipment completion posts stock once;
- timeout/retry returns original completion result;
- reversal restores only unreversed movement;
- split warehouse allocation;
- platform sync failure does not roll back local shipping;
- reconciliation finds local/remote status mismatch.

GitHub Actions is explicitly unnecessary.

## 17. Static maturity score

0–5:

- normalized order ingest: **4/5**
- OCR/manual-confirm controls: **4.5/5**
- duplicate detection: **4/5**
- shipment-task execution: **4/5**
- stock deduction audit trail: **4/5**
- reservation/allocation: **1.5/5**
- bin-level picking: **2/5**
- shipment idempotency proof: **2.5/5**
- multi-package/partial shipment: **1.5/5**
- platform sync durability: **2.5/5**
- serialised-product fulfilment traceability: **0.5/5**

## 18. Core judgment

Order fulfilment should be evolved, not replaced.

The highest-value transition is:

`check stock at fulfilment time`

->

`reserve/allocate stock when the business commits to the order, then consume that reservation through scan-based fulfilment with idempotent stock posting and durable platform reconciliation`.
