# TASK_INV_IMPL_E02_S04 — Reservation Lifecycle & ATP

## Status

`DESIGN_READY_BLOCKED_BY_E02_S03`

## Objective

Introduce first-class durable reservations so committed demand reduces promise availability before physical stock is finally issued.

## Problem being solved

Current flow can check stock and later deduct it, but without first-class reservation two open orders can both observe the same free quantity.

Example:

```text
on hand = 5
order A needs 4
order B needs 4
```

Without reservation, both may initially appear feasible. E02 must prevent that oversubscription.

## Core entities

### stock_reservations

Suggested fields:

```text
id INTEGER PK
reservation_key TEXT NOT NULL UNIQUE
material_id INTEGER NOT NULL
warehouse_id INTEGER NOT NULL
position_key TEXT NULL
quantity_total DECIMAL-SEMANTIC NOT NULL
quantity_consumed DECIMAL-SEMANTIC NOT NULL DEFAULT 0
quantity_released DECIMAL-SEMANTIC NOT NULL DEFAULT 0
status TEXT NOT NULL
reference_type TEXT NOT NULL
reference_id INTEGER NOT NULL
reference_line_id INTEGER NULL
business_operation_id INTEGER NULL
correlation_id TEXT
expires_at TEXT NULL
created_by INTEGER
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

Use explicit remaining quantity:

```text
remaining = total - consumed - released
```

Never derive remaining from mutable free-text workflow status alone.

## Reservation lifecycle

```text
active
 -> partially_consumed
 -> consumed
 -> partially_released
 -> released
 -> cancelled
 -> expired (only for policy-enabled temporary reservations)
```

State transitions must be deterministic and tested.

## ATP formula

For promise-eligible positions:

```text
ATP = on_hand
      - active_unconsumed_reservations
      - safety_buffer
```

If stock status is not promise-eligible, its quantity contributes zero ATP.

Do not subtract transfer quantity twice through both movement state and anonymous counters.

## Reservation command set

Domain commands:

```text
reserve_stock
increase_reservation
reduce_reservation
release_reservation
consume_reservation
move_reservation_scope
get_atp
```

Every consequential command uses E01 business-operation idempotency.

## Concurrency rule

Reservation creation/increase must lock the relevant SQLite write transaction before evaluating ATP.

```text
BEGIN IMMEDIATE
 -> idempotency admission
 -> resolve authoritative position/warehouse
 -> compute current ATP from balance + active reservations
 -> require requested <= ATP
 -> insert/update reservation
 -> audit/result receipt
COMMIT
```

Two concurrent requests cannot both consume the same ATP.

## Warehouse versus position allocation

E02 initially supports reservation at warehouse scope and optionally position scope where legacy location evidence is trustworthy.

Do not force bin allocation before E03.

Recommended distinction:

```text
reservation = promise against warehouse stock
allocation = physical position/bin choice
```

E03 can later refine reservation into pick allocations.

## Safety stock

Existing safety-stock concepts may feed `safety_buffer`, but policy must be explicit.

Do not silently reinterpret every existing `safety_stock` value without confirming current semantics.

## Expiry

Only temporary reservation classes that have a real business expiry may use `expires_at`.

A confirmed paid order should not suddenly release stock just because a generic timer expired unless the business process explicitly allows that behavior.

Expiry release must itself be a durable/idempotent operation and must not depend on GitHub Actions. If needed, use the E01 local durable worker/systemd runtime.

## Reservation evidence

Every reservation should identify:

```text
who/what reserved it
why
which business line it belongs to
when it was created
how much remains
which operations consumed/released it
```

Do not expose only one aggregate “locked quantity”.

## Relationship to movement

Creating/releasing a reservation does **not** physically move stock.

Consuming a reservation is coupled to the physical issue movement in one business transaction where appropriate:

```text
validate active reservation
 -> post shipment/issue movement
 -> increment consumed quantity
 -> update reservation status
 -> update balance projection
COMMIT
```

This prevents “reservation consumed but stock not issued” or the reverse.

## Legacy quantity_locked

Do not bulk-create reservations from legacy `quantity_locked` unless authoritative references prove what those locks mean.

Migration handling:

- report current non-zero locks;
- classify source if traceable;
- re-evaluate open business demand at cutover;
- ambiguous locks require operator review;
- no fabricated order linkage.

## Tests

- one reservation reduces ATP;
- two concurrent reservations cannot oversubscribe one balance;
- same idempotency key returns same reservation receipt;
- same key/different quantity conflicts;
- partial release restores ATP exactly once;
- full release restores ATP exactly once;
- partial consumption reduces on-hand and reservation remaining without double subtraction;
- consumed reservation cannot be released as if still free;
- cancelled/released reservation is not counted in ATP;
- stock status eligibility affects ATP deterministically;
- ambiguous legacy lock is reported, not fabricated;
- full Release Gate passes.

## Rollback

Before reservation becomes authoritative for order promise, it can remain shadow/diagnostic.

After authoritative activation, rollback must preserve active reservation records and use code that still honors them; old code that ignores reservations is unsafe.

## Acceptance

S04 is complete when ATP is a deterministic function of authoritative balance + active reservation + explicit buffer, and concurrency tests prove two demands cannot reserve the same free stock.

## Dependencies

E02-S03, E01 idempotency/action policy.

## Non-goals

- no pick-path/bin allocation;
- no manufacturing allocation;
- no lot/serial reservation;
- no channel ATP publication yet.