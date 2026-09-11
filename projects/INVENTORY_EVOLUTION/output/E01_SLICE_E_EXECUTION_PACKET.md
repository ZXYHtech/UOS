# E01 Slice E Execution Packet — Transactional Outbox + Persistent Correlation

## Status

`READY_TO_START_ONLY_AFTER_E01_SLICE_D_MERGE`

This slice proves durable external-delivery semantics without prematurely redesigning omnichannel business logic.

## 1. Entry gate

Required:

```text
E00 merged
E01 Slice A/B/C/D merged
Migration 2 business_operations active
Migration 3 jobs/job_attempts active
generic worker lease/fencing/retry tests PASS
full Release Gate PASS
```

Suggested branch:

```text
impl/e01-outbox-correlation
```

## 2. Purpose

Solve the crash window:

```text
local business transaction commits
 -> process crashes before external request is queued
```

and the opposite ambiguity:

```text
external provider may have accepted request
 -> local process times out before recording acknowledgement
```

without holding a SQLite transaction open during network I/O.

## 3. Core architecture

For a business action requiring later external delivery:

```text
BEGIN IMMEDIATE / ordinary domain transaction
 -> mutate authoritative local business state
 -> write authoritative audit/business evidence
 -> insert outbox_event
 -> enqueue matching outbox.deliver job
 -> mark local business operation succeeded if applicable
COMMIT

worker later:
 -> claim outbox.deliver job
 -> load outbox event
 -> provider delivery
 -> record acknowledgement / retry / reconciliation
```

Critical invariant:

> if the local business transaction rolls back, neither the outbox event nor its delivery job may survive.

## 4. Migration 4 — `outbox_events`

Migration sequence:

```text
1 baseline
2 business_operations
3 jobs + job_attempts
4 outbox_events
```

Suggested schema:

```text
id INTEGER PRIMARY KEY AUTOINCREMENT
event_type TEXT NOT NULL
aggregate_type TEXT NOT NULL
aggregate_id INTEGER
business_operation_id INTEGER
event_key TEXT
payload_json TEXT NOT NULL
correlation_id TEXT
status TEXT NOT NULL
available_at TEXT NOT NULL
attempt_count INTEGER NOT NULL DEFAULT 0
last_error_class TEXT
last_error_message TEXT
provider_ack_type TEXT
provider_ack_id TEXT
provider_ack_json TEXT
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
delivered_at TEXT
```

Statuses:

```text
pending
delivering
delivered
retry_wait
manual_review
dead_letter
cancelled
```

Recommended uniqueness when dedupe is meaningful:

```text
UNIQUE(event_type, event_key)
```

Do not require an event key for every event if the domain has no natural dedupe identity; explicit code contract should decide.

Indexes:

```text
(status, available_at, id)
(aggregate_type, aggregate_id, id DESC)
(correlation_id)
(business_operation_id)
(provider_ack_type, provider_ack_id)
```

## 5. Migration 5 — persistent correlation in `operation_logs`

Existing `operation_logs` already stores:

```text
user_id
action_type
target_type
target_id
before_json
after_json
ip
device
created_at
```

Migration 5 adds:

```text
correlation_id TEXT
```

plus an index suitable for support tracing.

Do not replace the existing audit table or rewrite historical rows. Old rows legitimately have `NULL correlation_id`.

Migration sequence remains:

```text
1 baseline
2 business_operations
3 jobs/job_attempts
4 outbox_events
5 operation_logs.correlation_id
```

## 6. Correlation contract

One bounded correlation ID should link, where applicable:

```text
HTTP request / RequestContext
 -> Action Policy
 -> business_operations
 -> operation_logs
 -> outbox_events
 -> jobs
 -> job_attempts
 -> provider acknowledgement
```

Rules:

- valid inbound ID may be accepted;
- otherwise generate server-side;
- never use as permission, warehouse scope or idempotency key;
- preserve across retries/worker hops;
- expose in support/error receipt where useful;
- no secrets or unbounded user content.

## 7. Outbox API

Suggested module:

```text
inventory_app/platform/outbox.py
```

Bounded public surface:

```text
append_outbox_event(conn, ...)
append_outbox_event_with_job(conn, ...)
load_outbox_event(conn, event_id)
mark_delivery_started(... generation-aware ...)
mark_delivery_succeeded(... provider ack ...)
mark_delivery_retry(...)
mark_delivery_manual_review(...)
```

The domain service/event producer must not perform network I/O.

## 8. Job integration

Each deliverable event gets one durable job such as:

```text
job_type = outbox.deliver
idempotency_key = outbox_event:<event_id>
correlation_id = event.correlation_id
payload = {"outbox_event_id": event_id}
```

Why both tables exist:

```text
outbox_events = business fact: an external side effect is owed
jobs          = operational fact: a worker is attempting delivery
```

Do not collapse them into one overloaded status table.

## 9. First delivery adopter

Use a low-risk delivery implementation whose failure cannot corrupt stock/payment/order truth.

Preferred first proof:

```text
test/dev fake provider handler
```

Optional later low-risk production pilot only if already operationally safe:

```text
notification delivery
```

Do **not** use as first adopter:

```text
Taobao stock publication
shipment confirmation
refund/payment
purchase order creation
customer financial transaction
```

Those belong to later domain waves after the substrate is proven.

## 10. Provider acknowledgement model

A successful provider call should record bounded evidence:

```text
provider_ack_type
provider_ack_id
provider_ack_json (bounded, secret-free)
delivered_at
```

Do not treat HTTP 200 alone as universal semantic success; each provider adapter later defines its success acknowledgement contract.

## 11. Timeout ambiguity / reconciliation

Most important rule:

> if a request may have reached the provider but the local process did not receive/record the acknowledgement, do not blindly repeat an irreversible call.

Such error classification becomes:

```text
manual_review / reconcile-before-retry
```

A future provider adapter may implement:

```text
lookup by external event/idempotency/business identity
 -> already accepted -> record ack locally
 -> definitely absent -> safe retry
 -> ambiguous -> manual review
```

This pattern is mandatory for high-consequence external actions.

## 12. Atomic enqueue test

Inject failure scenarios proving:

### Local rollback

```text
insert business row
insert outbox event
insert delivery job
raise before commit
```

Require:

- business row rolled back;
- outbox event absent;
- job absent.

### Successful local commit

Require:

- business row present;
- exactly one outbox event;
- exactly one delivery job;
- all share expected correlation/business identity.

### Duplicate business replay

Same business-operation replay:

- no second outbox event;
- no second delivery job;
- original local receipt returned.

## 13. Delivery fencing

Outbox delivery execution must inherit Slice D worker fencing.

A stale worker cannot mark an outbox event delivered after its job lease generation has been superseded.

Recommended flow:

```text
job claim owns generation N
 -> mark event delivering with expected job/generation evidence
 -> provider call
 -> terminal update checks current job ownership/generation
```

Exact schema linkage may stay minimal, but tests must prove stale completion cannot overwrite newer delivery/reconciliation state.

## 14. Correlation migration of existing audit call

Update `database.log_operation(...)` compatibly so callers may pass optional `correlation_id`.

Rules:

- existing callers without value still work;
- no mass edit of every historical route in this PR;
- Action Policy/pilot routes can propagate RequestContext correlation;
- future domains adopt progressively.

Do not make existing tests fail solely because old helper call signatures omit correlation.

## 15. Query/support helpers

Add bounded read helpers enabling support to answer:

```text
what happened for correlation X?
which business operation produced this external event?
which job attempts tried to deliver it?
what provider acknowledgement exists?
why is it retry_wait/manual_review/dead_letter?
```

No large dashboard is required in E01; deterministic query/test helpers are sufficient.

## 16. Required tests

### Transactional outbox

- commit iff event+job exist;
- rollback leaves neither;
- duplicate local replay creates neither duplicate;
- event/job use same correlation ID.

### Worker delivery

- one provider call under normal success;
- retryable technical failure schedules retry;
- permanent input becomes terminal;
- ambiguous acceptance becomes manual_review/reconciliation;
- stale worker cannot mark delivery terminal.

### Correlation

Prove one correlation ID can be found in:

```text
business_operations
operation_logs
outbox_events
jobs
job_attempts
```

where those records exist.

### Backward compatibility

- old `log_operation(...)` callers still pass;
- existing operation-log API/export remains compatible;
- old rows with null correlation render safely.

## 17. Release Gate additions

Required deterministic tests should be fail-closed in `tools/verify_release.py`, for example:

```text
tools/test_outbox.py
tools/test_correlation_trace.py
```

Full:

```bash
python3 tools/verify_release.py
```

## 18. Explicit non-goals

Not in Slice E:

- redesign Taobao/PDD/website connector semantics;
- publish central ATP to channels;
- external-object ledger;
- refund/reconciliation business rules;
- generic event bus/Kafka;
- microservices;
- exactly-once network delivery claim.

The actual guarantee is:

```text
exactly-once local event creation
+ at-least-once controlled delivery attempt
+ provider-specific dedupe/reconciliation for external uncertainty
```

Do not market this as magical exactly-once networking.

## 19. PR review checklist

```text
[ ] Migration 4/5 contiguous and immutable
[ ] outbox + job inserted in same local transaction
[ ] network never occurs inside local business transaction
[ ] local rollback leaves no orphan event/job
[ ] duplicate business replay produces no duplicate event/job
[ ] stale worker fenced
[ ] ambiguous provider timeout not blind-retried
[ ] old log_operation callers remain compatible
[ ] correlation is trace metadata, not auth/idempotency
[ ] no omnichannel rewrite mixed into PR
[ ] full Release Gate PASS
```

## 20. Rollback

Application rollback:

- stop creating new outbox events;
- stop `outbox.deliver` handler/worker processing if feature reverted;
- retain outbox/job/audit evidence;
- explicitly disposition pending owed external effects before disabling a production producer.

Do not drop outbox history during rollback.

## 21. Exit / unlock

Slice E completes when transactional outbox, delivery worker and correlation trace are proven.

Then unlock:

```text
E01 Slice F — bounded module extraction
```

and later domain waves may reuse the substrate rather than creating ad-hoc background retry loops.
