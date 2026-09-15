# TASK_INV_AUDIT_SCALABILITY_01 — Scalability, Concurrency and SQLite-to-PostgreSQL Evolution Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed server/thread model, SQLite connection/pragmas, schema/data-model audit, source architecture, durable OCR job patterns, pagination improvements and PostgreSQL placeholder schema.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite should **not** migrate to microservices or PostgreSQL merely because feature count is growing. The current architecture can support substantially more usage if its concurrency invariants, domain boundaries, pagination and durable jobs are strengthened first.

Current positive foundations include:

- `ThreadingHTTPServer` for concurrent request handling;
- SQLite WAL mode;
- 15-second connection/busy timeout;
- one-connection-per-operation patterns in many request paths;
- cursor pagination already introduced in major UI lists;
- durable OCR/image job state rather than only in-memory background tasks;
- lightweight deployment and low operational burden.

The primary scaling risks are **correctness under concurrent writes**, mega-file maintainability, growing query cost, weak schema integrity and severe SQLite/PostgreSQL schema drift—not raw HTTP throughput alone.

Preliminary maturity:

- small-team deployment simplicity: 4.5/5
- request concurrency foundation: 3/5
- write-concurrency proof: 2/5
- pagination/list scaling: 3/5
- durable background jobs: 2.5–3/5
- DB migration discipline: 1.5/5
- PostgreSQL production readiness: 1/5

## 2. Current server concurrency model

The server uses `ThreadingHTTPServer` with daemon threads. This is adequate for a small internal application, but it means multiple request threads can concurrently execute SQLite transactions.

SQLite WAL improves read/write coexistence, but it still has a single-writer constraint. The configured busy timeout reduces transient `database is locked` failures; it does not prove business operations are race-safe.

The important question is therefore not “can two users connect?” but:

```text
Can two users execute conflicting stock/order/receipt transitions concurrently
without oversubscription, lost update, duplicate movement or inconsistent state?
```

## 3. Critical write-concurrency risk

The current inventory service has application-level read/modify/write behavior. Under concurrency, this deserves deterministic testing for:

- two shipments deducting the same stock;
- shipment and transfer competing for stock;
- PO receive double submission;
- transfer receive double submission;
- inventory adjustment while count closes;
- order reservation once implemented;
- work-order issue/return once implemented;
- refund/reversal races;
- platform event replay.

A busy timeout protects lock acquisition, not business uniqueness or idempotency.

## 4. Transaction contract

Every consequential operation should explicitly define:

- transaction boundary;
- rows/aggregates read;
- state preconditions;
- uniqueness/idempotency key;
- mutation set;
- ledger/audit write;
- external side effects deferred until after commit.

Prefer one database transaction per business command.

For operations that depend on current balance/state, use SQL updates with guarded predicates where possible, for example conceptually:

```text
UPDATE balance
SET qty = qty - :n
WHERE id=:id AND qty >= :n
```

then verify affected row count, rather than trusting an earlier read indefinitely.

The exact implementation must respect the redesigned reservation/stock kernel.

## 5. Idempotency as a scale primitive

As network clients, integrations and workers increase, retry becomes normal.

Add a reusable operation identity layer for irreversible commands:

```text
business_operation_keys
  key
  operation_type
  canonical_object_id
  result_ref
  status
  created_at

UNIQUE(key)
```

or equivalent unique keys embedded in domain event tables.

Required for:

- platform imports;
- shipment completion;
- purchase receipt;
- transfer ship/receive;
- work-order material issue/output;
- RMA refund/stock disposition;
- settlement import;
- automation actions.

## 6. SQLite capacity boundary

SQLite remains a reasonable choice while:

- write concurrency is modest;
- deployment is primarily one application host;
- database size remains manageable;
- operational simplicity is more valuable than horizontal scale;
- background workers share the same host/storage carefully;
- deterministic backups/recovery are maintained.

Do not use arbitrary order-count thresholds as migration triggers.

Use evidence-based triggers such as:

- sustained write-lock contention;
- p95/p99 transaction latency increasing materially;
- need for multiple application hosts writing concurrently;
- reporting queries materially impacting operations;
- operational need for stronger online migration/replication/PITR;
- database size/backups exceeding acceptable RTO;
- concurrency tests demonstrating SQLite is the actual bottleneck.

## 7. Query scaling

As new domains arrive, likely large tables include:

- inventory movements;
- operation logs;
- external platform observations;
- order economic events;
- test measurements/artifacts metadata;
- serial/lot genealogy;
- service-case events;
- automation/job attempts.

Require indexes from actual query patterns rather than blanket indexing.

High-value index dimensions include:

- business ID/unique external key;
- status + due/created time;
- material + warehouse/location/state;
- order/shipment/RMA serial lookup;
- job status + next_run_at;
- platform account + external object ID;
- event timestamp for reporting.

Use `EXPLAIN QUERY PLAN` and synthetic production-like row counts in local load tests.

## 8. Pagination and large lists

Cursor pagination already exists in important areas and should become a platform convention.

Rules:

- stable deterministic ordering;
- indexed cursor field(s);
- avoid unbounded `SELECT *` lists;
- preserve filters/search in cursor contract;
- provide totals only when affordable or explicitly requested;
- large exports run as durable jobs rather than HTTP requests held open.

Avoid deep `OFFSET` pagination on high-volume event tables.

## 9. Caching

Do not introduce Redis merely because some dashboards aggregate data.

Use layers in order:

1. correct indexes/query shape;
2. request-local computation;
3. database materialized/cache tables or daily snapshots;
4. process cache only for clearly immutable/reference data;
5. external cache only when measured need exists.

Never use cache as the source of truth for stock, reservations or financial events.

## 10. Background jobs

OCR provides the right precedent: durable task/job state with attempts/errors.

Generalize to a common worker substrate or consistent domain outboxes for:

- marketplace synchronization;
- inventory publication;
- report generation;
- backups/verification;
- MRP;
- forecast refresh;
- settlement import/reconciliation;
- alerts/reminders;
- AI tasks;
- search indexing.

Required worker properties:

- durable queued state;
- claim/lease;
- retry with backoff;
- attempt history;
- idempotent action;
- dead-letter/manual review;
- cancellation where safe;
- metrics/health;
- graceful restart.

Run via systemd/server-local process, never requiring GitHub Actions.

## 11. File/blob scaling

RF test artifacts, images and controlled documents can grow faster than relational data.

Do not store large binary payloads in ordinary DB rows.

Define storage abstraction:

```text
artifact metadata in DB
 + immutable file/object key
 + size/hash/MIME
 + retention class
 + reference count/lifecycle
```

Start with local filesystem if sufficient; allow migration to NAS/object storage later without changing business identity.

Backups must cover DB + artifact store consistently.

## 12. Modular monolith before database migration

Large `server.py`, `services.py`, `app.js` and mobile files are a larger development-scale problem than current runtime scale.

Split domain modules while preserving behavior first. This enables:

- isolated tests;
- explicit transaction ownership;
- smaller code-review surface;
- clearer PostgreSQL adaptation later;
- safer addition of manufacturing/quality domains.

Do not combine a domain refactor, UI rewrite and database migration into one project.

## 13. Migration architecture

Replace ad-hoc cumulative migration logic with immutable numbered migrations:

```text
schema_migrations
  version
  applied_at
  checksum
```

Repository structure concept:

```text
migrations/
  0001_initial.py/sql
  0002_auth_sessions.py/sql
  ...
```

Each migration should support:

- fresh database application;
- upgrade from representative previous versions;
- validation after migration;
- clear irreversible steps;
- local test execution.

## 14. PostgreSQL evolution

The current `deploy/postgres/schema.sql` is materially behind SQLite and must not be treated as deployment-equivalent.

Recommended path:

### Stage A — canonical schema/migrations

Make SQLite's current production schema explicit and versioned.

### Stage B — remove SQLite-specific assumptions

Inventory SQL for:

- `INSERT OR IGNORE`/upsert semantics;
- rowid/lastrowid assumptions;
- date/time/text behavior;
- NULL uniqueness;
- pragma dependencies;
- transaction isolation;
- dynamic schema introspection.

### Stage C — database adapter boundary

Keep domain service behavior independent of backend-specific DDL/SQL where practical.

### Stage D — parity test

Run the same repository-local domain contract tests against SQLite and PostgreSQL.

### Stage E — migration rehearsal

Export/copy representative database to PostgreSQL, verify counts, constraints, checksums and business invariants, then benchmark.

Only after these pass should production migration be considered.

## 15. Horizontal scale

Do not design multi-host application scale until needed.

If eventually required, PostgreSQL plus external/shared artifact storage and stateless web processes are a natural next step. Durable workers can then claim jobs from the database.

This still does not require microservices.

## 16. Load-testing model

Repository-local tests should generate synthetic but realistic scenarios:

- 5k/50k/500k materials/movements depending target scale;
- concurrent shipment/receipt/transfer writes;
- high-volume platform event replay;
- dashboard and search under large history;
- batch import/export;
- OCR/test-artifact metadata growth;
- worker crash/restart during jobs.

Measure:

- p50/p95/p99 latency;
- lock wait/timeouts;
- transaction failures;
- duplicate operation count;
- memory;
- DB/file growth;
- recovery behavior.

## 17. Priority roadmap

### P0

1. deterministic concurrency tests for stock-changing operations;
2. reusable idempotency/business-operation keys;
3. explicit transaction/state-transition contracts;
4. immutable schema migrations;
5. index/query review for major list/event tables;
6. generalized durable worker pattern;
7. label PostgreSQL as unsupported until parity exists.

### P1

1. modularize backend/client hotspots;
2. production-like synthetic load suite;
3. DB-backed reporting snapshots;
4. artifact-storage abstraction;
5. SQLite/PostgreSQL SQL compatibility inventory;
6. dual-backend contract suite.

### P2

1. migrate to PostgreSQL only on measured operational need;
2. shared object/file storage if multi-host deployment appears;
3. read replicas/analytics separation only if measured query load warrants it.

## 18. Acceptance signals

- two concurrent stock-consuming commands cannot oversubscribe or lose updates;
- retrying a committed request returns/reuses the original result without duplicate ledger events;
- large lists remain bounded/paginated;
- job processing survives worker restart and does not double-apply actions;
- schema upgrades are reproducible from old fixtures and fresh DB;
- PostgreSQL cannot be labeled supported until the same domain suite passes there;
- scaling decisions are driven by measured contention/latency/RTO rather than feature count;
- no required load test, migration, worker or deployment path depends on GitHub Actions.

## 19. Core recommendation

Keep the **modular-monolith + SQLite** operating model for now, but harden it around concurrency, idempotency, migrations and durable jobs. Prepare PostgreSQL as a tested backend evolution—not as a premature rewrite. The safest scale strategy is to make business transactions deterministic first; infrastructure scale can follow measured demand.