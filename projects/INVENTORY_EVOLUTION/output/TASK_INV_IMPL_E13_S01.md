# TASK_INV_IMPL_E13_S01 — Business Event & Versioned Rule Identity

## Status
`DESIGN_READY_BLOCKED_BY_E01`

## Objective
Define stable event/rule identities so retries, scheduled observations and later rule edits remain explainable.

## Event contract
Each event has stable type/id, occurred/observed timestamps, source object references, correlation/causation IDs and a minimal immutable fact payload.

Examples:

```text
inventory.reservation_shortage
purchase.po_overdue
shipment.completed
quality.inspection_failed
quote.sent
rma.received
settlement.mismatch
```

Do not copy entire mutable objects into every event unnecessarily.

## Rule contract
Rule stores code/name, event type, structured condition, action type/params, risk class, approval policy, version/effectivity, enabled state, business/technical owner and approval evidence.

Historical execution always references exact rule version.

## Scheduled observations
Time/condition rules create explicit synthetic observations such as `po.overdue_detected`; record first detected, last detected and cleared timestamps.

## Tests
- repeated event identity is replay-safe;
- rule v2 does not rewrite v1 execution explanation;
- event causation/correlation chain is preserved;
- scheduled observation can transition true -> continuing -> cleared without duplicate spam.

## Done
Events and rules have stable, versioned identities suitable for durable automation evidence.