# TASK_INV_IMPL_E11 — Pricing Safety, Standard/Actual Cost & Channel Economics

## Status
`DESIGN_READY_SPLIT_EARLY_AND_LATE`

E11-S01/S02 are intentionally early safety bridges after E01 pricing extraction. Remaining E11 stories depend on E05–E10 execution evidence.

## Objective
Separate and connect four different commercial/cost truths:

```text
Pricing semantics / floor control
Reference engineering cost
Released standard manufacturing cost
Actual realized WO/order/channel economics
```

Do not collapse these into one `total_cost`, `margin_percent` or generic fee field.

## Boundaries

```text
current CostService = reference/engineering estimator
E05 = released MBOM/configuration
E06/E07/E08 = actual manufacturing/quality/subcontract evidence
E09 = channel observations/settlement source identity
E10 = refund/RMA/replacement evidence
E11 = cost snapshots, economic events, reconciliation and profitability
formal GL/tax filing = external accounting boundary unless scope expands intentionally
```

## Evidence quality
Commercial outputs label basis, e.g.:

```text
REFERENCE_ESTIMATE
RELEASED_STANDARD
PARTIALLY_ACTUAL
SETTLED
RECONCILED
```

Never present estimated contribution as finance-grade settled truth.

## Core formulas
Keep markup, gross margin and contribution margin explicitly distinct. Historical pricing formula semantics remain versioned.

## Manufacturing cost layers

```text
reference estimate
 -> released standard cost version
 -> WO actual material/labor/overhead/subcontract/rework/scrap
 -> accepted output unit cost
 -> post-close adjustment only, never silent rewrite
```

## Commerce economics
Use append-only normalized events for revenue, seller discount, platform subsidy, commission, payment fee, outbound/return freight, refund, penalty, after-sales and other attributable events.

Actual platform/carrier settlement observations reconcile against expected economics; they never rewrite original order price to hide differences.

## Definition of done
A user can explain:

- why a selling price was allowed;
- what cost basis a quote used;
- what a released product standard cost was;
- what a specific WO actually cost and why it varied;
- what a shipped order/channel actually contributed after fees/freight/refunds/RMA;
- which parts are estimated versus settled/reconciled evidence.