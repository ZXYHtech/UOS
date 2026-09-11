# TASK_INV_IMPL_E01_S09 — Correlation IDs Across Request / Action / Job / Outbox

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Make one business incident traceable across synchronous API handling, durable operations, jobs and external delivery without relying on free-text log searches.

Correlation is observability context only. It is never authentication, authorization, idempotency or business identity.

## Current integration point

The existing audit helper has the conceptual shape:

```text
log_operation(
  conn,
  user_id,
  action_type,
  target_type,
  target_id,
  before,
  after,
  ip,
  device
)
```

S09 should extend it compatibly with an optional `correlation_id=None` argument rather than replacing all existing audit calls at once.

Historical callers continue to work and historical rows remain `NULL`.

## End-to-end correlation chain

One bounded opaque ID propagates through:

```text
HTTP request
 -> RequestContext
 -> Action Policy execution
 -> business_operations
 -> operation_logs
 -> jobs
 -> job_attempt execution context
 -> outbox_events
 -> provider adapter request/ack diagnostic metadata
```

The ID answers:

> “Which records and asynchronous attempts belong to this one originating business interaction?”

It does not answer:

> “Is this action allowed?” or “Has this business command already happened?”

Those belong to Action Policy and S04 idempotency.

## ID format

Server-generated default:

```text
UUID4 string
```

Accept an inbound value only if it matches a conservative bounded token grammar, e.g.:

```text
1..64 chars
ASCII letters/digits plus . _ : -
must begin with alphanumeric
```

Conceptual regex:

```regex
^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$
```

Invalid/oversized values should be **replaced with a server-generated ID** for ordinary requests rather than causing a business request failure solely because tracing metadata is malformed.

Record a low-level diagnostic if useful, but never echo arbitrary rejected text into logs.

## Request lifecycle

At the API boundary:

```text
read inbound X-Correlation-ID (or chosen single header)
 -> validate bounded token
 -> preserve valid value OR generate UUID4
 -> put into RequestContext
```

One request gets exactly one root correlation ID.

Nested domain methods receive it through context/explicit execution metadata rather than repeatedly reading HTTP headers.

## Response exposure

Preferred API behavior:

```text
X-Correlation-ID: <id>
```

on both success and error responses where the HTTP adapter can add a common header without breaking existing payload shapes.

If the current response helpers make global header injection invasive, start by including correlation in structured error/operation receipts for migrated E01 routes and add common header support as a bounded adapter change.

Do not globally change every existing JSON response body merely to add tracing metadata.

## Migration ownership

**Proposed Migration 5**:

```text
ALTER TABLE operation_logs ADD COLUMN correlation_id TEXT;
```

Migrations 2–4 already include correlation fields for:

```text
business_operations
jobs
outbox_events
```

Recommended index:

```text
CREATE INDEX idx_operation_logs_correlation
ON operation_logs(correlation_id)
WHERE correlation_id IS NOT NULL;
```

Rationale: support/debugging is a primary use case and correlation lookups should not require a full audit-log scan.

Do not backfill fake IDs for historical rows.

## `log_operation` compatibility change

Target signature conceptually becomes:

```python
log_operation(
    conn,
    user_id,
    action_type,
    target_type,
    target_id=None,
    before=None,
    after=None,
    ip=None,
    device=None,
    correlation_id=None,
)
```

Rules:

- optional final parameter preserves existing positional call behavior;
- migrated E01 Action Policy routes pass `ctx.correlation_id`;
- legacy routes may remain NULL until migrated;
- audit log should store the ID as its own column, not bury it in `after_json`.

## Business Operation propagation

S04 creates the row using:

```text
correlation_id = RequestContext.correlation_id
```

A replay using the same idempotency key may arrive with a **different new HTTP correlation ID**.

Do not overwrite the original business operation's correlation ID.

Recommended semantics:

- original operation keeps original correlation ID as creation lineage;
- replay response may report both current request correlation and original operation/result identity;
- do not treat correlation mismatch as idempotency conflict.

## Job propagation

When synchronous business handling enqueues a job:

```text
jobs.correlation_id = current/root correlation ID
```

A retry/reclaim keeps the same job correlation ID across all attempts.

`job_attempts` does not need a duplicate correlation column in Migration 3 if it can be joined through `job_id`; worker logs should still emit the job's correlation ID structurally.

A child job intentionally spawned by a job should inherit the parent correlation ID unless the domain explicitly starts a new independent business interaction.

## Outbox propagation

Outbox producer writes:

```text
outbox_events.correlation_id = originating context correlation ID
```

The paired `outbox.deliver` job inherits the same value.

Provider adapters may send a correlation/request diagnostic header only when allowed by the provider contract. It must not be substituted for provider idempotency keys.

Provider acknowledgements stored locally retain the correlation link through the outbox event/job.

## Security/privacy boundary

Correlation IDs must contain no:

- user name/email/phone;
- order number unless the provider itself defines it as request identity;
- access token/session token;
- customer data;
- secrets.

Opaque random IDs avoid accidental PII leakage into logs/support exports.

Never trust inbound correlation ID to select another user's operation or bypass scope checks.

## Deterministic tests

### Parsing

- missing header -> server-generated valid UUID/token;
- valid bounded inbound ID -> preserved exactly;
- invalid characters -> replaced;
- >64 chars -> replaced;
- rejected raw input is not copied into audit fields.

### Synchronous pilot

For `transfer.receive` or another migrated pilot:

```text
request correlation X
 -> RequestContext X
 -> business_operations X
 -> operation_logs X
```

All must match.

### Replay

First call uses X, replay uses Y:

- original business operation remains correlated to X;
- replay does not mutate its row to Y;
- no second stock effect/audit business event;
- current request Y can still be present in transport diagnostics.

### Async chain

One fixture produces:

```text
business operation X
 -> outbox event X
 -> delivery job X
 -> retry attempt logs X
```

Querying by X can reconstruct the chain.

### Legacy compatibility

- old `log_operation(...)` calls without correlation still work;
- pre-migration historical rows are NULL, not fake-generated;
- existing audit-log APIs remain compatible if they do not request the new field.

## Acceptance

A deterministic end-to-end fixture starts with one request and can reconstruct all E01-produced synchronous and asynchronous evidence through one correlation ID without free-text search.

## Dependencies

E01-S01, S04, S05 and S08.

Runtime implementation remains blocked until:

```text
E00 real-checkout Release Gate = PASS
AND Inventory PR #3 reviewed/merged
```
