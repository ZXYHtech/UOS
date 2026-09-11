# TASK_INV_IMPL_E01_S06 — Worker CLI / Service Runtime

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Provide one server-owned process entry point for E01 durable jobs without GitHub Actions, in-process Web threads or a new queue product.

The implementation should borrow operational lessons from the existing OCR supervisor while keeping OCR itself unchanged during the first E01 rollout.

## Existing OCR lessons

Preserve these principles:

- Web process and worker process fail independently;
- expensive/native work can be isolated from Web;
- explicit timeout/shutdown behavior;
- DB claim transaction stays short;
- resource/backpressure policy belongs to worker/job type;
- interrupted work is not silently considered successful.

Generic worker adds S05 lease/fencing rather than relying on “mark every old running task failed on restart.”

## Proposed entry point

```text
inventory_app/worker.py
```

CLI:

```bash
python3 -m inventory_app.worker --once
python3 -m inventory_app.worker --loop
python3 -m inventory_app.worker --once --job-type report.generate
```

Configuration/options:

```text
worker ID override
poll interval
supported job-type filter
shutdown grace period
max jobs before optional recycle
log verbosity
```

Lease duration and retry policy are owned by registered job-type policy, not arbitrary CLI input in production.

## Worker identity

Default worker ID should be unique enough for one host/process, e.g. derived from:

```text
hostname + pid + process-start nonce
```

It is diagnostic/lease ownership identity, not authentication.

Do not reuse a static hostname-only worker ID across concurrent processes.

## Handler registry

Use code-owned registration:

```text
job_type -> handler + policy
```

Example conceptual registry:

```python
register_job(
    "report.generate",
    handler=generate_report,
    lease_seconds=120,
    max_attempts=3,
    retry_policy="standard_network",
)
```

Do not load arbitrary import paths from DB payloads.

Unknown `job_type` is a permanent configuration failure/manual-review case, never success.

## Execution loop

```text
receive stop signal?
  yes -> stop claiming new work

claim one eligible job using S05
  none -> --once exits 0 / --loop sleeps then repeats

resolve registered handler
  missing -> fenced transition to manual_review/permanent failure

execute outside DB write transaction
  optional heartbeat for long workload

handler outcome
 -> succeeded
 -> typed retryable failure
 -> permanent failure
 -> manual review

persist outcome using job_id + lease_owner + lease_generation fencing
repeat
```

## Handler contract

Handler receives a bounded immutable execution context, not a raw unrestricted DB connection by default:

```text
job_id
job_type
payload
attempt_no
lease_generation
correlation_id
worker_id
cancellation/ownership check helper
```

A handler that needs DB access opens/uses a normal domain-service connection according to that domain's rules.

Do not let generic worker handlers bypass permissions/business services merely because they run server-side.

For system-generated jobs, authorization provenance should be captured at enqueue time (actor/system source) where consequential behavior requires it.

## Fencing on publication

The handler may finish after losing its lease. Therefore the worker must not directly mark success from an in-memory assumption.

Completion call must verify:

```text
job.id
status='running'
lease_owner=current worker
lease_generation=current generation
```

Zero rows changed means ownership was lost. Discard/cleanup unpublished temporary output and log a stale-worker diagnostic.

## Graceful shutdown

### SIGTERM / SIGINT

On stop request:

1. stop claiming new jobs;
2. if no active handler, exit;
3. let active handler finish within configured grace period when safe;
4. maintain heartbeat during grace if required;
5. after grace, request cancellation/terminate isolated child where supported;
6. never force a succeeded DB transition after lease ownership is lost.

For non-isolated Python handlers that cannot be safely interrupted, process termination leaves the lease to expire and be handled by S07 policy.

## Isolation levels

Not every job requires a child process.

### In-process handler

Use for:

- small report metadata generation;
- lightweight notifications;
- deterministic short read-model refresh.

### Child-process handler

Prefer for:

- native libraries with memory-risk behavior;
- expensive image/OCR-like work;
- workloads requiring hard kill/timeouts;
- jobs where process-level resource limits matter.

Do not make every trivial job spawn a process just because OCR does.

## `--once` semantics

`--once` means:

```text
claim at most one eligible job
 -> if none: exit 0
 -> if claimed: execute/persist its outcome
 -> exit with a diagnostic process code
```

The job's durable state, not shell exit code alone, is authoritative.

`--once` is useful for deterministic tests/operations but is not the main production scheduler.

## `--loop` semantics

- continuously claim one job at a time in v1;
- no internal thread pool initially;
- horizontal process count can be increased only after claim/fencing tests prove safety;
- poll with bounded sleep when empty;
- react promptly to stop signals.

Start with one generic worker process. Measure before adding concurrency.

## Production supervision

Target unit:

```text
inventory-worker.service
```

Suggested relationship:

```text
After=network.target
WorkingDirectory=<APP_DIR>
User=<APP_USER>
Environment=INVENTORY_DB_PATH=<DB_PATH>
ExecStart=/usr/bin/python3 -m inventory_app.worker --loop
Restart=always
RestartSec=3
```

Resource limits should follow the E00 systemd style but be based on the first actual workload, not copied blindly from OCR memory limits.

The worker remains independently restartable from:

```text
inventory-lite.service
inventory-lite-ocr.service
inventory-lite-backup.service
```

## Deployment cutover behavior

Once this service exists, E00-style production update scripts must treat it as another business/background writer:

```text
pre-change backups pass
 -> stop inventory-worker before runtime dependency/code/schema cutover
 -> upgrade/migrate
 -> restart worker only after DB migration/integrity and Web health prerequisites pass
```

Do not forget the generic worker when quiescing production for future migrations.

## Data migration

None beyond E01-S05 Migration 3.

## Deterministic tests

### CLI

- `--once` with no job exits without mutation;
- `--once` processes at most one job;
- `--job-type` never claims unsupported type;
- invalid option/config fails at startup.

### Handler registry

- registered handler resolves deterministically;
- unknown handler becomes durable manual-review/permanent outcome;
- DB payload cannot select an arbitrary Python import/function.

### Lifecycle

- handler success fences/marks one job succeeded;
- handler exception goes through S07 typed failure transition;
- SIGTERM stops new claims;
- active expired lease can be reclaimed by another worker;
- stale first worker cannot complete afterward.

### Independence

- killing worker does not take Web API down;
- restarting Web does not erase queued jobs;
- restarting worker does not erase queued/retry/attempt history.

## Initial production workload

Use the same low-risk workload selected by S05, preferably a report/export or notification task.

Do not use stock mutation as the generic worker proof.

## Acceptance

One low-risk durable job executes end-to-end through:

```text
enqueue -> claim -> handler -> fenced completion
```

survives worker restart/lease expiry and requires no hosted scheduler/queue infrastructure.

## Dependencies

E01-S05, with retry policy completed by S07.

Runtime implementation remains blocked until:

```text
E00 real-checkout Release Gate = PASS
AND Inventory PR #3 reviewed/merged
```
