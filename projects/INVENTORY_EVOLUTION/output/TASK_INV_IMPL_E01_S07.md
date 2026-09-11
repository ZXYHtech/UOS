# TASK_INV_IMPL_E01_S07 — Retry Classes, Backoff & Dead-letter

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Prevent durable jobs from either retrying forever or failing permanently on transient infrastructure errors.

## Error classes

```text
RETRYABLE_TECHNICAL
  network timeout
  provider 5xx
  transient connection failure
  explicit rate limit / retry-after

PERMANENT_INPUT
  malformed payload
  deleted/nonexistent required object
  unsupported provider contract

MANUAL_REVIEW
  ambiguous mapping
  provider success/local acknowledgement uncertain
  unsafe replay state
```

Handlers return/raise typed failure outcomes; worker code must not infer retryability from arbitrary message text.

## State transitions

```text
running
 -> succeeded
 -> retry_wait(available_at)
 -> dead_letter
 -> manual_review
```

`attempt_count >= max_attempts` converts retryable failures to dead-letter unless job-type policy explicitly routes to manual review.

## Backoff

Use bounded deterministic policy with optional jitter at runtime. Store the resulting `available_at`; do not recompute historical retry times later.

Per-job-type policy owns:

- max attempts;
- base delay;
- maximum delay;
- retryable error classes;
- lease duration.

## Data migration

No new table if E01-S05 Migration 3 includes required status, `available_at`, attempt and max-attempt fields.

## Tests

- retryable failure schedules a future attempt;
- permanent input failure is not requeued;
- max attempts ends in dead-letter;
- manual-review case remains inspectable and unclaimed by normal worker;
- successful retry preserves earlier failed attempt evidence;
- stale worker cannot overwrite a newer retry generation.

## Acceptance

A deterministic fixture demonstrates transient failure → retry → success and repeated failure → dead-letter without busy-looping.

## Dependencies

E01-S05, E01-S06.
