# Current execution override — 2026-09-14

- Active implementation: `ZXYHtech/inventory-Pro`, start from its current `main`.
- Old E00 source `0e08704` is preserved as import provenance, NOT the current Pro HEAD.
- The old inventory PR #3 must NOT be merged as part of this project.
- Next: verify isolation, reproduce/fix E00 failures, pass Pro local gates, then begin E01.
- No production backup/preflight/cutover is authorized. Use isolated fixtures/test infrastructure.
- Local audit 2026-09-14: recovery + backup-job tests failed on macOS; snapshot test passed
  with canonical /private/tmp. Target Linux execution is still unverified.
- The remaining content is retained design/history; follow REPOSITORY_ISOLATION.md on conflict.

---

> Execution target: **ZXYHtech/inventory-Pro** only. Read [repository isolation](../REPOSITORY_ISOLATION.md) before acting; old production/PR instructions below are superseded.

# INVENTORY_EVOLUTION — Implementation Status

## Current state

**Project design coverage:** `E00–E15 COMPLETE AT IMPLEMENTATION-DESIGN LEVEL`  
**Runtime execution packets:** `E01 COMPLETE / E11 EARLY COMPLETE / E02 A–J COMPLETE / E03 A–G COMPLETE`  
**Runtime authority:** still blocked at E00 real-checkout gate.

```text
E00  IMPLEMENTED_AWAITING_LOCAL_VERIFICATION
E01  EXECUTION_PACKETS_READY_BLOCKED_BY_E00_GATE
E11-S01/S02  EXECUTION_PACKETS_READY_BLOCKED_BY_E01
E02  EXECUTION_PACKETS_A_TO_J_READY_BLOCKED_BY_E01_E11_EARLY_GATES
E03  EXECUTION_PACKETS_A_TO_G_READY_BLOCKED_BY_E02_FOUNDATION/AUTHORITY
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

- repo: `ZXYHtech/inventory-Pro`
- audited pre-E00 baseline/main: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`
- frozen pre-audit branch: `backup/pre-e00-audit-20260911`
- E00 implementation branch: `impl/e00-release-safety`
- reviewed/current PR head: `0e0870499f7e8b5e68a308231eae954f106bd5aa`
- PR: `legacy inventory#3 (historical only; do not merge)`
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

Index: `E01_EXECUTION_PACKETS_INDEX.md`

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

Index: `E11_EARLY_EXECUTION_PACKETS_INDEX.md`

Prepared:

```text
E11-A Pricing semantics — no migration
E11-B Floor/override safety — Migration 6 permission definition
```

Historical `margin_percent` arithmetic is preserved; `pricing.floor_override` is not auto-granted to any role.

## E02

Index: `E02_EXECUTION_PACKETS_INDEX.md`

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

### Procurement landed-cost prerequisite

`PURCHASE_PARTIAL_RECEIPT_LANDED_COST_SAFETY_REVIEW.md` records a credible risk that repeated partial receipts may repeatedly allocate the full PO-header freight/other amount. Fixture-prove or fix this in a separate bounded PR before E02-H; do not hide a commercial-cost formula change inside stock migration.

## E03

Index: `E03_EXECUTION_PACKETS_INDEX.md`

Prepared A–G:

```text
A Stable warehouse location identity
B Shared typed scan resolver
C Receiving staging + putaway
D Exact-bin picking
E Location-aware count observation/reconciliation
F Cycle count + simple putaway/pick policies
G Mobile/handheld guided scan UX
```

E03-wide invariants:

```text
E02 = stock/reservation authority
E03 = location/task/scan execution evidence
layout = presentation only
receipt != putaway
scan resolution != action authority
pick confirmation != physical stock issue
count observation != stock mutation
```

Critical E03 corrections found in static source review:

1. current layout-box deletion can delete the linked `warehouse_locations` row; E03-A decouples layout lifecycle from business-location identity;
2. current location edit can change `warehouse_id`; referenced locations become warehouse-immutable;
3. cross-warehouse relocation must create/use a destination location and move stock through E02, never rewrite historical location ownership;
4. mobile/offline caches never become authoritative write sources.

E03 schema slices use the **next contiguous migration at implementation time** rather than pre-reserving numbers, because E02-J may legitimately consume the next migration for a separately reviewed final constraint. Expected E03 numbering starts at 10 only if E02-J uses no additional migration.

# Canonical prepared migration chain through E02

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
10+ next contiguous additive migrations assigned from merged main
```

Never edit/reuse an applied migration number.

# Architecture invariants by later wave

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

The implementation bottleneck remains E00 runtime verification, not planning detail.

```text
1. real checkout inventory-Pro/main at its exact recorded head
2. run repository-local Release Gate
3. if PASS, review legacy PR #3 (superseded; do not merge) blockers
4. merge E00 safely
5. execute fresh production backup-only preflight before any server cutover
6. start E01 Slice A from new main
```

Until E00 passes, E01/E11/E02/E03 runtime implementation remains blocked even though execution packets are ready.