# TASK_INV_IMPL_E01 — Core Modularization, Action Policy & Durable Jobs

## Status

`DESIGN_READY_IMPLEMENTATION_BLOCKED_BY_E00`

This file is a pre-implementation contract only. No E01 runtime code is considered implemented while E00 remains `IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`.

## 1. Objective

Prevent future features from adding bespoke permission checks, replay handling, retry loops and background threads directly into `server.py` / `services.py`.

E01 establishes four shared contracts:

```text
Action Policy
Business Operation / Idempotency
Durable Job + Attempt / Lease
Transactional Outbox + Correlation
```

The target remains a modular monolith; these are internal platform primitives, not microservices or a general event-bus project.

## 2. Reuse existing proven patterns

Do not replace working concepts unnecessarily.

Reuse / generalize:

- backend `require_perm` / warehouse-scope helpers;
- `operation_logs` as business audit evidence;
- OCR queue's database-backed claim isolation and process separation;
- image derivative durable job state;
- current service-layer state validation;
- systemd-owned worker/process supervision;
- E00 numbered migration + local `verify_release` gate.

Do not require:

- Redis;
- Kafka/RabbitMQ;
- Celery/RQ;
- Kubernetes;
- GitHub Actions scheduler.

## 3. E01-S01 — common API/domain primitives

Create small shared modules rather than another giant utility file.

Suggested ownership:

```text
inventory_app/platform/
  errors.py
  request_context.py
  action_policy.py
  idempotency.py
  jobs.py
  outbox.py
  correlation.py
```

`request_context` should carry only stable execution context such as:

- actor/user ID;
- permissions/role-derived access;
- warehouse scope;
- correlation ID;
- request/source metadata.

It must not silently infer business state from client-supplied IDs.

## 4. E01-S02/S03 — Action Policy registry

### 4.1 Required metadata

Every consequential action should declare:

```text
action_code
  auth_required
  required_permission(s)
  scope_resolver
  allowed_state/precondition resolver
  idempotency class
  audit class
```

Example conceptual declaration:

```python
ActionPolicy(
    code="transfer.receive",
    permission="transfer.process",
    scope="transfer_destination_warehouse",
    transition="transfer.can_receive",
    idempotency="required",
    audit="ledger_or_operation_log",
)
```

### 4.2 Execution order

```text
resolve authenticated actor
 -> load authoritative target object
 -> permission check
 -> object/warehouse scope check
 -> state/precondition check
 -> idempotency admission
 -> domain service transaction
 -> audit/ledger evidence
 -> response receipt
```

Client-supplied warehouse/owner fields never replace scope derived from the loaded object.

### 4.3 Pilot routes

Migrate a deliberately small representative set first:

1. transfer receive or partial receive — warehouse scope + replay risk;
2. purchase receipt — stock mutation + replay risk;
3. shipment completion/reversal — state + stock mutation + audit.

Do not convert every endpoint in one change.

## 5. E01-S04 — Business Operation / Idempotency

### 5.1 Suggested table

```text
business_operations
  id
  operation_key          UNIQUE
  action_code
  actor_id
  request_fingerprint
  correlation_id
  status                 running|succeeded|failed|manual_review
  result_type
  result_id
  result_json             bounded/safe replay receipt only
  error_code
  started_at
  completed_at
```

### 5.2 Required semantics

Same `(action_code, operation_key)` + same canonical request fingerprint:

- if already succeeded: return/reconstruct the original receipt;
- if currently running: return deterministic in-progress/conflict semantics;
- if prior retryable technical failure: allow controlled retry policy;
- never execute the stock/business side effect twice.

Same key + different request fingerprint:

- reject as an idempotency-key conflict;
- never reinterpret the old key for a new request.

The operation record and consequential business mutation should be committed atomically where practical.

### 5.3 Key sources

Preferred order:

1. provider/business event ID where provider guarantees uniqueness;
2. explicit client-generated idempotency key;
3. server-generated operation key returned before/reused by controlled client flow.

UI button disabling is never treated as idempotency.

## 6. E01-S05/S06/S07 — generic durable jobs

### 6.1 Suggested tables

```text
jobs
  id
  job_type
  payload_json
  status                queued|running|retry_wait|succeeded|dead_letter|cancelled
  priority
  available_at
  lease_owner
  lease_until
  lease_generation
  attempt_count
  max_attempts
  idempotency_key
  correlation_id
  created_at
  updated_at

job_attempts
  id
  job_id
  attempt_no
  lease_generation
  worker_id
  started_at
  finished_at
  outcome
  error_class
  error_message
```

### 6.2 Claim contract for SQLite

Use a short transaction, compatible with the existing OCR precedent:

```text
BEGIN IMMEDIATE
 -> select one eligible queued/retry_wait job
 -> ensure lease absent/expired
 -> increment lease_generation
 -> set running + lease owner/expiry + attempt count
COMMIT
```

The expensive job executes outside the write transaction.

Completion/update must include the claimed `lease_generation`; a stale worker whose lease was reclaimed is fenced from committing completion for a newer generation.

### 6.3 Retry classes

Do not retry every exception blindly.

```text
RETRYABLE_TECHNICAL
  network timeout, provider 5xx, temporary rate limit

PERMANENT_INPUT
  invalid mapping, malformed required data

MANUAL_REVIEW
  ambiguous business mapping / unsafe replay state
```

Retry policy stores `available_at`, bounded attempts and final dead-letter/manual-review state.

### 6.4 Worker entry point

Suggested server-owned CLI:

```bash
python3 -m inventory_app.worker --once
python3 -m inventory_app.worker --loop
```

or an equivalent repository-local command.

Supervision target:

```text
inventory-worker.service
```

No GitHub scheduler/supervisor.

## 7. E01-S08 — Transactional Outbox

### 7.1 Suggested table

```text
outbox_events
  id
  event_type
  aggregate_type
  aggregate_id
  event_key             UNIQUE where dedupe is required
  payload_json
  correlation_id
  business_operation_id
  status                pending|delivering|delivered|retry_wait|dead_letter
  available_at
  attempt_count
  created_at
  delivered_at
```

### 7.2 Core invariant

For business flows that must trigger an external side effect:

```text
same DB transaction:
  update authoritative business state
  + insert outbox event
COMMIT

worker later:
  deliver externally
  -> record acknowledgement / retry / reconciliation
```

A rolled-back business transaction must leave no outbox event.

External provider success followed by local timeout must be reconciled by provider/external-object identity, not blindly repeated.

## 8. E01-S09 — Correlation IDs

One correlation ID should connect:

```text
HTTP request
 -> action execution
 -> business_operation
 -> operation log / stock ledger later
 -> job
 -> outbox event
 -> provider request/acknowledgement
```

Rules:

- accept a valid inbound correlation ID or generate one;
- never use correlation ID as authorization;
- log it structurally, not only in free-text messages;
- propagate it through job/outbox payload metadata;
- expose it in error/operation receipts for support diagnostics.

## 9. E01-S10 — first module extraction

Do not begin with the highest-risk inventory domain.

Recommended extraction order:

1. `backup/recovery` — E00 has already created clean module seams;
2. `pricing` — mature concepts and relatively bounded data ownership;
3. `procurement` service façade;
4. `integrations` adapters.

Each module should own:

```text
models/schema migrations
service/domain commands
API adapter/routes
permission/action declarations
tests
```

The central HTTP handler should parse/route and delegate, not acquire new business logic.

## 10. Required local tests before E01 can complete

### Action-policy matrix

For each pilot action:

- unauthenticated denied;
- wrong permission denied;
- permission but wrong warehouse/object scope denied;
- invalid business state denied;
- correct actor/scope/state allowed;
- exactly one audit/ledger receipt.

### Idempotency

- same key + same request posts side effect once;
- replay returns same business result/receipt;
- same key + different request rejected;
- timeout/retry cannot double-post stock.

### Job claim / lease

- two workers cannot own the same generation;
- expired lease can be reclaimed;
- old worker is fenced by generation;
- restart leaves queued/retry work recoverable;
- permanent errors do not loop forever;
- dead-letter/manual-review is inspectable.

### Outbox atomicity

- business commit creates exactly one outbox event;
- business rollback creates none;
- delivery retry does not create a second business event;
- external acknowledgement can be reconciled after process crash.

### Correlation

- same correlation ID appears across action/business operation/job/outbox evidence.

All tests belong in the same repository-local release gate introduced by E00.

## 11. Rollout sequence

```text
E00 PASS + PR #3 merged
 -> add E01 infrastructure migrations only
 -> add tests for infrastructure
 -> pilot one low-risk job
 -> pilot one replay-sensitive action
 -> pilot transactional outbox
 -> move 2–3 additional representative paths
 -> only then broaden adoption
```

Do not convert the whole application in one PR.

## 12. Explicit non-goals

E01 does not yet implement:

- Stock Position / Reservation (E02);
- MRP;
- manufacturing/quality;
- arbitrary workflow designer;
- distributed service bus;
- third-party plugin marketplace;
- Redis/Kafka requirement;
- autonomous AI action execution.

## 13. Operator decisions to settle during E01 pilot

1. default retry classes/max-attempt policy by job type;
2. dead-letter/manual-review owner/UX;
3. worker process count on current server;
4. correlation-ID exposure in support UI/log exports;
5. retention policy for completed jobs/attempts/outbox delivery history.

None of these should be guessed in schema defaults if they materially affect operations.

## 14. Entry gate

Implementation of this design may begin only after:

```text
E00 tools/verify_release.py = PASS
AND Inventory PR #3 reviewed/merged
```

Until then this document remains design evidence only.
