# TASK_INV_IMPL_E13_S07 — Automation Ownership, Observability & Periodic Review

## Status
`DESIGN_READY_BLOCKED_BY_E13_S01_S05`

## Objective
Make enabled automation operationally ownable and reviewable rather than invisible background logic.

## Rule governance
Every enabled rule has:

- business owner;
- technical owner;
- intent/evidence;
- risk class/approval policy;
- effective scope;
- last reviewed / next review date;
- execution/error/override/reversal metrics.

## Operations view
Show:

- enabled/paused rules;
- executions today/week;
- pending approvals;
- retrying/dead-letter;
- top firing rules;
- user overrides/reversals;
- rules with no recent trigger;
- circuit-breaker state;
- approximate manual work saved where measurable.

## Review
Process/policy changes can mark affected rules `REVIEW_REQUIRED`; stale rules are not silently carried forever.

High error/override/reversal rate can automatically pause or require review according to policy.

## Runtime
Scheduled condition evaluation and rule reviews use E01 durable jobs/server-owned scheduling. No GitHub Actions dependency.

## Tests
- missing owner/review policy blocks production enablement;
- dead-letter/approval backlog visible;
- review-required rule cannot silently continue if policy says pause;
- operational metrics link to exact execution records.

## Done
Automation is treated as an owned production subsystem with auditability and maintenance responsibility, not hidden convenience code.