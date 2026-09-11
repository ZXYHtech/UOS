# TASK_INV_IMPL_E01_S07 — Retry Classes, Backoff & Dead-letter

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Prevent durable jobs from either retrying forever or failing permanently on transient infrastructure errors, while ensuring ambiguous business state is never “fixed” by blind automatic replay.

## Core principle

Retry policy is based on **typed failure classification**, not exception message text.

The worker must never implement logic such as:

```python
if "timeout" in str(exc): retry()
```

Handlers/adapters translate provider/domain errors into a small controlled failure taxonomy.

## Failure classes

### `RETRYABLE_TECHNICAL`

Examples:

- network connect/read timeout before confirmed provider success;
- provider 5xx with no success acknowledgement;
- temporary DNS/connection failure;
- explicit rate limit / Retry-After;
- temporary local resource unavailable condition.

Eligible for bounded retry according to job-type policy.

### `PERMANENT_INPUT`

Examples:

- malformed/unsupported payload;
- referenced object permanently missing/deleted;
- unsupported provider contract/version;
- invalid static configuration that retry cannot repair.

No automatic retry.

Normally transition to `dead_letter` or an explicit failed-terminal policy state.

### `MANUAL_REVIEW`

Examples:

- ambiguous SKU/material mapping;
- provider may have accepted an external action but local acknowledgement was lost;
- external object state differs from the expected precondition;
- replay could duplicate shipment/refund/order acknowledgement;
- business owner must choose among multiple valid resolutions.

No normal worker reclaim until a human/reconciliation process explicitly resolves/requeues it.

### `CANCELLED`

Operator/domain cancellation where no retry should occur.

## Why timeout does not always mean retry

The phase of failure matters.

Safe retry example:

```text
connect timeout before request is accepted
 -> RETRYABLE_TECHNICAL
```

Unsafe ambiguity example:

```text
request body sent
 -> provider processed it
 -> response/ack lost
 -> local timeout
```

This is not automatically retryable for a non-idempotent provider operation. It becomes:

```text
MANUAL_REVIEW or reconciliation-required
```

unless the provider supplies a stable idempotency/external-object key that makes replay provably safe.

## Job-type policy

Each registered job type declares a code-owned policy:

```text
max_attempts
base_delay_seconds
max_delay_seconds
lease_seconds
retryable_error_codes/classes
manual_review_error_codes/classes
optional honor_retry_after flag
```

Do not store arbitrary executable retry formulas in DB.

## Backoff

Recommended v1 policy:

```text
delay = min(max_delay, base_delay * 2^(attempt_no-1))
```

Optional bounded jitter may be added by the worker to avoid synchronized retries.

Rules:

- persist the computed `available_at` at failure time;
- never recompute historical retry times later;
- provider `Retry-After` may increase the delay when the adapter validates it;
- cap absurd/unbounded provider retry values according to job-type policy;
- no sub-second busy-looping.

## Fenced failure transition

Failure handling must match current ownership:

```text
job_id
status='running'
lease_owner=current worker
lease_generation=current generation
```

### Retryable failure with attempts remaining

Same short transaction:

```text
UPDATE jobs
 SET status='retry_wait',
     available_at=?,
     lease_owner=NULL,
     lease_until=NULL,
     updated_at=?
 WHERE fenced ownership matches

UPDATE current job_attempts row
 SET outcome='retry_wait',
     error_class='RETRYABLE_TECHNICAL',
     error_message=?,
     finished_at=?
```

### Max attempts reached

```text
status='dead_letter'
lease cleared
attempt outcome='dead_letter'
```

### Permanent input

```text
status='dead_letter'
attempt outcome='permanent_failure'
```

### Manual review

```text
status='manual_review'
attempt outcome='manual_review'
```

A zero-row fenced update means ownership was lost; stale worker must not publish its failure state either.

## Attempt-count semantics

`attempt_count` increments only when a worker successfully claims a new generation.

Do not increment simply because:

- polling found the row;
- heartbeat happened;
- a stale worker tried to finish;
- an operator inspected/requeued the job.

`attempt_no` in `job_attempts` should equal the job's attempt count at claim time.

## Manual requeue contract

Manual requeue must be an explicit audited command, not direct SQL/UI field editing.

Required inputs:

```text
job_id
reason
actor/system identity
expected current terminal/manual state
```

Result:

```text
status -> queued or retry_wait
available_at -> now/explicit approved time
lease remains clear
payload is NOT silently replaced
attempt history remains intact
new operation/audit evidence appended
```

If the payload/business reference must change, create a new job with a new identity unless a domain-specific correction workflow explicitly owns mutation.

## Dead-letter visibility

Dead-letter is not a black hole.

Minimum operator/read-model information:

```text
job type
job id
business reference summary
attempt count / max attempts
last failure class/code
last bounded error message
correlation ID
first/last timestamps
manual requeue/cancel eligibility
```

Do not build a large admin dashboard in S07; a repository-local inspection command or simple API/read view is enough initially.

## Data migration

No new table if E01-S05 Migration 3 contains:

```text
status
available_at
attempt_count
max_attempts
lease fields
job_attempts
```

If later analytics needs full structured error codes, add an additive column/migration rather than overloading free-text messages.

## Deterministic tests

### Transient then success

```text
attempt 1 -> RETRYABLE_TECHNICAL
 -> retry_wait with future available_at
 -> not claimable early
 -> claim attempt 2
 -> success
```

Require both attempt rows remain visible.

### Repeated transient failure

- each claim increments attempt exactly once;
- delay grows/caps according to policy;
- when max attempts reached -> dead_letter;
- dead_letter never gets picked by normal claim.

### Permanent input

- one attempt;
- no retry_wait;
- dead-letter/permanent terminal state immediately.

### Manual-review ambiguity

- state becomes manual_review;
- normal worker ignores it;
- explicit audited requeue is required;
- no automatic replay occurs merely because time passes.

### Fencing

- generation N expires and N+1 is reclaimed;
- N cannot mark retry/dead-letter/success afterward;
- N+1 remains authoritative.

### Retry-After

- validated provider delay is persisted;
- cap is honored;
- invalid/negative/extreme raw values do not cause unbounded scheduling.

## Metrics/readiness signals

Even before a dashboard, expose/count:

```text
queued
running
retry_wait
manual_review
dead_letter
oldest eligible age
lease-expired count
success/failure by job_type
```

These become later observability inputs; they are not reasons to introduce Prometheus/Kafka in E01.

## Acceptance

A deterministic fixture demonstrates both:

```text
transient failure -> bounded retry -> success
```

and:

```text
repeated failure -> dead_letter
```

while an ambiguous provider-state fixture demonstrates:

```text
ambiguous outcome -> manual_review -> NO automatic replay
```

No failure path may busy-loop or allow a stale lease generation to overwrite a newer attempt.

## Dependencies

E01-S05 and E01-S06.

Runtime implementation remains blocked until:

```text
E00 real-checkout Release Gate = PASS
AND Inventory PR #3 reviewed/merged
```
