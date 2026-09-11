# E12 Implementation Sequence — Governed Reporting & Product Intelligence

## Status
`DESIGN_READY_BLOCKED_BY_DOMAIN_EVIDENCE`

## Slice A — Metric registry
Implement E12-S01 first. Existing dashboards continue unchanged while metric definitions become explicit.

## Slice B — Read models/drill-down
Implement E12-S02 for a small set of already trustworthy metrics. Prove aggregate=drilldown and freshness visibility.

## Slice C — Management cockpit pilot
Implement E12-S03 exception-first with direct links; do not expand into a 30-card BI wall.

## Slice D — Product hierarchy/scorecard
Implement E12-S04 initially with demand/price/inventory/lifecycle metrics that have sufficient evidence. Missing later-domain metrics remain `INSUFFICIENT_DATA`.

## Slice E — Risk roll-ups/archetypes
Implement E12-S05 only as E04/E07/E08/E11 evidence becomes authoritative.

## Slice F — Scheduled reports / role scope
Implement E12-S06 through E01 durable jobs/systemd-owned scheduling.

## Gates
- metric semantic/version tests;
- aggregate/drill-down parity;
- permission-scope tests;
- stale/missing evidence handling;
- full E00 Release Gate.

## Authority rule
Reporting projections are read-only derived views. Corrections happen in source domains, never by editing KPI snapshots to make numbers look right.