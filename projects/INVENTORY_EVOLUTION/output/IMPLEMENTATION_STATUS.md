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

Prepared S01–S10 covering shared context, Action Policy, consequential pilot actions, idempotency, durable jobs, worker/retry/dead-letter, transactional outbox, correlation and bounded module extraction.

Pilot bindings:

```text
transfer.receive  -> TransferService.receive
purchase.receive  -> ProcurementService.receive
shipment.complete -> ShipmentService.complete
```

Implementation order:

```text
S01/S02 -> S04 -> S03 -> S05/S06/S07 -> S08/S09 -> S10
```

See `E01_IMPLEMENTATION_SEQUENCE.md`.

# E11-S01/S02 — pricing safety bridge

Prepared:

```text
TASK_INV_IMPL_E11_S01.md  Pricing Formula Semantics & Legacy Rule Safety
TASK_INV_IMPL_E11_S02.md  Floor Price / Deal-price Override Safety
```

Current `margin_percent` arithmetic is a base/list-price uplift, not target gross-margin pricing. Historical arithmetic must remain compatible while new explicit semantics are added.

# E02 — stock truth / reservation kernel prepared

Prepared S01–S07 + `E02_IMPLEMENTATION_SEQUENCE.md`.

```text
Movement Ledger = why/how stock changed
Balance Projection = current physical quantity
Reservation = committed promise
ATP = quantity still promiseable
```

Migration is shadow-first, cutover-last. Only final E02 cutover may declare the new stock kernel authoritative. No historical bins/lots/serials/reservations are fabricated.

# E03 — warehouse execution prepared

Prepared S01–S07 + `E03_IMPLEMENTATION_SEQUENCE.md` covering stable locations, receiving/putaway, typed scan, exact-bin picking, location-aware counts, cycle policies and guided mobile scan. E03 calls E02 for authoritative stock changes.

# E04 — electronics component master prepared

Prepared S01–S08 + `E04_IMPLEMENTATION_SEQUENCE.md` covering internal part identity, Manufacturer+MPN, Supplier Part, package/footprint, typed parametrics, AML/AVL/substitutes, provenance and component workspace/provider staging.

Critical distinction remains:

```text
search/candidate similarity != engineering approval
```

# E05 — controlled engineering configuration prepared

Prepared S01–S08 + `E05_IMPLEMENTATION_SEQUENCE.md` covering part revision, EBOM/refdes, MBOM ancestry, EDA staging/diff, effectivity, ECN/ECO/deviation, controlled documents/firmware/test specs and legacy BOM compatibility/where-used.

# E06 — work order / manufacturing execution prepared

Prepared S01–S08 + `E06_IMPLEMENTATION_SEQUENCE.md` covering WO lifecycle/frozen configuration, requirement snapshot/reservation, kit/pick/issue to WO WIP, overissue/return/scrap, partial output, hold/cancel disposition, controlled substitution and prototype mode.

# E07 — traceability / quality / RF test evidence prepared

Prepared:

```text
TASK_INV_IMPL_E07.md      Master contract
TASK_INV_IMPL_E07_S01.md  Traceability Policy + Lot/Serial Identity
TASK_INV_IMPL_E07_S02.md  Lot-aware Receiving + Quality Stock State
TASK_INV_IMPL_E07_S03.md  IQC/IPQC/FQC Inspection + Quality Release
TASK_INV_IMPL_E07_S04.md  NCR / MRB-lite / Rework / Scrap
TASK_INV_IMPL_E07_S05.md  Work-order Genealogy + Finished Serial/Output Lot
TASK_INV_IMPL_E07_S06.md  Released Test Specification / Limit Execution
TASK_INV_IMPL_E07_S07.md  RF/Electrical Test Run / Measurements / Raw Artifacts
TASK_INV_IMPL_E07_S08.md  Equipment / Calibration / Setup Provenance
TASK_INV_IMPL_E07_S09.md  Final Quality Release / Shipment Trace / Recall Impact
E07_IMPLEMENTATION_SEQUENCE.md
```

Core evidence chain:

```text
supplier / receipt
 -> source lot/date code
 -> quality state
 -> E06 WO issue
 -> genealogy
 -> finished serial
 -> exact product/MBOM/firmware
 -> released test limits
 -> structured measurements + raw S2P/spectrum evidence
 -> equipment + calibration-at-test-time
 -> NCR/rework/retest where needed
 -> final quality release
 -> shipment/customer
```

Critical invariants:

- trace policy is risk-based; not every passive is serialized;
- legacy stock is never assigned invented genealogy;
- location, lot identity and quality state are independent dimensions;
- pending/quarantine/rejected stock is not normal ATP/MRP/WO supply;
- quality-state changes use E02 ledger/disposition, not direct text edits;
- genealogy advertises only the granularity actually captured;
- failed/aborted test runs remain after passing retest;
- raw RF artifacts are checksum-bound and linked to DUT/test run;
- historical result retains exact limit revision;
- equipment calibration validity is evaluated at test execution time;
- physical completion does not automatically grant saleable quality release;
- trace-controlled shipment preserves exact serial/lot identity to customer.

Before release-critical test evidence becomes authoritative, E00 recovery must be extended so retained raw artifacts/certificates are backup/restorable with checksum verification.

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

LATER
E08 MRP/subcontract
 -> remaining commerce/economics/automation/AI epics
```

## Hard stop

No E01/E11/E02/E03/E04/E05/E06/E07 runtime implementation should be merged while E00 remains `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`.

Planning may continue; production authority may not.
