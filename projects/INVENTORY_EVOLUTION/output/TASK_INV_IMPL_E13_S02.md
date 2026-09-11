# TASK_INV_IMPL_E13_S02 — Structured Condition Language & Type-safe Evaluation

## Status
`DESIGN_READY_BLOCKED_BY_E13_S01`

## Objective
Allow configurable rules without arbitrary code execution.

## Condition model
Use whitelisted typed predicates such as:

```text
all / any / not
field exists/equals/in/range
metric comparison
age/duration comparison
status transition
configured threshold/reference value
```

Example:

```text
all:
  - metric: stock.days_cover
    op: <
    value_from: supplier.lead_time_days
  - field: material.enabled
    op: =
    value: true
```

## Rules
- no arbitrary SQL/Python/shell/expression eval;
- fields/metrics are resolved through registered safe accessors;
- units/currencies/timezones/types are validated;
- missing/unknown input has explicit evaluation result, not implicit false/zero where unsafe;
- condition evaluation is side-effect free.

## Tests
- invalid field/operator/type is rejected at rule validation;
- unit/currency mismatch cannot silently compare;
- missing metric yields explicit unknown/insufficient result;
- deterministic input gives deterministic evaluation trace.

## Done
Business users can configure bounded conditions without turning the database into a code-execution surface.