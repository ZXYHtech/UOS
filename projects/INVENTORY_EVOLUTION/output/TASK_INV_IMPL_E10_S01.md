# TASK_INV_IMPL_E10_S01 — Customer / Contact / Opportunity Identity

## Status
`DESIGN_READY_BLOCKED_BY_E09_FOUNDATION`

## Objective
Create a minimal durable B2B/customer identity and opportunity object before an order exists.

## Customer model
Separate durable customer account from shipping receiver text. Support company/individual/distributor/platform-buyer categories and sales owner/customer group/status.

Contacts are separate records with role, phone/email/IM identifiers and primary flag.

## Opportunity
One lightweight inquiry/opportunity object carries:

- customer/contact;
- source/channel;
- sales owner;
- stage/status;
- technical summary;
- expected quantity/value/date when useful;
- next action / due date;
- lost/on-hold reason.

Suggested stages:

```text
new_inquiry
qualification
technical_review
quoted
sample_evaluation
negotiation
won
lost
on_hold
```

## Safety
- platform buyer is not auto-merged into a CRM customer without explicit/confident reviewed match;
- duplicate customer merge is controlled/audited;
- losing an opportunity never deletes quotes/activities;
- stage probability is optional; next-action ownership is mandatory for open opportunities.

## Tests
- inquiry can exist without order;
- one customer has multiple contacts;
- ambiguous platform-buyer match does not auto-merge;
- lost opportunity retains history and structured reason;
- overdue next action is queryable.

## Done
Every meaningful inquiry has a durable owner/context before it becomes an order.