# TASK_INV_IMPL_E13_S05 — Durable Rule Execution, Idempotency, Retry & Compensation

## Status
`DESIGN_READY_BLOCKED_BY_E01`

## Objective
Execute rule actions restart-safely while guaranteeing that event replay/retry does not duplicate the business effect.

## Deterministic execution key
Conceptually:

```text
rule_version + source_event_id + action_type + target_id
```

maps to one rule execution / E01 business operation.

## Flow

```text
event
 -> evaluate exact rule version
 -> create action request/job
 -> approval if required
 -> execute registered domain command
 -> durable result receipt
 -> retry/manual review/reversal evidence
```

## Retry boundary
Use E01 retry classification. Ambiguous external side effects reconcile before repetition. Bounded attempts move to dead-letter/manual review.

## Compensation
- notification/todo: close/cancel;
- draft document: cancel/delete if domain policy permits;
- reservation: release with compensating event;
- classification: controlled revert revision;
- stock/financial transaction: reversal/correction event, never history delete;
- external API: reconciliation/compensating command where possible.

## Tests
- duplicate event/retry creates one domain effect;
- same execution key with changed action input conflicts;
- worker restart resumes pending execution;
- failed A2/A3 action has no partial hidden write outside domain transaction;
- compensation links original execution.

## Done
Automation is restart/replay safe and every mutation has a defined correction path rather than destructive rollback.