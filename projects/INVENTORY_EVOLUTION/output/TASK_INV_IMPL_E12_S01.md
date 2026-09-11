# TASK_INV_IMPL_E12_S01 — Metric Registry, Lineage & Evidence Quality

## Status
`DESIGN_READY`

## Objective
Create one authoritative definition for each management KPI before building more dashboards.

## Metric contract
Each metric defines:

- `metric_code` / business question;
- formula and numerator/denominator;
- included/excluded statuses;
- source entities/events;
- business timestamp/timezone;
- scope/permission rules;
- freshness/refresh policy;
- owner;
- evidence class/limitations.

## Rules
- a metric code has versioned semantics; formula changes create a new semantic version/effective date;
- pages consume the registry rather than reimplementing private formulas;
- insufficient inputs yield explicit insufficient/estimated state, not fabricated zero;
- historical snapshot retains metric definition version used.

## Tests
- same metric queried from two surfaces returns same definition/value scope;
- changed formula does not rewrite historical snapshot semantics;
- unavailable denominator/input returns declared insufficient state;
- role scope is enforced server-side.

## Done
Terms such as contribution margin, RMA rate, stockout rate and first-pass yield have one documented meaning throughout the system.