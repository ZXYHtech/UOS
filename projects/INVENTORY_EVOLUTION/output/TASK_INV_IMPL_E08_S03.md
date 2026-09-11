# TASK_INV_IMPL_E08_S03 — Released MBOM Explosion & Dependent Demand

## Status
`DESIGN_READY_BLOCKED_BY_E07_GATE`

## Objective
Generate dependent material demand only from one exact released/effective E05 MBOM revision.

## Rules
Explosion must preserve:

- parent demand/source reference;
- exact MBOM revision/effectivity evidence;
- multilevel recursion;
- cycle detection;
- quantity propagation and UOM;
- DNF/optional/variant applicability;
- scrap/yield factors when configured;
- phantom/subassembly semantics when introduced.

## Hard boundaries
- never explode `material_bom` sales/kit semantics for manufacturing planning;
- never explode mutable draft EBOM/MBOM;
- do not silently switch to a newer MBOM after the planning run starts;
- alternate/substitute candidate discovery is separate from E04/E05 approval authority.

## Reproducibility
Each generated dependent-demand row records its parent demand, BOM header/line identity, revision and applied quantity/effectivity assumptions so a historical recommendation can be explained later.

## Tests
- multilevel quantity propagation;
- BOM-cycle rejection;
- DNF/variant exclusion;
- revision/effectivity selection;
- sales BOM cannot enter MRP explosion;
- draft MBOM is rejected;
- later MBOM release does not alter completed run inputs.

## Done
Dependent demand can be reconstructed from the exact released manufacturing configuration that produced it.