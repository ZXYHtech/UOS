# TASK_INV_IMPL_E15_S01 — Scale SLOs, Capacity Evidence & Migration Triggers

## Status
`DESIGN_READY`

## Objective
Define measurable operating limits so database/infrastructure decisions are based on observed contention, latency, recovery and workload rather than intuition.

## Measure
At minimum track by operation class:

- request/transaction p50/p95/p99 latency;
- SQLite busy/lock wait and timeout count;
- transaction rollback/failure rate;
- duplicate/idempotency conflict count;
- concurrent active write pressure;
- DB size/growth;
- artifact-store size/growth;
- backup duration/size;
- isolated restore verification duration;
- worker queue age/backlog;
- slow-query/read-model impact.

## SLO/threshold governance
Thresholds are configurable and reviewed for the actual business, e.g. maximum acceptable p95 stock transaction latency, lock timeout rate, backup/restore window and RTO/RPO.

Do not hard-code a PostgreSQL migration at an arbitrary row/order count.

## Decision record
When a scale threshold is breached, create evidence containing:

- metric/time window;
- affected operation/query;
- whether transaction/query/index/read-model optimizations were attempted;
- current hardware/storage/deployment topology;
- business impact;
- proposed remedy and expected benefit.

## Tests
- synthetic threshold breach produces an explicit scale review, not an automatic DB migration;
- short transient spike does not equal sustained breach unless policy says so;
- backup/RTO degradation is measured alongside request latency;
- evidence can distinguish application bug/query regression from actual backend capacity limit.

## Done
The project has an agreed evidence threshold for “SQLite is no longer sufficient” rather than a subjective migration decision.