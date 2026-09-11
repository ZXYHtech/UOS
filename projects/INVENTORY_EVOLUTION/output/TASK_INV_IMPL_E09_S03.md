# TASK_INV_IMPL_E09_S03 — Inbound Order Revisions & Remote State Transition Policy

## Status
`DESIGN_READY_BLOCKED_BY_E01_E02_GATES`

## Objective
Normalize marketplace order changes into durable observations and safe internal state transitions instead of blindly overwriting the current order row.

## Remote events
Initial normalized events include:

- created;
- paid/unpaid change;
- address/contact update;
- SKU/quantity update where platform permits;
- cancellation/closure;
- partial fulfilment;
- refund request/completion.

## Policy
Local state determines what a remote update may still change.

Examples:

```text
before confirmation/reservation -> mutable within policy
reserved -> changes may require reservation recompute
picking -> conflicting changes become operator exception
shipped -> address/quantity must not rewrite committed shipment snapshot
```

## Evidence
Preserve the remote observation/version that triggered each accepted local transition. Keep immutable shipment/order snapshots needed for historical truth.

## Tests
- late address change after shipment does not rewrite shipment evidence;
- remote quantity reduction before reservation updates canonical order safely;
- remote conflicting change during picking creates exception;
- repeated same state event is idempotent;
- remote cancellation delegates to S06 policy rather than deleting order.

## Done
Remote state evolves through controlled transition policy with full observation history rather than last-write-wins overwrites.