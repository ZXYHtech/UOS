# TASK_INV_AUDIT_CHANNEL_FINANCE_01 — Channel Settlement, Fees, Freight, Tax and Contribution Margin Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed pricing/order/platform/purchase-cost structures, the W2 pricing-margin audit, W4 omnichannel/RMA requirements and schema searches for first-class marketplace settlement, commission and coupon models.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite has a capable sales-price engine and useful product-cost estimation, but the inspected schema does not show a first-class **sales-channel settlement/economics ledger** for marketplace commissions, payment fees, coupons/subsidies, outbound freight, refunds, settlement statements or true contribution profit.

The purchase domain does contain `freight_amount` and tax fields, which is useful for acquisition landed cost, but that is economically different from outbound order/channel cost.

Therefore the system can currently reason about **quoted selling price** much better than **cash/settlement truth and realized contribution margin**.

Preliminary maturity:

- price determination/history: 4/5
- estimated/reference product cost: 3/5
- sales-channel fee model: 0.5/5
- settlement reconciliation: 0.5/5
- refund/after-sales economics: 0.5/5
- realized contribution margin: 1/5

## 2. Separate accounting boundary from operational economics

The application does not need to become a full general ledger to answer operational profitability questions.

A practical boundary is:

```text
Order / shipment / refund / channel observations
 -> Order economics ledger
 -> Settlement reconciliation
 -> Export/post summary to formal accounting system later
```

The inventory system should preserve enough source evidence to explain product/channel profit without implementing every accounting rule itself.

## 3. Revenue truth

Order economics should start from actual transaction-level revenue, not current list price.

Potential components:

- item gross price;
- seller discount;
- platform coupon funded by seller;
- platform subsidy funded by platform;
- shipping charged to customer;
- tax included/excluded according to policy;
- manual adjustment;
- partial refund;
- full refund;
- exchange/replacement effects.

Store who funded a discount. A platform-funded subsidy is not equivalent to a seller-funded discount when calculating contribution profit.

## 4. Fee taxonomy

Introduce normalized economic event types rather than one `fee` number.

Example categories:

```text
PRODUCT_REVENUE
SELLER_DISCOUNT
PLATFORM_SUBSIDY
PLATFORM_COMMISSION
PAYMENT_PROCESSING_FEE
ADVERTISING_ATTRIBUTED_COST (optional)
OUTBOUND_FREIGHT
RETURN_FREIGHT
WAREHOUSE_FULFILMENT_FEE
TAX
REFUND
REFUND_FEE_REVERSAL
PLATFORM_PENALTY
WARRANTY_REPLACEMENT_COST
RMA_REPAIR_COST
OTHER_ADJUSTMENT
```

Not every channel will provide every category. Preserve platform-native code/name alongside normalized type.

## 5. Economic events rather than mutable totals

Recommended model:

```text
order_economic_events
  id
  order_id
  order_line_id optional
  shipment_id optional
  rma_id optional
  platform_account_id
  event_type
  source_type
  external_event_id
  occurred_at
  currency
  amount
  quantity optional
  tax_component optional
  raw_description
  payload/reference
  reconciliation_status
  created_at
```

Use unique external identity so importing the same settlement statement twice does not double-count revenue/fees.

Corrections should post adjustment/reversal events rather than editing settled history silently.

## 6. Cost of goods sold basis

Order economics must state which product cost basis is used.

Possible progression:

- current reference cost — useful but not historical truth;
- released standard cost — stable planning/management view;
- actual WO/lot cost — best realized manufacturing evidence when available.

Persist a snapshot/reference at the relevant business event. Historical profit should not recalculate using today's BOM/purchase cost.

For serialized RF modules, eventual ideal chain is:

```text
order line
 -> shipped serial
 -> work order/output cost
 -> actual/standard COGS snapshot
```

## 7. Outbound shipping cost

Shipping cost is distinct from procurement freight.

Capture:

- shipment/package;
- carrier;
- quoted shipping charge;
- actual carrier cost;
- customer-paid amount;
- platform shipping subsidy;
- seller-borne freight;
- return/replacement freight.

A single order may have several packages or replacement shipments, so freight should link to shipment/package rather than only order header.

## 8. Marketplace commission and payment fee

Fee schedules can be complex and change over time. Do not rely solely on a static percentage field.

Two complementary layers:

### Expected fee policy

Useful for quotation/scenario analysis:

```text
channel_fee_rules
  platform/account/category
  valid_from/to
  fee_type
  rate/fixed amount
  thresholds/rule_json
```

### Actual observed fee event

Authoritative for realized economics when platform settlement data is available.

Always prefer actual settlement event for retrospective reporting and retain expected-vs-actual variance.

## 9. Coupons and promotions

Distinguish:

- seller-funded coupon;
- platform-funded coupon/subsidy;
- store promotion;
- bundle discount;
- manual negotiated price;
- post-sale price adjustment.

The customer may pay less while seller settlement remains partially subsidized by the platform. One generic `discount_amount` cannot always explain cash economics.

## 10. Refund economics

W4 RMA established that financial refund and physical return are separate.

Channel finance should capture:

- refund amount;
- refund date;
- which lines/quantities;
- platform fee refund/reversal;
- non-refundable commission/processing fee;
- shipping refund;
- return freight;
- restocked inventory value;
- scrap/repair/write-down;
- replacement shipment cost.

A refunded order is not automatically zero-profit or zero-revenue until all fee/recovery events are known.

## 11. Tax boundary

Tax treatment is jurisdiction/accounting-policy dependent. Avoid implementing legal conclusions from a universal formula.

The operational model should preserve:

- tax amount reported by platform/order if known;
- whether prices are tax-inclusive/exclusive;
- tax code/rate snapshot where the business supplies it;
- source of tax calculation;
- adjustments/refunds.

Formal filing/general-ledger ownership can remain external unless the product scope intentionally expands to accounting.

## 12. Settlement statement import

A high-value feature is importing marketplace settlement statements/API data into a staging/reconciliation workflow:

```text
platform statement/API
 -> raw immutable source
 -> normalize rows to economic events
 -> match order/refund/shipment
 -> unresolved rows queue
 -> reconcile expected vs actual
 -> approve/close statement
```

Never let spreadsheet import silently mutate historical order totals without preview and idempotency.

## 13. Settlement identity

Recommended entities:

```text
settlement_batches
  platform_account_id
  external_statement_id
  period_start/end
  currency
  source_file/hash
  imported_at
  status

settlement_lines
  batch_id
  external_line_id
  external_order_id
  event_type
  amount
  occurred_at
  match_status
  canonical_order_id
  economic_event_id
```

Duplicate file/hash/statement ID should be detected deterministically.

## 14. Reconciliation

The system should independently compare:

### Expected

From local order/price/shipment/refund state:

- expected customer/order revenue;
- expected channel commission;
- expected shipping burden;
- expected refund.

### Actual

From platform/payment/carrier observations:

- actual settlement amount;
- actual fees;
- actual refunds;
- actual freight.

Differences become exceptions with category and owner.

Do not overwrite local order price to make a settlement mismatch disappear.

## 15. Contribution margin formulas

Define formulas explicitly and version them.

Example operational view:

```text
Net revenue
= product/customer revenue
+ platform subsidy
- seller-funded discounts
- refunds

Contribution profit
= Net revenue
- product COGS
- platform commission
- payment fee
- seller-borne outbound freight
- return/replacement freight
- variable fulfilment cost
- directly attributable after-sales cost
```

Then:

```text
Contribution margin % = contribution profit / net revenue
```

Clearly distinguish this from gross margin and markup.

Advertising may be shown as a second contribution layer rather than forced into product gross margin if attribution quality is weak.

## 16. Profitability dimensions

Useful reporting dimensions:

- order;
- order line/SKU;
- product family;
- channel/platform;
- individual shop/account;
- customer/customer group;
- sales owner;
- month/quarter;
- campaign where trustworthy;
- product revision;
- new vs returning customer later.

Always expose data completeness. A channel with no imported settlement fees should not appear equally trustworthy to one with fully reconciled actual costs.

## 17. Margin evidence quality

Add a quality/status indicator:

```text
ESTIMATED
PARTIALLY_ACTUAL
SETTLED
RECONCILED
```

For example:

- product cost = standard estimate;
- carrier cost = actual;
- platform fee = expected rule;
- refund status = actual;

Then dashboard can state `Estimated contribution margin` rather than presenting false accounting precision.

## 18. Negative-margin and anomaly controls

High-value alerts:

- order contribution < 0;
- channel fee deviates materially from expected rule;
- freight exceeds expected threshold;
- refund without matching order;
- settlement row unmatched;
- settled amount differs from expected net receivable;
- price below approved floor;
- repeated loss on a SKU/channel;
- RMA/replacement cost destroys margin;
- payment/settlement overdue.

Alerts should lead to the source events and reconciliation evidence.

## 19. Interaction with pricing

Pricing should consume expected economics for decision support, while settlement records retrospective actual economics.

Quote/order decision can show:

```text
quoted selling price
estimated product cost
expected channel/payment fee
expected freight
estimated contribution margin
```

After fulfilment/settlement:

```text
actual/reconciled contribution margin
variance vs estimate
```

This closes the loop from price decision to business outcome.

## 20. Interaction with procurement/manufacturing

Manufacturing standard/actual cost feeds COGS but should not absorb marketplace economics.

Keep boundaries:

- procurement: acquisition/landed component cost;
- manufacturing: standard/actual product cost;
- commerce finance: revenue, channel fee, shipping, refund, contribution;
- accounting integration: formal ledger/tax/statutory treatment.

This modular separation avoids turning one `CostService` into an unmaintainable finance engine.

## 21. Data import and security

Settlement data may contain customer/order financial details. Apply:

- least-privilege access;
- account/channel scope;
- immutable source-file hash;
- import preview;
- idempotent external identity;
- masked sensitive fields where needed;
- audit logs for manual adjustments;
- backup and retention policy.

Never store platform secrets in settlement payloads/logs.

## 22. Automation architecture

Server-local workers can own:

- periodic settlement pull/import;
- fee/refund normalization;
- reconciliation;
- anomaly generation;
- daily contribution refresh.

Use durable jobs/cursors/idempotency and restart-safe processing. Required operation must not depend on GitHub Actions.

## 23. UX priority

Recommended views:

1. order economics detail — revenue through contribution profit;
2. settlement import/reconciliation queue;
3. unmatched statement rows;
4. expected-vs-actual fee variance;
5. SKU/channel contribution dashboard;
6. negative-margin orders;
7. after-sales cost impact;
8. data-completeness/evidence status.

## 24. Priority roadmap

### P0

1. normalized order economic-event ledger;
2. explicit selling-price/COGS snapshot basis;
3. outbound freight cost;
4. commission/payment/refund fee categories;
5. contribution-margin formula definitions;
6. settlement statement staging/import;
7. idempotent order/event matching;
8. evidence-quality state.

### P1

1. platform API settlement ingestion;
2. expected fee-rule engine;
3. settlement reconciliation exceptions;
4. SKU/channel/account profitability;
5. RMA/replacement economics;
6. negative-margin/anomaly dashboard.

### P2

1. accounting-system export/integration;
2. richer tax mapping according to accountant-approved policy;
3. campaign/ad attribution where evidence quality is sufficient;
4. profitability-driven channel inventory and pricing suggestions.

## 25. Acceptance signals

- procurement freight is never mistaken for outbound customer-order freight;
- importing the same settlement statement twice cannot duplicate fees/revenue;
- a platform-funded subsidy and seller-funded discount produce different economics;
- historical COGS/profit does not recalculate from today's product cost silently;
- refund and physical return can be represented independently;
- expected and actual platform fees can be compared without rewriting order price;
- contribution margin explicitly states formula and evidence status;
- RMA/replacement costs can reduce the originating order/customer/SKU contribution result;
- unmatched settlement rows remain visible as exceptions;
- no required settlement/scheduler/reconciliation/test path depends on GitHub Actions.

## 26. Core recommendation

Add a small independent **order economics + settlement reconciliation ledger** between commerce operations and formal accounting. This will convert the existing strong pricing/order foundation into trustworthy SKU/channel profitability without forcing Inventory Lite to become a full financial ERP.