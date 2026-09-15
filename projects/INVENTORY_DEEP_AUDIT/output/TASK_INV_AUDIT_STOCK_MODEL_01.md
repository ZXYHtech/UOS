# TASK_INV_AUDIT_STOCK_MODEL_01 — Inventory Quantity Model & Stock Semantics Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Primary evidence:

- `inventory_app/database.py`
- `inventory_app/services.py`
- `inventory_app/server.py`
- `tools/test_core_workflows.py`
- current development/iteration documentation

This is a source-level audit. Concurrency findings marked as risks require local reproducible tests before being labeled production defects. No GitHub Actions result is used or required.

## 1. Executive conclusion

The current inventory kernel is suitable for a lightweight small-team inventory/fulfilment system, but it is not yet a robust stock-reservation/WMS/manufacturing inventory kernel.

The strongest existing invariant is:

`business operation -> InventoryService.adjust_inventory -> inventory balance + inventory_logs + operation_logs`

That is worth preserving.

The largest gaps are not missing screens. They are stock semantics and transaction identity:

1. `quantity_available` is the only quantity actively mutated by `InventoryService.adjust_inventory`.
2. `quantity_locked` and `quantity_on_transfer` exist in schema/UI-related code but no corresponding business-rule use was found inside the full `services.py` source.
3. There is no first-class reservation/allocation entity linked to orders or shipment tasks.
4. Inventory identity does not include physical location, lot, serial or stock status.
5. the nullable `platform_account_id` in the UNIQUE key does not protect the logical NULL-account stock row at schema level.
6. `get_or_create_inventory` performs SELECT-then-INSERT, so concurrent creation of a NULL-account row needs explicit local race testing.
7. `adjust_inventory` performs application-side read-modify-write rather than a single conditional atomic update, so concurrent stock changes need explicit lost-update/lock-contention testing.
8. irreversible stock-changing operations do not share a universal idempotency-key primitive.

For current low-concurrency internal use, many flows may behave correctly because SQLite transactions serialize writes and service logic performs checks. But the model should be strengthened before larger multi-client e-commerce volume, manufacturing, or automated platform synchronization.

## 2. Current stock identity

Current table shape:

```text
inventory
  material_id
  warehouse_id
  platform_account_id nullable
  location_id nullable
  quantity_available
  quantity_locked
  quantity_on_transfer
  safety_stock
```

Declared uniqueness:

```text
UNIQUE(material_id, warehouse_id, platform_account_id)
```

### Interpretation

The canonical balance identity is effectively:

`material + warehouse + platform account`

not:

`material + warehouse + physical location`

and not:

`material + warehouse + lot/serial + status`.

Therefore `location_id` behaves like one optional attribute of the aggregate stock row, not a true balance dimension.

## 3. Active quantity semantics

### 3.1 `quantity_available`

`InventoryService.adjust_inventory`:

1. loads or creates the inventory row;
2. computes `after = current quantity_available + delta` in Python;
3. blocks negative result;
4. updates `quantity_available`;
5. inserts `inventory_logs` with delta and quantity-after;
6. writes `operation_logs`.

This creates a clear ledger trail for aggregate warehouse stock changes.

### 3.2 `quantity_locked`

The field exists in schema. A whole-file search of pinned `services.py` found no business-service reference to `quantity_locked`.

A direct server-side inventory-row update path can write the field, but no first-class order reservation lifecycle was found.

**Conclusion:** do not describe current `quantity_locked` as a complete reservation system.

### 3.3 `quantity_on_transfer`

Likewise the field exists in schema, but no business-service reference was found in pinned `services.py`.

Actual transfer state is instead represented by:

- transfer document state;
- `transfer_out` ledger movements;
- `transfer_out_revoke` ledger movements;
- `transfer_in` ledger movements;
- received quantities and transfer receipt events.

That document/ledger approach is stronger than maintaining a second mutable counter, but it means `quantity_on_transfer` currently appears semantically dormant or legacy rather than authoritative.

Recommendation: choose one model. Either derive in-transit quantity from transfer documents/events, or explicitly represent an in-transit stock location/status. Avoid maintaining an unrelated mutable counter without a strict invariant.

## 4. Reservation gap and e-commerce oversubscription risk

The existing fulfilment flow evaluates warehouse stock before shipping, while final inventory deduction occurs on shipment completion. No durable per-order reservation entity was found.

Potential scenario:

```text
Stock = 5
Order A requires 4 -> precheck says enough
Order B requires 4 -> precheck also says enough
A completes -> stock becomes 1
B completes -> final check fails
```

If final completion rechecks stock, negative inventory may still be prevented; however the business has already accepted more demand than the warehouse can fulfil.

This is a **late-failure/oversubscription gap**, not necessarily a negative-stock bug.

### Recommended reservation model

Add a first-class entity such as:

```text
stock_reservations
  id
  material_id
  warehouse_id
  location_id optional
  order_id / order_item_id
  shipment_task_id optional
  quantity
  status: active/released/consumed/expired
  reservation_key UNIQUE
  created_at
  expires_at optional
  released_at
```

Semantics:

```text
on_hand = physical balance
reserved = active reservations
available_to_promise = on_hand - reserved - quarantine/blocked
allocated = reservation assigned to a fulfilment task/location
picked = physical pick confirmed but shipment not yet posted
```

Do not overload one `quantity_locked` number to represent every stage.

## 5. Nullable unique-key risk

`platform_account_id` is nullable while included in the UNIQUE constraint.

In SQLite and PostgreSQL normal unique semantics, multiple rows containing NULL in the nullable component can coexist. Therefore the database itself does not guarantee that only one `(material, warehouse, no-platform-account)` inventory row exists.

The service query uses:

```sql
WHERE material_id=? AND warehouse_id=? AND platform_account_id IS ?
```

which correctly finds an existing NULL-account row during normal sequential execution.

But `get_or_create_inventory` is a two-step:

```text
SELECT
if not found -> INSERT
```

so two concurrent requests can both observe “not found” before insertion. With the current nullable uniqueness rule, the unique constraint may not collapse that race.

### Recommended fixes

Best long-term choice:

- replace nullable account semantics with a non-null `stock_scope_id` / owner dimension.

Lower-change alternatives:

- partial unique index for `platform_account_id IS NULL`;
- separate unique index for non-null account rows;
- normalized sentinel account only if business semantics make that safe.

Before migration, run an orphan/duplicate query against production data.

## 6. Read-modify-write concurrency risk

Current stock mutation conceptually does:

```text
SELECT quantity_available
Python: after = before + delta
UPDATE quantity_available = after
INSERT ledger
```

This should be tested under concurrent independent database connections.

Possible failure classes to test:

- `database is locked` / busy-timeout behavior;
- two requests reading the same old balance;
- lost update if both later write different computed `after` values;
- duplicate logical stock-row creation;
- ledger `quantity_after` no longer matching final balance;
- user retries after timeout applying the same business operation twice.

Do not assume SQLite WAL alone proves business-level atomicity.

### Safer mutation patterns

For decrement:

```sql
UPDATE inventory
SET quantity_available = quantity_available - :qty,
    updated_at = :now
WHERE id = :id
  AND quantity_available >= :qty;
```

Then require exactly one updated row and read the resulting balance in the same transaction.

For increment, use an atomic increment rather than overwriting a value computed from a stale read.

For operation replay, combine this with a durable idempotency/event record protected by a UNIQUE operation key.

## 7. Transfer semantics — a comparatively strong area

Transfer code already uses ledger evidence to guard repeated operations:

- before `transfer_out`, it sums existing `transfer_out` and `transfer_out_revoke` movements for the transfer/material;
- if net is zero, it posts the expected transfer-out;
- if net equals the expected negative quantity, it does not post again;
- inconsistent net values fail closed;
- undo shipment posts `transfer_out_revoke` only when appropriate;
- receiving can backfill missing expected outbound movement and posts only the actual received quantity;
- `transfer_items.received_quantity` supports cumulative partial receiving.

This is better than blindly updating an `on_transfer` counter.

### Remaining concurrency concern

The check-then-post sequence still lacks a universal unique business-event key visible in the audited model. Two concurrent identical receive/ship requests must therefore be tested.

Recommended movement identity:

```text
operation_key = transfer:<transfer_id>:<line_id>:ship:<generation/event>
operation_key UNIQUE
```

For partial receipts, each receipt event should have its own stable request/event ID.

## 8. Physical stock-state gap

For electronics operations, one quantity is insufficient. Required future states may include:

- available;
- reserved;
- picked;
- in transit;
- receiving inspection;
- quarantine;
- rejected;
- damaged;
- scrap;
- engineering/sample stock;
- production/WIP;
- consigned/customer-owned stock.

Do not necessarily add a column for each state. Prefer a normalized stock-status/location dimension plus movement/reservation events.

## 9. Safety-stock source-of-truth risk

The model stores safety stock both on `materials` and each `inventory` row. New inventory rows copy the material-level value.

This may be intentional as a default + per-warehouse override, but that policy is not obvious from the schema itself.

Define explicitly:

```text
material.default_safety_stock
warehouse_material_policy.safety_stock_override nullable
```

Then effective safety stock is deterministic. Avoid silently copying a default into many rows if future changes are expected to propagate.

## 10. Quantity/UOM policy

Core stock is integer while purchase and one project-BOM quantity path support fractional values.

Electronics manufacturing includes legitimate fractional-stock units:

- wire/cable length;
- solder paste/adhesive mass;
- heat-shrink length;
- sheet/film area;
- chemicals/cleaning consumables.

Recommended future model:

- base UOM per material;
- allowed conversion rules;
- fixed decimal quantity representation;
- UOM-specific precision;
- no implicit `int()` coercion in shared quantity utilities.

## 11. Target stock kernel

Recommended modular-monolith design:

```text
Part/Material
   |
   +--> StockLocation hierarchy
   +--> StockLot / Serial
   +--> StockStatus

Business documents
   |
   +--> Reservation
   +--> StockMovement / StockMovementLine
             |
             +--> source location/status/lot
             +--> destination location/status/lot
             +--> quantity + UOM
             +--> business reference
             +--> operation/idempotency key
             +--> actor + time

StockBalance = fast projection of posted movement + reservation state
```

The current `inventory` table can remain temporarily as the balance projection while the event model is introduced behind it.

## 12. Reconciliation tooling

Add repository-local commands such as:

```bash
python3 tools/check_inventory_integrity.py
python3 tools/rebuild_inventory_projection.py --dry-run
python3 tools/test_inventory_concurrency.py
```

Checks should include:

- duplicate logical inventory keys;
- negative balances;
- ledger latest `quantity_after` vs current balance;
- transfer net movement vs transfer state;
- completed shipment expected movements vs ledger;
- active reservations <= eligible stock;
- orphan references;
- location/lot balances sum to warehouse balance after migration.

These tools are the verification authority. GitHub Actions is not required.

## 13. Priority recommendations

### P0

1. repair NULL-account uniqueness at database level;
2. build local concurrent stock mutation test;
3. change mutation to atomic SQL transaction semantics;
4. add durable idempotency key for irreversible stock operations;
5. define authoritative meaning of `quantity_locked` and `quantity_on_transfer` or deprecate them;
6. introduce first-class reservation/allocation before high-volume automated order sync;
7. define multi-bin stock identity before expanding warehouse scanning.

### P1

1. location-level balances;
2. stock status/quarantine;
3. lot/batch support;
4. serial support;
5. decimal/UOM policy;
6. formal reconciliation command and scheduled server-side integrity check.

### P2

1. ATP/CTP planning;
2. replenishment policy by warehouse/part;
3. advanced allocation strategies;
4. WIP/subcontract/consigned stock.

## 14. Static maturity score

0–5:

- basic warehouse balance: **4/5**
- movement audit trail: **4/5**
- negative-stock protection: **4/5** in normal service flow
- reservation/allocation: **1.5/5**
- multi-bin physical stock: **1.5/5**
- in-transit model clarity: **2.5/5**
- concurrency robustness evidence: **2/5**
- idempotency platform primitive: **2/5**
- lot/serial traceability: **0.5/5**
- manufacturing stock semantics: **1/5**

## 15. Core judgment

The current stock kernel is a sound lightweight operational base, but the next generation should stop treating “inventory” as one mutable quantity per material/warehouse.

The strategic transition is:

`single aggregate quantity -> explicit physical location/status + reservation + durable movement identity + reconciliation`

That change is foundational for both e-commerce scale and electronic-product manufacturing.