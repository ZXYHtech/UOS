# TASK_INV_IMPL_E12 — Governed Reporting, Management Cockpit & Product Intelligence

## Status
`DESIGN_READY_BLOCKED_BY_DOMAIN_EVIDENCE`

## Objective
Build management reporting from governed metrics and drill-down evidence, not from ad-hoc dashboard SQL or opaque scores.

Architecture:

```text
transactional domains
 -> governed metric definitions / read models
 -> optional snapshots/caches
 -> role-scoped APIs
 -> operator dashboard OR management cockpit
 -> product scorecard / management actions
```

## Principles
- keep current operator action board separate from management cockpit;
- every KPI defines formula, scope, timestamp, source and evidence quality;
- every critical management number drills to source records;
- missing/incomplete data is labeled, never silently treated as zero;
- product intelligence is multi-dimensional and transparent, not one magic AI score;
- reporting read models never become a write authority for transactional domains;
- scheduled report generation uses server-owned jobs/systemd, never GitHub Actions.

## Evidence states
Examples:

```text
COMPLETE_ACTUAL
PARTIAL_ACTUAL
ESTIMATED
STALE
INSUFFICIENT_DATA
```

Product metric evidence may additionally classify `MEASURED`, `DERIVED`, `ESTIMATED`, `MANUAL_ASSESSMENT`.

## Definition of done
Management can answer what needs attention, whether performance is improving, and which product/supplier/channel deserves action—with every answer traceable to governed source evidence.