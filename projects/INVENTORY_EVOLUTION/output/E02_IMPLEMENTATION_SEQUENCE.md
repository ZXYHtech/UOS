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

Suggested branch:

```text
impl/e02-stock-projection
```

Expected next migration:

```text
8 = stock_balances projection + required indexes/constraints
```

If implementation discovers the need to split projection/index changes into multiple migrations, keep them contiguous starting at 8 and update this sequence before merge.

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

## Slice D — Shadow Posting Pilot

Suggested branch:

```text
impl/e02-shadow-stock
```

Scope:

- choose one existing stock-changing path;
- legacy path remains authoritative;
- emit shadow movement + projection in the same SQLite transaction;
- record reconciliation evidence.

Preferred first pilot:

```text
manual/test-controlled adjustment
```

before shipment/transfer/procurement.

Gate:

- no divergence through deterministic fixture set;
- forced failure rolls legacy + shadow changes back together;
- no async best-effort shadow gaps.

## Slice E — Reservation / ATP

Suggested branch:

```text
impl/e02-reservation-atp
```

Expected migration after projection migrations:

```text
next contiguous migration = stock_reservations + indexes
```

Scope:

- E02-S04;
- additive `stock_reservations`;
- reservation lifecycle/ATP queries;
- initially isolated/shadow mode;
- no customer promise authority until concurrency tests pass.

Critical tests:

- two concurrent reservations cannot oversubscribe;
- release/consume exact-once;
- ATP formula deterministic;
- ambiguous legacy lock not fabricated.

## Slice F — Order / Shipment Integration

Suggested branch:

```text
impl/e02-order-reservation
```

Scope:

- E02-S05;
- confirmed demand creates reservation;
- shipment completion consumes reservation + posts movement atomically;
- cancellation/reassignment/reversal integration;
- platform sync remains Outbox-based.

Migrate one shipment path at a time and run full Release Gate after each.

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

- manual adjustment becomes explicit movement;
- set-to quantity computes server-side delta;
- existing count reconciliation uses movement bridge;
- count observation remains separate from balance mutation.

## Slice J — Authoritative Cutover

Suggested branch:

```text
impl/e02-stock-cutover
```

Scope:

- E02-S07;
- final parity report;
- open-state reservation migration;
- authority switch;
- direct legacy write fencing;
- compatibility reads/writes only where documented;
- backup/recovery verifier expanded for all E02 tables.

This is the only slice allowed to declare E02 authoritative.

## Mandatory cutover gate

```text
fresh production prechange code snapshot PASS
fresh production SQLite backup PASS
isolated restore PASS
final legacy/new reconciliation PASS
open-order reservation migration PASS
unresolved divergence = 0
forbidden direct legacy writer scan PASS
full Release Gate PASS
```

If any fail, stay on old authority.

## Migration numbering rule

Migration numbers are now anchored through version 7 by the prepared execution chain.

```text
1-6 fixed before E02
7 movement ledger
8 expected balance projection
9+ reservations / later additive stock migrations as actually approved
```

If Slice C or later needs more than one migration, allocate the next contiguous number and update this document before merging. Never edit/reuse a migration already recorded in production.

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
- a migrated route still has an independent direct balance writer;
- rollback would require discarding posted stock evidence;
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