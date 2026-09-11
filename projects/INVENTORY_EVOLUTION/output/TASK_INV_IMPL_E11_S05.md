# TASK_INV_IMPL_E11_S05 — Manufacturing Cost Variance Classification

## Status
`DESIGN_READY_BLOCKED_BY_E11_S03_S04`

## Objective
Explain why actual manufacturing cost differs from released standard cost instead of exposing only one opaque total variance.

## Variance classes
Initial categories:

```text
PURCHASE_PRICE
MATERIAL_USAGE
SUBSTITUTION
SCRAP_YIELD
LABOR
OVERHEAD
SUBCONTRACT
REWORK_QUALITY
FREIGHT_OTHER
```

## Evidence
Each variance records work order, standard basis/version, actual source evidence, standard amount, actual amount, variance and source references/explanation.

Examples:
- supplier price changed -> purchase-price variance;
- more components consumed than allowed for accepted output -> usage variance;
- approved alternate cost differs -> substitution variance;
- failed output/rework -> scrap/rework variance.

## Rules
- do not “fix” variance by editing historical MBOM standard after the fact;
- unknown/unallocated difference remains explicit rather than silently forced into one category;
- quality/rework source should link E07 evidence;
- variance analytics are operational/management accounting, not statutory journal entries.

## Tests
- purchase-price and usage variance remain distinguishable;
- scrap increases actual cost and variance;
- approved substitute variance links actual material;
- standard revision remains frozen;
- unexplained difference cannot disappear through rounding/update.

## Done
A high-cost WO can be decomposed into actionable causes rather than simply labeled “over budget”.