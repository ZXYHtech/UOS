# TASK_INV_AUDIT_EBOM_MBOM_01 — Engineering BOM to Manufacturing BOM Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `material_bom`, `project_bom_lines`, BOM cost recursion, material usage categories and absence of reference-designator/work-order manufacturing structures.

## 1. Executive conclusion

Current BOM capability serves two useful but different purposes:

- `material_bom`: sales/fulfilment bundle-component explosion;
- `project_bom_lines`: project/product component structure used for costing/import-oriented workflows.

Neither is yet a true released EBOM/MBOM system.

The system should not force one table to simultaneously represent e-commerce bundles, engineering design BOM and manufacturing BOM. Those have different semantics.

## 2. Required BOM layers

### Sales/kit BOM

Purpose: what physical inventory is deducted when a sellable SKU ships.

Keep current lightweight `material_bom` semantics for this role where appropriate.

### EBOM

Purpose: engineering definition of the designed product.

Needs:

- parent product revision
- component internal part
- quantity
- reference designators
- notes/variant applicability
- do-not-fit/optional state
- engineering revision

### MBOM

Purpose: what manufacturing actually consumes/builds.

May differ from EBOM by:

- panelization
- consumables
- labels/packaging
- cables/accessories
- subassemblies
- phantom assemblies
- process-specific materials
- yield/scrap factors

## 3. Reference designators are important

Static search did not find first-class reference-designator data.

For electronics, a line such as `10 × 10k resistor` is insufficient for troubleshooting or assembly. EBOM should preserve locations such as:

```text
R1,R2,R7,R12...
```

Do not treat reference designators as the primary inventory identity; they belong to BOM placement/design context.

## 4. Multilevel BOM

Existing recursive cost/explosion behavior is useful and should be reused.

Future BOM engine needs:

- multilevel hierarchy;
- cycle prevention;
- revision selection;
- quantity propagation;
- phantom/subassembly handling;
- alternate/AVL resolution separately;
- effective date/revision.

## 5. EBOM import

For Altium/KiCad/EDA imports, use a staging/review model:

```text
EDA export
 -> normalize manufacturer/MPN/refdes/value/package
 -> match internal part
 -> unresolved/ambiguous lines
 -> engineering review
 -> draft EBOM revision
 -> compare with previous revision
 -> release
```

Never let an EDA import silently rewrite the currently released production BOM.

## 6. EBOM to MBOM transformation

Start simple. In a small RF company, many products may initially have EBOM ≈ MBOM.

Represent this explicitly:

```text
MBOM revision based_on EBOM revision
```

Then allow manufacturing additions/removals with reasons.

Typical RF-module manufacturing additions:

- PCB panel/substrate
- solder paste/consumables if controlled by quantity/cost
- shielding cover
- enclosure
- screws/connectors/cables
- labels
- packaging
- calibration accessory where consumed

## 7. Variant/configuration support

Do not duplicate a complete BOM for every small RF option if a controlled variant rule can express it.

Possible dimensions:

- connector type
- frequency option
- gain option
- power supply option
- enclosure option

But avoid a full configurator initially. First support explicit variant applicability on BOM lines and released SKU/revision combinations.

## 8. Cost relationship

The current recursive cost engine can continue using BOM structures for estimated cost, but future rules must specify which BOM it uses:

- EBOM engineering estimate;
- MBOM standard manufacturing cost;
- actual work-order consumption for realized cost.

Do not mix these figures under one `total_cost` label.

## 9. MRP relationship

MRP should explode the **released effective MBOM** for production demand, not e-commerce kit BOM and not a mutable draft EBOM.

This is a hard dependency for trustworthy production planning.

## 10. Minimal target schema

```text
bom_headers
  id
  parent_material_id
  bom_type: sales | engineering | manufacturing
  revision_code
  status
  based_on_bom_id
  effective_from/to

bom_lines
  bom_id
  component_material_id
  quantity
  refdes
  line_type
  optional/dnf
  variant_condition
  scrap_factor
  notes
```

Existing BOM tables can be migrated gradually; do not remove current fulfilment behavior until compatibility tests pass.

## 11. Priorities

### P0

1. separate sales BOM from engineering/manufacturing BOM semantics;
2. revisioned EBOM header/lines;
3. reference designators;
4. released effective MBOM;
5. EDA import staging/diff review.

### P1

1. EBOM -> MBOM inheritance/diff;
2. subassembly/phantom support;
3. variant applicability;
4. packaging/process materials;
5. standard-cost selection by MBOM revision.

## 12. Acceptance signals

- a sales bundle can change without silently changing released manufacturing BOM;
- an EDA import creates a draft/diff, not a production rewrite;
- a BOM revision preserves reference designators;
- MRP explodes a specified released MBOM revision;
- historical work order continues to resolve the exact BOM it used.

No acceptance test requires GitHub Actions.

## 13. Preliminary maturity

- sales/fulfilment BOM: 3.5/5
- recursive component costing: 3/5
- project component list: 2.5/5
- released EBOM: 0.5/5
- reference designators: 0/5
- MBOM: 0.5/5
- EBOM/MBOM transformation: 0/5

## 14. Core recommendation

Preserve the current sales BOM, but stop stretching it toward manufacturing. Introduce typed, revisioned BOMs and make the released MBOM the production-planning contract.