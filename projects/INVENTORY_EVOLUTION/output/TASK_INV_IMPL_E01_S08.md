# TASK_INV_IMPL_E01_S08 — Transactional Outbox

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Guarantee that business state and required external side-effect intent cannot diverge because a process crashes between DB commit and provider/API call.

## Migration ownership

**Proposed Migration 4**:

```text
outbox_events
  id INTEGER PK
  event_type TEXT NOT NULL
  aggregate_type TEXT NOT NULL
  aggregate_id INTEGER NOT NULL
  event_key TEXT
  payload_json TEXT NOT NULL
  correlation_id TEXT
  business_operation_id INTEGER
  status TEXT NOT NULL
  available_at TEXT NOT NULL
  attempt_count INTEGER NOT NULL DEFAULT 0
  delivered_at TEXT
  last_error TEXT
  created_at TEXT NOT NULL

UNIQUE(event_key) where an event type requires dedupe
```

Use application-enforced uniqueness if SQLite conditional uniqueness is not appropriate for all event types.

## Core invariant

For any business command that must later call an external system:

```text
BEGIN
  authoritative business mutation
  + outbox insert
COMMIT
```

If the business transaction rolls back, no outbox event may survive.

## Delivery

The E01 worker claims pending outbox delivery work through the generic durable-job framework or a thin outbox dispatcher sharing the same lease/retry primitives.

Provider success + local timeout must reconcile by provider/business identity before retry. Blindly repeating non-idempotent external calls is forbidden.

## Pilot event

Use a low-risk notification/report/integration event first. Platform inventory/order synchronization can adopt the outbox only after the primitive is proven.

## Tests

- business commit creates exactly one event;
- business rollback creates zero events;
- replayed business operation does not insert a duplicate event;
- delivery retry does not mutate business state again;
- crash after provider acknowledgement can reconcile without duplicate external effect;
- dead-letter retains payload/reference for manual recovery.

## Rollback

Migration 4 additive. Do not delete undelivered events during code rollback; pause dispatcher and reconcile explicitly.

## Acceptance

One pilot business transaction and its external side-effect intent are atomically coupled and recoverable after simulated process crash.

## Dependencies

E01-S04, E01-S05, E01-S06, E01-S07.
