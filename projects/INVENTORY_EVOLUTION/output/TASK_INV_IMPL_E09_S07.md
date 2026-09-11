# TASK_INV_IMPL_E09_S07 — Periodic Reconciliation & Mismatch Exceptions

## Status
`DESIGN_READY_BLOCKED_BY_E01_E02_GATES`

## Objective
Detect drift that incremental polling/webhooks/retries cannot guarantee away.

## Reconciliation scopes
Per platform account, periodically compare:

- open order state;
- shipment acknowledgement;
- refund state;
- SKU mapping state;
- desired vs remote inventory quantity;
- listing/product enabled state where connector supports it.

## Rule
Reconciliation surfaces a difference; it does not silently choose local or remote as winner.

Mismatch record includes:

- account/object identity;
- local state snapshot/reference;
- remote state snapshot/reference;
- difference type;
- severity/action recommendation;
- first/last observed;
- resolution status/actor/reason.

## Examples
- remote says cancelled, local shipped;
- local shipment complete but no remote acknowledgement;
- desired stock 5, remote stock 12;
- remote SKU mapping changed/unknown;
- refund completed remotely but internal financial event missing.

## Tests
- same unresolved mismatch is updated, not duplicated every run;
- resolved mismatch can re-open if drift returns;
- reconciliation never mutates stock/order history without an authorized domain action;
- source snapshots are sufficient to explain the mismatch.

## Done
The system can prove whether local and remote channel state agree and gives operators a controlled way to resolve disagreements.