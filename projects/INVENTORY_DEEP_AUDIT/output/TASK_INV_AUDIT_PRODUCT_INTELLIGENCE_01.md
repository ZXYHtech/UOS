# TASK_INV_AUDIT_PRODUCT_INTELLIGENCE_01 — Product Portfolio and Commercial Intelligence Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed material/product master, pricing, orders, inventory, dashboard/KPI findings, W3 manufacturing/cost requirements and W4 CRM, forecasting, RMA and channel-economics designs.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite has enough operational data to become a strong **product portfolio intelligence system**, but it should not begin by inventing one opaque product score.

The product decision problem for an RF/electronics company spans several dimensions that currently live in separate domains:

```text
market demand
+ conversion
+ realized margin
+ inventory efficiency
+ supply risk
+ manufacturing complexity
+ quality/aftersales burden
+ product lifecycle
+ strategic fit
```

The correct architecture is a transparent product scorecard with source metrics and evidence quality, followed by configurable decision rules. A composite score may be added only as a convenience layer.

Preliminary maturity:

- product master/commercial attributes: 3/5
- sales and inventory evidence: 2.5–3/5
- realized profitability evidence: 1/5 until channel economics exists
- inquiry/conversion evidence: 0.5/5 until CRM exists
- manufacturing/quality complexity evidence: 0.5/5 until W3 execution exists
- portfolio scorecard: 0.5/5

## 2. Questions the product scorecard should answer

For every sellable product/SKU/family, management should be able to answer:

- Is demand growing, flat, intermittent or declining?
- Are inquiries converting into orders?
- Does the product generate gross and contribution profit?
- How much cash is tied up in its finished/component inventory?
- Does it stock out often?
- Does it create slow/dead stock?
- Is its BOM exposed to single-source/EOL/high-lead-time parts?
- Is it difficult to build/test?
- Does it generate disproportionate RMA/support workload?
- Is it strategically important despite weak current volume?
- Should we stock more, improve it, reprice it, redesign it, promote it, make-to-order it or retire it?

## 3. Product identity and aggregation hierarchy

Do not score only raw material rows. Establish hierarchy:

```text
Product family
 -> Product / SPU
 -> Variant / configuration
 -> Sellable SKU
 -> Product revision
```

Examples for RF modules:

- family: LNA module;
- product: 1.6 GHz low-noise amplifier;
- variant: SMA / enclosure / supply option;
- SKU: exact commercial item;
- revision: hardware release.

Commercial metrics may aggregate at SKU/product/family level; quality and manufacturing metrics often need revision-level drill-down.

## 4. Metric groups

### Demand

- units/revenue by 30/90/180/365-day window;
- trend;
- order count;
- inquiry count;
- quote count;
- quote-to-order conversion;
- unique customers;
- repeat purchase;
- lost opportunities by reason;
- stockout-censored demand warning.

### Profitability

- list/average realized selling price;
- standard/reference product cost;
- realized COGS where available;
- gross profit/margin;
- contribution profit/margin;
- RMA/warranty cost;
- channel/account mix;
- price discount/override frequency.

### Inventory efficiency

- on-hand/nettable stock;
- inventory value;
- days of cover;
- turns;
- aging;
- slow/dead stock value;
- stockout days/events;
- fill rate/backorder;
- write-off/scrap exposure.

### Supply risk

- approved sources count;
- preferred supplier lead time;
- supplier OTIF/quality;
- sole-source component count;
- lifecycle/EOL exposure;
- alternate/substitute readiness;
- MOQ/cash exposure;
- long-lead component concentration.

### Manufacturing complexity

- BOM line count/depth;
- unique critical parts;
- operation count;
- standard labor/test time;
- first-pass yield;
- rework/scrap;
- calibration/tuning intensity;
- subcontract dependency;
- actual-vs-standard variance.

### Quality and service burden

- NCR rate;
- RMA rate;
- warranty rate;
- first-pass test failure;
- support cases per shipped unit;
- common issue/root-cause concentration;
- average support/repair cost.

### Strategic/lifecycle

- lifecycle state;
- market/brand importance;
- platform/channel coverage;
- product roadmap role;
- custom/standard nature;
- certification/document readiness;
- replacement/successor product.

## 5. Measured versus inferred metrics

Every metric should declare its evidence class.

Recommended labels:

```text
MEASURED
DERIVED
ESTIMATED
MANUAL_ASSESSMENT
INSUFFICIENT_DATA
```

Examples:

- shipped units: measured;
- inventory turns: derived;
- expected contribution margin before settlement: estimated;
- strategic importance: manual assessment;
- repurchase rate without customer identity: insufficient data.

Do not rank products using unavailable metrics as if they were zeros.

## 6. Metric lineage

Reuse the dashboard KPI registry concept.

For each metric store/define:

- code/name;
- formula;
- source entities;
- time basis;
- scope/status filters;
- freshness;
- evidence class;
- limitations;
- owner.

This prevents `RMA rate` or `margin` from changing meaning between screens.

## 7. Product scorecard, not one magic score

Recommended top-level scorecard:

```text
Demand            0–5 / evidence
Profitability     0–5 / evidence
Inventory health  0–5 / evidence
Supply risk       0–5 / evidence
Manufacturability 0–5 / evidence
Quality/service   0–5 / evidence
Lifecycle         status
Strategic value   manual/configured
```

Scores should be banded from transparent metrics, not produced by an unexplained AI model.

## 8. Optional composite score

If a roadmap score is desired later:

```text
Composite = weighted dimensions
```

But expose:

- weights;
- raw metrics;
- missing-data handling;
- score date/version;
- reason for material score change.

Different decisions need different weights. `Stock more?` and `Develop successor?` should not necessarily use the same composite score.

## 9. Decision archetypes

Instead of only ranking 1–100, classify products into actionable groups.

Examples:

### Star / invest
High demand + healthy contribution + manageable supply/manufacturing risk.

### Demand exists, economics weak
Reprice, reduce cost, improve channel mix or simplify product.

### Profitable but supply constrained
Secure AVL/alternates, redesign risky parts or carry strategic stock.

### Good product, poor discoverability/conversion
Improve content, sales materials, channel listing or quote response.

### Inventory trap
Low movement + high stock value; stop buying, promote, repurpose or phase out.

### Quality burden
Good sales but high RMA/rework/support; prioritize engineering corrective action.

### Strategic niche
Low volume but intentionally retained for brand/key customers/platform coverage.

## 10. RF-specific portfolio insights

For RF modules, product intelligence should eventually reveal:

- which frequency bands receive most inquiries;
- gain/NF/power/attenuation ranges customers request but portfolio lacks;
- which connector/supply/enclosure variants create little sales but much complexity;
- which MMIC/SAW/filter parts create supply concentration;
- which products require unusually long tuning/test time;
- which product revisions drive failures;
- where a common core design can create a family of variants economically.

This can feed R&D roadmap decisions directly.

## 11. Inquiry-to-product-gap intelligence

CRM technical requirements provide a powerful future signal.

Aggregate unmet demand such as:

```text
requested frequency range
requested gain/power/NF
requested interface/enclosure
requested target price
quantity opportunity
reason current products do not fit
```

Then compare against existing product specifications.

Do not infer market demand solely from search terms or one inquiry. Weight by opportunity value, recurrence, customer diversity and conversion evidence.

## 12. Inventory cash view

For each product/family, include cash tied in:

- finished goods;
- dedicated components;
- shared components apportioned carefully;
- WIP;
- external/subcontract stock;
- obsolete/slow stock.

Avoid double-counting shared component inventory across several products. A shared-component exposure view is better than pretending each product owns the full stock value.

## 13. Component risk roll-up

Released MBOM/AVL allows a product-level supply-risk roll-up:

- component has no approved alternate;
- only one supplier;
- long lead time;
- NRND/EOL;
- high MOQ/value;
- recurrent IQC issue;
- low current cover.

The result should identify the specific risky components, not just display `Supply risk = 72`.

## 14. Product complexity cost

Low-volume electronics often loses profit through complexity rather than BOM material alone.

Track proxies:

- number of variants;
- unique BOM lines;
- manual assembly operations;
- calibration/tuning time;
- test duration;
- exception rate;
- rework rate;
- support burden;
- document/configuration variants.

This can identify products where redesign/simplification has greater value than negotiating component price.

## 15. Lifecycle decisions

Recommended lifecycle states:

```text
CONCEPT
ENGINEERING
INTRODUCTION
ACTIVE
LIMITED / MTO
NRND
LAST_TIME_BUY
EOL
OBSOLETE
```

Transitions should consider open quotes/orders, service obligations, remaining stock and component availability.

Retiring a SKU must not erase historical commercial/manufacturing data.

## 16. Product review cadence

Useful cadence:

- weekly: exceptions such as stockout/negative margin/quality spike;
- monthly: product scorecard and stock/cash review;
- quarterly: portfolio investment/retirement roadmap review.

Calculations can run server-side; GitHub Actions is not required.

## 17. Minimal analytical model

Avoid prematurely copying all metrics into product-master columns.

Use materialized/cache snapshots where needed:

```text
product_metric_snapshots
  product/material/revision scope
  metric_code
  period_start/end
  value
  evidence_class
  calculated_at
  source_version

product_review_decisions
  product_id
  review_date
  decision_type
  owner
  rationale
  linked_metrics_snapshot
  next_review_at
```

Many metrics can remain query-derived until scale requires caching.

## 18. Priority roadmap

### P0

1. product/family/SKU/revision aggregation contract;
2. metric lineage/evidence classification;
3. demand + price + inventory + lifecycle scorecard;
4. explicit missing-data handling;
5. inventory cash/aging/stockout indicators;
6. product review decision history.

### P1

1. contribution-margin metrics from channel finance;
2. inquiry/conversion/lost-reason metrics from CRM;
3. supply-risk roll-up from AVL/MRP;
4. manufacturing complexity/yield metrics;
5. RMA/support burden;
6. actionable archetype classification.

### P2

1. configurable composite product score;
2. AI-assisted insight summaries with cited source metrics;
3. portfolio scenario planning;
4. unmet technical-demand clustering;
5. product-family platform/market expansion recommendations.

## 19. Acceptance signals

- a product scorecard distinguishes measured/derived/estimated/missing data;
- one weak data source does not silently become zero and depress the score;
- any risk/score can drill into its underlying metric and source objects;
- product profitability uses explicit cost/evidence basis;
- stock cash does not double-count shared components without disclosure;
- product revision quality problems can be separated from family-wide performance;
- lost RF requirement patterns can be traced to actual opportunities;
- a management decision such as `MTO`, `invest`, `reprice` or `retire` is recorded with rationale and next review;
- no required calculation/report process depends on GitHub Actions.

## 20. Core recommendation

Build product intelligence as a **transparent multi-dimensional scorecard and decision history**, not a black-box ranking. The system's unique opportunity is to combine commerce, engineering, supply, manufacturing, test and after-sales evidence into one product view—exactly the information needed to decide what RF products to stock, improve, redesign or discontinue.