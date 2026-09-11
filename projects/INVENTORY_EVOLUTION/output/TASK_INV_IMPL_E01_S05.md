# TASK_INV_IMPL_E01_S05 — Generic Durable Job Model

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Generalize the proven database-backed claim pattern already used by OCR/image processing into one reusable durable-job primitive for low-risk reports, notifications and integrations, without destabilizing the working OCR queue.

## Existing precedent to preserve

The audited OCR worker already demonstrates several correct ideas:

```text
DB-backed queued/running state
BEGIN IMMEDIATE claim
conditional queued -> running update
commit claim quickly
execute expensive OCR outside DB write transaction
child-process isolation
hard timeout / terminate / kill
memory backpressure
independent service from Web API
```

Current OCR restart behavior intentionally marks interrupted `running` tasks failed rather than blindly replaying them. That is safe for OCR but not yet a generic retry/lease model.

E01-S05 adds the missing reusable concepts:

```text
lease expiry
lease generation / fencing token
attempt history
retry_wait
dead_letter/manual_review
job-type policy
```

Do not migrate OCR merely to prove the abstraction.

## Migration ownership

**Proposed Migration 3**:

```text
jobs
  id INTEGER PRIMARY KEY AUTOINCREMENT
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
  completed_at TEXT

job_attempts
  id INTEGER PRIMARY KEY AUTOINCREMENT
  job_id INTEGER NOT NULL
  attempt_no INTEGER NOT NULL
  lease_generation INTEGER NOT NULL
  worker_id TEXT NOT NULL
  started_at TEXT NOT NULL
  finished_at TEXT
  outcome TEXT
  error_class TEXT
  error_message TEXT

CHECK(jobs.status IN (
  'queued','running','retry_wait','succeeded','dead_letter','cancelled','manual_review'
))
```

Recommended uniqueness/indexes:

```text
UNIQUE(job_type, idempotency_key) WHERE idempotency_key IS NOT NULL
INDEX jobs(status, available_at, priority DESC, id)
INDEX jobs(job_type, status, available_at, id)
INDEX jobs(lease_until, status)
UNIQUE(job_attempts.job_id, job_attempts.attempt_no)
INDEX job_attempts(job_id, attempt_no)
```

`idempotency_key` is enqueue dedupe, not permission and not the same as E01-S04 business-operation idempotency.

## Time contract

Use one canonical application timestamp convention consistent with existing `database.now()` / deployed business timezone until a later explicit timestamp migration is approved.

Lease comparisons must use server-generated timestamps only. Never trust client/provider clock values for `available_at` or lease ownership.

For elapsed-time logic inside a worker process, use monotonic time where appropriate; persist wall-clock timestamps for cross-process lease state.

## Claim algorithm

SQLite v1 contract:

```text
BEGIN IMMEDIATE

SELECT one eligible row
 WHERE (
   status IN ('queued','retry_wait')
   AND available_at <= now
 )
 OR (
   status='running'
   AND lease_until < now
 )
 ORDER BY priority DESC, available_at, id
 LIMIT 1

if no row:
  COMMIT
  return None

new_generation = lease_generation + 1
new_attempt = attempt_count + 1

UPDATE jobs
 SET status='running',
     lease_owner=?,
     lease_until=?,
     lease_generation=new_generation,
     attempt_count=new_attempt,
     updated_at=?
 WHERE id=?
   AND lease_generation=old_generation
   AND eligibility still true

require rowcount == 1

INSERT job_attempts(
  job_id,attempt_no,lease_generation,worker_id,started_at
)

COMMIT
```

The write transaction ends immediately after claim. Expensive work executes outside it.

## Why lease_generation is mandatory

Lease owner alone is insufficient.

Failure case:

```text
Worker A claims generation 4
 -> stalls past lease expiry
Worker B reclaims same job as generation 5
 -> B starts valid work
Worker A wakes up late
```

Without fencing, A can overwrite B's newer result.

Every completion/failure/heartbeat mutation must therefore match:

```text
job_id
AND status='running'
AND lease_owner=<this worker>
AND lease_generation=<this attempt generation>
```

If rowcount is zero, that worker is stale and must discard its result.

## Completion contract

Successful handler result:

```text
BEGIN
UPDATE jobs
 SET status='succeeded',
     lease_owner=NULL,
     lease_until=NULL,
     completed_at=?,
     updated_at=?
 WHERE id=?
   AND status='running'
   AND lease_owner=?
   AND lease_generation=?

require rowcount == 1

UPDATE matching job_attempts
 SET outcome='succeeded', finished_at=?
COMMIT
```

A stale worker is not allowed to “helpfully” force completion.

## Heartbeat / lease extension

Heartbeat is optional and job-type-specific.

For short jobs:

- choose a lease duration comfortably longer than expected runtime;
- no heartbeat complexity.

For genuinely long jobs:

```text
UPDATE jobs SET lease_until=?,updated_at=?
WHERE id=?
  AND status='running'
  AND lease_owner=?
  AND lease_generation=?
```

A failed heartbeat/fencing update means ownership is lost; handler must stop publishing results.

## Retry handoff

S05 stores the state required for retry but S07 owns classification/backoff policy.

State transition shape:

```text
running
 -> succeeded
 -> retry_wait
 -> dead_letter
 -> manual_review
 -> cancelled
```

Do not convert arbitrary exceptions directly back to `queued`.

## Payload boundary

`payload_json` contains small immutable business references/parameters, not large content.

Good:

```json
{"report_type":"daily_inventory","warehouse_id":3,"requested_by":7}
```

Bad:

```text
base64 images
full PDFs
large OCR raw payloads
secrets/API tokens
mutable copied business records
```

Files remain in controlled storage and are referenced by stable IDs/paths.

## Handler result boundary

The generic jobs table should not become an unbounded result store.

Prefer:

```text
handler creates domain artifact/notification/export row
 -> jobs row records succeeded state + optional result reference
```

Large report files belong in artifact storage, not `jobs.payload_json` or `job_attempts.error_message`.

## Initial workload

First adopter must be non-stock-mutating and low consequence.

Recommended candidates:

1. management/report export generation;
2. notification delivery/digest preparation;
3. non-authoritative cache/read-model refresh.

Do not start with:

- inventory movement;
- purchase receipt;
- shipment completion;
- refund;
- BOM release;
- quality release.

Those need stronger business-operation semantics and/or approval.

## Deterministic tests

### Claim ownership

- two connections/workers cannot own one generation;
- highest priority then oldest eligible row is selected deterministically;
- future `available_at` is not claimable;
- non-expired running job is not claimable.

### Lease recovery

- expired running lease is reclaimable;
- reclaim increments generation and attempt number;
- new attempt row is appended;
- prior attempt history is never overwritten.

### Fencing

- old generation cannot complete after reclaim;
- old generation cannot heartbeat after reclaim;
- current generation can complete exactly once.

### Restart

- queued jobs survive process restart;
- expired running job can recover after restart;
- succeeded/dead-letter/cancelled jobs are not reclaimed.

### Payload / dedupe

- payload survives JSON round trip;
- duplicate `(job_type,idempotency_key)` enqueue is deterministic;
- same dedupe key must not silently replace payload of an existing job.

## Rollback

Migration 3 is additive. Existing OCR/image queues remain operational and authoritative for their current workloads until explicitly migrated.

On code rollback, leave job history tables intact/inert.

## Acceptance

One low-risk workload can be:

```text
enqueued
 -> atomically claimed
 -> executed outside write transaction
 -> completed with fencing
```

and can recover from a simulated worker death/expired lease without duplicate completion.

No hosted queue, Redis, Kafka or GitHub scheduler is required.

## Dependencies

E00 Migration framework and E01-S01.

Runtime implementation remains blocked until:

```text
E00 real-checkout Release Gate = PASS
AND Inventory PR #3 reviewed/merged
```
