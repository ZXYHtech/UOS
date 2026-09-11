# TASK_INV_IMPL_E13 — Safe Event Rules & Automation Governance

## Status
`DESIGN_READY_BLOCKED_BY_E01_DOMAIN_COMMANDS`

## Objective
Add a small event + rules + durable action framework that automates low-risk work safely without becoming a generic BPM/low-code engine or bypassing domain invariants.

Target:

```text
business event / scheduled observation
 -> versioned structured rule evaluation
 -> deterministic action request
 -> approval when risk requires
 -> normal domain command via E01
 -> durable result/retry/reversal evidence
```

## Risk classes

```text
A0 read-only insight
A1 notification / todo / draft
A2 reversible business mutation
A3 high-consequence mutation
```

A3 default = human approval unless a narrowly scoped operator-approved policy explicitly says otherwise.

## Hard boundaries
- no arbitrary Python/SQL stored as rules;
- rules call domain commands, never mutate tables directly;
- each rule version remains historically explainable;
- every action has idempotency/deduplication and declared reversal semantics;
- observe-only/dry-run precedes broad/high-impact enablement;
- automation loops/cascades have depth/rate/cycle controls;
- global/domain/rule kill switches exist;
- pausing automation never disables manual core business commands;
- scheduling uses E01 jobs/systemd/cron, never GitHub Actions.

## Definition of done
A user can answer “why did this automation fire, which rule/version/inputs caused it, who approved it, what domain command ran, and how can it be reversed or reconciled?”