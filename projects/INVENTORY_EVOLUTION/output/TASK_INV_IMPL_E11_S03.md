# TASK_INV_IMPL_E11_S03 — Released Standard Cost Version

## Status
`DESIGN_READY_BLOCKED_BY_E05_E04_FOUNDATIONS`

## Objective
Create an immutable, effective standard-cost version distinct from the current live/reference estimator.

## Contract
Standard-cost version freezes:

- cost version/effective dates/status;
- material/product revision;
- released MBOM revision;
- component standard/acquisition assumptions;
- labor/overhead profiles;
- subcontract/freight standard assumptions where used;
- calculation snapshot and total standard cost.

## Rules
- released standard cost is immutable; new assumptions create a new version;
- historical quote/order/WO can reference the version used at that time;
- current `CostService` remains a reference estimate until explicitly backed by a released version;
- valuation method/accounting policy is not invented by this story.

## Tests
- new MBOM/current prices do not rewrite released standard cost;
- draft cost version cannot be used where released standard is required;
- same revision may have sequential effective standard versions without destroying old one;
- calculation snapshot identifies source assumptions.

## Done
The system can answer “what cost did we formally plan for this product/revision at that time?” independently of today’s BOM/prices.