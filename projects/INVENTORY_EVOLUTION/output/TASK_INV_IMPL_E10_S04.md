# TASK_INV_IMPL_E10_S04 — Sample / Evaluation Lifecycle & Customer Link

## Status
`DESIGN_READY_BLOCKED_BY_E02_E07_FOUNDATIONS`

## Objective
Manage samples and evaluation units as explicit customer/opportunity transactions instead of zero-price orders or free-text stock adjustments.

## Dispositions
At minimum distinguish:

```text
gift
paid_sample
loan/evaluation
refundable_sample
```

Lifecycle may include:

```text
requested -> approved -> prepared -> shipped -> customer_evaluating
 -> return_due -> returned | converted_to_sale | lost/damaged | closed
```

## Inventory rules
- sample reservation/issue uses E02 stock/reservation ledger;
- loaned/evaluation units remain company-owned but are excluded from normal ATP;
- gifted units leave company ownership through explicit movement;
- returned serialized RF units enter E07 quarantine/verification before saleable restock;
- exact serial is recorded for high-value serialized products.

## CRM linkage
Each sample links customer, opportunity, owner, purpose, expected return where applicable, quote/order conversion where relevant and activity timeline.

## Tests
- loaned unit remains company-owned/non-ATP;
- gifted sample is not tracked as receivable asset;
- overdue return is queryable;
- returned sample cannot directly enter ATP without quality policy;
- conversion to sale preserves original sample/serial history.

## Done
Sample activity becomes visible customer/product evidence rather than unexplained inventory leakage.