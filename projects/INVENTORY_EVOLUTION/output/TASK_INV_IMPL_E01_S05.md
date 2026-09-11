# TASK_INV_IMPL_E01_S05 — Generic Durable Job Model

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Generalize the existing OCR/image-job durability pattern into one reusable DB-backed job framework for reports, notifications and integration workloads.

## Migration ownership

**Proposed Migration 3**:

```text
jobs
  id INTEGER PK
  job_type TEXT NOT NULL
  payload_json TEXT NOT NULL
  status TEXT NOT NULL
  priority INTEGER NOT NULL DEFAULT 0
  available_at TEXT NOT NULL
  lease_owner TEXT
  lease_until TEXT
  lease_generation INTEGER NOT NULL DEFAULT 0
  attempt_count INTEGER NOT NULL DEFAULT 0
  max_attempts INTEGER NOT NULL DEFAULT 5
  idempotency_key TEXT
  correlation_id TEXT
  created_at TEXT NOT NULL
  updated_at TEXT NOT NULL

job_attempts
  id INTEGER PK
  job_id INTEGER NOT NULL
  attempt_no INTEGER NOT NULL
  lease_generation INTEGER NOT NULL
  worker_id TEXT NOT NULL
  started_at TEXT NOT NULL
  finished_at TEXT
  outcome TEXT
  error_class TEXT
  error_message TEXT
```

Suggested indexes:

- jobs(status, available_at, priority, id);
- jobs(job_type, status, id);
- job_attempts(job_id, attempt_no).

## Claim algorithm

SQLite v1 contract:

```text
BEGIN IMMEDIATE
 -> select eligible queued/retry_wait row
 -> require lease absent/expired
 -> increment lease_generation
 -> set running + owner + lease_until + attempt_count
 -> insert attempt row
COMMIT
```

Expensive work executes outside the write transaction.

Completion/failure update must match `(job_id, lease_generation, lease_owner)` so an old worker cannot publish after its lease is reclaimed.

## Payload boundary

Payloads are business references and small immutable parameters, not large binary content. Files/artifacts remain in controlled storage and are referenced by ID/path.

## Initial workload

First adopter should be low-risk and non-stock-mutating, e.g. report generation or notification delivery. OCR migration is optional later; E01 should not destabilize the currently working OCR queue just to prove reuse.

## Tests

- two claimers cannot own one generation;
- expired lease reclaim increments generation;
- stale worker completion is fenced;
- restart preserves queued/running-expired work;
- job payload survives round trip;
- attempt history is append-only evidence.

## Rollback

Migration 3 additive. Existing OCR/image queues remain operational until explicitly migrated.

## Acceptance

One non-critical workload can be enqueued, claimed, completed and recovered after simulated worker death using only repository/server-local infrastructure.

## Dependencies

E00 Migration framework, E01-S01. Correlation becomes complete with E01-S09.
