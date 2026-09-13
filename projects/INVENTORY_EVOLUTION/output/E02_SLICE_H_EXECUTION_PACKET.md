# E02 Slice H Execution Packet — Procurement Receipt Stock Integration

## Status

`READY_AFTER_E02_SLICE_G_AND_LANDED_COST_SAFETY_GATE`

This packet migrates purchase-receipt physical stock effects onto the authoritative E02 movement/balance kernel without prematurely adding E03 receiving/putaway or E07 IQC/lot semantics.

## Entry gate

All must be true:

```text
E02-G transfer integration PASS
current stock reconciliation = zero unexplained divergence
PURCHASE_PARTIAL_RECEIPT_LANDED_COST_SAFETY_REVIEW resolved by fixture/fix
current main full Release Gate PASS
```

Suggested branch:

```text
impl/e02-purchase-receipt-stock
```

Migration:

```text
NONE expected
```

Use existing procurement tables plus Migration 7/8 stock truth.

## 1. Current procurement behavior to preserve

Current `ProcurementService.receive()` already has useful business objects:

```text
purchase_order
purchase_order_items
purchase_receipts
purchase_receipt_items
material_purchase_prices
```

It also currently:

- requires PO status `approved` or `part_received`;
- validates each receipt quantity against remaining ordered quantity;
- supports partial receipt;
- creates one receipt identity;
- updates line `received_quantity`;
- changes PO status to `part_received` or `completed`;
- posts inventory increase;
- writes purchase/audit evidence.

Preserve those business semantics unless a separate reviewed defect fix changes them first.

## 2. Physical stock authority

After E02-H pilot/cutover for selected receipts:

```text
purchase_receipt stock movement
+ stock_balances
```

becomes authoritative physical stock evidence.

The legacy `InventoryService.adjust_inventory(... movement_type='purchase_receipt' ...)` direct balance mutation must no longer be an independent second stock effect for the authoritative cohort.

Compatibility `inventory` / `inventory_logs` may remain projected/written in the same transaction only for existing UI/report compatibility until Slice J.

## 3. Receipt transaction

Target transaction:

```text
BEGIN IMMEDIATE
 -> E01 business-operation admission
 -> load PO + lines
 -> permission + warehouse scope + PO-state validation
 -> validate submitted receipt quantities against remaining receivable qty
 -> create one purchase_receipt header
 -> create purchase_receipt_items
 -> perform approved landed-cost/commercial evidence writes
 -> post one E02 purchase_receipt movement operation with lines
 -> update stock_balances
 -> update PO item received_quantity
 -> update PO status/completed_at
 -> append audit/result receipt
COMMIT
```

Everything commits or rolls back together.

No network/provider call inside the transaction.

## 4. Movement direction

Each receipt line is explicit:

```text
EXTERNAL_SUPPLIER
 -> destination warehouse receiving/current stock scope
```

Quantity uses E02 Decimal/UOM rules.

Do not create a fake supplier warehouse.

E03 may later change destination from current available/unassigned semantics to a `receiving_staging` position before putaway.

E07 may later change receipt eligibility into `PENDING_INSPECTION`/quality-controlled state.

E02-H preserves today's business availability semantics unless those later domains are already active.

## 5. Receipt identity / idempotency

The outer E01 operation key is required before receipt creation.

On first successful execution:

```text
purchase_receipt.id
receipt_no
stock_movement_operation.id
```

are stored in the E01 result receipt.

Replay same operation key/same payload returns the original receipt identifiers without:

- inserting a second purchase_receipt;
- incrementing `received_quantity` twice;
- posting stock twice;
- adding duplicate purchase-price/cost evidence.

Same key/different quantities/remark/effect -> idempotency conflict according to canonical fingerprint policy.

## 6. Stock operation key

After receipt identity exists in the same transaction, bind stock evidence conceptually as:

```text
purchase_receipt:<receipt_id>:post
```

The E01 business operation remains the outer replay owner.

Do not rely on `receipt_no` timestamp uniqueness as the only exactly-once guard.

## 7. Partial receipt

Example:

```text
PO line ordered = 10
receipt #1 = 4
receipt #2 = 6
```

Require:

```text
receipt #1 stock +4 once
received_quantity = 4
PO status = part_received

receipt #2 stock +6 once
received_quantity = 10
PO status = completed
```

Each receipt has separate immutable receipt/movement identity.

No later receipt can exceed remaining ordered quantity under default policy.

## 8. Over-receipt policy

Preserve current safe default:

```text
received cumulative quantity > ordered quantity -> reject
```

If business later needs tolerance/over-receipt:

- explicit policy;
- dedicated permission/threshold;
- reason;
- immutable evidence;
- separate reviewed change.

Do not silently increase PO ordered quantity or bypass validation inside E02-H.

## 9. Landed-cost boundary

E02-H must not hide a commercial allocation change inside stock migration.

Before this slice, resolve:

`PURCHASE_PARTIAL_RECEIPT_LANDED_COST_SAFETY_REVIEW.md`

Important rules:

- physical receipt quantity can become E02 stock truth independently of the costing implementation;
- cost allocation must be deterministic and separately regression-tested;
- if current partial-receipt allocation is confirmed defective, merge the bounded cost fix first;
- do not rewrite historical purchase cost rows automatically during E02-H.

## 10. Failure injection

### Failure after receipt header

Inject before items/movement.

Require whole rollback:

- no receipt header;
- no PO received increment;
- no stock movement;
- no balance change.

### Failure after movement/balance

Inject before PO state/audit/operation success.

Require movement + balance rollback too.

### Failure in landed-cost evidence

If commercial evidence is part of current required receipt transaction, stock must not commit while required receipt/cost rows failed.

Do not leave “stock arrived but canonical receipt record missing”.

## 11. Lost response / retry

Scenario:

```text
receipt commits fully
 -> response lost
 -> client retries same operation key
```

Require:

```text
same receipt_id / receipt_no returned
one stock movement
one balance increase
one received_quantity increment
one required purchase-cost record set
```

No duplicate effect.

## 12. Concurrency

Two simultaneous receipts against the same PO line must not both consume the same remaining receivable quantity.

Fixture:

```text
ordered = 10
already received = 6
A receives 4
B receives 4 concurrently
```

Require at most one succeeds.

Use short `BEGIN IMMEDIATE`/caller-owned transaction and re-read authoritative line state under the transaction before accepting quantity.

A pre-flight UI remaining quantity is not authority.

## 13. Warehouse scope

Preserve existing purchase receive policy:

```text
purchase/manage authority
+ PO warehouse derived from server-side PO row
```

Do not trust request payload warehouse as authority.

The movement destination warehouse must equal the authoritative PO/receipt warehouse unless a separately reviewed procurement change exists.

## 14. Legacy compatibility

During coexistence:

- existing procurement receipt screens continue to use current PO/receipt records;
- old inventory list may consume compatibility `inventory` projection;
- `inventory_logs` may be emitted as compatibility audit representation in the same transaction;
- E02 movement/balance is the authoritative stock source for migrated receipt cohort.

No independent legacy `quantity_available += qty` path may survive beside authoritative stock posting.

## 15. Receiving location/status

E02-H does **not** implement:

- receiving dock/staging task;
- putaway;
- bin scan;
- supplier lot/date code;
- IQC/quarantine.

Use the currently approved E02 canonical destination identity, often warehouse + legacy/unassigned available scope for backward parity.

Later E03/E07 migrations move future receipts through richer states using explicit movements rather than rewriting historical receipt evidence.

## 16. Open PO migration/previews

No special migration is needed merely because open POs exist; they are commercial future supply, not current physical stock.

However, provide a read-only preview over open/partial POs to identify:

```text
PO/line
ordered
legacy received_quantity
existing receipt item sum
remaining receivable
warehouse
inconsistency flags
```

Block authoritative receipt integration for lines where:

```text
received_quantity != sum(canonical receipt evidence)
```

unless explicitly reconciled.

Do not invent missing receipts to match the counter.

## 17. Integrity/reconciliation

Extend checks:

```text
sum purchase_receipt_items quantity per PO line
<= ordered quantity (unless approved policy exists)

PO line received_quantity
== sum canonical receipt quantities for authoritative cohort

sum purchase_receipt stock movements
== canonical receipt item quantities
```

Surface mismatches as blockers.

## 18. Focused tests

Required:

1. approved PO partial receipt posts stock exactly once;
2. final receipt transitions PO to completed;
3. duplicate response retry returns same receipt;
4. same key/different quantity conflicts;
5. over-receipt rejected;
6. concurrent receipts cannot exceed remaining qty;
7. forced failure rolls PO/receipt/cost/stock effects back together;
8. movement destination matches authoritative PO warehouse;
9. open-PO preview finds fixture inconsistency;
10. stock reconciliation remains zero unexplained divergence.

## 19. Expected files

Likely touchpoints:

```text
inventory_app/domains/stock/movement.py
inventory_app/domains/stock/balances.py
inventory_app/domains/procurement/service.py or compatibility facade
inventory_app/platform/action_policy.py
inventory_app/db_integrity.py
tools/test_purchase_receipt_stock_kernel.py
tools/test_purchase_receipt_concurrency.py
tools/preview_open_po_receipts.py
tools/reconcile_stock_kernel.py
tools/verify_release.py
```

The landed-cost fix, if required, should remain a distinct commit/PR boundary.

## 20. Gate commands

```bash
python3 tools/test_purchase_receipt_stock_kernel.py
python3 tools/test_purchase_receipt_concurrency.py
python3 tools/preview_open_po_receipts.py --check
python3 tools/reconcile_stock_kernel.py --check
python3 tools/verify_release.py
```

Linux release host:

```bash
python3 tools/verify_release.py --require-bash
```

## 21. PR review checklist

```text
[ ] landed-cost safety prerequisite resolved separately
[ ] receipt quantity revalidated under write transaction
[ ] purchase receipt has one stable E01 operation identity
[ ] stock movement tied to receipt identity
[ ] partial receipts remain separate immutable events
[ ] duplicate retry cannot duplicate receipt/cost/stock
[ ] over-receipt rejected by explicit policy
[ ] PO warehouse is server-derived
[ ] no E03/E07 scope leakage
[ ] compatibility legacy balance is not independent truth
[ ] reconciliation zero unexplained divergence
[ ] full Release Gate PASS
```

Any `no` blocks merge.

## 22. Rollback

Once selected purchase receipts are E02-authoritative, rollback must deploy code that continues to honor Migration 7/8 stock evidence.

Do not revert those receipts to direct legacy balance posting.

New receipt processing may be paused while existing receipt/movement evidence remains intact.

## 23. Exit / unlock

Slice H completes when controlled real purchase receipts prove:

```text
partial receipt identity is exact
PO remaining quantity is concurrency-safe
physical stock posts exactly once
PO/receipt/stock/audit commit together
costing ambiguity is separately resolved
reconciliation has zero unexplained divergence
```

Then unlock:

```text
E02 Slice I — Manual Adjustment / Count Bridge
```
