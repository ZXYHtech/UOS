# Post-E00 Runtime Execution Handoff

## Status

`READY_TO_EXECUTE_AFTER_E00_REAL_GATE`

This is the shortest operational handoff for moving from the current E00 draft implementation into actual post-E00 business/runtime development.

## Current E00 external state

Inventory PR:

```text
repo: ZXYHtech/inventory
PR: #3
branch: impl/e00-release-safety
head: 0e0870499f7e8b5e68a308231eae954f106bd5aa
state: open
Draft: true
mergeable: true (informational only)
merged: false
```

`mergeable=true` is not completion evidence.

## Mandatory E00 gate

From a real checkout of the exact PR head:

```bash
git fetch origin
git switch impl/e00-release-safety
git pull --ff-only origin impl/e00-release-safety
git rev-parse HEAD
python3 tools/verify_release.py
python3 tools/verify_release.py --require-bash
```

Required:

```text
exact tested head recorded
both required commands exit 0 / PASS
no unresolved review blocker
```

Then merge PR #3.

Before any production server cutover, independently run fresh pre-change protection:

```text
exact deployed-code snapshot
+ production DB consistent backup
+ isolated restore verification
+ manifest/checksums
+ off-host Recovery Bundle when configured
```

Do not reuse an old development/test backup as production rollout proof.

# Runtime execution chain after E00 merge

## E01-A — Shared Context / Action Policy
Packet: `E01_SLICE_A_EXECUTION_PACKET.md`  
Branch: `impl/e01-platform-policy`  
Migration: `NONE`

## E01-B — Business-operation idempotency
Packet: `E01_SLICE_B_EXECUTION_PACKET.md`  
Branch: `impl/e01-idempotency`

```text
Migration 2 = business_operations
```

## E01-C — Consequential pilots
Packet: `E01_SLICE_C_EXECUTION_PACKET.md`

```text
impl/e01-pilot-transfer-receive
 -> impl/e01-pilot-purchase-receive
 -> impl/e01-pilot-shipment-complete
```

Each pilot runs the full gate before the next.

## E01-D — Durable Jobs
Packet: `E01_SLICE_D_EXECUTION_PACKET.md`  
Branch: `impl/e01-durable-jobs`

```text
Migration 3 = jobs + job_attempts
```

## E01-E — Transactional Outbox / Correlation
Packet: `E01_SLICE_E_EXECUTION_PACKET.md`  
Branch: `impl/e01-outbox-correlation`

```text
Migration 4 = outbox_events
Migration 5 = operation_logs.correlation_id
```

## E01-F — Bounded modular extraction
Packet: `E01_SLICE_F_EXECUTION_PACKET.md`

```text
impl/e01-domain-backup
impl/e01-domain-pricing
impl/e01-domain-procurement
impl/e01-domain-integrations
```

No Stock semantics in this refactor. Pricing extraction preserves behavior before E11.

# Mandatory early E11 bridge

Index: `E11_EARLY_EXECUTION_PACKETS_INDEX.md`

## E11-A — Pricing semantics
Packet: `E11_SLICE_A_EXECUTION_PACKET.md`  
Branch: `impl/e11-pricing-semantics`  
Migration: `NONE`

Hard invariant:

```text
historical margin_percent arithmetic unchanged
```

## E11-B — Floor / override safety
Packet: `E11_SLICE_B_EXECUTION_PACKET.md`  
Branch: `impl/e11-floor-safety`

```text
Migration 6 = pricing.floor_override permission definition
```

Migration 6 grants the permission to no role by default.

# E02 runtime chain

## E02-A — Stock Identity / UOM
Packet: `E02_SLICE_A_EXECUTION_PACKET.md`  
Branch: `impl/e02-stock-identity`  
Migration: `NONE`

Outputs:

```text
canonical stock-position identity
Decimal/UOM contract
legacy identity mapping report
explicit review/block flags
```

## E02-B — Immutable Movement Ledger
Packet: `E02_SLICE_B_EXECUTION_PACKET.md`  
Branch: `impl/e02-movement-ledger`

```text
Migration 7 = stock_movement_operations + stock_movement_lines
```

No production stock authority cutover.

## E02-C — Balance Projection / Opening Reconciliation
Packet: `E02_SLICE_C_EXECUTION_PACKET.md`  
Branch: `impl/e02-stock-projection`

```text
Migration 8 = stock_balances projection
```

First slice that may honestly prove concurrent spend cannot overspend the new balance projection. Ordinary business reads remain legacy-authoritative.

## E02-D — Same-transaction Shadow Posting
Packet: `E02_SLICE_D_EXECUTION_PACKET.md`  
Branch: `impl/e02-shadow-stock`  
Migration: `NONE`

First pilot:

```text
POST /api/inventory/adjust
```

Legacy inventory remains authority. Legacy DML + legacy logs + new Movement/Balance shadow evidence commit or roll back together.

## E02-E — Reservation / ATP Shadow Kernel
Packet: `E02_SLICE_E_EXECUTION_PACKET.md`  
Branch: `impl/e02-reservation-atp`

```text
Migration 9 = stock_reservations + stock_reservation_events
```

Reservation/ATP are durable and concurrency-tested but remain diagnostic/shadow for normal customer promise.

## E02-F — Order / Shipment Reservation Authority Pilot
Packet: `E02_SLICE_F_EXECUTION_PACKET.md`

Suggested branch family:

```text
impl/e02-order-reservation-fixed-warehouse
impl/e02-order-reservation-open-pool
impl/e02-shipment-reservation-consume
```

Critical authority boundary:

```text
ShipmentService.ship
 = physical shipment_issue movement
 + stock balance change
 + reservation consume
 + shipped state
one transaction
```

`ShipmentService.complete` cannot create a second stock issue/consume. OCR/unconfirmed demand never reserves stock, and open-pool tasks reserve only when a warehouse is authoritatively selected/accepted.

# Canonical migration sequence through E02-E

```text
1  baseline_current_schema_20260810          E00
2  business_operations                       E01-B
3  jobs + job_attempts                       E01-D
4  outbox_events                             E01-E
5  operation_logs.correlation_id             E01-E
6  pricing.floor_override permission         E11-B
7  stock movement operation/line ledger      E02-B
8  stock_balances projection                 E02-C
9  stock_reservations + reservation events   E02-E
10+ only as explicitly approved by later slices
```

Never reuse/edit an already-recorded migration.

# Remaining E02 sequence

```text
E02-G Transfer Integration
 -> E02-H Procurement Receipt Integration
 -> E02-I Manual Adjustment / Count authoritative bridge
 -> E02-J final authority cutover / legacy direct-write fencing
```

See `E02_IMPLEMENTATION_SEQUENCE.md` for the dependency/gate contract.

# Universal PR discipline

Every runtime slice:

```text
current merged main
 -> small dedicated branch
 -> focused deterministic tests
 -> existing regressions
 -> tools/verify_release.py
 -> Linux shell gate where applicable
 -> PR review
 -> merge
 -> next branch from new main
```

Do not stack the whole program onto one long-lived feature branch.

# Universal stop conditions

Stop and split/escalate if any PR begins to require:

- guessing unresolved legacy stock/account/location semantics;
- external network I/O inside SQLite business transaction;
- hidden permission expansion;
- silently changing historical pricing arithmetic;
- consuming reservation separately from physical issue;
- direct stock balance writes outside the E02 migration plan;
- destructive deletion of evidence/history;
- microservices/Redis/Kafka/Kubernetes merely to implement current scope;
- bypassing fresh production code+DB backup/recovery before server cutover.

# Immediate next action

The project is no longer blocked by lack of design/execution detail.

Immediate action remains exactly:

```text
run E00 real-checkout Release Gate
 -> review result
 -> merge E00 only if PASS
 -> start E01-A
```

Everything after that already has a bounded implementation handoff.