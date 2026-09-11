# TASK_INV_IMPL_E08_S08 — MRP Run Lifecycle, Scheduler & Exception Workbench

## Status
`DESIGN_READY_BLOCKED_BY_E07_GATE`

## Objective
Make planning runs reproducible, operable and reviewable without depending on GitHub Actions or hiding planning state in a dashboard-only calculation.

## MRP run lifecycle

```text
queued -> running -> completed | failed | cancelled
```

Each run records:

- run number;
- site/material scope;
- horizon start/end;
- policy/version assumptions;
- source snapshot timestamp/references;
- actor or scheduler source;
- started/completed timestamps;
- status/error summary.

Completed run outputs remain immutable evidence. A later run supersedes planning advice but does not rewrite history.

## Execution
- manual run is always supported;
- scheduled runs use E01 durable jobs and server-owned systemd/cron triggering;
- no required planning path depends on GitHub Actions;
- only one conflicting run per planning scope may publish final recommendations at a time; concurrent/duplicate requests are idempotent or queued safely.

## Exception workbench
Provide actionable views for:

- shortages;
- overdue releases;
- late PO/WO/subcontract return;
- no approved source;
- quality-induced shortage;
- MOQ excess;
- demand cancellation/excess;
- substitute review required;
- failed/stale MRP run.

Each exception deep-links to source documents and its calculation/pegging evidence.

## Staleness
Recommendations expose when their source state has materially changed since the run. Stale advice may be viewed but conversion can require rerun/revalidation.

## Tests
- duplicate scheduled/manual trigger does not publish duplicate run output;
- failed run publishes no partial executable recommendations;
- completed run remains queryable after later run;
- stale recommendation is detected before conversion;
- scheduler works through local durable jobs/systemd without hosted CI.

## Done
MRP is a controlled production-owned planning process with durable run history and an exception-focused operator surface.