# TASK_INV_AUDIT_PRICING_MARGIN_01 — Pricing, Margin and Commercial Truth Audit

## 0. Scope

Pinned evidence: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed pricing tables, `PricingService`, order-item price snapshots/revisions, purchase-cost history and recursive BOM cost behavior. No GitHub Actions dependency is used or recommended.

## 1. Executive conclusion

Inventory Lite already has a useful **commercial pricing engine**, not merely a single sales-price field. It supports price lists, validity windows, minimum quantity, channel/customer-group conditions, pricing rules, order-item price snapshots and price revision history.

However, it is not yet a reliable **profitability engine**. The current model can answer “what price should I quote?” much better than “did this sale actually make money after product cost, freight, platform fee, payment fee, refund, tax and after-sales cost?”.

The biggest semantic risk is `margin_percent`: current calculation applies the percentage to the selected list price (`list_price * (1 + value/100)`), which is a markup-like operation on selling price, not a cost-based gross-margin target. Calling this `margin_percent` can mislead users and future automation.

## 2. Confirmed capabilities

### Price master

Current schema contains:

- `price_lists`
- `material_prices`
- `pricing_rules`
- `material_price_revisions`
- `order_item_price_revisions`

Material prices include:

- price list
- price type
- amount
- minimum quantity
- validity range
- priority
- enabled state
- version

Price lists include currency, channel and customer group.

### Quote selection

`PricingService.quote()` selects an enabled price valid on a date and applicable to quantity, then applies a matching pricing rule.

Supported rule result types include:

- fixed price
- discount percent
- discount amount
- `margin_percent`

### Transaction price history

Order items can retain:

- list unit price
- deal unit price
- selected price list
- material price record
- pricing rule
- discount amount
- serialized price snapshot
- recorded timestamp/actor

Manual transaction-price change requires a reason and has revision history. This is a good audit-control foundation.

## 3. Important semantic issue: margin versus markup

Current `margin_percent` behavior is equivalent to:

```text
deal_price = list_price × (1 + percent)
```

That is not standard gross-margin target pricing.

For example, if cost is 80 and target gross margin is 20%:

```text
correct selling price = 80 / (1 - 0.20) = 100
```

A 20% markup on cost would instead produce:

```text
80 × 1.20 = 96
```

And applying 20% to an existing list price is a third concept again.

Recommendation:

- rename existing behavior to `markup_percent_on_base_price` if retained;
- introduce an explicit `target_gross_margin_percent` rule that requires authoritative cost input;
- distinguish gross margin, markup and discount everywhere in UI/API/docs.

## 4. Cost truth is not yet transaction truth

`CostService.material_cost()` can derive a useful estimated material/product cost from purchase history, BOM recursion and operation profiles.

That is valuable for quotation and product planning, but it is not enough for realized order profitability because the system currently lacks a unified order-level cost ledger for:

- actual component lot cost used by a manufactured unit;
- actual manufacturing labor/overhead from work orders;
- shipping cost;
- marketplace/platform commission;
- payment fee;
- advertising attribution where desired;
- tax;
- refund/return cost;
- replacement shipment/RMA cost;
- write-off or warranty reserve.

Therefore current “cost” should be labeled **estimated/reference cost** until W3 manufacturing traceability exists.

## 5. Recommended profitability model

Keep pricing and profitability separate.

### Pricing domain

Answers:

- what list price applies?
- what negotiated/customer/channel price applies?
- why did this price apply?
- who changed it?

### Cost domain

Answers:

- estimated standard product cost
- latest/weighted purchase cost
- manufacturing standard cost
- actual manufacturing cost when work orders exist

### Order economics domain

Per order/order line:

```text
Revenue
- discount
- product COGS
- platform fee
- payment fee
- outbound freight
- tax borne by seller
- refund/return loss
- after-sales/replacement cost
= contribution profit
```

Then expose:

- gross profit
- gross margin %
- contribution profit
- contribution margin %
- channel profitability
- SKU profitability
- customer profitability

## 6. Snapshot requirement

Profit reporting must not recompute all historical sales from today’s product cost.

When an order reaches an appropriate economic event, persist snapshots/events for:

- selling price
- cost basis and source
- channel fee basis
- shipping cost
- tax basis
- currency/exchange-rate basis if multi-currency is later introduced

Revisions must be additive/audited rather than silently rewriting history.

## 7. Missing commercial controls

### Floor price is a type but not yet a complete approval policy

A `floor` price type exists, but mature use requires:

- explicit floor-price resolution;
- warning/block policy;
- override permission;
- override reason;
- approval workflow above configurable thresholds;
- order history showing the exception.

### Customer pricing is lightweight

Customer group exists as a pricing condition, but there is not yet a mature customer/account contract model. W4 CRM/quote work should avoid embedding full CRM into PricingService; use customer IDs/groups as inputs.

### Channel economics are incomplete

`channel` can influence pricing selection, but channel fee schedules are not yet modeled as a first-class cost source.

## 8. Recommended implementation priority

### P0

1. Fix terminology around `margin_percent` before wider use.
2. Define canonical formulas for margin, markup and contribution margin.
3. Keep historical order-item price snapshots immutable/audited.
4. Do not present recursive BOM/purchase estimate as realized profit.

### P1

1. Introduce order economics records/events.
2. Add platform/payment/freight/refund cost categories.
3. Add floor-price override policy and audit trail.
4. Add standard cost version/effective date.
5. Add profit views by order/SKU/channel.

### P2

1. Link actual work-order cost and lot cost after W3 manufacturing exists.
2. Add scenario pricing and sensitivity analysis.
3. Add quote approval based on contribution margin thresholds.

## 9. Acceptance signals

A future implementation should locally verify:

- a target gross-margin rule produces mathematically correct price from authoritative cost;
- markup and margin tests use values where the results differ so terminology errors cannot hide;
- a historical completed order retains its price/cost snapshot after master prices/costs change;
- floor-price override requires permission and reason;
- platform fee/freight/refund change contribution profit without rewriting product master cost.

Run these via repository-local Python tests. An external CI may call them, but GitHub Actions is not required.

## 10. Preliminary maturity

0–5 static maturity:

- price-list model: 4/5
- rule-based quoting: 3.5/5
- price revision/audit: 4/5
- terminology/formula safety: 2.5/5
- standard/estimated product cost: 3/5
- realized order profitability: 1/5
- channel contribution margin: 1/5

## 11. Core recommendation

Do not turn pricing into accounting. Preserve the good pricing engine, fix margin semantics, then add a small independent **order economics ledger**. This gives the company reliable SKU/channel profitability without importing a full financial ERP.