# TASK_INV_IMPL_E15 — Conditional Scale & PostgreSQL Evolution

## Status
`DESIGN_READY_CONDITIONAL_NOT_SCHEDULED`

## Objective
Keep the modular-monolith + SQLite operating model while it meets measured correctness/performance/recovery needs, and prepare PostgreSQL as a tested backend evolution only when objective triggers justify the added operational complexity.

## Core decision

```text
SQLite remains supported/default
until measured trigger + dual-backend parity + migration rehearsal + rollback proof
```

PostgreSQL adoption is **not** an E15 definition-of-done requirement.

## Measured triggers
Potential migration triggers include sustained/meaningful:

- write-lock contention or busy timeouts;
- p95/p99 consequential transaction latency outside agreed SLO;
- requirement for multiple application hosts writing concurrently;
- reporting/analytics load materially harming operations despite read models/indexes;
- DB/artifact/backup size causing unacceptable RTO/RPO;
- operational need for replication/PITR/online migration features;
- concurrency/load tests proving SQLite itself is the bottleneck after query/transaction fixes.

Do not use feature count or arbitrary order/material row counts alone as the trigger.

## Architecture boundary
Even after PostgreSQL:

```text
modular monolith
+ one primary relational database
+ durable workers/outbox
+ shared artifact storage only if required
```

No microservices, Kafka, Redis or read replicas are mandatory merely because PostgreSQL is introduced.

## Preconditions inherited from E00–E14
- immutable numbered migrations;
- deterministic transaction/idempotency contracts;
- domain modularization;
- durable jobs/outbox;
- governed reporting/read models;
- backup/restore verification;
- artifact metadata/hash/storage contract;
- repository-local release/load/migration tests independent of GitHub Actions.

## PostgreSQL support rule
The existing stale `deploy/postgres/schema.sql` must never be presented as production-equivalent. PostgreSQL may be labeled supported only when:

1. schema/migration parity exists;
2. backend-specific SQL assumptions are controlled;
3. the same domain contract/regression suite passes on SQLite and PostgreSQL;
4. representative data migration is rehearsed and reconciled;
5. production cutover/rollback and backup/recovery runbooks are proven;
6. measured need justifies migration.

## Definition of done
E15 is complete when scaling decisions are evidence-driven, SQLite has explicit operating limits/SLO monitoring, PostgreSQL compatibility/parity can be proven on demand, and a safe migration path exists without forcing an unnecessary production database change.