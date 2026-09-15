# TASK_INV_AUDIT_EXEC_REPORTING_01 — Owner / Management Reporting and Operational Cockpit Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed current dashboard/todo behavior, orders, inventory, purchasing, pricing, operation logs and the W3/W4 target domains for manufacturing, quality, CRM, after-sales and channel economics.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The existing dashboard is already useful as an **operator action board**. It should not be overloaded into a 30-card management dashboard.

Management needs a separate cockpit answering three progressively deeper questions:

```text
1. What is at risk today?
2. Is the business/process getting better or worse?
3. Where should cash, engineering time and management attention go next?
```

The correct reporting model is therefore:

```text
Exception cockpit
 -> Functional health trends
 -> Business economics / portfolio decisions
```

All management metrics must expose definition, source, freshness and evidence quality. Profitability, manufacturing yield, CRM conversion and RMA metrics must not be fabricated before their underlying target domains exist.

Preliminary management-reporting maturity: **1.5/5**, while the current operational dashboard itself is approximately **3.5/5**.

## 2. Preserve the operational home screen

The existing dashboard already surfaces actionable signals such as:

- pending order confirmation;
- pending shipments;
- transfer work;
- stock warnings;
- platform synchronization issues;
- completed activity;
- exceptions/todos.

Keep that as the staff default.

Management reporting should be a separate view/drill-down so routine operators are not forced through finance/strategy charts to ship an order.

## 3. Management cockpit structure

Recommended top-level sections:

### A. Attention now

- critical stockouts/shortages;
- overdue purchase orders;
- orders at SLA risk;
- platform sync/reconciliation failures;
- production shortage/late WO later;
- quarantine/NCR backlog;
- overdue RMA/customer cases;
- negative-margin or settlement anomalies.

Every item must have an owner and direct action/drill-down.

### B. Flow health

- sales/orders;
- fulfilment;
- procurement;
- inventory;
- manufacturing;
- quality/test;
- after-sales.

Show trends and bottlenecks, not only totals.

### C. Economics and capital

- revenue;
- gross/contribution profit;
- inventory value/cash tied up;
- excess/slow/dead stock;
- purchase commitments;
- WIP/external WIP;
- product/channel profitability;
- RMA/warranty burden.

### D. Product/strategy

- top/bottom product scorecards;
- demand gaps;
- supply-risk products;
- quality-burden products;
- products needing reprice/redesign/EOL decision.

## 4. Daily management view

A daily owner view should be concise and exception-first.

Suggested contents:

```text
Critical exceptions
Orders received / shipped / overdue
Stockouts and imminent shortages
POs due/late
Platform sync/settlement failures
Customer/RMA cases overdue
Production/quality blockers later
Yesterday/today cash-impact anomalies
```

Do not use daily revenue alone as the primary health indicator for low-volume project/RF sales; show pipeline and operational risk too.

## 5. Weekly operating review

Recommended weekly sections:

### Sales / CRM

- inquiries opened;
- quotes sent/accepted/lost;
- quote conversion;
- overdue follow-up;
- major opportunities;
- samples outstanding.

### Commerce / fulfilment

- orders/units/revenue;
- on-time shipment;
- cancellation/refund;
- stockout/backorder;
- channel synchronization exceptions.

### Procurement / inventory

- overdue POs;
- supplier on-time performance;
- shortage incidents;
- inventory value/cover;
- slow/dead-stock movement;
- major price changes.

### Manufacturing / quality after W3 implementation

- WOs due/completed;
- material readiness;
- first-pass yield;
- scrap/rework;
- NCR/quarantine;
- test failures.

### Customer / after-sales

- cases opened/closed;
- SLA breaches;
- RMA/warranty rate;
- repeated failure patterns.

### Economics

- contribution profit by channel/product;
- negative-margin orders;
- settlement mismatches;
- major cost variance.

## 6. Monthly management review

Monthly reporting should focus less on individual tickets and more on resource allocation:

- revenue and contribution trend;
- inventory turns/working capital;
- product portfolio scorecard;
- supplier concentration/risk;
- manufacturing yield/cost trend;
- warranty/RMA cost;
- forecast/replenishment accuracy;
- channel profitability;
- product development demand signals;
- strategic actions from prior review and completion status.

Record management decisions and owners so the report becomes an operating loop rather than passive BI.

## 7. KPI governance

Reuse the W2 dashboard recommendation for a metric registry.

Every KPI should define:

```text
metric_code
business question
formula
numerator / denominator
included statuses
excluded statuses
source tables/events
business timestamp
timezone
scope rules
freshness
owner
evidence class / limitations
```

A management dashboard without these contracts will eventually display internally inconsistent numbers.

## 8. Evidence-quality states

Important especially during phased rollout.

Recommended badge:

```text
COMPLETE_ACTUAL
PARTIAL_ACTUAL
ESTIMATED
STALE
INSUFFICIENT_DATA
```

Example:

`Contribution Margin: ESTIMATED` because product cost is standard and platform settlement has not been imported.

Do not hide incomplete data behind precise percentages.

## 9. Metric drill-down invariant

Every important management number should drill down to the records that compose it.

Examples:

```text
Late PO: 8
 -> list of eight POs

Quarantine value: ¥X
 -> lots/NCRs

Negative contribution orders: 5
 -> order economics events

RMA rate: 3.1%
 -> shipped population + RMA cases
```

If a number cannot explain itself, it should not be used as a management control metric.

## 10. Time-series discipline

Persist lifecycle timestamps rather than infer all history from `updated_at`.

Required examples across domains:

- order imported/confirmed/reserved/shipped;
- PO submitted/approved/promised/received;
- WO released/started/completed;
- quality inspection opened/released;
- RMA opened/received/resolved;
- quote sent/accepted/lost;
- settlement event occurred.

Historical trend must use the business event date appropriate to the question.

## 11. Inventory capital view

A particularly important owner view for electronics:

```text
Total inventory value
 -> saleable finished goods
 -> components/raw material
 -> reserved stock
 -> engineering/project stock
 -> quarantine
 -> WIP
 -> subcontract/external WIP
 -> slow/dead/EOL exposure
```

Then identify top cash-concentration materials/products and whether supply risk justifies it.

Do not use one raw quantity balance to value every stock state equally without accounting/cost policy.

## 12. Cash commitment / purchase exposure

Show:

- approved/open PO value;
- due this week/month;
- overdue undelivered value;
- supplier concentration;
- long-lead commitments;
- orders placed for demand that was later cancelled;
- EOL/last-time-buy exposure.

This complements physical inventory and helps prevent cash being trapped in components.

## 13. Fulfilment/service view

Management should see both speed and promise quality:

- order-to-ship median/P90;
- on-time shipment vs promised/due time when available;
- backorders;
- stockout-caused delay;
- split/replacement shipment;
- cancellation/refund rate;
- platform reconciliation errors.

Do not optimize average cycle time while hiding long-tail exceptions.

## 14. Procurement/supplier view

Useful indicators:

- supplier on-time delivery;
- actual lead time vs planned;
- purchase price trend;
- IQC rejection rate;
- supplier NCR/SCAR;
- shortage exposure by supplier;
- sole-source risk;
- open PO aging;
- expedite frequency/cost.

Provide supplier and critical-item drill-down.

## 15. Manufacturing/quality view

Once W3 is implemented:

- WO schedule attainment;
- material readiness;
- standard vs actual consumption;
- first-pass yield;
- rework/scrap;
- test pass/fail trend;
- quarantine/NCR aging;
- actual unit cost variance;
- subcontract yield/late return.

For low-volume RF builds, use counts plus context; percentages over tiny sample sizes can be misleading.

## 16. Sales/product view

Combine CRM and product intelligence:

- inquiry volume by product/frequency/spec need;
- quote conversion;
- win/loss reasons;
- average selling price;
- contribution margin;
- stock availability;
- support/RMA burden;
- supply/manufacturing risk;
- product lifecycle.

This enables decisions such as `stock more`, `reprice`, `improve listing`, `redesign`, `make-to-order` or `retire`.

## 17. Alerts versus reports

Use two different semantics:

### Alert

Condition requires action now; deduplicated, owned and resolvable.

### Report/KPI

Trend/context for management decision; not itself a workflow object.

Do not create alerts for every KPI movement. Alert fatigue will destroy the value of the operational cockpit.

## 18. Decision/action log

Monthly/weekly review should record decisions:

```text
management_actions
  source_review/report
  decision_type
  object/product/supplier/domain
  action_text
  owner
  due_date
  status
  expected_outcome
  closed_at
```

Examples:

- build alternate supplier for SAW filter;
- stop replenishing slow SKU;
- raise price floor;
- redesign high-RMA module;
- buy safety stock before component EOL.

Next review should show whether previous actions were completed and whether metrics improved.

## 19. Reporting implementation architecture

Use simple layers first:

```text
transactional DB
 -> metric queries/views
 -> cached daily snapshots where needed
 -> API
 -> dashboard/report UI
```

Only introduce a separate analytics warehouse if data volume/query load eventually justifies it.

For historical management metrics, daily/monthly metric snapshots can preserve reproducibility and reduce expensive recalculation.

## 20. Scheduled reports

Possible server-side outputs:

- daily exception digest;
- Monday operating review;
- month-end management pack;
- product/supplier risk review.

Use application worker/systemd timer/cron. Required generation/delivery must not depend on GitHub Actions.

## 21. Role-tailored views

Recommended tailoring:

- owner: cross-domain exceptions, cash, profit, product decisions;
- warehouse lead: fulfilment/inventory/transfer;
- procurement: shortage/PO/supplier;
- production/quality: WO/yield/NCR/test;
- sales/support: opportunity/quote/case/RMA;
- finance/admin: settlements/cost/economic reconciliation.

Do not rely on frontend hiding alone; metric/query scope must respect server-side permissions.

## 22. Priority roadmap

### P0

1. keep operator dashboard separate from management cockpit;
2. metric registry/definitions;
3. exception-first daily owner view;
4. inventory cash/aging/stockout views from available trustworthy data;
5. PO/fulfilment trend drilldowns;
6. metric evidence-quality state;
7. management action log.

### P1

1. CRM/quote conversion;
2. channel contribution/settlement;
3. W3 manufacturing/quality KPIs;
4. product/supplier scorecards;
5. scheduled daily/weekly/monthly reports;
6. snapshot/caching for historical trends.

### P2

1. predictive risk/anomaly summaries;
2. scenario planning;
3. natural-language management query over governed metrics;
4. separate analytics store only if scale requires it.

## 23. Acceptance signals

- operator home page remains fast/action-oriented rather than becoming a BI wall;
- every management KPI has definition/source/time scope/evidence state;
- every critical number drills into supporting business records;
- incomplete contribution/manufacturing metrics are labeled estimated/insufficient rather than invented;
- inventory view distinguishes saleable/reserved/quarantine/WIP/etc. as those domains become available;
- weekly/monthly decisions have owner/due date and are reviewed later;
- P90/exception trends prevent averages from hiding operational pain;
- role-scoped users cannot gain unauthorized data through analytics APIs;
- no required reporting/snapshot/scheduler path depends on GitHub Actions.

## 24. Core recommendation

Preserve the strong operational action board and add a separate **exception-first management cockpit with governed metrics, drill-down evidence and decision follow-through**. The purpose is not more charts; it is to connect inventory, orders, procurement, manufacturing, quality, product and profit data to the next management action.