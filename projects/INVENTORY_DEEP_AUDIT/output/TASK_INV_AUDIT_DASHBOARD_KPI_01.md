# TASK_INV_AUDIT_DASHBOARD_KPI_01 — Dashboard, Alerts & Decision-Support Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed dashboard aggregation, unified todo concept, stock warnings, platform-sync counts and current source/data-model capabilities.

## 1. Executive conclusion

The current dashboard is a useful **operational action board**, not yet an executive/management BI system. That distinction should be preserved.

It already surfaces meaningful daily work signals such as pending confirmation, shipments, transfers, stock warnings, platform sync exceptions and completed activity. This is appropriate for a small team and should remain the default home screen.

The missing layer is decision support across time: inventory turns, aging, stockout service level, procurement performance, order cycle time, profitability, product contribution and manufacturing quality. Those should be added as drill-down analytical views rather than turning the home page into a dense BI dashboard.

## 2. Current dashboard behavior

The server-side dashboard is warehouse-scope aware and supports period filters such as today/week/month.

Observed counters include:

- period orders
- shipments created/completed
- transfers
- inventory movements
- pending confirmation
- pending shipments
- pending warehouse acceptance
- safety-stock warnings
- pending transfers/transfer confirmation
- pending platform sync or sync exception
- completed shipments
- exception orders

This is evidence of a genuine operational dashboard, not static UI cards.

## 3. Strong design principle: actionability

The home page should answer:

```text
What needs attention now?
Who owns it?
How urgent is it?
What is the next action?
```

It should not attempt to answer every management question.

The existing `UnifiedTodoService` is a good direction because it can aggregate work across domains instead of forcing staff to inspect ten modules manually.

## 4. KPI layers should be separated

### Layer A — Operational action board

Audience: warehouse/customer-service/operators.

Examples:

- orders needing review
- shipment tasks awaiting acceptance
- shipments waiting logistics
- stock below threshold
- transfer exceptions
- platform reconciliation failures
- OCR failures
- overdue receiving

Refresh frequently and link directly to the action.

### Layer B — Functional performance

Audience: functional owners.

Examples:

Warehouse:
- pick/pack cycle time
- shipment on-time rate
- count variance rate
- transfer lead time

Procurement:
- supplier on-time delivery
- PO aging
- purchase price variance
- shortage frequency

Sales/e-commerce:
- order volume
- cancellation/refund rate
- fulfilment cycle
- stockout-lost-order proxy

R&D/production later:
- shortage count by project/work order
- BOM readiness
- first-pass yield
- rework/scrap

### Layer C — Management economics

Audience: owner/management.

Examples:

- revenue
- gross profit
- contribution profit
- cash tied in inventory
- inventory turns
- aging/slow stock
- SKU/channel profitability
- forecast versus actual demand
- working-capital risk

Do not fabricate these from incomplete data. Each management KPI needs a declared data lineage.

## 5. Inventory analytics gaps

Current safety-stock warning is useful but insufficient.

Future inventory analytics should include:

- days of supply
- stockout events
- inventory age
- last movement date
- ABC/XYZ classification
- dead/slow moving inventory
- excess inventory
- demand velocity
- reserve/committed quantity
- transfer-in-transit quantity
- quality-hold quantity
- WIP once manufacturing exists

A single `quantity_available <= safety_stock` rule cannot represent all replenishment risk.

## 6. Time and denominator discipline

Metrics should define:

- event timestamp used
- timezone
- included/excluded statuses
- warehouse scope
- channel scope
- denominator
- late-arriving corrections

For example, “shipment completion rate” is meaningless unless the denominator is explicit: orders created, orders due, or shipment tasks accepted?

## 7. KPI lineage registry

Recommend a small registry:

```text
metric_code
name
description
owner
numerator_query/source
denominator_query/source
time_basis
scope_rules
freshness
limitations
```

This can be implemented as code/YAML or DB metadata. It prevents the dashboard from becoming a collection of numbers whose meaning changes over time.

## 8. Event timestamps need enrichment

Good operational analytics require lifecycle timestamps for business events, not only created/updated.

Future domains should persist timestamps such as:

- ordered/paid/imported/confirmed
- allocated
- picked/packed/shipped/delivered
- PO submitted/approved/promised/received
- work order released/started/completed
- NCR opened/dispositioned/closed

Do not derive all durations from mutable `updated_at`.

## 9. Alert model

A mature alert has:

- alert type
- severity
- object/domain
- actor/owner
- first detected
- last detected
- current state
- acknowledgement
- resolution
- deduplication key
- recommended next action

The current exception/todo aggregation can evolve into this without adding an external alerting platform initially.

## 10. Dashboard UX recommendation

Home screen:

1. top: critical actions and exceptions;
2. middle: today/this week workload and flow;
3. bottom: a small number of health indicators;
4. provide drill-down pages for analytical detail.

Avoid adding 30 KPI cards.

Recommended management landing views:

- Inventory Health
- Fulfilment Health
- Procurement Health
- Product Profitability
- Manufacturing/Quality Health after W3

## 11. Automation opportunities

Examples:

- low-stock alert becomes replenishment suggestion;
- repeated stockout triggers safety-stock review;
- overdue PO creates supplier follow-up todo;
- repeated OCR correction on one SKU creates master-data review;
- platform sync error creates retry job then human todo only after threshold;
- slow stock creates disposal/marketing review;
- negative contribution margin creates pricing review rather than silent report-only status.

## 12. No-Actions requirement

Metric calculation and alert generation must run through:

- request-time lightweight queries;
- server-side scheduled jobs;
- DB-backed worker tasks;
- optional cached aggregate tables.

Schedulers should be systemd timer/cron/application worker. GitHub Actions is not part of the runtime design.

## 13. Priorities

### P0

1. keep home dashboard operational/action-focused;
2. document metric definitions and scope;
3. add real lifecycle timestamps when new workflows are implemented;
4. avoid publishing profitability KPIs until order economics data exists;
5. unify exception/todo deduplication and ownership.

### P1

1. inventory age/turns/days-of-supply;
2. fulfilment cycle/SLA;
3. procurement lead-time/on-time delivery;
4. SKU/channel profitability after economics ledger;
5. alert acknowledgement/resolution state.

### P2

1. trend forecasting and anomaly detection;
2. management scorecards;
3. product roadmap scoring fed from sales/profit/stock/support data.

## 14. Preliminary maturity

- operational dashboard: 3.5/5
- warehouse scope/actionability: 3.5/5
- unified todo direction: 3.5/5
- time-series operational analytics: 2/5
- inventory health analytics: 2/5
- procurement performance: 1.5/5
- profitability/management BI: 1/5
- metric lineage/governance: 1/5

## 15. Core recommendation

Do not replace the useful action board with an ERP-style dashboard wall. Build a three-layer measurement system: **actions now -> functional performance -> management economics**, and require every KPI to have a traceable data definition.