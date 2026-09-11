# TASK_INV_IMPL_E11_S04 — Work-order Actual Cost & Cost Close

## Status
`DESIGN_READY_BLOCKED_BY_E06_E07_E08_FOUNDATIONS`

## Objective
Calculate what one completed manufacturing order actually consumed/incurred using execution evidence, then freeze a reviewed cost-close snapshot.

## Actual cost sources
At minimum:

- actual material issue less return plus scrap/substitution cost;
- actual/standard labor as configured;
- overhead basis;
- subcontract processing and external-WIP charges;
- rework/quality cost evidence;
- relevant freight or fixed/setup charges according to policy;
- accepted output quantity.

## Cost close

```text
WO operationally complete
 -> reservations/WIP/returns/scrap resolved
 -> accepted output known
 -> actual cost calculated
 -> exceptions reviewed
 -> cost closed
```

Post-close correction creates explicit adjustment; do not silently recompute the frozen close.

## Unit cost
Allocate total WO actual cost over accepted output according to explicit policy. Failed/scrapped output cost cannot simply disappear from denominator/economics.

## Rules
- actual material cost derives from actual movement/cost-layer evidence, not current BOM price;
- company-consigned subcontract material is not counted twice;
- actual cost remains distinct from reference and standard cost;
- serial-specific incremental repair/rework can be additive when materially different.

## Tests
- issue/return/scrap changes actual material cost correctly;
- partial accepted output affects unit-cost denominator;
- subcontract fee included without double-counting company material;
- closed snapshot does not change when current purchase prices/BOM change;
- post-close correction is an adjustment with actor/reason.

## Done
The system can answer “what did WO X actually cost?” from traceable source events rather than re-running today’s estimator.