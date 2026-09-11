# TASK_INV_IMPL_E08_S06 — Subcontract Order, Consigned Material & External WIP

## Status
`DESIGN_READY_BLOCKED_BY_E07_GATE`

## Objective
Represent outside processing as a first-class operational transformation while preserving ownership of company-supplied material.

## Order contract
A subcontract order references:

- supplier;
- source WO where applicable;
- exact product/material revision;
- released MBOM / release package;
- planned output quantity;
- expected return date;
- input ownership mode: supplier-owned, company-consigned or mixed;
- linked commercial PO/service line where applicable.

Lifecycle starts:

```text
draft -> approved -> material_prepared -> sent
```

## Dispatch / external WIP
Company-owned material dispatch must:

- reserve and pick through E02/E03;
- post an E02 movement from local usable stock to an external-WIP/custody state;
- retain subcontract order, material line and lot/serial references;
- remove quantity from local ATP;
- keep quantity visible as company-owned asset/WIP at the subcontractor.

Do not model a subcontractor as a normal internal warehouse merely to reuse transfer screens.

## Material line evidence
Track at least required, reserved, sent, returned-unused, consumed, scrap/process-loss and unresolved-variance quantities, plus ownership and actual captured lot/serial level.

## Tests
- sent company-owned material leaves local ATP;
- ownership remains company-owned;
- supplier-owned input does not create company stock;
- mixed ownership remains separable;
- released package/revision is frozen;
- duplicate dispatch is blocked by idempotency.

## Done
The system can answer exactly how much company material is currently physically held by each subcontractor and why.