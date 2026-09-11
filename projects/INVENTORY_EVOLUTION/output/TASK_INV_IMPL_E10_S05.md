# TASK_INV_IMPL_E10_S05 — Customer Service Case, SLA & Append-only Timeline

## Status
`DESIGN_READY_BLOCKED_BY_E09_FOUNDATION`

## Objective
Add a customer-facing case layer without replacing the existing internal `ExceptionService`.

## Separation

```text
Operational Exception = internal process problem
Service Case = customer-facing issue/request
```

They may link, but neither automatically closes the other.

## Case identity
A service case can exist without an order and may link customer/contact, order, shipment, platform account, serial, RMA and one or more operational exceptions.

Suggested statuses:

```text
OPEN
IN_PROGRESS
WAITING_CUSTOMER
WAITING_INTERNAL
WAITING_LOGISTICS
WAITING_RMA
RESOLVED
CLOSED
```

## SLA / work management
Capture owner, first-response due/actual, next action/due date, resolution target, opened/resolved/closed timestamps and aging. Policy may vary by customer/channel/severity.

## Timeline
Use append-only events for notes, inbound/outbound message summaries, calls, assignment/status changes, escalation, linked exception/RMA and attachments. Internal/customer-visible visibility is explicit.

## Rules
- mutable remarks do not replace case history;
- internal notes never leak through customer-facing output;
- reopen preserves prior resolution history;
- external-message replay uses E09 durable identity when connectors are added.

## Tests
- case can exist without order;
- linked internal exception closing does not auto-close case;
- internal note cannot render as customer-visible;
- first-response/next-action overdue queues are deterministic;
- reopen retains old resolution evidence.

## Done
Support staff has one owned, auditable customer context instead of reconstructing history from order remarks.