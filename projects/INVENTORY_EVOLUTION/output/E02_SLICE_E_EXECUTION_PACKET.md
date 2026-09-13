# E02 Slice E Execution Packet — Reservation / ATP Shadow Kernel

## Status

`READY_AFTER_E02_SLICE_D`

This packet introduces first-class reservations and ATP calculation, but does **not** yet make them authoritative for customer orders, shipment promises or channel publication.

## Entry gate

All must be true:

```text
E02-A stock identity/UOM complete
E02-B Movement Ledger Migration 7 complete
E02-C Balance Projection Migration 8 complete
E02-D same-transaction shadow pilot complete
shadow reconciliation = zero unexplained divergence for agreed pilot evidence window
full current-main Release Gate = PASS
```

Suggested branch:

```text
impl/e02-reservation-atp
```

Migration:

```text
9 = stock_reservations + stock_reservation_events
```

Migration 9 is additive. It does not rewrite `quantity_locked` and does not create fake reservations from historical aggregate locks.

## 1. Purpose

Create one deterministic answer to:

```text
what stock is physically on hand?
what quantity is already promised?
what quantity can still be promised?
```

Core formula for promise-eligible stock:

```text
ATP = eligible_on_hand
    - active_unconsumed_reservation
    - explicit_safety_buffer
```

Slice E proves this kernel in isolation/shadow mode.

It does not yet change:

- order confirmation behavior;
- shipment allocation;
- platform published stock;
- normal UI promise quantity.

## 2. Authority mode

During Slice E:

```text
legacy inventory remains operational authority
new stock_balances remains reconciled shadow projection
stock_reservations = new durable reservation evidence
ATP = diagnostic/shadow until Slice F
```

Reservation APIs/tests may operate on controlled fixtures and privileged diagnostic paths.

Do not let ordinary order creation call `reserve_stock()` yet.

## 3. Migration 9 schema

### `stock_reservations`

Recommended fields:

```text
id INTEGER PRIMARY KEY AUTOINCREMENT
reservation_key TEXT NOT NULL UNIQUE
material_id INTEGER NOT NULL
warehouse_id INTEGER NOT NULL
position_key TEXT
uom_code TEXT NOT NULL
quantity_total TEXT NOT NULL
quantity_consumed TEXT NOT NULL DEFAULT '0'
quantity_released TEXT NOT NULL DEFAULT '0'
status TEXT NOT NULL
reservation_class TEXT NOT NULL
reference_type TEXT NOT NULL
reference_id INTEGER NOT NULL
reference_line_id INTEGER
business_operation_id INTEGER
correlation_id TEXT
expires_at TEXT
created_by INTEGER
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

Use deterministic Decimal serialization from E02-A. Do not use binary floating point as authoritative reservation quantity.

Suggested status vocabulary:

```text
active
partially_consumed
partially_released
consumed
released
cancelled
expired
```

Suggested initial reservation classes:

```text
test
manual_controlled
```

Order/work-order/project classes are added only when their integration slices become authoritative.

### `stock_reservation_events`

Keep current reservation state efficient while preserving lifecycle evidence.

Recommended fields:

```text
id INTEGER PRIMARY KEY AUTOINCREMENT
reservation_id INTEGER NOT NULL
event_no INTEGER NOT NULL
event_type TEXT NOT NULL
quantity TEXT NOT NULL
business_operation_id INTEGER
correlation_id TEXT
reason TEXT
created_by INTEGER
created_at TEXT NOT NULL
UNIQUE(reservation_id, event_no)
```

Event types initially:

```text
created
increased
reduced
consumed
released
cancelled
expired
scope_moved
```

Do not treat this as a second stock movement ledger. Reservation events describe **promise state**, not physical movement.

## 4. Quantity invariant

For every reservation:

```text
remaining = quantity_total - quantity_consumed - quantity_released
```

Require:

```text
quantity_total >= 0
quantity_consumed >= 0
quantity_released >= 0
remaining >= 0
```

Status is derived/validated from quantities and lifecycle rules; do not trust a client-submitted status string.

Examples:

```text
remaining > 0, consumed=0, released=0         -> active
remaining > 0, consumed>0                     -> partially_consumed
remaining > 0, released>0                     -> partially_released
remaining = 0 and consumed=total              -> consumed
remaining = 0 and released=total              -> released
```

Cancellation/expiry require explicit policy/event semantics and cannot resurrect consumed quantity.

## 5. Reservation identity

Every reservation has a stable `reservation_key`.

For controlled tests/manual diagnostic reservations:

```text
manual:<business_operation_id>:<material>:<warehouse>
```

Future order integration should use exact source-line identity, for example conceptually:

```text
order:<order_id>:line:<line_id>:generation:<n>
```

Do not derive key from current timestamp alone.

`reservation_key` is identity/idempotency evidence, not permission.

## 6. Position scope

E02 begins with warehouse-scope reservation by default:

```text
warehouse promise
!= physical bin allocation
```

`position_key` may remain NULL/unallocated for warehouse-level promise.

If a trusted exact position is used in controlled tests, it must come from E02-A canonical identity.

E03 owns physical bin allocation/pick assignment later.

Do not force location allocation in Slice E.

## 7. ATP query contract

Introduce a pure/domain query contract such as:

```text
get_atp(material_id, warehouse_id, optional_position_scope, as_of=None)
```

Return evidence, not only one number:

```text
material_id
warehouse_id
uom_code
eligible_on_hand
active_reserved
safety_buffer
atp
balance_last_operation_id
reservation_count
policy_evidence
calculated_at
mode = shadow
```

Do not expose a naked number without its basis during migration.

## 8. Stock-status eligibility

Only explicitly promise-eligible `stock_balances` rows contribute to ATP.

At Slice E, use the minimal status contract already approved/provisioned by E02-A/C.

Do not invent E07 quality taxonomy prematurely.

If the business policy for a status is unresolved:

```text
exclude it from authoritative promise
or mark ATP policy unresolved in diagnostic output
```

Do not silently treat unknown/hold stock as available.

## 9. Safety-buffer policy

Existing `safety_stock` values are not automatically reinterpreted as the new ATP buffer unless the operator decision explicitly approves that mapping.

Implementation should support an explicit policy resolver:

```text
resolve_safety_buffer(material_id, warehouse_id, context)
```

During Slice E, allowed states:

```text
explicit approved value
zero in deterministic test fixture
unresolved -> diagnostic ATP flagged not production-authoritative
```

Never accept safety buffer from untrusted client payload as authority.

## 10. Reserve command transaction

`reserve_stock()` uses E01 atomic-local idempotency and a short SQLite write transaction.

Conceptually:

```text
BEGIN IMMEDIATE
 -> E01 business-operation admission
 -> validate actor/scope/action policy
 -> resolve canonical material/warehouse/UOM
 -> read authoritative new shadow balance projection
 -> calculate active reservation remaining
 -> resolve explicit safety buffer/policy state
 -> ATP = eligible balance - reserved - buffer
 -> require requested quantity <= ATP
 -> insert reservation current row
 -> append reservation created event
 -> append operation audit/receipt
COMMIT
```

No external call inside the transaction.

Two concurrent reservation attempts for the same free quantity must serialize so both cannot reserve it.

## 11. Increase / reduce / release

### Increase

Re-check current ATP for the incremental quantity inside `BEGIN IMMEDIATE`.

Do not trust ATP calculated earlier by the UI.

### Reduce/release

Release only still-unconsumed quantity.

Append an event and update current reservation totals/status atomically.

Replay with the same business operation returns the original receipt.

### Cancel

Cancellation is a business action, not `DELETE FROM stock_reservations`.

Record event, actor/reason and final state.

A consumed portion remains consumed historically.

## 12. Consume reservation

Slice E implements the reservation-side primitive but does not connect it to a production shipment route yet.

The target atomic contract for later Slice F is already fixed:

```text
BEGIN IMMEDIATE
 -> idempotency
 -> validate active reservation remaining
 -> post physical stock movement
 -> update stock balance
 -> increase reservation consumed quantity
 -> append reservation consume event
 -> audit/receipt
COMMIT
```

Never allow:

```text
consume reservation in transaction A
stock issue in transaction B
```

because crash/retry could separate promise consumption from physical stock.

In Slice E, use isolated fixture movement to prove this transaction shape without migrating customer fulfilment.

## 13. Legacy `quantity_locked` audit

Create a read-only report over current legacy rows where:

```text
quantity_locked != 0
```

Report at least:

```text
legacy inventory row
material
warehouse
platform account/location
quantity_locked
known source reference if deterministically discoverable
classification = traceable | ambiguous | invalid
```

Rules:

- do not create reservation rows from ambiguous locks;
- do not set new reserved total equal to `quantity_locked` merely to make totals match;
- open demand is migrated later from authoritative business objects, not anonymous counters;
- unresolved legacy lock evidence is a cutover blocker or explicit operator disposition item.

## 14. Expiry policy

`expires_at` is nullable and disabled by default for reservation classes without explicit expiry policy.

Do not give confirmed paid/customer orders a generic timeout.

For test/manual temporary reservation classes, deterministic fixture expiry may be used.

Future expiry processing:

```text
E01 durable job/systemd runtime
 -> identify eligible expired reservation
 -> idempotent release/expire command
```

No GitHub Actions dependency.

## 15. Required concurrency proof

Fixture:

```text
eligible_on_hand = 5
safety_buffer = 0
reservation A = 4
reservation B = 4
```

Run A/B with separate SQLite connections/threads.

Require:

```text
only one 4-unit reservation succeeds
other receives deterministic insufficient ATP/conflict result
active reserved total = 4
ATP = 1
no negative ATP caused by race
```

Repeat with idempotent same-key replay and different-key contention.

## 16. Required lifecycle tests

Prove:

1. create 4 from on-hand 5 -> ATP 1;
2. same operation key replay -> one reservation/event only;
3. same key with quantity 3 after original 4 -> idempotency conflict;
4. release 2 -> remaining 2, ATP restores exactly 2;
5. replay same release -> no second restoration;
6. consume 1 through isolated fixture movement -> physical on-hand decreases 1, reservation remaining decreases 1, ATP does **not** double-decrement;
7. consumed quantity cannot be released as free stock;
8. full release/cancel leaves history, row not deleted;
9. unknown/non-eligible stock status contributes zero promise supply;
10. ambiguous legacy `quantity_locked` produces review evidence, not fabricated reservation.

## 17. ATP double-subtraction test

This deserves an explicit regression test.

Example before shipment:

```text
on_hand 10
reservation 4
ATP 6
```

After consuming/issuing 4:

```text
on_hand 6
reservation remaining 0
ATP 6
```

It must **not** become 2 by subtracting the same fulfilled promise twice.

## 18. Shadow-mode UI/API boundary

Allowed in Slice E:

- admin/debug reservation fixture tools;
- read-only ATP comparison endpoint/view clearly labeled `SHADOW`;
- reconciliation/export evidence.

Forbidden:

- normal order page promising availability from new ATP;
- connector publishing new ATP to platforms;
- shipment route requiring reservation;
- customer-facing stock messaging based on shadow ATP.

Those authority transitions belong to later slices.

## 19. Backup/recovery expansion

After Migration 9, E00 recovery verification must include:

```text
stock_reservations
stock_reservation_events
```

Integrity checks should detect:

- reservation references missing material/warehouse;
- consumed/released totals exceeding total;
- invalid status/quantity relationship;
- duplicate reservation key;
- reservation event referencing missing reservation.

Do not wait until final E02 cutover to make the new evidence recoverable.

## 20. Focused files

Expected additions/edits after prior E02 slices:

```text
inventory_app/domains/stock/reservations.py
inventory_app/domains/stock/atp.py
inventory_app/schema_migrations.py          # immutable Migration 9
inventory_app/db_integrity.py
inventory_app/recovery_verifier.py
tools/test_stock_reservations.py
tools/test_stock_atp_concurrency.py
tools/report_legacy_stock_locks.py
tools/verify_release.py
```

Do not migrate order/shipment routes in this PR.

## 21. Gate commands

Focused:

```bash
python3 tools/test_stock_reservations.py
python3 tools/test_stock_atp_concurrency.py
python3 tools/report_legacy_stock_locks.py --check
python3 tools/reconcile_stock_kernel.py --check
python3 tools/verify_release.py
```

Linux release host:

```bash
python3 tools/verify_release.py --require-bash
```

## 22. PR review checklist

```text
[ ] Migration 9 additive/immutable/contiguous
[ ] no fabricated legacy reservations
[ ] Decimal/UOM helper reused
[ ] reservation != physical movement
[ ] current row + immutable event history both coherent
[ ] reserve/increase ATP check occurs under write transaction
[ ] two concurrent reservations cannot oversubscribe
[ ] consume test proves no ATP double subtraction
[ ] no normal order/shipment/channel authority switched
[ ] safety buffer policy explicit/not client-trusted
[ ] new tables included in integrity/recovery checks
[ ] full Release Gate PASS
```

Any `no` blocks merge.

## 23. Rollback

Before Slice F activates reservation authority for orders:

```text
stop shadow reservation/ATP diagnostic usage
revert application behavior if needed
retain Migration 9 tables/evidence
```

Do not drop reservations/events destructively.

If any real controlled reservation exists, it remains evidence even if authority has not moved to customer-order workflows.

## 24. Exit / unlock

Slice E completes when:

```text
Reservation lifecycle is durable/idempotent
ATP formula is evidence-backed
concurrency proves no double reservation
consume/release math is exact
legacy anonymous locks are honestly reported
new tables are backup/recovery verified
normal customer promise still remains unchanged
```

Then unlock:

```text
E02 Slice F — Order / Shipment Reservation Integration
```
