# INVENTORY_EVOLUTION — Implementation Status

## Current state

**Project design coverage:** `E00–E15 COMPLETE AT IMPLEMENTATION-DESIGN LEVEL`  
**Runtime execution packets:** `E01 COMPLETE / E11 EARLY COMPLETE / E02 A–J COMPLETE`  
**Runtime authority:** still blocked at E00 real-checkout gate.

```text
E00  IMPLEMENTED_AWAITING_LOCAL_VERIFICATION
E01  EXECUTION_PACKETS_READY_BLOCKED_BY_E00_GATE
E11-S01/S02  EXECUTION_PACKETS_READY_BLOCKED_BY_E01
E02  EXECUTION_PACKETS_A_TO_J_READY_BLOCKED_BY_E01_E11_EARLY_GATES
E03  DESIGN_READY_BLOCKED_BY_E02_FOUNDATION
E04  DESIGN_READY_BLOCKED_BY_E03_GATE
E05  DESIGN_READY_BLOCKED_BY_E04_GATE
E06  DESIGN_READY_BLOCKED_BY_E05_GATE
E07  DESIGN_READY_BLOCKED_BY_E06_GATE
E08  DESIGN_READY_BLOCKED_BY_E07_GATE
E09  DESIGN_READY_BLOCKED_BY_E01_E02_GATES
E10  DESIGN_READY_BLOCKED_BY_E04_E07_E09_FOUNDATIONS
E11-S03..S08  DESIGN_READY_BLOCKED_BY_MANUFACTURING_COMMERCE_EVIDENCE
E12  DESIGN_READY_BLOCKED_BY_DOMAIN_EVIDENCE
E13  DESIGN_READY_BLOCKED_BY_E01_DOMAIN_COMMANDS
E14  DESIGN_READY_BLOCKED_BY_GOVERNED_DOMAIN_CONTRACTS
E15  DESIGN_READY_CONDITIONAL_NOT_SCHEDULED
```

## External implementation / safety baseline

- repo: `ZXYHtech/inventory`
- audited pre-E00 baseline/main: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`
- frozen pre-audit branch: `backup/pre-e00-audit-20260911`
- E00 implementation branch: `impl/e00-release-safety`
- reviewed/current PR head: `0e0870499f7e8b5e68a308231eae954f106bd5aa`
- PR: `ZXYHtech/inventory#3`
- latest connector check: `2026-09-14`, `open`, `draft=true`, `mergeable=true`, `merged=false`

Do **not** mark E00 complete until the repository-local gate runs from a real checkout and passes:

```bash
python3 tools/verify_release.py
python3 tools/verify_release.py --require-bash
```

`mergeable=true` is informational only and is not verification evidence.

Do **not** claim production database backup evidence exists before the actual production host (or explicitly authorized copy) executes the preflight/update path.

Every future production release preserves:

```text
exact deployed-server code snapshot
 -> consistent current DB backup
 -> isolated restore verification
 -> manifest/checksums
 -> off-host Recovery Bundle when configured
 -> quiesce writers
 -> dependency/runtime change only after backup proof
 -> local Release Gate
 -> code sync
 -> numbered migration + integrity postflight
 -> restart + health
```

No required production, migration, backup, worker, report, automation or AI path depends on GitHub Actions.

# Full target sequence

```text
E00 Release Safety / Migration / Recovery
 -> E01 Action Policy / Idempotency / Durable Jobs / Outbox
 -> E11-S01/S02 Pricing Semantics + Floor Safety
 -> E02 Stock Ledger / Balance / Reservation / ATP
 -> E03 Warehouse Location / Staging / Putaway / Scan / Pick / Count
 -> E04 Electronics Part / Manufacturer+MPN / Supplier Part / Parametrics / AVL
 -> E05 Part Revision / EBOM / MBOM / ECN / Controlled Documents
 -> E06 Work Orders / WIP / Issue-Return-Scrap / Partial Output / Prototype
 -> E07 Lot-Serial / Quality / NCR / RF Test / Equipment Calibration / Release Trace
 -> E08 MRP / Pegging / Recommendations / Subcontract External WIP
 -> E09 Omnichannel External-object / ATP Publication / Outbox / Reconciliation
 -> E10 Technical CRM / Quote / Samples / Service Case / RMA
 -> E11-S03..S08 Standard Cost / WO Actual Cost / Settlement / Contribution
 -> E12 Governed Metrics / Management Cockpit / Product Intelligence
 -> E13 Safe Rules Automation
 -> E14 Evidence-bound AI Copilot
 -> E15 Conditional Scale / PostgreSQL Readiness
```

# Runtime execution handoff artifacts

## E01

Index:

`E01_EXECUTION_PACKETS_INDEX.md`

Prepared A–F:

```text
A RequestContext / Action Policy
B Business Operation Idempotency — Migration 2
C transfer.receive / purchase.receive / shipment pilot actions
D Durable Jobs / Lease/Fencing — Migration 3
E Transactional Outbox / Correlation — Migrations 4/5
F bounded Backup/Pricing/Procurement/Integrations extraction
```

## E11 early

Index:

`E11_EARLY_EXECUTION_PACKETS_INDEX.md`

Prepared:

```text
E11-A Pricing semantics — no migration
E11-B Floor/override safety — Migration 6 permission definition
```

Historical `margin_percent` arithmetic is preserved; `pricing.floor_override` is not auto-granted to any role.

## E02

Index:

`E02_EXECUTION_PACKETS_INDEX.md`

Prepared A–J:

```text
A Stock Identity/UOM — no migration
B Movement Ledger — Migration 7
C Balance Projection — Migration 8
D Same-transaction manual-adjust shadow pilot
E Reservation/ATP shadow kernel — Migration 9
F Order/Shipment reservation authority pilot
G Transfer issue -> in-transit -> receipt
H Purchase receipt stock integration
I Manual adjustment + count authoritative bridge
J Final authority cutover / legacy-write fencing
```

Canonical stock invariants:

```text
Movement Ledger = why/how stock changed
Balance Projection = current physical quantity
Reservation = committed promise
ATP = quantity still promiseable
```

Critical E02 corrections discovered during execution preparation:

1. `ShipmentService.ship()` is the physical shipment stock-effect point; `complete()` must not double issue/consume.
2. authoritative transfer receipt must not preserve legacy behavior that backfills a missing source issue at receive time.
3. count observation remains separate from approved count-adjustment movement.
4. Slice J is the only stage allowed to declare the new stock kernel globally authoritative.

## Procurement landed-cost prerequisite

File:

`PURCHASE_PARTIAL_RECEIPT_LANDED_COST_SAFETY_REVIEW.md`

Static review found a credible risk that repeated partial receipts may repeatedly allocate the full PO-header freight/other amount.

This must be fixture-proven or fixed in a separate bounded PR before E02-H. Do not hide a commercial cost formula change inside the stock-ledger migration.

# Canonical prepared migration chain

```text
1  baseline_current_schema_20260810
2  business_operations
3  jobs + job_attempts
4  outbox_events
5  operation_logs.correlation_id
6  pricing.floor_override permission
7  stock_movement_operations + stock_movement_lines
8  stock_balances
9  stock_reservations + stock_reservation_events
10+ only through later explicitly approved additive migrations
```

Never edit/reuse an applied migration number.

# Architecture invariants by later wave

## E03
Warehouse scan/tasks validate execution; E02 remains stock authority. Layout is projection, not stock/location truth.

## E04

```text
materials.id = internal part
Manufacturer + MPN = manufacturer-part identity
supplier SKU = supplier-part identity
channel SKU = commerce identity
```

Alias/similarity/availability never equals engineering substitution approval.

## E05
Sales BOM, released EBOM and released MBOM are separate semantics. Released revisions/artifacts are immutable; EDA import stages/diffs rather than rewriting released production data.

## E06
WO release freezes exact product/MBOM/release package; material requirements are snapshots; issued material becomes WO-owned WIP; cancel requires full disposition.

## E07
Risk-based lot/serial + quality stock states + RF test evidence. Physical completion is not saleable release. Raw S2P/spectrum artifacts, limit revision, firmware, equipment and calibration-at-test-time remain traceable.

## E08
MRP uses dated typed supply/demand, qualified stock, released MBOM and approved source data. It recommends/explains; humans firm/convert. Subcontract company material remains company-owned external WIP.

## E09
Remote observations have account-scoped identity; central ATP is published via durable outbox; desired and acknowledged remote states remain separate; reconciliation never silently chooses a winner.

## E10
Customer lifecycle joins inquiry, technical requirements, immutable quote revision, sample/evaluation, order, service case and serial-aware RMA. Refund/return/repair/warranty remain distinct.

## E11 late
Reference estimate, released standard cost, WO actual cost and realized channel economics remain separate. Margin/markup/contribution formulas and evidence quality are explicit.

## E12
One KPI has one versioned definition. Missing evidence is never fake zero. Aggregates drill to source records. Product intelligence is transparent multi-dimensional evidence, not a black-box score.

## E13
No arbitrary SQL/Python rule execution. A0/A1 first; A2 must be reversible/policy-controlled; A3 defaults to human approval. Observe-only, idempotency, compensation, loop controls and kill switches are mandatory.

## E14
AI interprets/extracts/ranks/summarizes/drafts; deterministic services validate facts and business rules. No direct SQL/secrets. Writes require structured preview, current-state validation and approval.

## E15
SQLite remains default while measured SLOs are healthy. PostgreSQL is conditional on measured need plus dual-backend parity/migration/recovery proof.

# Immediate next executable step

The project bottleneck is no longer missing design or E01/E02 execution detail. It remains E00 runtime verification.

```text
1. real checkout inventory/impl/e00-release-safety at exact PR head
2. run repository-local Release Gate
3. if PASS, review PR #3 blockers
4. merge E00 safely
5. execute fresh production backup-only preflight before any server cutover
6. start E01 Slice A from new main
```

Until that happens, E01/E11/E02 runtime implementation remains blocked even though the execution packets are ready.