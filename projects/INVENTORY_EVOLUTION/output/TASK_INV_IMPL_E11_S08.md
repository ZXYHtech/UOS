# TASK_INV_IMPL_E11_S08 — Realized Contribution Profitability & Evidence Quality

## Status
`DESIGN_READY_BLOCKED_BY_E11_S03_S04_S06_S07`

## Objective
Expose trustworthy profitability by order/SKU/channel/customer while clearly labeling which inputs are estimated, actual, settled or reconciled.

## Formula layers
Keep explicit definitions such as:

```text
Net revenue
= product/customer revenue
+ platform-funded subsidy
- seller-funded discount
- refunds

Contribution profit
= net revenue
- COGS
- platform commission/payment fee
- seller-borne outbound/return/replacement freight
- variable fulfilment cost
- directly attributable RMA/repair/replacement cost
```

`Contribution margin % = contribution profit / net revenue` when denominator policy is valid.

Gross margin, markup and contribution margin remain different named metrics.

## Evidence state
At order/report level expose:

```text
ESTIMATED
PARTIALLY_ACTUAL
SETTLED
RECONCILED
```

and component evidence such as COGS basis, fee source, freight source and refund/RMA state.

## Dimensions
Support analysis by order, line/SKU, product/revision, channel/account, customer/group, sales owner and time period. Do not imply finance-grade precision when settlement/cost evidence is incomplete.

## Alerts
High-value exceptions include negative contribution, unusual fee/freight variance, unmatched settlement, price below floor, repeated loss by SKU/channel and RMA/replacement cost destroying margin.

## Tests
- same selling price with platform subsidy vs seller discount yields different contribution;
- reference-cost result is labeled estimated;
- actual WO COGS upgrades evidence quality without rewriting prior snapshots destructively;
- RMA/refund costs reduce originating order/customer/SKU contribution;
- reconciled result requires settlement reconciliation evidence.

## Done
Management can see not only “margin %” but what formula, cost basis and settlement evidence make that number trustworthy.