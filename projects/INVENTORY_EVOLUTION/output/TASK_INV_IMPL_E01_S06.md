# TASK_INV_IMPL_E01_S06 — Worker CLI / Service Runtime

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Provide one server-owned process entry point for E01 durable jobs without GitHub Actions, in-process web threads or a new queue product.

## Proposed entry point

```text
inventory_app/worker.py
```

CLI modes:

```bash
python3 -m inventory_app.worker --once
python3 -m inventory_app.worker --loop
```

Required options/config:

- worker ID override;
- poll interval;
- supported job types / queue filter;
- graceful shutdown timeout;
- lease duration defaults owned by job type policy.

## Process model

Preferred production supervision:

```text
inventory-worker.service
```

The worker must be independently restartable from Web/OCR. No job correctness may depend on a Python background thread living inside the HTTP process.

## Execution loop

```text
claim one eligible job
 -> dispatch registered handler by job_type
 -> heartbeat/lease extension only when workload requires it
 -> complete / retry / dead-letter through durable state transition
 -> repeat
```

Unknown job type must not be treated as success; classify as manual-review/permanent configuration error.

## Data migration

None beyond E01-S05 Migration 3.

## Tests

- `--once` exits after zero/one claim deterministically;
- `--loop` can be interrupted gracefully without corrupting lease state;
- unknown handler does not drop the job;
- handler exception is persisted through job failure policy;
- worker restart can reclaim expired lease;
- Web process availability is independent of worker death.

## Deployment

Add systemd unit only after deterministic worker tests pass. Resource limits should follow the E00 pattern and be explicit per workload class.

## Acceptance

A durable job can be executed end-to-end by a repository-local worker CLI/service and survives process restart with no hosted scheduler dependency.

## Dependencies

E01-S05.
