# TASK_INV_IMPL_E01_S04 — Business Operation / Idempotency

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Make replay-sensitive business commands safe against double-click, client retry, proxy retry and timeout ambiguity without introducing a second database or distributed transaction system.

This design is grounded in the audited current application:

- authenticated API work already executes inside a request-owned `with get_conn() as conn` block;
- pilot services (`TransferService`, `ProcurementService`, `ShipmentService`) accept the caller's SQLite connection;
- current service methods write business rows/audit evidence through that connection rather than owning an external transaction coordinator;
- OCR/image job claim paths already prove `BEGIN IMMEDIATE` is an accepted SQLite concurrency primitive in this codebase.

## Migration ownership

**Proposed Migration 2** after E00 baseline migration 1:

```text
business_operations
  id INTEGER PRIMARY KEY AUTOINCREMENT
  operation_key TEXT NOT NULL
  action_code TEXT NOT NULL
  actor_id INTEGER
  target_type TEXT
  target_id INTEGER
  request_fingerprint TEXT NOT NULL
  correlation_id TEXT
  status TEXT NOT NULL
  result_type TEXT
  result_id INTEGER
  result_json TEXT
  error_code TEXT
  started_at TEXT NOT NULL
  completed_at TEXT

UNIQUE(action_code, operation_key)
CHECK(status IN ('running','succeeded','failed','manual_review'))
```

Indexes:

```text
(status, started_at)
(actor_id, started_at DESC)
(target_type, target_id, started_at DESC)
(correlation_id)
```

Do not overload `operation_logs`: `business_operations` answers replay/command identity; `operation_logs` remains audit evidence.

## Idempotency key contract

Preferred source order:

1. provider/business event ID when the provider guarantees stable uniqueness;
2. explicit client-generated idempotency key persisted across retries;
3. server-generated key issued to a controlled UI flow before commit.

The key must be bounded and opaque. It is not authorization and must never encode trusted warehouse/user authority.

UI button disabling is UX only, never an idempotency guarantee.

## Canonical request fingerprint

Compute SHA-256 over canonical JSON containing only stable business-effect inputs:

```text
action_code
authoritative target identity
normalized quantity/item lines
business options that change the effect
```

Exclude:

```text
correlation ID
request timestamp
client rendering fields
transient retry metadata
presentation-only text
```

Canonicalization rules must be deterministic:

- JSON object keys sorted;
- integers normalized as integers;
- whitespace/irrelevant ordering removed where semantics allow;
- item ordering sorted only where business semantics are order-independent;
- never normalize away a field that changes stock or state.

## Two idempotency classes

E01 must distinguish local atomic commands from future external/long-running workflows.

### Class A — `atomic_local`

Used by the first stock-affecting pilots:

```text
transfer.receive
purchase.receive
shipment.complete
```

Everything consequential is in the same SQLite database transaction.

### Class B — `durable_external`

Reserved for later commands that involve external providers or long-running processing.

They must not hold a SQLite write transaction while waiting on a network call. Those flows require S05–S08 durable jobs/outbox/reconciliation.

Do not use the Class A algorithm to wrap marketplace/payment/carrier calls.

## Exact Class A execution algorithm

Read-only authorization resolution happens first:

```text
RequestContext
 -> load authoritative target
 -> permission
 -> object-derived warehouse scope
 -> existing business precondition/state validation
 -> normalize request + compute fingerprint
```

Then the idempotency/business transaction begins:

```text
BEGIN IMMEDIATE

SELECT business_operations
 WHERE action_code=? AND operation_key=?

if existing:
  fingerprint differs
    -> ROLLBACK / idempotency_conflict

  status=succeeded
    -> read stored result receipt
    -> COMMIT/close read path
    -> return original result without invoking service

  status=running/failed/manual_review
    -> apply explicit state policy; never blindly re-execute

if absent:
  INSERT business_operations(status='running', fingerprint, actor, target, correlation)
  -> invoke existing domain service using SAME conn
  -> existing stock/business rows mutate using SAME conn
  -> existing log_operation/audit evidence uses SAME conn
  -> serialize a bounded deterministic result receipt
  -> UPDATE business_operations SET status='succeeded', result..., completed_at=...
  -> COMMIT
  -> return result
```

`BEGIN IMMEDIATE` intentionally acquires SQLite write ownership before the first persistent operation row. This follows existing queue-claim precedent and prevents two same-key writers from both owning execution.

## Critical atomicity invariant

For `atomic_local` actions:

> `business_operations.succeeded`, the business/stock mutation and the corresponding authoritative audit evidence must commit together or roll back together.

Never:

```text
commit operation admission
then mutate inventory in another transaction
```

and never:

```text
mutate inventory
commit
then separately write idempotency success
```

Both create a crash window that can double-post on retry.

## Failure semantics

### Validation/scope/state failure before `BEGIN IMMEDIATE`

- no `business_operations` row required;
- no stock/business mutation;
- deterministic API/domain error returned.

### Exception after Class A transaction begins but before commit

- explicit rollback;
- operation row, business mutation and audit changes from that transaction all disappear together;
- there must be no false `succeeded` row.

For the first local pilots, do **not** force a durable `failed` row inside the same rolled-back transaction. If durable failure telemetry is desired, record it after rollback through a separate non-authoritative diagnostic path.

### Response loss after successful commit

This is the key replay case:

```text
first request commits business effect + succeeded receipt
 -> HTTP response is lost
 -> client retries same key/fingerprint
 -> existing succeeded operation is returned
 -> service is NOT invoked again
```

## Persistent `running` rows

For a pure Class A transaction, a process crash before commit normally rolls back the uncommitted `running` row together with business effects.

Therefore a visible persistent `running` row should be treated as unusual evidence, not casually retried.

Future Class B/durable workflows may intentionally persist running state across transactions; S05–S08 own lease/retry/reconciliation semantics for those cases.

## Result receipt

Store only enough deterministic result to answer a retry without re-running the mutation, for example:

```json
{
  "target_type": "transfer_order",
  "target_id": 123,
  "status": "completed",
  "receipt_event_id": 456
}
```

Rules:

- bounded JSON size;
- no secrets/tokens;
- no large attachments/raw documents;
- prefer IDs + stable status/quantity summary;
- public API adapter may reconstruct the current compatible response from this receipt.

## Pilot 1 recommendation

Start with `transfer.receive` because it has:

- explicit destination warehouse scope;
- clear stock-in consequence;
- existing transfer receipt event/audit evidence;
- obvious duplicate-receipt risk.

Then apply to:

```text
purchase.receive
shipment.complete
```

Run the full repository Release Gate after each pilot slice.

## Concurrency tests

### Same key, same fingerprint

Run two connections/threads against the same SQLite fixture:

```text
request A begins
request B starts concurrently with same key
```

Require:

- only one service invocation;
- exactly one stock delta/business transition;
- exactly one authoritative audit/receipt event;
- both callers resolve to the same final business result (or B receives deterministic in-progress semantics until replayed after A commits).

### Same key, different fingerprint

Require:

- second caller gets idempotency conflict;
- no second mutation;
- original succeeded result remains unchanged.

### Crash/rollback before commit

Inject failure after business DML but before operation success update/commit:

- DB transaction rolls back;
- no stock delta remains;
- no succeeded operation remains;
- retry can execute once normally.

### Lost response after commit

Commit, suppress first response, retry:

- service call count remains one;
- same stored receipt returned;
- stock/audit counts unchanged.

## Interaction with current request connection

The pilot action wrapper should receive the existing request-owned `conn`; it must not open a second business connection for the mutation.

Before issuing `BEGIN IMMEDIATE`, the pilot path must not have performed DML on that connection. Existing authentication/session resolution that uses other connection scopes remains separate.

Tests should assert the pilot wrapper either:

- begins from `conn.in_transaction == False`; or
- fails loudly if a caller tries to enter the atomic-local wrapper with an already-active write transaction.

Do not silently create nested transaction behavior.

## External side-effect boundary

A Class A idempotent transaction must not make an irreversible external network call while holding SQLite write ownership.

Instead:

```text
business mutation
+ outbox event
+ business operation success
COMMIT

later worker
 -> external provider call
 -> provider acknowledgement / retry / reconciliation
```

S08 owns this pattern.

## Data migration / rollout

Migration 2 is additive. On code rollback the table remains inert; do not destructively drop operation history.

Suggested rollout:

```text
Migration 2 + table tests
 -> no route uses it yet
 -> transfer.receive pilot
 -> Release Gate
 -> purchase.receive
 -> Release Gate
 -> shipment.complete
 -> Release Gate
```

## Acceptance

At least one consequential local write path is proven business-exactly-once under:

- duplicate click;
- deterministic client retry;
- concurrent same-key attempt;
- response loss after commit;
- injected failure before commit.

The proof must show the business mutation itself happens once, not merely that duplicate HTTP responses are suppressed.

## Dependencies

E01-S01, E01-S02 and E01-S03 design.

Runtime implementation remains blocked until:

```text
E00 real-checkout Release Gate = PASS
AND Inventory PR #3 reviewed/merged
```
