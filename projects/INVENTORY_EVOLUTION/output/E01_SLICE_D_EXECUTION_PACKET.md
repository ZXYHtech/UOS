# E01 Slice D Execution Packet — Durable Jobs / Worker / Retry

## Status

`READY_TO_START_ONLY_AFTER_E01_SLICE_C_MERGE`

This slice introduces the reusable DB-backed durable job substrate. It does **not** migrate OCR or stock mutations in the first PR.

## 1. Entry gate

Required:

```text
E00 merged
E01 Slice A/B/C merged
full Release Gate PASS on current main
```

Suggested branch:

```text
impl/e01-durable-jobs
```

## 2. Existing implementation to preserve

Current `inventory_app/ocr_queue.py` already proves several good patterns:

```text
BEGIN IMMEDIATE claim
 -> short DB ownership
 -> commit claim
 -> expensive OCR in isolated child process
 -> timeout/terminate/kill
 -> web process remains isolated
```

It also deliberately avoids blindly replaying interrupted OCR: startup converts stale `running` OCR tasks to failed rather than assuming re-execution is safe.

These behaviors are evidence, not code to immediately replace.

## 3. Why a generic job framework is still required

Current OCR/image queues do not provide the reusable guarantees needed for future connectors/outbox/MRP/AI jobs:

```text
lease expiry
lease owner
lease generation/fencing token
attempt history
available_at scheduling
bounded retry classes
manual_review / dead_letter
job idempotency key
correlation propagation
worker-generic handler registry
```

Do not solve these independently in every future feature.

## 4. Migration 3

Migration sequence:

```text
1 baseline
2 business_operations
3 jobs + job_attempts
```

Suggested `jobs` contract:

```text
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
max_attempts INTEGER NOT NULL
idempotency_key TEXT
correlation_id TEXT
last_error_class TEXT
last_error_message TEXT
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
completed_at TEXT
```

Statuses:

```text
queued
running
retry_wait
succeeded
dead_letter
manual_review
cancelled
```

Suggested uniqueness:

```text
UNIQUE(job_type, idempotency_key) WHERE idempotency_key IS NOT NULL
```

If SQLite migration helper cannot express a partial unique constraint portably in current style, use an equivalent unique index and cover it with tests.

Suggested indexes:

```text
(status, available_at, priority DESC, id)
(lease_until, status)
(correlation_id)
(job_type, created_at DESC)
```

`job_attempts`:

```text
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
UNIQUE(job_id, attempt_no)
```

## 5. Target files

Add:

```text
inventory_app/platform/jobs.py
inventory_app/worker.py
tools/test_durable_jobs.py
tools/test_worker_runtime.py
```

Modify:

```text
inventory_app/schema_migrations.py
inventory_app/db_integrity.py
tools/verify_release.py
deploy/linux/setup_server.sh       # only after CLI worker tests are stable
deploy/linux/restart_service.sh    # only if worker service is enabled in this slice
```

Do not delete or redirect `ocr_queue.py` in the first implementation.

## 6. Claim algorithm

Claim must be short and transactional:

```text
BEGIN IMMEDIATE
 -> find one eligible queued/retry_wait job
      status eligible
      available_at <= now
      lease absent/expired
 -> increment lease_generation
 -> increment attempt_count
 -> set status=running
 -> set lease_owner
 -> set lease_until
 -> insert job_attempts(attempt_no, generation, worker)
COMMIT
```

Then execute handler **outside** the write transaction.

Do not hold the SQLite write lock while performing network, OCR, file conversion or long calculations.

## 7. Fencing invariant

`lease_generation` is not display metadata. It is the fencing token.

Every completion/failure/heartbeat mutation must require:

```text
job.id = claimed job
AND status = running
AND lease_owner = current worker
AND lease_generation = claimed generation
```

If zero rows change:

```text
worker has lost ownership
 -> it must not publish completion
 -> it must not overwrite newer result/error state
```

This prevents:

```text
worker A stalls
lease expires
worker B reclaims generation 2
worker A wakes up late
worker A incorrectly overwrites B
```

## 8. Lease / heartbeat

First version should support bounded heartbeat extension for handlers that legitimately run longer than one lease interval.

Rules:

- heartbeat updates only the matching owner+generation;
- heartbeat cannot revive cancelled/dead/succeeded jobs;
- lease duration is configured by job type or safe worker default;
- no per-second high-frequency writes; heartbeat cadence should be substantially lower than lease duration.

## 9. Handler registry

Code-owned static registry:

```text
job_type
handler
retry policy
default max_attempts
default lease duration
payload validator
```

No DB-stored arbitrary Python import path.

Unknown `job_type` must fail deterministically to manual_review/dead-letter policy, not execute dynamic code.

## 10. First adopter

Use a low-risk, non-stock-mutating fixture/job.

Good candidates:

- deterministic test artifact generation;
- no-op/echo fixture available only to tests/dev;
- bounded housekeeping calculation that does not change business truth.

Do **not** make first adopter:

- inventory adjustment;
- shipment;
- purchase receipt;
- payment/refund;
- external order push.

## 11. Retry taxonomy

At minimum:

### RETRYABLE_TECHNICAL

Examples:

```text
timeout before known acceptance
temporary DNS/network failure
provider 5xx
rate-limit with deterministic retry-after
transient lock/busy condition where operation is replay-safe
```

Behavior:

```text
status=retry_wait
available_at=backoff time
```

### PERMANENT_INPUT

Examples:

```text
invalid payload
missing required mapping
unsupported enum/provider
malformed identifier
```

Behavior:

```text
dead_letter or terminal failed policy
no automatic loop
```

### MANUAL_REVIEW

Examples:

```text
provider may have accepted request but acknowledgement lost
ambiguous mapping
conflicting remote/local state
unsafe replay uncertainty
```

Behavior:

```text
manual_review
no blind retry
```

## 12. Backoff

Use deterministic bounded backoff with optional jitter only where appropriate.

Persist `available_at`; do not `sleep()` inside a worker while holding job ownership just to wait for the next retry.

Suggested policy must be configurable per registered job type, for example:

```text
attempt 1 -> immediate/short
attempt 2 -> minutes
attempt 3 -> longer
then terminal/manual review
```

Do not create unbounded exponential retry.

## 13. Worker CLI

Required local entry point:

```bash
python3 -m inventory_app.worker --once
python3 -m inventory_app.worker --loop
```

Useful options:

```text
--worker-id
--job-type (optional constrained filter)
--poll-seconds
```

Worker ID should be generated if absent but remain stable for the process lifetime.

No GitHub scheduler.

## 14. Systemd rollout

Only after CLI fixture tests pass:

```text
inventory-lite-worker.service
```

Requirements:

- same app user/data path as main deployment;
- restart on crash;
- independent from Web process;
- stop before schema cutover in update script;
- restart only after migration/health gate;
- bounded memory/tasks settings appropriate to current server.

Do not introduce a process pool yet. Start with one generic worker unless measured throughput requires more.

## 15. Cancellation

Cancellation is a state transition, not process kill alone.

Queued/retry jobs:

```text
-> cancelled
```

Running job:

- mark cancellation requested or use explicit cancel state policy;
- handler cooperatively checks where safe;
- stale worker still cannot commit after generation/ownership changes.

Do not claim arbitrary external side effects can always be cancelled.

## 16. Required tests

### Claim exclusivity

Two DB connections/workers race:

- only one claims generation N;
- one attempt row created for that claim.

### Lease reclaim

- job claimed by A;
- lease expires;
- B reclaims with generation N+1;
- B owns new attempt.

### Fencing

After B reclaims:

- A completion update changes zero rows;
- A cannot mark success/failure;
- B can complete.

### Restart recovery

- queued/retry jobs survive worker restart;
- expired running job can be reclaimed according to policy;
- non-expired running job is not stolen.

### Retry classes

Prove different behavior for:

```text
retryable technical
permanent input
manual review
```

### Max attempts

- repeated retryable failure eventually stops;
- no infinite loop.

### Idempotent enqueue

Where idempotency_key is supplied:

- duplicate enqueue produces/references one logical job;
- same logical external delivery is not multiplied.

### Correlation

- correlation ID survives enqueue -> claim -> attempt -> terminal state.

## 17. Interaction with existing OCR

First release:

```text
OCR remains on inventory_app.ocr_queue
image derivative queue remains unchanged
```

Reason:

- existing paths are operationally proven;
- migrating them at the same time would mix framework validation with behavior migration;
- OCR has special child-process/memory/timeout semantics worth preserving.

After generic worker is stable, a later explicit adapter story may migrate OCR if benefits justify it.

No E01 completion criterion requires OCR migration.

## 18. Audit / observability

Job history is operational evidence, not the same as human business audit.

Expose query helpers for:

```text
job state
attempt history
last error class/message
correlation ID
next available_at
lease owner/until/generation
```

Do not log secrets/full provider tokens into payload or error text.

## 19. PR review checklist

```text
[ ] Migration 3 contiguous/immutable
[ ] claim uses short BEGIN IMMEDIATE transaction
[ ] handler runs outside DB write transaction
[ ] every terminal update checks owner + generation
[ ] stale worker cannot commit
[ ] retry taxonomy explicit
[ ] max attempts bounded
[ ] manual-review ambiguity never blind-retried
[ ] first adopter non-stock-mutating
[ ] OCR not rewritten in same PR
[ ] worker CLI works without systemd
[ ] systemd, if added, is server-local not GitHub-based
[ ] full Release Gate PASS
```

## 20. Rollback

Application rollback:

- stop generic worker;
- stop enqueueing new generic jobs;
- keep `jobs` and `job_attempts` history;
- do not delete evidence.

Any queued work requiring continuation must be explicitly dispositioned before disabling the feature that owns it.

## 21. Exit / unlock

Slice D completes when lease/fencing/retry/restart behavior is proven and server-local worker operation is stable.

Then unlock:

```text
E01 Slice E — Transactional Outbox + persistent Correlation
```
