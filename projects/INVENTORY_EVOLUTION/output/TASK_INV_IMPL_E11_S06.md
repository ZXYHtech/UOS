# TASK_INV_IMPL_E11_S06 — Order Economics Event Ledger

## Status
`DESIGN_READY_BLOCKED_BY_E09_E10_FOUNDATIONS`

## Objective
Represent realized commerce economics as append-only normalized events rather than mutable order totals.

## Event types
Initial normalized categories include:

```text
PRODUCT_REVENUE
SELLER_DISCOUNT
PLATFORM_SUBSIDY
PLATFORM_COMMISSION
PAYMENT_PROCESSING_FEE
OUTBOUND_FREIGHT
RETURN_FREIGHT
FULFILMENT_FEE
TAX_OBSERVATION
REFUND
REFUND_FEE_REVERSAL
PLATFORM_PENALTY
WARRANTY_REPLACEMENT_COST
RMA_REPAIR_COST
OTHER_ADJUSTMENT
```

Preserve native platform/carrier code/name alongside normalized type.

## Identity
Economic event may link order/line/shipment/RMA/platform account and has external event identity where observed remotely. Duplicate settlement/API import cannot duplicate economics.

## Cost basis
COGS event/snapshot states whether it uses reference estimate, released standard or actual WO/serial cost. Historical order profit never silently recalculates from current cost.

## Rules
- seller-funded discount and platform-funded subsidy are distinct;
- procurement inbound freight is not outbound customer freight;
- refund event does not imply inventory return;
- corrections post reversal/adjustment events rather than mutate settled history;
- currency/source/evidence date remain explicit.

## Tests
- duplicate external event is idempotent;
- seller discount and platform subsidy produce different net revenue;
- refund without return changes economics but not stock;
- outbound freight links shipment/package;
- later cost master changes do not rewrite historical COGS snapshot.

## Done
One order can be explained as a sequence of revenue/cost events rather than an opaque current profit number.