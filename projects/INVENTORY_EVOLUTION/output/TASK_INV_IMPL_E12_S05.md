# TASK_INV_IMPL_E12_S05 — Supply / Manufacturing / Quality Risk Roll-up & Decision Archetypes

## Status
`DESIGN_READY_BLOCKED_BY_E04_E07_E08_E11_FOUNDATIONS`

## Objective
Turn detailed component, manufacturing and after-sales evidence into transparent product-level risks and actionable review archetypes.

## Roll-ups
Examples:

### Supply risk
- no approved alternate;
- sole supplier;
- long lead time;
- EOL/NRND;
- high MOQ/cash exposure;
- recurrent IQC issue;
- low cover.

### Manufacturing complexity
- BOM line/depth;
- unique critical parts;
- manual operations;
- calibration/tuning/test time;
- subcontract dependency;
- yield/rework/scrap;
- actual-vs-standard variance.

### Quality/service burden
- NCR/RMA/warranty rate;
- first-pass test failure;
- support cases per shipped unit;
- common defect/root-cause concentration;
- average repair/RMA cost.

## Decision archetypes
Transparent rule-driven categories may include:

```text
INVEST / STAR
DEMAND_EXISTS_ECONOMICS_WEAK
PROFITABLE_SUPPLY_CONSTRAINED
GOOD_PRODUCT_LOW_CONVERSION
INVENTORY_TRAP
QUALITY_BURDEN
STRATEGIC_NICHE
MTO / REPRICE / REDESIGN / RETIRE candidates
```

## Rules
- every risk names specific underlying parts/events, not only a score;
- low sample size is disclosed;
- shared component stock/cash is not double-counted across every product;
- strategic value may remain manual but is auditable/reviewed.

## Tests
- sole-source component identifies exact component/source evidence;
- quality burden normalizes against shipped population where available;
- shared inventory exposure avoids naive double count;
- archetype can explain which governed metrics triggered it.

## Done
A product review points to specific supply/manufacturing/quality causes and suggested decision class rather than a mysterious risk number.