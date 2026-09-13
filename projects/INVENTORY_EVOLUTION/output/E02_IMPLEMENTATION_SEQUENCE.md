# E02 Implementation Sequence — Shadow First, Cut Over Last

## Status

`READY_AFTER_E00_E01_E11_GATES`

## Entry condition

Do not create E02 runtime implementation until all are true:

```text
E00 Release Gate PASS and PR #3 merged
E01 slices complete/merged
E11-S01 pricing semantics safety complete
E11-S02 floor/override safety complete
full current-main Release Gate PASS
```

Branch every E02 slice from the then-current `main`.

Canonical migrations before E02:

```text
1 E00 baseline
2 E01 business_operations
3 E01 jobs + job_attempts
4 E01 outbox_events
5 E01 operation_logs.correlation_id
6 E11 pricing.floor_override permission
```

## Slice A — Stock Identity / UOM Contract

Execution packet:

`E02_SLICE_A_EXECUTION_PACKET.md`

Suggested branch:

```text
impl/e02-stock-identity
```

Migration:

```text
NONE
```

Scope:

- E02-S01;
- canonical position identity helpers/contracts;
- legacy inventory mapping report;
- decimal/UOM policy helpers;
- no production stock ownership change.

Gate:

- every legacy inventory row maps deterministically or is explicitly flagged;
- null/unassigned scopes normalize safely;
- platform-account physical ownership is never guessed;
- no quantity is dropped/merged silently;
- full Release Gate.

Rollback: pure/additive.

## Slice B — Movement Ledger

Execution packet:

`E02_SLICE_B_EXECUTION_PACKET.md`

Suggested branch:

```text
impl/e02-movement-ledger
```

Migration:

```text
7 = stock_movement_operations + stock_movement_lines
```

Scope:

- E02-S02;
- additive immutable movement evidence;
- effect fingerprint / operation-key replay protection;
- explicit endpoint direction;
- immutable reversal model;
- isolated fixture posting only at first;
- no production-authoritative route migration.

Critical tests:

- one operation posts once;
- multi-line atomicity;
- same key/different fingerprint conflicts;
- line validation failure rolls back all evidence;
- reversal/partial reversal bounded;
- original movement remains immutable.

Important boundary:

```text
Slice B does NOT yet prove authoritative negative-stock/concurrent overspend prevention,
because stock_balances projection is not authoritative until Slice C.
```

That concurrency gate moves to Slice C.

## Slice C — Balance Projection + Opening Migration

Execution packet:

`E02_SLICE_C_EXECUTION_PACKET.md`

Suggested branch:

```text
impl/e02-stock-projection
```

Migration:

```text
8 = stock_balances projection + required indexes/constraints
```

If implementation discovers the need to split projection/index changes into multiple migrations, stop and update the canonical migration plan before consuming Migration 9.

Scope:

- E02-S03;
- additive `stock_balances` projection;
- opening-balance importer;
- deterministic reconciliation command/report;
- rebuild-to-temp tooling;
- atomic ledger + projection posting for isolated/new-kernel fixtures.

Do not switch UI/business reads yet.

Gate:

```text
legacy opening totals == new opening totals
projection rebuild == live projection
unresolved opening mapping = 0 before shadow pilot
concurrent spend against projection cannot overspend
negative resulting physical balance is rejected by kernel
```

## Slice D — Same-transaction Shadow Posting Pilot

Execution packet:

`E02_SLICE_D_EXECUTION_PACKET.md`

Suggested branch:

```text
impl/e02-shadow-stock
```

Migration:

```text
NONE
```

First pilot:

```text
POST /api/inventory/adjust
```

Scope:

- legacy `inventory`/`inventory_logs` remain authoritative;
- selected adjustment path also emits Movement Ledger + Balance Projection shadow evidence;
- legacy and new effects occur in the same SQLite transaction;
- E02-A canonical identity mapping is reused;
- narrow affected-row parity assertion before commit;
- normal UI/business readers still use legacy quantity.

Critical gates:

- forced shadow failure rolls legacy DML/logs back too;
- forced legacy failure leaves no shadow residue;
- lost-response retry does not double legacy or shadow effects;
- no async/best-effort shadow writer;
- zero unexplained divergence through deterministic fixtures and agreed observation window.

Do not migrate shipment/transfer/procurement in Slice D.

## Slice E — Reservation / ATP Shadow Kernel

Execution packet:

`E02_SLICE_E_EXECUTION_PACKET.md`

Suggested branch:

```text
impl/e02-reservation-atp
```

Migration:

```text
9 = stock_reservations + stock_reservation_events
```

Scope:

- E02-S04;
- durable reservation current state + immutable lifecycle events;
- Decimal/UOM quantities;
- warehouse-scope promise before E03 bin allocation;
- ATP query with balance/reservation/buffer evidence;
- reserve/increase/release/consume primitives;
- legacy `quantity_locked` audit/report;
- initially diagnostic/shadow mode only.

Critical tests:

- two concurrent reservations cannot oversubscribe one free balance;
- same idempotency key produces one reservation/event effect;
- same key/different quantity conflicts;
- partial/full release restores ATP exactly once;
- consume + physical fixture movement does not double-subtract ATP;
- unknown/non-eligible status contributes no promise supply;
- ambiguous legacy locks are reported, never fabricated.

Important authority boundary:

```text
Slice E does NOT yet change normal customer-order/shipment/channel promise behavior.
```

That starts only in Slice F.

## Slice F — Order / Shipment Reservation Integration

Suggested branch:

```text
impl/e02-order-reservation
```

Scope:

- E02-S05;
- confirmed/committed demand creates reservation under explicit order policy;
- shipment issue consumes reservation + posts physical movement + updates balance atomically;
- cancellation/reassignment/reversal releases/restores promise correctly;
- platform sync remains E01 Outbox-based;
- migrate one shipment lifecycle path at a time.

Mandatory invariant:

```text
reservation consume
+ shipment movement
+ balance update
+ shipment/order state
+ audit/result receipt
= one business transaction
```

No `consume reservation` in one commit and `deduct stock` in another.

## Slice G — Transfer Integration

Suggested branch:

```text
impl/e02-transfer-stock
```

Scope:

- E02-S06 transfer portion;
- source issue -> explicit in-transit -> destination receipt;
- partial receipt/exception/reversal;
- compatibility with existing transfer receipt events.

Do not collapse transport time into one instantaneous warehouse-to-warehouse movement.

## Slice H — Procurement Receipt Integration

Suggested branch:

```text
impl/e02-purchase-receipt-stock
```

Scope:

- E02-S06 purchase portion;
- approved PO/receipt identity -> stock receipt movement;
- retry/over-receipt policy;
- no IQC/lot/putaway redesign yet.

## Slice I — Manual Adjustment / Count Bridge

Suggested branch:

```text
impl/e02-adjustment-bridge
```

Scope:

- manual adjustment becomes authoritative explicit movement;
- set-to quantity computes server-side delta;
- existing count reconciliation uses movement bridge;
- count observation remains separate from balance mutation;
- retire Slice D shadow-only adapter for this path only after parity evidence.

## Slice J — Authoritative Cutover

Suggested branch:

```text
impl/e02-stock-cutover
```

Scope:

- E02-S07;
- final parity report;
- authoritative open-state reservation migration;
- authority switch;
- direct legacy write fencing;
- compatibility reads/writes only where documented;
- backup/recovery verifier expanded for all E02 evidence tables.

This is the only slice allowed to declare E02 authoritative globally.

## Mandatory cutover gate

```text
fresh production prechange code snapshot PASS
fresh production SQLite backup PASS
isolated restore PASS
final legacy/new reconciliation PASS
open-order reservation migration PASS
legacy lock ambiguity disposed/reviewed
unresolved divergence = 0
forbidden direct legacy writer scan PASS
full Release Gate PASS
```

If any fail, stay on old authority.

## Canonical migration numbering

Prepared migration chain through Slice E:

```text
1  E00 baseline
2  E01 business_operations
3  E01 jobs + job_attempts
4  E01 outbox_events
5  E01 operation_logs.correlation_id
6  E11 pricing.floor_override permission
7  E02 stock movement operations + lines
8  E02 stock_balances projection
9  E02 stock_reservations + reservation events
10+ later additive E02 migrations only when an approved slice requires them
```

Never edit/reuse a migration already recorded in production.

If implementation discovers Migration 8 genuinely needs to split, stop before publishing Migration 9 and update the canonical chain explicitly; do not silently renumber after release.

## Merge discipline

Every slice:

```text
current main
 -> small branch
 -> deterministic focused tests
 -> existing regressions
 -> full tools/verify_release.py
 -> PR review
 -> merge
 -> next slice starts from new main
```

Do not stack A–J into one branch.

## Explicit stop conditions

Stop the current slice and document a blocker if any of these appear:

- legacy stock identity cannot be mapped without guessing;
- shadow divergence cannot be explained;
- reservation concurrency test oversubscribes;
- reservation consume and physical issue cannot be made atomic;
- a migrated route still has an independent direct balance writer;
- rollback would require discarding posted stock/reservation evidence;
- production backup/recovery verifier does not include the new stock truth tables.

## Exit condition

E02 is complete only after Slice J cutover and stabilization evidence prove:

```text
movement ledger authoritative
balance projection reconciled
reservations authoritative for order promise
all supported stock-changing paths use one kernel
legacy direct writes fenced
recovery path verified
```