# E01 Implementation Sequence — Small PR / Gate Strategy

## Status

`READY_AFTER_E00_GATE`

This sequence turns E01-S01…S10 into small independently verifiable implementation slices. It intentionally does not follow story number order when risk/dependency suggests a safer code order.

## Entry condition

Do not create/merge E01 runtime implementation until:

```text
Inventory E00 branch Release Gate = PASS
AND Inventory PR #3 reviewed/merged to main
```

Then branch from the new `main`, never from the old `78d5cda...` baseline.

## Slice A — Platform Context + Action Policy

Suggested branch:

```text
impl/e01-platform-policy
```

Scope:

- E01-S01 shared errors/request context/responses;
- E01-S02 action policy metadata/executor;
- no production write-route migration yet;
- no schema migration.

Gate:

- new action-policy unit matrix;
- existing auth/security/core tests;
- full `tools/verify_release.py`.

Rollback: pure code.

## Slice B — Idempotency Infrastructure

Suggested branch:

```text
impl/e01-idempotency
```

Scope:

- Migration 2: `business_operations`;
- E01-S04 operation-key/fingerprint/admission/result utility;
- test with an isolated synthetic/low-risk command before binding stock mutations.

Critical tests:

- same key/same request executes once;
- same key/different request conflicts;
- response-loss retry returns original receipt;
- concurrent same-key ownership is exclusive;
- rollback cannot leave false success.

Rollback:

- application code can stop using the table;
- do not drop production operation evidence.

## Slice C — Pilot Consequential Actions

Suggested branch:

```text
impl/e01-action-pilots
```

Scope:

- E01-S03;
- route one transfer receive/partial receive path through Action Policy + Idempotency;
- then purchase receipt;
- then shipment complete/reversal only after the preceding pilot passes.

Do not change E02 stock semantics here.

Gate after **each** pilot:

- permission/scope/state matrix;
- replay test;
- existing workflow parity;
- full Release Gate.

If one pilot uncovers incompatible legacy semantics, stop the slice and record it rather than broadening the rewrite.

## Slice D — Durable Jobs + Worker + Retry

Suggested branch:

```text
impl/e01-durable-jobs
```

Scope:

- Migration 3: `jobs`, `job_attempts`;
- E01-S05 job claim/lease/generation fencing;
- E01-S06 worker CLI/service;
- E01-S07 retry/dead-letter/manual-review policy;
- first adopter is non-stock-mutating.

Critical concurrency tests:

- two claimers cannot own the same generation;
- expired lease can be reclaimed;
- stale worker cannot complete after reclaim;
- worker restart preserves recoverability;
- retryable vs permanent vs manual-review classifications behave differently.

Deployment:

- local CLI first;
- systemd worker only after CLI fixture is stable;
- no GitHub scheduler.

## Slice E — Transactional Outbox + Correlation

Suggested branch:

```text
impl/e01-outbox-correlation
```

Scope:

- Migration 4: `outbox_events`;
- Migration 5: `operation_logs.correlation_id`;
- E01-S08 transactional outbox;
- E01-S09 correlation propagation;
- one low-risk external-delivery pilot.

Critical tests:

- business commit iff outbox event exists;
- rollback leaves no event;
- replay creates no duplicate event;
- provider-success/local-timeout path reconciles before retry;
- one correlation ID can query request/action/operation/job/outbox evidence.

## Slice F — Bounded Modular-monolith Extraction

Suggested branch family:

```text
impl/e01-domain-backup
impl/e01-domain-pricing
impl/e01-domain-procurement
impl/e01-domain-integrations
```

Do not combine all extraction waves into one large PR.

### F1 — backup/recovery

Move existing E00 seams behind `domains/backup/` with compatibility re-exports only. No semantic change.

### F2 — pricing

Move `PricingService` and pure formula helpers behind `domains/pricing/` **with exact current behavior preserved**.

This is an important bridge to E11-S01/S02: do not fix `margin_percent` while moving the code.

### F3 — procurement

Move `ProcurementService` behind a domain façade while preserving caller-owned SQLite transaction boundaries.

### F4 — integrations

Move provider/order adapters, `TaobaoApiClient`, account service and future job/outbox handlers after S05–S09 primitives exist.

Do not move Inventory/Stock yet; E02 defines its future semantic boundary.

Gate after each extraction:

- no duplicate implementation left in old file;
- import/startup smoke;
- existing API contract unchanged;
- full Release Gate.

## Why S04 precedes S03 in runtime implementation

The catalog numbers describe feature stories, not mandatory merge order. It is safer to prove the idempotency primitive on an isolated command before routing stock-affecting production actions through the new execution wrapper.

Therefore E01 implementation order is intentionally:

```text
S01/S02
 -> S04
 -> S03
 -> S05/S06/S07
 -> S08/S09
 -> S10 extraction waves
```

## Migration contract

```text
1  baseline_current_schema_20260810         [E00]
2  business_operations                     [E01-S04]
3  jobs + job_attempts                     [E01-S05]
4  outbox_events                           [E01-S08]
5  operation_logs.correlation_id           [E01-S09]
```

Each numbered migration must be immutable, contiguous, checksum-verified and pass E00 pre/post integrity semantics.

## Merge rule for every E01 slice

```text
branch based on current main
 -> deterministic new tests PASS
 -> existing regression suites PASS
 -> tools/verify_release.py PASS
 -> PR review clean
 -> merge
 -> next slice rebases/branches from new main
```

Do not stack all E01 work on an unmerged long-lived branch unless there is a temporary review reason; doing so would recreate the large-change risk E00 was designed to prevent.

# Post-E01 bridge — E11-S01/S02 before E02

The project master plan explicitly places pricing/commercial safety before the Stock Position/Reservation rewrite.

After E01 completes and pricing has a bounded domain boundary:

```text
E11-S01 Pricing Formula Semantics & Legacy Rule Safety
 -> E11-S02 Floor Price / Deal-price Override Safety
 -> only then E02 Stock Position / Movement / Reservation Kernel
```

Why this bridge exists:

1. pricing formula semantics are high-impact but relatively isolated;
2. the current `margin_percent` label is commercially misleading;
3. fixing it before broader inventory/manufacturing changes prevents unsafe pricing automation from spreading;
4. E11-S01/S02 can be validated without waiting for manufacturing actual-cost truth;
5. realized order profitability remains deferred until later E11 stories after manufacturing/economics dependencies exist.

## E11 bridge gate

Before E02 starts:

```text
E01 complete and merged
AND E11-S01 legacy pricing parity + new margin formula tests PASS
AND E11-S02 below-floor enforcement tests PASS
AND full Release Gate PASS
AND no unresolved pricing migration/rollback blocker
```

Do **not** interpret this as permission to build full order economics early. The bridge is only formula terminology + commercial floor safety.

## E02 entry rule

E02 begins from the then-current `main` only after the above bridge passes.

E02 must reuse E01 primitives rather than inventing alternatives:

```text
Action Policy
Business Operations / Idempotency
Correlation IDs
Durable Jobs / Outbox when external side effects exist
Versioned migrations / Release Gate
```

The Stock kernel must not embed a second authorization/idempotency/job framework.