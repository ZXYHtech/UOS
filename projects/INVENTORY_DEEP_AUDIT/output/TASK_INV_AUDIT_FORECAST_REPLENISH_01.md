# TASK_INV_AUDIT_FORECAST_REPLENISH_01 — Demand Forecast and Intelligent Replenishment Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed order history, inventory/safety-stock fields, purchasing, dashboard/KPI findings, platform/channel integration and W3 MRP requirements.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The application currently has enough data to build useful sales-velocity and low-stock analysis, but not enough planning semantics to justify opaque “AI replenishment.” The correct evolution is:

```text
clean demand history
 -> classify demand and anomalies
 -> calculate velocity/lead-time exposure
 -> policy-based reorder recommendation
 -> measure forecast/recommendation accuracy
 -> only then add advanced forecasting
```

The current `safety_stock` field is useful but too simple to represent different service levels, lead times, channel demand, manufacturing demand, MOQ/order multiple and slow-moving risk.

Preliminary maturity:

- basic stock warning: 2.5/5
- sales velocity analysis: 1.5/5
- lead-time-aware reorder: 1/5
- forecast engine: 0.5/5
- recommendation explainability: 0.5/5

## 2. Separate MRP from demand forecasting

W3 MRP answers dependent manufacturing demand and dated supply/demand netting.

Forecast/replenishment answers questions such as:

- how much of a stocked finished good or purchased component is likely to be needed;
- when should the company reorder to avoid stockout;
- how much safety stock is economically justified;
- which items are becoming slow/dead stock.

Forecast output should become an input to MRP/planning where appropriate, not replace MRP.

## 3. Demand history needs cleaning

Raw order quantities are not automatically true demand.

Classify/exclude or flag:

- cancelled orders;
- duplicate imports;
- refunded orders where sale was reversed;
- free samples;
- internal/project consumption;
- one-time bulk/customer project orders;
- replacement/warranty shipments;
- stockouts that suppressed actual demand;
- channel migration or listing downtime;
- abnormal promotion spikes.

Preserve both raw and adjusted series. Never silently rewrite history for the sake of model smoothness.

## 4. Demand dimensions

Recommended aggregation dimensions:

- internal SKU/material;
- product family;
- channel/platform/shop;
- customer/customer class;
- warehouse/fulfilment region;
- day/week/month;
- normal vs promotion/project/sample demand.

For low-volume RF modules, monthly or rolling 30/90/180-day views may be more meaningful than high-frequency forecasting.

## 5. Product classification

Different products require different policies.

Suggested simple classification:

### A — stable/fast-moving stocked product
Use statistical replenishment and service-level policy.

### B — intermittent/slow-moving product
Use longer windows, manual review and conservative stocking.

### C — project/custom/make-to-order product
Avoid demand-forecast stocking; plan from confirmed opportunities/orders.

### D — lifecycle/EOL product
Reduce replenishment and surface excess-risk controls.

Do not apply one forecast algorithm to every RF module, connector and expensive MMIC.

## 6. Baseline forecast models

Start with transparent baselines:

- trailing average;
- weighted moving average;
- exponential smoothing;
- same-period historical comparison where enough data exists;
- intermittent-demand methods later if justified.

Always compare advanced models against a naive baseline. A complicated model that cannot beat “last 90-day average” should not drive purchasing.

## 7. Lead-time demand

The key replenishment quantity is not simply monthly sales.

At minimum estimate:

```text
lead_time_demand
= expected demand during supplier/manufacturing lead time
```

Then:

```text
reorder_point
= lead_time_demand + safety_stock
```

Inputs must come from real supplier/source policies:

- lead time;
- MOQ;
- order multiple;
- reliability/late-delivery variability;
- approved source/alternate availability.

W3 MRP and AVL/supplier models are therefore prerequisites for trustworthy component replenishment.

## 8. Safety stock

Do not treat safety stock as one manually entered permanent integer.

Support policy/evidence:

- fixed quantity;
- days/weeks of cover;
- target service level later;
- lead-time variability;
- demand variability;
- criticality;
- supplier risk;
- lifecycle risk;
- product margin/value.

For expensive low-volume RF ICs, a manager may intentionally accept lower service level to reduce cash tied up. The system should show the tradeoff rather than hide it in an algorithm.

## 9. Days of inventory / cover

High-value operational metrics:

```text
stock cover days = nettable stock / recent average daily demand
```

Use warnings for:

- below lead-time cover;
- below target cover;
- excessive cover;
- no sales for N days;
- large stock value with low movement.

For intermittent items, clearly mark when cover metrics are unstable or not meaningful.

## 10. Reorder recommendation

Recommendation should be explainable:

```text
Suggested buy 200 pcs
because:
  nettable stock 48
  reserved 20
  open PO 50 due in 12 days
  expected lead-time demand 160
  target safety stock 40
  MOQ 100 / order multiple 100
```

Users should be able to accept, modify or reject with reason. Do not silently create purchase orders.

## 11. Open purchase orders

Replenishment must net:

- ordered quantity;
- already received quantity;
- remaining quantity;
- expected date;
- supplier delay risk.

A late PO should not be treated as equivalent to stock available today.

## 12. Channel effects

Omnichannel data can reveal:

- channel-specific velocity;
- listing launch/closure;
- promotional bursts;
- regional demand differences;
- marketplace stock caps hiding demand.

Forecast should operate on canonical internal SKU, then optionally provide channel breakdown. Do not independently forecast unmapped platform SKUs.

## 13. Lost-sales/stockout censoring

A product with zero sales while out of stock does not imply zero demand.

Track:

- stockout intervals;
- listing active/inactive state;
- unfulfilled/backordered demand;
- customer inquiry/quote demand where useful.

At least flag forecast periods contaminated by stockout so the model does not learn artificially low demand.

## 14. Lifecycle and EOL

Electronics inventory needs lifecycle-aware replenishment:

- active;
- NRND/not recommended;
- last-time-buy;
- EOL;
- obsolete.

For EOL components, replenishment may intentionally exceed normal forecast during last-time-buy, but that should be an approved risk decision with project/product coverage evidence.

## 15. Slow/dead stock

Useful classification should combine:

- no movement age;
- stock value;
- days of cover;
- open demand;
- product/component lifecycle;
- substitute/use-across-BOM opportunities.

Then actions:

- stop/reduce purchasing;
- transfer/reallocate;
- bundle/promote finished stock;
- use approved substitute strategy;
- consume in prototype/internal use;
- return to supplier if possible;
- write-off/scrap through controlled process.

## 16. Forecast accuracy

Every forecast version should later be scored.

Useful metrics:

- MAE;
- bias;
- WAPE/weighted error where appropriate;
- stockout rate;
- service level/fill rate;
- excess inventory value;
- planner override rate.

Do not optimize forecast error while ignoring inventory outcomes.

## 17. Recommendation history

Store each recommendation:

```text
replenishment_recommendations
  material/site
  generated_at
  model/policy_version
  horizon
  demand_forecast
  nettable_supply
  open_supply
  suggested_qty/date
  explanation_json
  accepted/changed/rejected
  final_qty
  actor/reason
```

This enables later learning from planner overrides and verifying whether automation improves outcomes.

## 18. Automation architecture

Scheduling and recalculation should run through server-local workers/timers, not GitHub Actions.

Possible cadence:

- nightly velocity/reorder calculation;
- immediate recalculation after large order/cancellation/PO change;
- weekly slow-stock review;
- monthly forecast accuracy review.

All jobs should be durable/restart-safe where business decisions depend on them.

## 19. UX priority

Recommended views:

1. replenishment action queue;
2. item planning card: stock, reservations, PO, velocity, lead time, cover;
3. forecast/history plot;
4. reason/explanation drawer;
5. slow/dead-stock board;
6. planner override history;
7. forecast accuracy dashboard.

Avoid an AI score without visible data inputs.

## 20. Priority roadmap

### P0

1. clean canonical demand history;
2. authoritative nettable stock/reservations;
3. supplier lead time/MOQ/order multiple;
4. rolling velocity/cover;
5. explainable reorder point recommendation;
6. open-PO netting;
7. slow/dead-stock exceptions.

### P1

1. transparent forecast baselines;
2. product demand classification;
3. safety-stock policy variants;
4. channel breakdown;
5. forecast accuracy/override tracking;
6. stockout-censored periods.

### P2

1. intermittent-demand models;
2. service-level optimization;
3. probabilistic forecasts;
4. opportunity/quote-weighted demand for selected custom products;
5. scenario simulation for supplier disruptions/EOL.

## 21. Acceptance signals

- cancelled/refunded/sample demand can be separated from ordinary sell-through;
- reorder calculation uses nettable stock and open PO remaining supply, not raw physical quantity;
- a late PO affects shortage timing;
- MOQ/order multiple explain why suggested buy differs from raw shortage;
- users can see exactly why a recommendation exists and override it with reason;
- stockout periods are flagged rather than learned as zero demand;
- forecast accuracy and inventory outcomes are measured after the fact;
- no required schedule/recalculation/test path depends on GitHub Actions.

## 22. Core recommendation

Start with **transparent lead-time-aware replenishment and inventory-cover analytics**, not black-box AI. Once the business has clean canonical demand, reservations, source lead times and recommendation history, more advanced forecasting can be added and objectively evaluated.