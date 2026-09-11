# TASK_INV_IMPL_E08_S01 — Planning Policy & Approved Sourcing Inputs

## Status
`DESIGN_READY_BLOCKED_BY_E07_GATE`

## Objective
Define the deterministic per-material/site assumptions MRP is allowed to use. Do not infer buy/make behavior from free text or historical transactions.

## Contract
Create a planning-policy layer keyed by internal material + site/warehouse with explicit fields for:

- procurement type: `buy | make | transfer | mixed`;
- safety stock / reorder policy where used;
- daily planning horizon;
- purchase lead time / manufacturing lead time;
- lot sizing policy (P0: lot-for-lot);
- MOQ and order multiple;
- preferred approved supplier source;
- enabled/effective dates.

Supplier sourcing must reuse E04 `supplier_parts` / AML approval and must not reinterpret supplier availability as engineering approval.

## Safety rules
- legacy `materials.safety_stock` may seed a reviewed policy but does not become the whole policy model;
- no unapproved manufacturer part or substitute may be selected merely because it is cheaper/in stock;
- expired/disabled supplier source is not valid planning supply;
- missing approved source produces an exception, not an invented supplier;
- policy changes are audited and historical MRP runs retain the assumptions actually used.

## Tests
- buy item with MOQ/order multiple produces deterministic rounded recommendation;
- make item does not generate a PO suggestion;
- disabled/unapproved source is excluded;
- missing source raises `NO_APPROVED_SOURCE`;
- policy effective dates do not rewrite historical run evidence.

## Done
One material/site has one explainable planning contract that future netting can consume without guessing.