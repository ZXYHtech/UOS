# TASK_INV_IMPL_E10_S08 — Follow-up Automation, Support Templates & Product-quality Feedback

## Status
`DESIGN_READY_BLOCKED_BY_E01_E07_FOUNDATIONS`

## Objective
Turn structured CRM/support/RMA records into actionable reminders and product-quality learning without giving automation or AI consequential authority.

## Safe automations
Server-owned E01 jobs may generate:

- overdue opportunity next-action reminder;
- quotation-expiry reminder;
- sample-return reminder;
- stale opportunity warning;
- service-case SLA/next-action warning;
- RMA diagnosis/repair overdue warning;
- platform dispute deadline alert;
- repeated defect/reason cluster review task.

Notifications deduplicate and retain source reference.

## Templates
Support reviewed RF troubleshooting checklists and reply macros for common scenarios such as supply/50-ohm setup, cable loss, control state, serial/firmware collection, RMA instruction and shipping delay.

Templates are versioned/reviewed content; they do not automatically determine warranty, refund or technical safety conclusions.

## Feedback loop
Aggregate structured lost reasons, customer requirements, case categories, RMA defect/root-cause and product/revision/lot links into product/quality insight candidates.

Possible outcomes:

- documentation/KB update;
- product roadmap candidate;
- quality/NCR review;
- ECO investigation;
- supplier-quality follow-up.

Do not infer systemic defect from raw case volume alone; normalize by shipments/installed base where possible.

## AI boundary
Future E14 may summarize/classify/draft, but deterministic policy/human approval owns warranty, refund, engineering change and customer-facing consequential action.

## Tests
- duplicate reminder not emitted repeatedly for same due condition;
- internal-only template/note cannot become customer-visible automatically;
- repeated RMA issue can create review candidate without auto-opening ECO/NCR;
- reminder scheduler uses E01 worker/systemd, never GitHub Actions.

## Done
Sales/support work stops falling through gaps and recurring customer evidence can feed product improvement without unsafe autonomous decisions.