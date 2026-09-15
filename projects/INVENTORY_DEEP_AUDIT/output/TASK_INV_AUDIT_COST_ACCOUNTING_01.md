# TASK_INV_AUDIT_COST_ACCOUNTING_01 — Actual Manufacturing Cost and Variance Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `CostService`, purchase-price/landed-cost history, BOM recursion, labor/overhead profiles, BOM operations and the manufacturing-domain gaps identified in W3.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The current system has a useful **cost-estimation engine**, not manufacturing cost accounting.

Existing capability can:

- calculate a weighted historical purchase cost from `material_purchase_prices`;
- recursively roll component cost through the current BOM/project-BOM fallback;
- calculate modeled labor and overhead from setup/run minutes and cost profiles;
- include fixed operation cost;
- expose a total estimated material cost.

That is valuable for product/pricing analysis, but it does not answer:

- what did Work Order X actually cost;
- which exact BOM revision and purchase-cost basis applied;
- how much variance came from purchase price vs substitution vs scrap vs labor;
- how much rework/subcontract/freight was consumed;
- what unit cost belongs to a particular finished lot/serial;
- whether margin is based on current estimate, standard cost or actual realized cost.

Preliminary maturity:

- estimated component cost: 3/5
- modeled labor/overhead: 2.5/5
- standard-cost revision control: 0.5/5
- work-order actual cost: 0/5
- variance accounting: 0/5
- lot/serial actual cost traceability: 0/5

## 2. Preserve three different cost concepts

Do not collapse all cost into a single `total_cost` field.

### 2.1 Current/reference estimate

“What would this product roughly cost using current/default assumptions?”

Useful for quick quoting and engineering decisions.

### 2.2 Standard cost

“What cost did the company formally plan/use for this product/revision during a defined period?”

Needs released revision/effective date.

### 2.3 Actual realized cost

“What did this specific work order/output lot actually consume and incur?”

Needs actual material, labor, scrap, subcontract and other execution records.

These values may intentionally differ.

## 3. Current cost calculation limitations

The inspected `CostService.material_cost()` uses purchase history aggregated as quantity × landed unit cost, then recursively selects `material_bom` or falls back to `project_bom_lines`, and adds modeled labor/overhead/fixed operation cost.

Key limitations for manufacturing accounting:

1. purchase average is historical aggregate rather than a controlled valuation policy by effective date/site/lot;
2. BOM selection is not revision/effectivity controlled;
3. sales BOM and manufacturing BOM can be mixed semantically;
4. operation times are standards, not actual execution evidence;
5. no work-order actual issue/return/scrap basis;
6. no actual substitution variance;
7. no quality/rework cost path;
8. no subcontract order actual processing cost;
9. no finished-output quantity denominator tied to accepted output;
10. no cost close/freeze period.

Therefore the current result should be labeled clearly as an **estimated/reference cost** until these controls exist.

## 4. Standard cost model

Introduce released standard-cost versions.

```text
standard_cost_headers
  id
  cost_version
  effective_from/to
  status: draft | released | closed
  method
  created_by/released_by

standard_cost_items
  header_id
  material_id
  product_revision_id
  mbom_revision_id
  material_cost
  labor_cost
  overhead_cost
  subcontract_cost
  freight_cost
  total_standard_cost
  calculation_snapshot_json
```

A released standard cost should preserve assumptions rather than recalculate from today's BOM and prices.

For a small company, monthly or revision-triggered standards may be enough; do not implement complex fiscal costing periods before needed.

## 5. Material valuation choices

Inventory valuation policy is an accounting decision and should not be invented by application logic.

Possible methods include:

- weighted average;
- moving weighted average;
- FIFO;
- standard cost with purchase-price variance.

The existing purchase-average calculation is useful analytically but is not automatically a complete accounting valuation method.

Recommendation for initial operational analytics:

- preserve actual landed receipt unit cost per receipt/lot;
- compute work-order actual material cost from the specific issued stock cost layer where feasible;
- keep a separately labeled current/reference average for quoting.

Formal accounting integration can later map to the company's required finance policy.

## 6. Landed cost

The current procurement model already stores landed unit cost history. Build on it.

Potential landed-cost components:

- supplier unit price;
- freight;
- tax/duty where capitalized by policy;
- customs/broker fee;
- insurance;
- other acquisition cost.

Allocate cost using explicit rules and preserve the receipt-level allocation snapshot.

A prior W2 audit flagged a possible risk around repeated landed-cost allocation across partial receipts; this should be fixture-tested before relying on current landed cost for accounting.

## 7. Work-order actual material cost

Actual material cost should derive from real transactions:

```text
issued material cost
- returned unused material cost
+ scrapped material cost
+ substitute material actual cost
= net actual material consumed cost
```

Do not simply multiply released BOM quantity by current price after the work order completes.

For lot-controlled stock, use the cost layer associated with the actual lot/receipt policy.

## 8. Purchase price variance

If standard cost is used:

```text
PPV = actual acquisition cost - standard material acquisition cost
```

Expose variance separately from usage variance so the user can tell whether the problem is supplier price or manufacturing consumption.

Useful dimensions:

- supplier;
- MPN/source;
- material;
- month;
- product/work order;
- expedited vs normal purchase.

## 9. Material usage variance

For a work order:

```text
standard allowed quantity for accepted output
vs
actual net consumed quantity
```

Causes may include:

- scrap;
- overissue not returned;
- feeder/setup loss;
- rework;
- BOM error;
- engineering deviation;
- substitute quantity difference.

Do not hide these by increasing BOM quantity after the fact.

## 10. Labor and overhead

Current labor profiles and BOM operations are a useful standard-cost basis.

Separate:

- standard setup time;
- standard run time per unit/batch;
- standard labor rate;
- standard overhead rate;
- actual labor/time where captured;
- actual machine/test time where valuable.

For a small RF business, detailed clock-in MES labor capture may be excessive initially. Start with:

- optional actual labor minutes per WO/operation;
- explicit rework labor;
- calibration/test labor where material;
- standard-vs-actual comparison.

## 11. Fixed/setup cost allocation

A fixed setup charge should not be multiplied incorrectly by every unit.

Cost formulas must distinguish:

```text
batch/setup cost
per-unit run cost
per-order fixed external cost
```

Then divide batch costs across **accepted output quantity** according to policy.

Small work orders can show high unit cost due to setup; preserving this is useful for MOQ/pricing decisions.

## 12. Scrap and yield

Yield materially affects RF/electronics product cost.

Capture separately:

- input material scrap;
- failed subassembly/output;
- rework recovered output;
- accepted output.

Example:

```text
planned 20 units
material consumed for 22 equivalent units
18 pass first time
2 pass after rework
2 scrapped
```

Actual cost per accepted unit should not pretend the two scrapped units cost nothing.

## 13. Quality and rework cost

NCR/rework should contribute:

- additional material;
- replacement component;
- technician labor;
- retest time;
- subcontract rework fee;
- scrap/credit recovery.

This creates a valuable `cost of poor quality` view later.

Do not require finance-grade COPQ accounting on day one; preserve source transactions so it can be derived.

## 14. Subcontract cost

From `TASK_INV_AUDIT_SUBCONTRACT_01`, actual outside-processing cost can include:

- processing fee;
- setup/tooling;
- supplier-provided material;
- freight;
- rework/expedite;
- accepted scrap/loss.

Company-consigned material must not be counted again as purchased material from the subcontractor.

## 15. Firmware/test cost

For many RF modules, test/calibration can be a nontrivial cost driver.

Possible modeled/actual cost components:

- test technician time;
- long VNA/spectrum/power sweep station time;
- burn-in duration;
- calibration/tuning labor;
- consumables;
- test fixture amortization if policy justifies it.

Initially, model these as operation/labor/overhead lines and capture actual exceptions/rework rather than implementing equipment depreciation accounting.

## 16. Finished lot/serial cost

Recommended hierarchy:

- work order actual cost total;
- accepted output quantity;
- allocated actual unit cost;
- optional serial-specific additional rework/cost.

Not every serial needs a unique base cost if all units share one WO/lot. Add serial-level adjustments only where events differ.

## 17. Margin semantics

Pricing/margin screens should expose which cost basis they use.

For example:

```text
Quoted gross margin (reference cost)
Standard gross margin (released standard cost)
Realized gross margin (actual COGS/cost)
```

Never show `margin 42%` without cost basis/date/currency semantics.

For e-commerce channels, realized profitability may also require:

- platform fees;
- shipping subsidy/cost;
- refunds;
- promotion discounts;
- after-sales/replacement cost.

Those belong to later commerce/profitability integration, but the manufacturing cost foundation should support them.

## 18. Cost snapshot and reproducibility

Every important cost calculation should preserve:

- calculation date;
- cost method/version;
- BOM revision;
- standard-cost version where applicable;
- purchase cost/receipt sources;
- labor/overhead profiles;
- currency/rate assumptions if multi-currency;
- formula/software version when necessary.

A number that changes when opened next month is not a reliable historical cost record unless clearly labeled as `current estimate`.

## 19. Cost-close workflow

For work orders:

```text
WO operationally completed
 -> ensure material/return/scrap/subcontract transactions resolved
 -> quality accepted output known
 -> calculate actual cost
 -> review exceptions
 -> cost closed
```

Post-close corrections should create adjustment records, not silently rewrite the original close.

A lightweight close is sufficient initially.

## 20. Minimal target model

```text
work_order_cost_snapshots
  work_order_id
  status
  cost_method
  standard_cost_version_id
  material_actual
  labor_actual
  overhead_actual
  subcontract_actual
  freight_actual
  rework_actual
  scrap_cost
  accepted_output_qty
  actual_unit_cost
  closed_at/by

cost_variances
  work_order_id
  variance_type: purchase_price | usage | labor | overhead | subcontract | scrap | other
  standard_amount
  actual_amount
  variance_amount
  explanation/reference

cost_adjustments
  source_cost_snapshot_id
  amount
  reason
  approved_by
  created_at
```

Detailed transaction cost should continue to live with source receipts/issues/events; the snapshot summarizes and freezes the result.

## 21. Priority roadmap

### P0

1. relabel current `total_cost` output as estimated/reference cost where appropriate;
2. released MBOM-based standard cost;
3. cost-version/effectivity snapshot;
4. WO actual material from issue/return/scrap;
5. accepted-output denominator;
6. subcontract actual cost;
7. simple WO cost close.

### P1

1. standard vs actual variance categories;
2. actual labor/rework capture;
3. lot/receipt cost-layer linkage;
4. quality/scrap cost analytics;
5. margin screens with explicit cost basis.

### P2

1. accounting-system integration;
2. formal moving-average/FIFO/standard valuation according to finance policy;
3. period close and financial reconciliation;
4. product-line/customer/channel realized profitability.

## 22. Acceptance signals

- opening a historical standard cost does not silently recalculate using today's BOM/prices;
- a completed WO's actual material cost derives from actual issue/return/scrap events;
- purchase-price and material-usage variances are distinguishable;
- rework and scrap increase actual cost rather than disappearing;
- subcontract processing cost is included without double-counting consigned material;
- partial/failed output uses accepted quantity when calculating actual unit cost according to policy;
- pricing shows whether it uses current estimate, standard or actual cost;
- post-close correction is an adjustment with reason/actor rather than destructive overwrite;
- no required costing/close/reconciliation path depends on GitHub Actions.

## 23. Core recommendation

Keep and rename the current recursive cost engine as a strong **reference/engineering cost estimator**, then add revisioned standard cost and work-order actual-cost snapshots. The critical transition is from `what should this product cost?` to `what did this specific released build actually consume and why did it vary?`.