# E11 Implementation Sequence — Pricing, Cost & Realized Economics

## Status
`DESIGN_READY_SPLIT_EARLY_AND_LATE`

## Early bridge
After E01 pricing extraction and E00 gate:

### Slice A — S01 pricing terminology/formulas
Preserve legacy arithmetic exactly; introduce explicit target gross-margin semantics.

### Slice B — S02 floor/override safety
Add server-side floor resolution, dedicated override authority and immutable evidence.

These two may land before E02 because they are bounded safety fixes.

## Late manufacturing/economics wave

### Slice C — S03 released standard cost
Requires E04/E05 configuration truth. Does not change current reference estimator.

### Slice D — S04 WO actual-cost shadow calculation
Requires E06–E08 execution evidence. Start report-only and compare against hand fixtures before cost close authority.

### Slice E — S05 variance classification
Add actionable standard-vs-actual categories after actual-cost parity is proven.

### Slice F — S06 order economic-event ledger
Add append-only commerce events without settlement import initially.

### Slice G — S07 settlement staging/reconciliation
Pilot one channel/account with immutable source hash/idempotent matching.

### Slice H — S08 contribution profitability/read models
Only publish `SETTLED/RECONCILED` evidence states after upstream proof exists; otherwise label estimated/partial.

## Gates
Every slice runs deterministic local tests + E00 Release Gate. High-risk invariants:

- historical pricing arithmetic unchanged;
- below-floor override cannot bypass authority;
- released standard cost immutable;
- WO actual cost derives from source events;
- closed cost changes only by adjustment;
- settlement re-import cannot duplicate events;
- order price is never rewritten to hide settlement mismatch;
- formula/basis/evidence state accompanies every margin metric.

## Non-goals
No full GL/payroll/statutory tax engine. Accounting integration/export may come later under accountant-approved policy.