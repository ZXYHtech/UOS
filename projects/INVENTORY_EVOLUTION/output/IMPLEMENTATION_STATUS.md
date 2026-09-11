# INVENTORY_EVOLUTION — Implementation Status

## Current state

**Phase:** E00 Release Safety / Migration / Recovery Foundation  
**E00:** `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`  
**E01:** `DESIGN_READY_BLOCKED_BY_E00_GATE`  
**E11-S01/S02:** `DESIGN_READY_BLOCKED_BY_E01`  
**E02:** `DESIGN_READY_BLOCKED_BY_E00_E01_E11_GATES`  
**E03:** `DESIGN_READY_BLOCKED_BY_E02_FOUNDATION`  
**E04:** `DESIGN_READY_BLOCKED_BY_E03_GATE`  
**E05:** `DESIGN_READY_BLOCKED_BY_E04_GATE`  
**E06:** `DESIGN_READY_BLOCKED_BY_E05_GATE`  
**E07:** `DESIGN_READY_BLOCKED_BY_E06_GATE`  
**E08:** `DESIGN_READY_BLOCKED_BY_E07_GATE`  
**E09:** `DESIGN_READY_BLOCKED_BY_E01_E02_GATES`  
**E10:** `DESIGN_READY_BLOCKED_BY_E04_E07_E09_FOUNDATIONS`

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

```text
frozen pre-audit Git source
 -> confirm production DB exists
 -> clone target into /tmp using existing bootstrap tools
 -> narrow compile gate for backup/recovery tooling
 -> snapshot exact deployed server code
 -> consistent SQLite production snapshot
 -> isolated restore verification
 -> manifest/checksums
 -> off-host Recovery Bundle when configured
 -> stop backup/OCR/Web writers
 -> only then allow apt/pip changes
 -> full Release Gate
 -> rsync target code
 -> numbered migration + integrity postflight
 -> restart + health
```

`INVENTORY_PREFLIGHT_ONLY=1` performs backup/recovery proof and target gate using current dependencies, then exits before dependency/runtime/schema changes.

# E00 — implemented, runtime gate still required

Coverage:

```text
E00-S01 migration registry / baseline adoption
E00-S02 historical DB fixtures
E00-S03 integrity / orphan checks
E00-S04 authoritative local Release Gate
E00-S05 isolated restore verification
E00-S06 recovery manifest / checksums / config
E00-S07 off-host copy / health / scheduler
```

Required real-checkout command:

```bash
python3 tools/verify_release.py
```

Linux strict profile:

```bash
python3 tools/verify_release.py --require-bash
```

Any failure keeps E00 open. See `E00_LOCAL_VERIFICATION_HANDOFF.md`.

# E01 — core execution primitives prepared
Prepared S01–S10 covering shared context, Action Policy, consequential pilot actions, idempotency, durable jobs, worker/retry/dead-letter, transactional outbox, correlation and bounded module extraction. See `E01_IMPLEMENTATION_SEQUENCE.md`.

# E11-S01/S02 — pricing safety bridge
Prepared pricing formula semantics/legacy safety and floor/deal-price override controls. Historical arithmetic remains compatible while new explicit semantics are added.

# E02 — stock truth / reservation kernel prepared
Prepared S01–S07 + `E02_IMPLEMENTATION_SEQUENCE.md`.

```text
Movement Ledger = why/how stock changed
Balance Projection = current physical quantity
Reservation = committed promise
ATP = quantity still promiseable
```

# E03 — warehouse execution prepared
Prepared S01–S07 + `E03_IMPLEMENTATION_SEQUENCE.md` covering stable locations, receiving/putaway, typed scan, exact-bin picking, location-aware counts, cycle policies and guided mobile scan.

# E04 — electronics component master prepared
Prepared S01–S08 + `E04_IMPLEMENTATION_SEQUENCE.md` covering internal part identity, Manufacturer+MPN, Supplier Part, package/footprint, typed parametrics, AML/AVL/substitutes, provenance and component workspace/provider staging.

# E05 — controlled engineering configuration prepared
Prepared S01–S08 + `E05_IMPLEMENTATION_SEQUENCE.md` covering part revision, EBOM/refdes, MBOM ancestry, EDA staging/diff, effectivity, ECN/ECO/deviation, controlled documents/firmware/test specs and legacy BOM compatibility/where-used.

# E06 — work order / manufacturing execution prepared
Prepared S01–S08 + `E06_IMPLEMENTATION_SEQUENCE.md` covering WO lifecycle/frozen configuration, requirement snapshot/reservation, kit/pick/issue to WO WIP, overissue/return/scrap, partial output, hold/cancel disposition, controlled substitution and prototype mode.

# E07 — traceability / quality / RF test evidence prepared
Prepared S01–S09 + `E07_IMPLEMENTATION_SEQUENCE.md` covering lot/serial, quality states, IQC/FQC, NCR/rework, genealogy, released test limits, structured RF measurements/raw artifacts, equipment/calibration and final release/shipment trace.

# E08 — MRP planning + subcontract prepared
Prepared S01–S08 + `E08_IMPLEMENTATION_SEQUENCE.md` covering planning policy, dated demand/supply, MBOM explosion, time-phased netting, pegging, planner recommendation, external WIP subcontract and durable MRP runs.

# E09 — omnichannel durable reconciliation prepared
Prepared S01–S08 + `E09_IMPLEMENTATION_SEQUENCE.md` covering external-object identity, SKU mapping lifecycle, remote order revisions, central ATP publication, fulfilment outbox, cancellation/refund policy, reconciliation and connector health/cursors.

# E10 — technical CRM / quotation / service / RMA prepared

Prepared:

```text
TASK_INV_IMPL_E10.md      Master contract
TASK_INV_IMPL_E10_S01.md  Customer / Contact / Opportunity Identity
TASK_INV_IMPL_E10_S02.md  Technical Requirements / Product Candidate Evaluation
TASK_INV_IMPL_E10_S03.md  Revisioned Quotation / Approval / Quote-to-Order
TASK_INV_IMPL_E10_S04.md  Sample / Evaluation Lifecycle
TASK_INV_IMPL_E10_S05.md  Customer Service Case / SLA / Timeline
TASK_INV_IMPL_E10_S06.md  RMA Intake / Return Quarantine / Warranty Decision
TASK_INV_IMPL_E10_S07.md  Diagnosis / Repair / Retest / Exchange / Refund
TASK_INV_IMPL_E10_S08.md  Follow-up Automation / Templates / Feedback Loop
E10_IMPLEMENTATION_SEQUENCE.md
```

Customer lifecycle:

```text
customer/contact
 -> inquiry/opportunity
 -> structured RF/electronics requirements
 -> existing/custom candidate
 -> immutable quotation revision
 -> sample/evaluation
 -> accepted quote/order
 -> service case
 -> RMA/refund/repair/exchange
 -> quality/product feedback
```

Critical invariants:

- marketplace receiver text is not automatically a durable customer master;
- parametric similarity does not create an engineering/commercial promise;
- sent/accepted quote revisions are immutable and order conversion preserves the exact accepted revision;
- sample/loan/gift dispositions use explicit stock semantics;
- `ExceptionService` remains internal operational exception engine; service cases are separate and linked;
- refund, physical return, repair/diagnosis and warranty decisions are distinct lifecycles;
- returned product enters quarantine, never direct ATP;
- serialized RMA resolves original shipment/product/WO/test history;
- failed tests remain visible after repair/retest;
- exchange preserves original and replacement serials;
- reminders run through E01 server-owned jobs, never GitHub Actions.

# Current transition path

```text
NOW
E00 real-checkout Release Gate PASS
 -> review/merge Inventory PR #3

THEN
E01 core execution primitives
 -> E11-S01/S02 pricing safety
 -> E02 stock truth/reservation
 -> E03 warehouse execution
 -> E04 electronics part identity/AVL
 -> E05 controlled configuration
 -> E06 work-order execution
 -> E07 traceability/quality/RF test evidence
 -> E08 MRP/subcontract
 -> E09 omnichannel reconciliation
 -> E10 technical CRM/after-sales

NEXT DESIGN WAVES
E11 remaining channel economics/manufacturing actual cost
 -> E12 reporting/product intelligence
 -> E13 safe automation rules
 -> E14 evidence-bound AI Copilot
 -> E15 conditional scale/PostgreSQL
```

## Hard stop
No E01–E10 runtime implementation should be merged while E00 remains `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`. Planning may continue; production authority may not.