# INVENTORY_EVOLUTION — Implementation Status

## Current state

**Phase:** E00 Release Safety / Migration / Recovery Foundation  
**E00 implementation:** `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`  
**E01:** `DESIGN_READY_BLOCKED_BY_E00_GATE`  
**E11-S01/S02 early bridge:** `DESIGN_READY_BLOCKED_BY_E01`  
**E02:** `DESIGN_READY_BLOCKED_BY_E00_E01_E11_GATES`  
**E03:** `DESIGN_READY_BLOCKED_BY_E02_FOUNDATION`

External implementation:

- repo: `ZXYHtech/inventory`
- audited pre-E00 baseline/main: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`
- frozen pre-audit branch: `backup/pre-e00-audit-20260911`
- E00 implementation branch: `impl/e00-release-safety`
- reviewed E00 head: `0e0870499f7e8b5e68a308231eae954f106bd5aa`
- PR: `ZXYHtech/inventory#3`
- latest connector state checked 2026-09-11: `open`, `draft=true`, `mergeable=true`, `merged=false`

Do **not** mark E00 complete until the repository-local Release Gate is executed from a real checkout.
Do **not** claim the production DB has already been backed up; production backup evidence only exists after the production host (or explicitly authorized copy) actually runs the preflight/update path.

## Mandatory production-change protection

See `PRODUCTION_CHANGE_SAFETY_POLICY.md`.

Current contract:

```text
frozen pre-audit Git source
 -> confirm production DB exists
 -> require existing git/python3 bootstrap tools
 -> clone target into /tmp only
 -> narrow compile gate for backup/recovery tooling
 -> snapshot exact currently deployed server code
 -> consistent SQLite production snapshot
 -> isolated DB restore verification
 -> manifest/checksums
 -> off-host Recovery Bundle when configured/required
 -> stop backup/OCR/Web writers
 -> only now allow apt/pip runtime changes
 -> full repository Release Gate
 -> rsync target code
 -> numbered migration + integrity postflight
 -> restart + health
```

`INVENTORY_PREFLIGHT_ONLY=1` executes fresh backup/recovery proof and the target Release Gate on currently installed dependencies, then exits before apt/pip, service stop, code sync or production schema migration.

## E00 coverage

| Story | Code | Runtime validation | Evidence |
|---|---|---|---|
| E00-S01 migration registry/baseline adoption | Implemented | Awaiting real checkout | `TASK_INV_IMPL_E00_S01.md` |
| E00-S02 historical DB fixtures | Implemented | Awaiting real checkout | `TASK_INV_IMPL_E00_S02.md` |
| E00-S03 integrity/orphan checks | Implemented + expanded | Awaiting real checkout | `TASK_INV_IMPL_E00_S03.md` |
| E00-S04 authoritative Release Gate | Implemented + fail-closed | Awaiting real checkout | `TASK_INV_IMPL_E00_S04.md` |
| E00-S05 isolated restore verification | Implemented + transaction-aligned | Awaiting real checkout | `TASK_INV_IMPL_E00_S05.md` |
| E00-S06 recovery manifest/checksums/config | Implemented + expanded | Awaiting real checkout | `TASK_INV_IMPL_E00_S06.md` |
| E00-S07 off-host copy/health/scheduler | Implemented + fail-closed | Awaiting real checkout | `TASK_INV_IMPL_E00_S07.md` |

## Required E00 gate

From a real checkout of `impl/e00-release-safety` at the current reviewed head:

```bash
python3 tools/verify_release.py
```

Linux strict profile:

```bash
python3 tools/verify_release.py --require-bash
```

When Node is an agreed release-host dependency:

```bash
python3 tools/verify_release.py --require-bash --require-node
```

Any failure keeps E00 open. Detailed handoff: `E00_LOCAL_VERIFICATION_HANDOFF.md`.

# E01 — prepared but blocked

Prepared stories:

```text
TASK_INV_IMPL_E01_S01.md  Shared API/domain primitives
TASK_INV_IMPL_E01_S02.md  Action Policy registry
TASK_INV_IMPL_E01_S03.md  Pilot high-risk routes
TASK_INV_IMPL_E01_S04.md  Business operation / idempotency
TASK_INV_IMPL_E01_S05.md  Durable jobs
TASK_INV_IMPL_E01_S06.md  Worker CLI/service
TASK_INV_IMPL_E01_S07.md  Retry / dead-letter / manual-review
TASK_INV_IMPL_E01_S08.md  Transactional outbox
TASK_INV_IMPL_E01_S09.md  Correlation propagation
TASK_INV_IMPL_E01_S10.md  Modular-monolith extraction
```

Pilot bindings to existing business services:

```text
transfer.receive  -> TransferService.receive
purchase.receive  -> ProcurementService.receive
shipment.complete -> ShipmentService.complete
```

Implementation order is intentionally:

```text
S01/S02
 -> S04 idempotency primitive
 -> S03 consequential pilots
 -> S05/S06/S07 durable worker/retry
 -> S08/S09 outbox/correlation
 -> S10 bounded extraction
```

`E01_IMPLEMENTATION_SEQUENCE.md` defines the small-PR merge/gate strategy.

Proposed E01 migrations after E00:

```text
Migration 1 = audited E00 baseline adoption
Migration 2 = business_operations
Migration 3 = jobs + job_attempts
Migration 4 = outbox_events
Migration 5 = operation_logs.correlation_id
```

Exact later migration numbers must follow the actual contiguous merged history rather than design-document guesses.

# E11-S01/S02 — early pricing safety bridge

The master project plan explicitly places limited pricing safety before the stock-kernel rewrite.

Prepared:

```text
TASK_INV_IMPL_E11_S01.md  Pricing Formula Semantics & Legacy Rule Safety
TASK_INV_IMPL_E11_S02.md  Floor Price / Deal-price Override Safety
```

Confirmed current risk:

```text
PricingService result_type='margin_percent'
currently computes list_price * (1 + percent/100)
```

This is a base/list-price uplift, not target gross-margin pricing.

S01 therefore preserves historical arithmetic for legacy stored rules while introducing explicit new semantics. S02 strengthens existing deal-price revision history with server-side floor resolution, dedicated override authority, reason and evidence.

Do not build full order economics/settlement early; this bridge is only formula terminology + floor safety.

# E02 — fully decomposed design, runtime blocked

Prepared master/story set:

```text
TASK_INV_IMPL_E02.md      Stock Position / Movement / Reservation master contract
TASK_INV_IMPL_E02_S01.md  Canonical Stock Identity & Quantity/UOM
TASK_INV_IMPL_E02_S02.md  Movement Operation/Line Ledger & Reversal
TASK_INV_IMPL_E02_S03.md  Balance Projection / Shadow / Reconciliation
TASK_INV_IMPL_E02_S04.md  Reservation Lifecycle & ATP
TASK_INV_IMPL_E02_S05.md  Order / Shipment Reservation Integration
TASK_INV_IMPL_E02_S06.md  Transfer / Procurement / Manual-adjust Migration
TASK_INV_IMPL_E02_S07.md  Authoritative Cutover / Legacy-write Retirement
E02_IMPLEMENTATION_SEQUENCE.md
```

E02 core architecture:

```text
Movement Ledger = why/how stock changed
Balance Projection = current physical quantity
Reservation = committed promise
ATP = quantity still promiseable
```

Confirmed legacy reasons for redesign:

- current stock identity excludes `location_id`;
- nullable `platform_account_id` weakens logical uniqueness;
- `adjust_inventory()` is read/compute/update plus `inventory_logs` rather than canonical movement-operation identity;
- no first-class order reservation links committed demand to quantity;
- `quantity_locked` / `quantity_on_transfer` cannot substitute for durable business-linked reservations/movements.

E02 uses a **shadow-first, cutover-last** migration:

```text
identity mapping
 -> additive movement ledger
 -> opening balance + balance projection
 -> same-transaction shadow posting
 -> reconciliation/parity window
 -> reservation/ATP
 -> order/shipment integration
 -> transfer/procurement/manual-adjust integration
 -> final cutover
 -> fence direct legacy writes
```

Only E02-S07 / Slice J may declare the new stock kernel authoritative.

No historical bins/lots/serials/reservations are fabricated during migration.

# E03 — warehouse execution design ready, runtime blocked

Prepared:

```text
TASK_INV_IMPL_E03.md      Warehouse execution master contract
TASK_INV_IMPL_E03_S01.md  Stable Warehouse Location Identity
TASK_INV_IMPL_E03_S02.md  Receiving Staging and Putaway
TASK_INV_IMPL_E03_S03.md  Typed Scan Resolution
TASK_INV_IMPL_E03_S04.md  Exact Bin Allocation and Scan-first Picking
TASK_INV_IMPL_E03_S05.md  Location-aware Count Observation and Reconciliation
TASK_INV_IMPL_E03_S06.md  Cycle Count and Simple Warehouse Policies
TASK_INV_IMPL_E03_S07.md  Mobile / Handheld Scan Execution UX
E03_IMPLEMENTATION_SEQUENCE.md
```

Existing strengths are intentionally reused:

- `warehouse_locations` / `warehouse_layout_items`;
- shipment scan evidence;
- `inventory_count_sessions` / `inventory_count_items`;
- the existing material code/alias/barcode/QR matcher;
- current count approval behavior that posts variance through the inventory mutation path rather than directly overwriting a balance.

E03 architecture:

```text
E03 task / scan / observation
 -> validates warehouse execution
 -> calls E02 reservation/movement contract
 -> E02 remains sole stock truth
```

Target inbound flow:

```text
PO / transfer receipt
 -> receiving/staging location
 -> putaway task
 -> exact storage bin
```

Target outbound flow:

```text
E02 reservation
 -> exact bin allocation
 -> scan location/material
 -> pick evidence
 -> E02 reservation consumption + shipment movement
```

Target count flow:

```text
count task
 -> physical observation by location/material
 -> variance review
 -> approved E02 adjustment movement
```

Important boundaries:

- scan resolver identifies; it never directly changes stock;
- `warehouse_layout_items` remains visual projection, not identity/stock truth;
- lot/serial/quality-state authority remains E07;
- no wave/cluster picking, cartonization, slotting AI or MFC in E03 P0;
- exact E03 migration numbers are assigned only after E01/E02/E11 merged history is known.

Pure location/scan infrastructure may begin only after E02 location/stock identity is frozen. Stock-mutating putaway/pick/count execution remains blocked until the relevant E02 movement/balance contracts are authoritative and locally verified.

# Current transition path

```text
NOW:
E00 real-checkout Release Gate PASS
 -> review/merge Inventory PR #3

THEN:
E01 small PRs
 -> E11-S01/S02 pricing safety
 -> E02 shadow-first stock kernel
 -> E03 location / staging / putaway / scan / pick / count

LATER:
E04 electronic part identity
 -> E05 controlled EBOM/MBOM/revision
 -> E06 work orders
 -> E07 lot/serial/quality/RF test evidence
 -> E08 MRP/subcontract
 -> remaining commerce/economics/automation/AI epics
```

## Hard stop

No E01/E11/E02/E03 runtime implementation should be merged while E00 remains `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`.

Planning may continue; production authority may not.
