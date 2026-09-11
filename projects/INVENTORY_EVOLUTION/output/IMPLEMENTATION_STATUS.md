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

Prepared S01–S07 + `E03_IMPLEMENTATION_SEQUENCE.md`:

```text
stable warehouse location identity
receiving staging + putaway
typed scan resolver
exact-bin allocation / scan-first picking
location-aware count observation/reconciliation
cycle count + simple policies
mobile/handheld guided scan UX
```

E03 validates warehouse execution and calls E02 reservation/movement; E02 remains sole stock truth. Scan identifies but never directly mutates stock. Lot/serial/quality remains E07.

# E04 — electronics component master prepared

Prepared S01–S08 + `E04_IMPLEMENTATION_SEQUENCE.md`.

Canonical identity:

```text
materials.id            = internal part identity
materials.material_code = internal part number
manufacturer_parts      = Manufacturer + MPN identity
supplier_parts          = supplier-scoped SKU/source identity
platform_sku_mappings   = sales/channel identity
```

Safety distinctions:

```text
alias != approved manufacturer part
MPN existence != AML approval
supplier availability != engineering approval
parametric similarity != substitute authority
provider confidence != canonical truth
```

# E05 — controlled engineering configuration prepared

Prepared:

```text
TASK_INV_IMPL_E05.md      Master contract
TASK_INV_IMPL_E05_S01.md  Product / Part Revision Identity
TASK_INV_IMPL_E05_S02.md  Revisioned EBOM + RefDes
TASK_INV_IMPL_E05_S03.md  MBOM Derivation / Manufacturing Differences
TASK_INV_IMPL_E05_S04.md  EDA Import Staging / BOM Diff
TASK_INV_IMPL_E05_S05.md  Release Effectivity Resolution
TASK_INV_IMPL_E05_S06.md  ECN/ECO / Deviation / Impact Control
TASK_INV_IMPL_E05_S07.md  Controlled Docs / Firmware / Test Specs
TASK_INV_IMPL_E05_S08.md  Legacy BOM Compatibility / Where-used / Cost Source
E05_IMPLEMENTATION_SEQUENCE.md
```

Configuration chain:

```text
Internal Material
 -> Product/Part Revision
 -> Released EBOM Revision
 -> Released MBOM Revision based on EBOM
 -> Controlled Documents/Firmware/Test Specs
 -> Release Package
 -> Work Order snapshot (E06)
```

Key invariants:

- released revisions are immutable;
- `material_bom` remains sales/fulfilment BOM;
- `project_bom_lines` may seed staging/draft only, never auto-release;
- EDA import creates staging/diff/draft only;
- MBOM retains ancestry to one released EBOM;
- effectivity selects current released configuration without moving historical references;
- ECO records before/after objects and unresolved impacts block approval;
- controlled released files are checksum-bound and superseded, never overwritten in place;
- cost/where-used queries name exact BOM type/revision.

E05 completes only when E06 can reference one exact immutable released manufacturing configuration.

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

LATER
E06 work orders
 -> E07 lot/serial/quality/RF test evidence
 -> E08 MRP/subcontract
 -> remaining commerce/economics/automation/AI epics
```

## Hard stop

No E01/E11/E02/E03/E04/E05 runtime implementation should be merged while E00 remains `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`.

Planning may continue; production authority may not.
