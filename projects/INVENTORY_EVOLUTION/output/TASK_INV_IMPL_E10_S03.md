# TASK_INV_IMPL_E10_S03 — Revisioned Quotation, Approval & Quote-to-Order Conversion

## Status
`DESIGN_READY_BLOCKED_BY_E11_PRICING_E04_E05_FOUNDATIONS`

## Objective
Make customer quotations immutable commercial evidence after send/acceptance, while reusing the existing pricing domain rather than creating parallel price logic.

## Quote structure
Separate stable quotation identity from immutable revisions.

Revision states:

```text
draft -> approved -> sent -> accepted | rejected | superseded
```

Sent/accepted revisions are not edited in place; negotiation creates a new revision.

## Line snapshot
Each quote line freezes:

- material/product revision/configuration;
- quantity/price tier;
- list/base price and applied pricing rule;
- quoted unit price;
- cost basis type/as-of evidence;
- gross/contribution margin estimate when available;
- lead-time promise basis;
- technical description snapshot;
- custom/optional flags.

## Approval
Reuse E11 pricing semantics/floor controls. Low-margin/floor override requires dedicated authority and reason. Unknown/stale cost basis produces warning/evidence quality, not invented margin certainty.

## Conversion
Accepted quote revision converts through an E01 idempotent action to one sales-order draft/commit path. The order preserves exact accepted quote revision, prices, terms and product identity snapshot.

## Tests
- Rev A remains unchanged after Rev B;
- accepted revision cannot be mutated;
- duplicate conversion creates one order;
- floor override requires authority/reason;
- master-price change after quote does not change historical quote/order commercial evidence.

## Done
Every order derived from a quote can prove exactly which commercial and technical revision the customer accepted.