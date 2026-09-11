# TASK_INV_IMPL_E08_S04 — Daily Netting, PAB, Pegging & Planning Exceptions

## Status
`DESIGN_READY_BLOCKED_BY_E07_GATE`

## Objective
Calculate shortages by date, not by one aggregate quantity, and preserve why each shortage/recommendation exists.

## Calculation
P0 uses daily buckets:

```text
PAB(t) = PAB(t-1)
       + qualified scheduled receipts(t)
       + firm planned receipts(t) when policy allows
       - gross requirements(t)
```

When PAB violates zero/safety-policy threshold, calculate net requirement and suggested release date using lead time and lot-sizing rules.

## Pegging
Maintain links from shortage/recommendation back to:

```text
component
 -> dependent-demand line
 -> parent WO/planned production
 -> originating sales/project demand when known
```

## Exceptions
At minimum:

- shortage by need date;
- release overdue;
- PO/WO/subcontract return late to demand;
- no approved source;
- invalid/unreleased MBOM;
- MOQ/order multiple creates excess;
- demand cancellation leaves excess;
- quality loss creates shortage;
- long-lead item outside horizon;
- substitute requires engineering approval.

## Determinism
Same run inputs and policies must yield the same PAB, shortage date, rounded quantity and exception set.

## Tests
Include partial incoming supply, multiple dated demands, MOQ rounding, lead-time release date, cancellation/excess, quarantine loss and pegging trace.

## Done
A planner can click any shortage and see the dated equation and business documents that produced it.