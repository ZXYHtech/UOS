# TASK_INV_IMPL_E01_S09 — Correlation IDs Across Request / Action / Job / Outbox

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Make one business incident traceable across synchronous API handling, durable operations, jobs and external delivery without using free-text log searches.

## Correlation contract

One bounded opaque correlation ID propagates through:

```text
HTTP request
 -> RequestContext
 -> Action execution
 -> business_operations
 -> operation_logs
 -> jobs / job_attempts
 -> outbox_events
 -> provider request / acknowledgement metadata
```

## ID rules

- accept inbound ID only when syntax/length is valid;
- otherwise generate server-side UUID/ULID-style opaque ID;
- never use correlation ID for authentication, authorization or idempotency;
- expose it in error/success receipts where useful for support;
- log it as a structured field.

## Migration ownership

**Proposed Migration 5**:

```text
ALTER TABLE operation_logs ADD COLUMN correlation_id TEXT;
```

`business_operations`, `jobs` and `outbox_events` already include correlation fields in Migrations 2–4.

Add index only if measured support queries justify it; do not index every trace field by default.

## Backward compatibility

Historical `operation_logs.correlation_id` remains NULL. Never synthesize fake historical traces.

## Tests

- missing inbound ID generates one;
- invalid/oversized inbound ID is replaced/rejected deterministically;
- valid inbound ID propagates unchanged;
- one pilot action produces matching IDs in business operation and audit log;
- job created from that action keeps the same ID;
- outbox event/delivery evidence keeps the same ID;
- correlation mismatch is detectable in fixture assertions.

## Acceptance

A deterministic end-to-end fixture starts with one request and can query all produced evidence by a single correlation ID.

## Dependencies

E01-S01, E01-S04, E01-S05, E01-S08.
