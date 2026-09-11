# E13 Implementation Sequence — Safe Automation Rules

## Status
`DESIGN_READY_BLOCKED_BY_E01_DOMAIN_COMMANDS`

## Slice A — Event/rule identity
Implement E13-S01 and emit/observe a very small set of existing domain events without actions.

## Slice B — Structured condition evaluator
Implement E13-S02 with pure deterministic tests. No arbitrary expressions/code.

## Slice C — Action registry/risk approvals
Implement E13-S03 using E01 Action Policy and existing domain commands.

## Slice D — Observe-only
Implement E13-S04. Pilot rules such as overdue follow-up, PO overdue, backup age or stale report in simulation/notification-only mode.

## Slice E — Durable A1 actions
Implement E13-S05 for notification/todo/draft actions first.

## Slice F — Narrow reversible A2 pilot
Enable one bounded reservation/classification action only after dry-run evidence and explicit reversal test.

## Slice G — Loop/circuit controls
E13-S06 must be active before broader chained rules.

## Slice H — Governance/observability
Implement E13-S07 before scaling rule count.

## A3 policy
Do not treat A3 autonomous execution as an E13 completion requirement. High-consequence actions remain human-approved by default.

## Gates
- deterministic condition traces;
- event/action idempotency;
- approval boundary tests;
- compensation/reversal tests;
- loop/rate/circuit-breaker tests;
- E00 Release Gate.

No required scheduler/runtime path may depend on GitHub Actions.