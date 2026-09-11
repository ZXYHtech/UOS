# TASK_INV_IMPL_E02 — Stock Position, Movement Ledger & Reservation Kernel

## Status

`DESIGN_READY_BLOCKED_BY_E00_E01_E11_GATES`

## Objective

Replace “mutable aggregate quantity as the primary truth” with a controlled stock kernel that separates:

```text
Movement Ledger = what physically/accountingly changed
Balance Projection = what quantity is currently on hand
Reservation = what quantity has been promised/committed
ATP = what can still be promised
```

E02 evolves the current working fulfilment/transfer/procurement flows; it does not replace the whole application.

## Entry gate

Runtime implementation must not begin until:

```text
E00 complete / merged
AND E01 execution/idempotency/job/outbox primitives complete
AND E11-S01/S02 pricing-safety bridge complete
AND full local Release Gate PASS
```

E02 branches from the then-current `main`.

## Confirmed baseline risks

Pinned audit/source baseline: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

### Current balance identity

Current `inventory` uniqueness is effectively:

```text
material_id + warehouse_id + platform_account_id
```

while `location_id` is a mutable column but not part of the unique stock identity.

`platform_account_id` is nullable, so schema-level uniqueness does not fully protect the logical “no account” row under SQL NULL uniqueness semantics.

### Current mutation primitive

Current `InventoryService.adjust_inventory()` approximately performs:

```text
load/get-or-create inventory row
 -> after = quantity_available + delta in Python
 -> reject if after < 0
 -> UPDATE inventory quantity
 -> INSERT inventory_logs with quantity_after
 -> operation log
```

This is useful audit history but not yet a canonical operation/line ledger with database-enforced business-operation identity.

### Current reservation gap

`quantity_locked` and `quantity_on_transfer` exist, but the audit did not find a first-class reservation entity linking promised stock to an order/order line/shipment allocation.

Order fulfilment can check availability and final deduction can reject negative stock, but two open demands can still compete for the same unreserved stock.

## Architectural invariant

After E02 cutover:

```text
No consequential stock change may directly edit a balance without a stock movement operation.
No committed demand may reduce ATP without a first-class reservation record.
No retry may post the same movement/reservation effect twice.
No reversal deletes historical movement; it posts a compensating operation.
```

## Domain boundary

Create a bounded stock domain, e.g.:

```text
inventory_app/domains/stock/
  identity.py
  movement.py
  balances.py
  reservations.py
  atp.py
  reconciliation.py
  compatibility.py
```

Do not turn this into a microservice. It remains the same process/database and receives the caller-owned SQLite connection.

## Core entities

### stock_movement_operations

One consequential business stock command.

Suggested fields:

```text
id
operation_key UNIQUE
action_code
reference_type
reference_id
reversal_of_operation_id NULL
correlation_id
business_operation_id
status
reason
created_by
occurred_at
created_at
```

An operation is immutable after posting except explicitly controlled metadata/status needed for recovery. A reversal is another operation.

### stock_movement_lines

One quantity effect inside an operation.

Suggested fields:

```text
id
operation_id
line_no
material_id
quantity
uom_code
from_position_key / dimensions
into_position_key / dimensions
movement_type
line_reference_type/id
created_at
UNIQUE(operation_id, line_no)
```

For simple receipt/issue, one side may represent external/source/sink rather than a physical location.

### stock_balances

Fast current projection.

Suggested conceptual identity:

```text
material
+ warehouse
+ normalized location scope
+ normalized owner/account scope
+ stock status
+ future lot/serial dimensions only when those domains become authoritative
```

Do not use nullable uniqueness as the invariant. Normalize optional dimensions to deterministic non-null scope keys or enforce complementary indexes that make NULL behavior explicit.

### stock_reservations

First-class promise/allocation record.

Suggested fields:

```text
id
reservation_key UNIQUE
material_id
warehouse_id
position_scope / optional allocated position
quantity
status
reference_type
reference_id
reference_line_id
expires_at NULL
business_operation_id
correlation_id
created_by
created_at
updated_at
```

Lifecycle:

```text
active
 -> partially_consumed
 -> consumed
 -> released
 -> cancelled
 -> expired (only for reservation types where expiry is valid)
```

Never infer reservation identity only from `quantity_locked`.

## ATP contract

Define terms explicitly:

```text
on_hand = physical/current posted balance eligible for promise
reserved = active unconsumed reservation quantity
safety_buffer = configured non-promisable buffer where policy applies
ATP = on_hand - reserved - safety_buffer
```

Do not subtract transfer quantities twice. Transfer semantics must be represented by movement/reservation state rather than overlapping anonymous counters.

Different stock statuses may or may not be ATP-eligible. E02 should begin with a minimal controlled vocabulary and leave quality/lot expansion to E07.

## Quantity / UOM boundary

Do not assume every future electronic material is integer pieces.

E02 must define a canonical quantity representation policy usable later for cable, paste, adhesive and similar fractional materials.

If SQLite remains primary, use deterministic decimal serialization/application arithmetic rather than unconstrained binary floating point for new authoritative quantity math.

Do not bulk-convert all legacy integer quantities merely to satisfy architecture aesthetics; migrate only with explicit reconciliation.

## No fabricated trace history

E02 must not invent:

- historical bins that were never recorded;
- lots/serials that did not exist in source evidence;
- old reservations that cannot be proven;
- fake movement chronology for legacy balances.

Legacy opening quantities enter the new ledger/projection through a clearly identified **migration opening-balance operation/snapshot**, with source-row provenance and reconciliation evidence.

## Coexistence / migration strategy

Do not switch all writes/readers in one release.

Recommended phases:

```text
Phase A: schema + reconciliation tooling, no production ownership
Phase B: shadow-post new movement ledger for selected pilot while old inventory remains authoritative
Phase C: continuously compare old balance versus new projection
Phase D: make stock kernel authoritative for one pilot action
Phase E: migrate reservation-aware order flow
Phase F: move remaining transfer/procurement/manual-adjust paths
Phase G: retire direct legacy balance writes only after parity window passes
```

At every phase, divergence is a blocker, not something to silently auto-correct.

## Shadow ledger rule

During shadow mode:

- one legacy business action may write legacy inventory and a shadow stock operation in the **same SQLite transaction** where feasible;
- shadow projection never drives customer/operator availability until parity is proven;
- reconciliation identifies exact action/reference that diverged;
- do not create asynchronous best-effort shadow posting that can silently miss events.

## Reservation migration rule

Do not derive historical reservations from `quantity_locked` without authoritative links.

At cutover:

- current open business demand is re-evaluated deterministically;
- reservations are created from authoritative open order/shipment state through a controlled migration/reconciliation command;
- shortages/ambiguities go to an operator review list;
- no demand is silently over-reserved.

## Reversal rule

Executed movement history is immutable.

Example:

```text
shipment completion operation: -2
shipment reversal operation: +2, reversal_of=<completion>
```

A second reversal of the same remaining effect must be blocked by operation identity/state.

## Concurrency rule

Stock posting and reservation changes are consequential SQLite writes and must use an explicit transaction/locking strategy compatible with E01 business-operation idempotency.

A status check alone is not a concurrency guarantee.

For high-contention balance/reservation update:

```text
BEGIN IMMEDIATE
 -> idempotency admission
 -> load authoritative dimensions/state
 -> validate ATP/current balance
 -> insert movement/reservation evidence
 -> update projection
 -> audit/result receipt
COMMIT
```

Keep write transactions short; external API calls never occur inside them.

## E01 primitive reuse

E02 must reuse:

```text
Action Policy
RequestContext / scope
business_operations idempotency
correlation_id
local Release Gate
outbox for external side effects
```

Do not create stock-specific alternatives for the same cross-cutting concerns.

## API compatibility

Existing APIs may initially keep their response shape through a compatibility façade, but internal stock mutation routes should migrate to stock-domain commands.

Do not expose raw ledger tables as the primary public API. Expose business commands/queries such as:

```text
post_adjustment
reserve
release_reservation
consume_reservation
post_transfer_issue
post_transfer_receipt
post_purchase_receipt
post_shipment_issue
reverse_operation
get_atp
reconcile_stock
```

## Story decomposition

Recommended E02 stories:

```text
E02-S01 Stock identity + quantity/UOM contract
E02-S02 Movement operation/line ledger + reversal
E02-S03 Balance projection + shadow reconciliation
E02-S04 Reservation lifecycle + ATP
E02-S05 Order/shipment reservation integration
E02-S06 Transfer/procurement/manual-adjust migration
E02-S07 Cutover, parity window and legacy-write retirement
```

Each story should be a separate small PR or tightly bounded sequence of PRs.

## Global tests

At minimum E02 eventually proves:

- same operation key cannot post stock twice;
- same key/different payload conflicts;
- concurrent deductions cannot oversell physical balance;
- two orders competing for insufficient ATP cannot both reserve the same quantity;
- reservation release restores ATP exactly once;
- reservation consumption and shipment movement do not double-decrement availability;
- transfer issue/receipt balances reconcile end-to-end;
- reversal compensates without deleting original history;
- shadow projection equals legacy authoritative totals through a defined parity window;
- migration opening balance exactly reconciles to legacy source totals;
- unknown/ambiguous legacy rows stop cutover and produce a review report;
- full `tools/verify_release.py` passes.

## Rollback philosophy

Schema additions are additive and evidence tables are retained.

Before new stock kernel becomes authoritative, rollback can return reads/writes to the legacy path while preserving shadow evidence.

After authoritative cutover, rollback must be treated as a controlled compatibility operation; never simply run old code that bypasses new movement/reservation truth.

## Non-goals

- no advanced zone/bin workflow (E03);
- no lot/serial genealogy (E07);
- no manufacturing WO allocation (E06);
- no MRP (E08);
- no PostgreSQL cutover (E15);
- no Kafka/Redis/event sourcing platform;
- no attempt to reconstruct nonexistent historical trace data.

## Acceptance

E02 is complete only when the new stock kernel is the sole authoritative path for migrated stock writes, reservation-based ATP prevents oversubscription, reconciliation proves balances, and direct legacy balance mutation has been retired or explicitly fenced from production use.