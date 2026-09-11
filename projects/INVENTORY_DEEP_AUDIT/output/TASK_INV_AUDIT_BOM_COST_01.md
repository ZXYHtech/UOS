# TASK_INV_AUDIT_BOM_COST_01 — BOM, Bundle & Product Cost Capability Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `material_bom`, project-BOM structures, BOM staging/import concepts, `bom_operations`, labor profiles and `CostService.material_cost`. No GitHub Actions result is used as proof.

## 1. Executive conclusion

Inventory Lite already has a meaningful **cost-estimation BOM**, but it does not yet have a controlled engineering/manufacturing BOM system.

The current model supports:

- a sales-material -> component relation;
- component quantity;
- project/import BOM lines;
- BOM staging/import assistance;
- recursive material cost;
- purchase-price history as component cost input;
- labor profiles;
- BOM operations with setup/run time and fixed cost;
- circular BOM detection in recursive costing.

This is valuable for estimating an RF module/product cost.

The key limitation is governance: a BOM is effectively a current relation set attached to a material, rather than a released, versioned engineering object with revision/effectivity/change history.

## 2. Two BOM concepts currently coexist

### `material_bom`

Simple normalized relation:

```text
sales_material_id
component_material_id
component_quantity
remark
creator/time
```

Current server code creates component quantity using integer conversion.

This is well suited to:

- sales bundles;
- kits;
- simple assembly explosion;
- fulfilment component deduction.

### `project_bom_lines`

A richer imported/project line structure can preserve:

- sales/product association;
- component code/name/model text;
- bound component material ID when matched;
- fractional quantity;
- source/import metadata.

This is useful for ingesting imperfect engineering/source BOM data before all lines are normalized.

### Risk

Without an explicit BOM-type/header model, these two concepts can become ambiguous:

- Is `material_bom` sales kit or production BOM?
- Is `project_bom_lines` temporary import data or engineering truth?
- Which one wins when both exist?

`CostService.material_cost` currently uses `material_bom` components first and falls back to `project_bom_lines` only when no normalized components are found. That is deterministic, but not an engineering release policy.

## 3. Recursive cost calculation

`CostService.material_cost`:

- detects circular nesting through a traversal trail;
- loads purchase-price history;
- calculates a weighted historical landed purchase cost;
- recursively expands component costs;
- uses normalized `material_bom` or falls back to bound project-BOM lines;
- combines component and operation/labor cost to derive product cost.

This is a useful management estimate.

### Strength

Circular BOM detection is important and should be retained in any future revisioned BOM engine.

### Limitation A — historical purchase cost basis

The current purchase-cost basis appears to average accumulated purchase history for a material rather than explicitly support selectable costing methods such as:

- latest purchase;
- moving weighted average;
- standard cost;
- lot actual cost;
- FIFO layer cost;
- contract/supplier quote cost.

For product planning, different contexts need different bases.

### Limitation B — estimated versus actual manufacturing cost

Current BOM/labor rollup is an **estimated cost**. There is no work order with actual issued lots, actual labor time, scrap/rework and production output quantity from which to calculate realized batch/serial cost.

The UI/reporting must never label estimated BOM rollup as actual manufacturing cost.

## 4. BOM revision gap

A manufacturing-grade BOM needs an object like:

```text
BOM
  product_id
  bom_type

BOMRevision
  revision
  state
  effective_from/to
  released_by/at

BOMLine
  line_no
  component_part_id
  quantity
  uom
  reference_designators
  scrap_factor
  substitute_group
  notes
```

Current audited schema does not establish that hierarchy.

Consequences today:

- editing components changes the current BOM without a formal released revision snapshot;
- historical orders/cost calculations may not be able to explain which BOM version was intended at that time;
- future production cannot guarantee that a specific serial was built to BOM Rev A vs Rev B;
- ECN/ECO impact cannot be traced cleanly.

## 5. Electronics-specific BOM fields

High-value fields for PCB/RF products:

- reference designators (`R1,R2,U3...`);
- manufacturer/MPN;
- internal part;
- package/footprint;
- quantity per assembly;
- DNP/optional population;
- substitute/AVL group;
- approved manufacturer/source;
- assembly side/location where useful;
- variant/configuration rule;
- firmware dependency;
- schematic/PCB/product revision linkage.

A search of the pinned current source did not find a first-class `reference_designator` implementation.

## 6. EBOM / MBOM separation

For a small team, do not build an enterprise PLM suite. But distinguish at least:

- **EBOM** — what engineering designed;
- **MBOM** — what production actually issues/builds;
- **Sales/Kit BOM** — what fulfilment explodes for shipping.

The current `material_bom` is already used in fulfilment-like component expansion, so making it the sole future manufacturing BOM would mix responsibilities.

Recommended migration:

1. classify current BOM relations;
2. preserve sales-kit behavior;
3. introduce controlled engineering BOM revision;
4. derive/copy an MBOM when production needs different packaging/process components;
5. link all three rather than silently reuse one table.

## 7. Operation and labor model

Existing `labor_cost_profiles` and `bom_operations` include useful planning fields such as:

- operation name;
- labor cost profile;
- setup minutes;
- run minutes;
- worker count;
- fixed cost;
- overhead rate.

This is a good seed for routing, but it lacks production execution semantics such as:

- work center;
- operation sequence;
- queue/setup/run status;
- actual start/stop;
- operator/equipment;
- yield/scrap;
- rework;
- capacity calendar.

Do not expand cost operations directly into a full MES in one step. First introduce a minimal routing/work-order layer.

## 8. Cost model gaps for electronics products

A realistic RF module cost may include:

```text
component material
PCB
SMT/assembly subcontract
connector/mechanical parts
housing
cable/labels/packaging
labor
test time
equipment/fixture allocation
scrap/yield
shipping/import landed cost
warranty/RMA reserve
platform/payment fee for commercial margin
```

These belong to different accounting layers:

- engineering standard/estimated cost;
- purchase landed cost;
- manufacturing actual cost;
- commercial contribution margin.

Do not collapse them into one `cost` number.

## 9. Recommended cost layers

```text
StandardComponentCost
EstimatedBOMCost
EstimatedRoutingCost
StandardManufacturingCost
ActualWorkOrderMaterialCost
ActualWorkOrderLabor/ProcessCost
ActualBatchUnitCost
CommercialContributionMargin
```

The current `CostService.material_cost` can continue serving as the estimated-rollup engine while later layers are added.

## 10. Change control

Future BOM modification should follow:

```text
Draft revision
 -> validate all parts/quantities
 -> compare to previous revision
 -> where-used impact
 -> approval/release
 -> effective date/serial/work-order boundary
 -> previous revision remains immutable
```

For urgent substitutions, use an approved deviation/substitute event rather than editing historical released BOM data.

## 11. Import workflow

The project already has project-BOM/staging concepts, which are useful for importing spreadsheets or EDA exports.

Recommended future pipeline:

```text
raw import
 -> column mapping
 -> normalize manufacturer/MPN/refdes/qty
 -> match internal parts
 -> unresolved lines queue
 -> duplicate/refdes validation
 -> compare against current revision
 -> create DRAFT BOM revision
 -> human review/release
```

Never let raw BOM import directly replace the released production BOM.

## 12. Cost refresh strategy

Cost calculation should declare its inputs and timestamp:

```text
CostSnapshot
  product_revision
  calculation_method
  component_cost_basis
  labor/routing version
  currency/rate basis
  calculated_at
  result breakdown
```

This prevents a historical quote from silently changing when today's purchase price changes.

## 13. Automation opportunities without Actions

Independent server/local jobs can:

- recalculate impacted product cost when component price changes;
- detect BOM cycles;
- flag missing/unmatched BOM lines;
- find EOL parts in released BOMs;
- compute where-used impact;
- compare BOM revisions;
- flag cost increase beyond threshold;
- generate draft substitution suggestions;
- refresh cost snapshots.

Use durable DB jobs and independent worker/systemd timer/cron. GitHub Actions must not be required.

## 14. Priority roadmap

### P0

1. define BOM types (sales kit vs engineering vs manufacturing);
2. ensure current fulfilment behavior remains explicit;
3. label current cost rollup as estimated cost;
4. add deterministic BOM/cost local regression tests;
5. define decimal/UOM rules;
6. verify partial-receipt landed-cost basis before trusting component cost history.

### P1

1. BOM header/revision/line model;
2. reference designators;
3. release/effectivity;
4. manufacturer/MPN/AVL linkage;
5. BOM revision diff + where-used;
6. cost snapshots;
7. routing/work-center minimal model.

### P2

1. ECN/ECO;
2. EBOM->MBOM transformation;
3. variant BOM rules;
4. actual work-order cost;
5. yield/scrap/rework cost;
6. serial/batch cost genealogy.

## 15. Local/server verification — no Actions

Recommended direct commands:

```bash
python3 tools/test_bom.py
python3 tools/test_cost_rollup.py
python3 tools/test_bom_revision.py
```

Required scenarios:

- multi-level BOM;
- circular BOM rejected;
- shared subassembly cost;
- fractional material quantity;
- missing/unbound imported component;
- sales-kit BOM not confused with production BOM;
- revision A remains immutable after B is released;
- effective revision selection;
- cost snapshot unchanged after later purchase-price change;
- substitute part approval;
- where-used impact.

GitHub Actions is not part of the required path.

## 16. Static maturity score

0–5:

- simple normalized BOM/kit: **4/5**
- imported/project BOM handling: **3.5/5**
- recursive estimated cost: **4/5**
- circular dependency protection: **4/5**
- labor/operation cost seed: **3/5**
- BOM revision/effectivity: **0.5/5**
- refdes/engineering data: **0.5/5**
- EBOM/MBOM governance: **0.5/5**
- actual manufacturing cost: **0.5/5**
- ECN/ECO: **0/5**

## 17. Core judgment

Keep the existing BOM/cost engine as a lightweight estimation and fulfilment foundation, but do not stretch it into manufacturing by merely adding more columns.

The strategic evolution is:

`current mutable component relation + recursive estimated cost`

->

`typed BOMs + immutable released revisions + engineering identity + routing + work-order actuals`,

with the existing cost rollup retained as one clearly named layer.