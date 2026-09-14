> Execution target: **ZXYHtech/inventory-Pro** only. Read [repository isolation](../REPOSITORY_ISOLATION.md) before acting; old production/PR instructions below are superseded.

# E02 Execution Packets Index — Stock Truth / Reservation / ATP

## Status

`ALL_E02_EXECUTION_PACKETS_READY_BLOCKED_BY_E00_E01_E11_GATES`

This is the direct handoff index for implementing E02 after E00, E01 and the early E11 pricing-safety bridge are complete.

## Entry gate

Do not start E02 runtime work until:

```text
E00 real Release Gate PASS + merged
E01 A-F complete/merged
E11-A pricing semantics complete
E11-B floor/override safety complete
full current-main Release Gate PASS
```

Each slice branches from then-current `main`.

## Canonical migrations before E02

```text
1  E00 baseline
2  E01 business_operations
3  E01 jobs + job_attempts
4  E01 outbox_events
5  E01 operation_logs.correlation_id
6  E11 pricing.floor_override permission
```

## Slice A — Stock Identity / UOM

Packet:

`E02_SLICE_A_EXECUTION_PACKET.md`

Branch:

`impl/e02-stock-identity`

Migration:

`NONE`

Purpose:

- define canonical stock-position identity;
- define Decimal/UOM contract;
- map every legacy inventory row or flag ambiguity;
- never guess platform-account ownership or missing locations.

Unlocks B.

## Slice B — Immutable Movement Ledger

Packet:

`E02_SLICE_B_EXECUTION_PACKET.md`

Branch:

`impl/e02-movement-ledger`

Migration:

```text
7 = stock_movement_operations + stock_movement_lines
```

Purpose:

- immutable stock operation/line evidence;
- explicit FROM/TO direction;
- idempotent effect fingerprint;
- compensating reversal;
- isolated fixtures first.

Important: B alone does not prove overspend prevention because Balance Projection is not yet active.

Unlocks C.

## Slice C — Balance Projection / Opening Reconciliation

Packet:

`E02_SLICE_C_EXECUTION_PACKET.md`

Branch:

`impl/e02-stock-projection`

Migration:

```text
8 = stock_balances projection
```

Purpose:

- current-balance projection;
- opening-balance import with provenance;
- rebuild-to-temp;
- reconciliation L1/L2/L3;
- first legitimate concurrent-negative-balance proof.

Ordinary business reads remain legacy-authoritative.

Unlocks D.

## Slice D — Same-transaction Shadow Posting

Packet:

`E02_SLICE_D_EXECUTION_PACKET.md`

Branch:

`impl/e02-shadow-stock`

Migration:

`NONE`

First real pilot:

```text
POST /api/inventory/adjust
```

Authority:

```text
legacy = business truth
E02 movement/balance = shadow
```

Critical rule:

```text
legacy mutation + legacy log + new movement + new balance
commit or rollback together
```

No async shadow writer.

Unlocks E.

## Slice E — Reservation / ATP Shadow Kernel

Packet:

`E02_SLICE_E_EXECUTION_PACKET.md`

Branch:

`impl/e02-reservation-atp`

Migration:

```text
9 = stock_reservations + stock_reservation_events
```

Purpose:

- reservation current state + immutable event evidence;
- warehouse-scope promise;
- ATP = eligible on-hand - active reservation - explicit buffer;
- concurrency/no-double-reservation proof;
- legacy quantity_locked audit;
- still diagnostic/shadow for ordinary customer promise.

Unlocks F.

## Slice F — Order / Shipment Reservation Authority Pilot

Packet:

`E02_SLICE_F_EXECUTION_PACKET.md`

Suggested branches:

```text
impl/e02-order-reservation-fixed-warehouse
impl/e02-order-reservation-open-pool
impl/e02-shipment-reservation-consume
```

Critical correction:

```text
ShipmentService.ship = physical stock issue integration point
```

not only `complete()`.

`complete()` must never double issue/consume.

Rules:

- OCR/unconfirmed candidate never reserves;
- open-pool demand reserves only after authoritative warehouse acceptance;
- shipment issue + balance + reservation consume + shipment state are atomic;
- pre-ship cancel releases promise only;
- post-ship reversal restores physical stock by compensating movement.

Unlocks G.

## Slice G — Transfer Issue / In-transit / Receipt

Packet:

`E02_SLICE_G_EXECUTION_PACKET.md`

Suggested branches:

```text
impl/e02-transfer-issue
impl/e02-transfer-receipt
impl/e02-transfer-reversal
```

Model:

```text
source available
 -> transfer_issue
 -> transfer-specific in-transit
 -> partial/full transfer_receipt
 -> destination
```

Critical migration rule:

- old receipt code may backfill missing source-out evidence;
- E02 authoritative receipt may **not** do this;
- missing transfer_issue becomes reconciliation blocker.

Unlocks H.

## Procurement safety prerequisite before H

File:

`PURCHASE_PARTIAL_RECEIPT_LANDED_COST_SAFETY_REVIEW.md`

Static code review found a credible risk that every partial receipt may reallocate the full PO header `freight_amount + other_amount`.

E02-H starts only after:

```text
fixture proves current semantics intentionally correct
OR
a bounded landed-cost partial-receipt fix is merged + Gate PASS
```

Do not hide this cost correction inside the stock-ledger PR.

## Slice H — Purchase Receipt Stock Integration

Packet:

`E02_SLICE_H_EXECUTION_PACKET.md`

Branch:

`impl/e02-purchase-receipt-stock`

Migration:

`NONE expected`

Purpose:

- PO/receipt/receipt item identity preserved;
- physical receipt posts E02 stock exactly once;
- partial receipt supported;
- concurrent remaining-receivable check;
- over-receipt rejected by default;
- PO/receipt/cost-required evidence/stock state commit together.

No E03 putaway or E07 IQC/lot expansion.

Unlocks I.

## Slice I — Manual Adjustment / Count Bridge

Packet:

`E02_SLICE_I_EXECUTION_PACKET.md`

Suggested branches:

```text
impl/e02-adjustment-authority
impl/e02-count-adjustment-bridge
```

Migration:

`NONE expected`

Purpose:

- turn Slice-D manual adjustment from shadow into E02 authority;
- legacy inventory becomes compatibility projection for this path;
- set-to quantity computes delta server-side under transaction;
- count observation remains observation;
- approved count difference posts explicit `count_adjustment` movement;
- direct legacy stock-writer scan becomes release evidence.

Count snapshot drift policy must be explicit before changing current count approval arithmetic.

Unlocks J.

## Slice J — Global Authoritative Cutover

Packet:

`E02_SLICE_J_EXECUTION_PACKET.md`

Branch:

`impl/e02-stock-cutover`

Migration:

`NONE expected; Migration 10 only if a separately reviewed final structural constraint is genuinely required`

This is the only slice allowed to declare E02 globally authoritative.

Production cutover:

```text
fresh deployed-code snapshot
 -> fresh DB backup
 -> isolated restore proof
 -> quiesce writers
 -> final physical/reservation/transfer/receipt/count reconciliation
 -> migrate justified open promises/current transfer state
 -> resolve legacy locks
 -> set stock_kernel_authority=e02_v1
 -> technically fence direct legacy writes
 -> switch read authority to stock_balances/reservations/ATP
 -> integrity + smoke
 -> restart workers
 -> stabilization monitoring
```

Rollback after post-cutover transactions cannot mean deploying pre-E02 code that ignores new evidence.

## Canonical E02 migration chain

```text
7 movement ledger
8 balance projection
9 reservations + reservation events
10+ only when a later approved slice genuinely needs additive schema
```

Never edit a migration already recorded.

## Universal E02 stop conditions

Stop a slice if:

- legacy stock identity requires guessing;
- Movement/Balance diverge;
- reservation concurrency oversubscribes;
- promise consumption and physical issue cannot be atomic;
- transfer receipt lacks authoritative issue evidence;
- purchase receipt commercial-cost ambiguity is unresolved;
- count approval policy cannot safely handle stock movement during count;
- unnamed direct legacy writers remain before cutover;
- recovery verifier does not cover E02 truth;
- rollback requires deleting posted evidence.

## E02 completion

E02 is complete only after Slice J produces retained production/staging-authorized evidence that:

```text
Movement Ledger = authoritative stock change truth
Balance Projection = authoritative current stock
Reservation = authoritative committed promise
ATP = authoritative promise availability
Shipment/Transfer/Purchase/Manual/Count all use one kernel
legacy direct mutation is fenced
backup/restore proves E02 evidence recoverable
```

Then unlock E03 warehouse execution.