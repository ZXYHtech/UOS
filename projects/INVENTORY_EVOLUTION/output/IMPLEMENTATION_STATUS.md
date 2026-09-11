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
**E11:** `DESIGN_READY_SPLIT_EARLY_AND_LATE`

External implementation:
- repo: `ZXYHtech/inventory`
- audited pre-E00 baseline/main: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`
- frozen pre-audit branch: `backup/pre-e00-audit-20260911`
- E00 implementation branch: `impl/e00-release-safety`
- reviewed E00 head: `0e0870499f7e8b5e68a308231eae954f106bd5aa`
- PR: `ZXYHtech/inventory#3`
- latest connector state checked 2026-09-11: `open`, `draft=true`, `mergeable=true`, `merged=false`

Do **not** mark E00 complete until the repository-local Release Gate is executed from a real checkout. Do **not** claim the production DB has already been backed up; production backup evidence exists only after the production host (or authorized copy) actually runs the preflight/update path.

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
Coverage: E00-S01..S07. Required real-checkout commands:

```bash
python3 tools/verify_release.py
python3 tools/verify_release.py --require-bash
```

Any failure keeps E00 open. See `E00_LOCAL_VERIFICATION_HANDOFF.md`.

# E01 — core execution primitives prepared
Prepared S01–S10 + `E01_IMPLEMENTATION_SEQUENCE.md`: shared context, Action Policy, consequential pilots, idempotency, durable jobs, worker/retry/dead-letter, transactional outbox, correlation and bounded module extraction.

# E02 — stock truth / reservation kernel prepared
Prepared S01–S07 + `E02_IMPLEMENTATION_SEQUENCE.md`.

```text
Movement Ledger = why/how stock changed
Balance Projection = current physical quantity
Reservation = committed promise
ATP = quantity still promiseable
```

# E03 — warehouse execution prepared
Prepared S01–S07 + `E03_IMPLEMENTATION_SEQUENCE.md`: stable locations, receiving/putaway, typed scan, exact-bin picking, location-aware counts, cycle policies and guided mobile scan.

# E04 — electronics component master prepared
Prepared S01–S08 + `E04_IMPLEMENTATION_SEQUENCE.md`: internal part identity, Manufacturer+MPN, Supplier Part, package/footprint, typed parametrics, AML/AVL/substitutes, provenance and component workspace/provider staging.

# E05 — controlled engineering configuration prepared
Prepared S01–S08 + `E05_IMPLEMENTATION_SEQUENCE.md`: part revision, EBOM/refdes, MBOM ancestry, EDA staging/diff, effectivity, ECN/ECO/deviation, controlled documents/firmware/test specs and legacy BOM compatibility/where-used.

# E06 — work order / manufacturing execution prepared
Prepared S01–S08 + `E06_IMPLEMENTATION_SEQUENCE.md`: WO lifecycle/frozen configuration, requirement snapshot/reservation, kit/pick/issue to WO WIP, overissue/return/scrap, partial output, hold/cancel disposition, controlled substitution and prototype mode.

# E07 — traceability / quality / RF test evidence prepared
Prepared S01–S09 + `E07_IMPLEMENTATION_SEQUENCE.md`: lot/serial, quality states, IQC/FQC, NCR/rework, genealogy, released test limits, structured RF measurements/raw artifacts, equipment/calibration and final release/shipment trace.

# E08 — MRP planning + subcontract prepared
Prepared S01–S08 + `E08_IMPLEMENTATION_SEQUENCE.md`: planning policy, dated demand/supply, MBOM explosion, time-phased netting, pegging, planner recommendation, external WIP subcontract and durable MRP runs.

# E09 — omnichannel durable reconciliation prepared
Prepared S01–S08 + `E09_IMPLEMENTATION_SEQUENCE.md`: external-object identity, SKU mapping lifecycle, remote order revisions, central ATP publication, fulfilment outbox, cancellation/refund policy, reconciliation and connector health/cursors.

# E10 — technical CRM / quotation / service / RMA prepared
Prepared S01–S08 + `E10_IMPLEMENTATION_SEQUENCE.md`: customer/opportunity, technical requirements, revisioned quotes, samples, service case/SLA, RMA quarantine/warranty, repair/retest/exchange/refund and safe reminders/templates/feedback.

# E11 — pricing safety, cost and realized economics prepared

Prepared:

```text
TASK_INV_IMPL_E11.md      Master contract
TASK_INV_IMPL_E11_S01.md  Pricing Formula Semantics / Legacy Safety
TASK_INV_IMPL_E11_S02.md  Floor Price / Deal-price Override Safety
TASK_INV_IMPL_E11_S03.md  Released Standard Cost Version
TASK_INV_IMPL_E11_S04.md  Work-order Actual Cost / Cost Close
TASK_INV_IMPL_E11_S05.md  Manufacturing Cost Variance Classification
TASK_INV_IMPL_E11_S06.md  Order Economics Event Ledger
TASK_INV_IMPL_E11_S07.md  Settlement Import / Matching / Reconciliation
TASK_INV_IMPL_E11_S08.md  Realized Contribution Profitability / Evidence Quality
E11_IMPLEMENTATION_SEQUENCE.md
```

E11 intentionally has an early and late wave:

```text
EARLY after E01:
S01 formula semantics
 -> S02 floor/override safety

LATE after E05-E10 evidence exists:
S03 released standard cost
 -> S04 WO actual cost close
 -> S05 variance classification
 -> S06 order economic events
 -> S07 channel settlement reconciliation
 -> S08 realized contribution profitability
```

Critical invariants:
- markup, gross margin and contribution margin are distinct, versioned formulas;
- current `CostService` remains reference/engineering estimator rather than being overloaded into finance truth;
- released standard cost is immutable;
- WO actual cost derives from actual execution evidence and closed cost changes only through adjustments;
- manufacturing variance causes remain distinguishable;
- revenue/fee/freight/refund/RMA economics are append-only events;
- duplicate settlement imports cannot duplicate economics;
- settlement mismatch never rewrites original order price;
- every profitability result exposes cost basis and evidence quality (`ESTIMATED`, `PARTIALLY_ACTUAL`, `SETTLED`, `RECONCILED`);
- no full GL/payroll/statutory tax engine is implied.

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
 -> E11-S03..S08 standard/actual cost + channel economics

NEXT DESIGN WAVES
E12 reporting/product intelligence
 -> E13 safe automation rules
 -> E14 evidence-bound AI Copilot
 -> E15 conditional scale/PostgreSQL
```

## Hard stop
No E01–E11 runtime implementation should be merged while E00 remains `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`. Planning may continue; production authority may not.