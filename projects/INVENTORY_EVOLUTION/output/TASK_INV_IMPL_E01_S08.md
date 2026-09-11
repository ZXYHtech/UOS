# TASK_INV_IMPL_E01_S08 — Transactional Outbox

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Guarantee that authoritative business state and required external side-effect intent cannot diverge because a process crashes between DB commit and provider/API call.

The outbox is not a second event platform. It is a small durable boundary inside the same modular monolith/database.

## Current gap

The existing system already has platform/order sync status such as `orders.platform_sync_status`, but status fields alone cannot prove:

```text
business transaction committed
AND required provider action was durably recorded
AND a retry/reconciliation path exists
```

E01 adds that missing delivery intent/evidence layer before more aggressive omnichannel automation.

## Migration ownership

**Proposed Migration 4**:

```text
outbox_events
  id INTEGER PRIMARY KEY AUTOINCREMENT
  event_type TEXT NOT NULL
  aggregate_type TEXT NOT NULL
  aggregate_id INTEGER NOT NULL
  event_key TEXT
  destination_type TEXT
  destination_id INTEGER
  payload_json TEXT NOT NULL
  business_operation_id INTEGER
  correlation_id TEXT
  status TEXT NOT NULL DEFAULT 'pending'
  external_reference TEXT
  delivered_at TEXT
  last_error_code TEXT
  last_error TEXT
  created_at TEXT NOT NULL
  updated_at TEXT NOT NULL

CHECK(status IN ('pending','delivered','manual_review','dead_letter','cancelled'))
```

Indexes:

```text
UNIQUE(event_key) WHERE event_key IS NOT NULL
INDEX outbox_events(status, created_at, id)
INDEX outbox_events(aggregate_type, aggregate_id, id)
INDEX outbox_events(correlation_id)
INDEX outbox_events(business_operation_id)
```

Do not put lease/attempt counters into `outbox_events`; E01-S05 `jobs` owns execution attempts.

## Why Outbox and Job are separate

They answer different questions.

### `outbox_events`

Business evidence:

> “Because transaction X committed, external effect Y must eventually be reconciled/delivered.”

### `jobs`

Execution evidence:

> “Worker Z is currently attempting delivery, with lease generation N and retry policy P.”

Do not let job retry state become the business source of truth for whether an external effect is required.

## Core atomic invariant

For any business command that requires an external effect:

```text
BEGIN business transaction

  authoritative business mutation
  + business operation success state where applicable
  + operation/audit evidence
  + INSERT outbox_events(status='pending')
  + INSERT jobs(job_type='outbox.deliver', payload={outbox_event_id})

COMMIT
```

If that transaction rolls back:

```text
business mutation = absent
outbox event = absent
delivery job = absent
```

There must be no crash window between “event exists” and “worker has something durable to process.”

## Event key

`event_key` provides domain-level dedupe in addition to S04 command idempotency.

Example conceptual keys:

```text
order:<id>:shipment-confirmed:v1
material:<id>:channel-inventory-publication:<account-id>:<stock-version>
rma:<id>:refund-requested:<revision>
```

Rules:

- deterministic from the business event identity;
- not based on wall-clock randomness;
- include version/revision only when a new effect is genuinely intended;
- duplicate event key must not replace payload silently.

S04 replay normally avoids re-entering the service transaction at all, but `event_key` remains defense-in-depth for producers that do not originate from an HTTP business operation.

## Payload boundary

Outbox payload is an immutable delivery command/reference snapshot, not the entire business database row.

Prefer:

```json
{
  "platform_account_id": 12,
  "order_id": 345,
  "external_order_id": "...",
  "shipment_id": 678
}
```

Avoid:

- API secrets/session tokens;
- entire customer/order object dumps;
- large files/base64;
- mutable values the adapter should re-read authoritatively when appropriate.

Sensitive external credentials remain resolved at delivery time through the approved integration credential boundary.

## Delivery job contract

Job type:

```text
outbox.deliver
```

Payload:

```json
{"outbox_event_id":123}
```

The worker:

1. claims the durable job with S05 lease/fencing;
2. loads the outbox event;
3. if already `delivered`, completes job as idempotent no-op;
4. resolves destination adapter by code-owned registry;
5. performs provider-specific preflight/reconciliation where needed;
6. calls provider only when replay safety is known;
7. persists acknowledgement/outbox terminal state;
8. completes/retries/manual-reviews the job through S07.

## No network inside business transaction

Never:

```text
BEGIN SQLite write transaction
 -> call marketplace/payment/carrier HTTP API
 -> wait seconds
 -> commit
```

This would hold SQLite write ownership across network latency and still would not solve provider-ack ambiguity.

Correct pattern:

```text
business mutation + outbox + delivery job
COMMIT quickly

later worker
 -> external call
```

## Provider acknowledgement model

Adapter result should be typed, for example:

```text
DELIVERED
  external_reference / acknowledgement evidence

RETRYABLE_TECHNICAL
  definitely no confirmed effect; S07 may retry

RECONCILE_REQUIRED
  provider may have accepted effect; query by external/idempotency identity first

PERMANENT_INPUT
  dead-letter / correction required

MANUAL_REVIEW
  unsafe ambiguity
```

Do not infer these from free-text response messages.

## Provider success + local crash/timeout

This is the key Outbox problem.

Example:

```text
worker sends shipment acknowledgement
provider commits success
network response is lost / worker crashes
local outbox still pending
```

On next attempt the adapter must first use a stable provider identity when available:

```text
platform_account_id
+ external_order_id / provider operation ID / provider idempotency key
```

Then:

- if provider already reflects the intended effect -> mark outbox delivered without repeating it;
- if provider proves no effect -> safe retry;
- if state cannot be established -> manual_review, not blind repeat.

## Current platform boundary

Future marketplace integration should bind external identity at least to the account context, not global order number alone.

Preferred canonical identity shape from the audit:

```text
platform_account_id + external_order_id
```

Outbox adoption must not silently assume one external order ID is globally unique across all accounts/channels.

## Outbox status vs job status

Do not duplicate every execution state into Outbox.

Use:

```text
outbox.pending
  delivery still required; job may be queued/running/retry_wait

outbox.delivered
  external effect confirmed/reconciled

outbox.manual_review
  business-level external ambiguity requires intervention

outbox.dead_letter
  terminal delivery failure after policy exhaustion/correction required

outbox.cancelled
  domain explicitly cancelled the required effect before delivery where legal
```

Detailed attempts belong to `jobs/job_attempts`.

## First implementation proof

Stage 1 should use a deterministic fake/test adapter to prove atomicity and crash recovery without touching a real marketplace.

Then adopt one low-consequence real external effect if an appropriate provider is available, such as a notification/webhook-like integration.

Do **not** make marketplace inventory publication, refund or shipment acknowledgement the very first production proof.

## Deterministic tests

### Producer atomicity

- business commit -> exactly one outbox event + one `outbox.deliver` job;
- business rollback -> zero event/job;
- S04 replay -> no duplicate event/job;
- duplicate `event_key` with different payload rejected.

### Delivery

- successful provider acknowledgement -> outbox delivered + job succeeded;
- transient pre-call failure -> job retry_wait, outbox remains pending;
- already-delivered event -> delivery job no-op success;
- permanent input -> terminal state without business mutation replay.

### Crash ambiguity

Simulate:

```text
fake provider records success
 -> worker crashes before local delivered update
```

Next attempt must reconcile fake provider identity and mark delivered without invoking the external effect twice.

### Fencing

- old lease generation cannot mark outbox delivered after job reclaim;
- only current job generation can publish final acknowledgement.

## Rollback

Migration 4 is additive.

If code rollback occurs:

- pause outbox delivery worker/job type;
- retain pending/manual/dead-letter events;
- do not delete or mark them delivered merely to make rollback clean;
- reconcile explicitly before later re-enablement.

## Acceptance

One deterministic business transaction proves:

```text
business state + outbox intent + delivery job
```

commit atomically, and a simulated provider-success/local-crash scenario proves external reconciliation avoids duplicate effect.

## Dependencies

E01-S04, S05, S06 and S07.

Runtime implementation remains blocked until:

```text
E00 real-checkout Release Gate = PASS
AND Inventory PR #3 reviewed/merged
```
