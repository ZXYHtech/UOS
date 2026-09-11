# TASK_INV_IMPL_E12_S04 — Product Hierarchy & Transparent Portfolio Scorecard

## Status
`DESIGN_READY_BLOCKED_BY_E04_E10_E11_FOUNDATIONS`

## Objective
Create a product scorecard across commercial, inventory, supply, manufacturing, quality and lifecycle dimensions without hiding missing data or collapsing everything into one opaque score.

## Aggregation hierarchy

```text
Product family
 -> Product / SPU
 -> Variant / configuration
 -> Sellable SKU
 -> Product revision
```

Commercial metrics may roll up to SKU/product/family; quality/manufacturing must retain revision drill-down.

## Scorecard dimensions

- Demand
- Profitability
- Inventory health
- Supply risk
- Manufacturability
- Quality/service burden
- Lifecycle
- Strategic value

Each dimension shows source metrics and evidence class (`MEASURED`, `DERIVED`, `ESTIMATED`, `MANUAL_ASSESSMENT`, `INSUFFICIENT_DATA`).

## Rules
- missing metric is not zero;
- optional composite score exposes weights, raw metrics, missing-data handling and score version;
- different decisions may use different weighting, e.g. `stock more` vs `develop successor`;
- product/revision history remains after lifecycle retirement.

## Tests
- missing profitability evidence does not depress score as zero;
- revision-specific RMA/test failure can be separated from family trend;
- score drill-down resolves raw governed metrics;
- changing weights creates a new score version rather than rewriting prior review evidence.

## Done
Portfolio decisions can be explained from source evidence instead of trusting one black-box ranking.