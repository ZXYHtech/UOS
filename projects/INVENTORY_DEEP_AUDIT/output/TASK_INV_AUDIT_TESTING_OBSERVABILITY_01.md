# TASK_INV_AUDIT_TESTING_OBSERVABILITY_01 — Automated Testing, Migrations, Logging and Observability Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed repository-local test tools, source architecture/data model, deployment patterns, operation logs, OCR stress tests and searches for conventional structured logging/metrics instrumentation.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite already has **meaningful local regression assets**. The repository is not an untested prototype. Evidence includes substantial `test_core_workflows.py`, auth-security tests, client-routing tests, recognition workflow/sample tests and OCR/image stress tests.

The next maturity step is to turn those tests into a **governed contract suite organized by business invariants**, then add migration fixtures, deterministic concurrency tests and production observability.

Repository search did not identify a conventional `logging.getLogger` pattern or Prometheus/trace instrumentation, so technical observability appears materially less developed than business `operation_logs`.

Preliminary maturity:

- local regression test existence: 3.5–4/5
- core workflow coverage: 3.5/5
- security regression baseline: 3/5
- stress testing in OCR/image area: 3.5/5
- state-machine contract organization: 2/5
- migration compatibility testing: 1.5/5
- concurrency/idempotency testing: 1.5–2/5
- structured application logs: 1.5/5
- metrics/traces/alerts: 1/5

## 2. Existing test assets worth preserving

Observed tools include at least:

- `tools/test_core_workflows.py`;
- `tools/test_auth_security.py`;
- `tools/test_client_routing.js`;
- `tools/test_image_derivative_stress.py`;
- `tools/test_ocr_stress_100_items.py`;
- `tools/test_recognition_samples.py`;
- `tools/test_recognition_workflows.py`;
- OCR evaluation tooling;
- local start/admin recovery tooling.

The size of the core workflow test indicates the project has accumulated substantial scenario coverage. Do not discard it during refactoring; use it as characterization coverage.

## 3. Reorganize around business contracts

As domains expand, tests should answer invariant questions rather than mirror file structure.

Recommended suite families:

```text
tests/
  contract/
    inventory/
    orders/
    fulfilment/
    transfer/
    procurement/
    pricing/
    integrations/
    manufacturing/
    quality/
    rma/
  security/
  migrations/
  concurrency/
  performance/
  client/
  recovery/
```

The current scripts can be migrated gradually; do not stop supporting direct CLI invocation.

## 4. Stock-kernel contract tests

Highest priority because many later domains depend on it.

Required cases:

- no negative nettable/physical balance according to policy;
- one logical stock identity cannot duplicate because of nullable scope;
- multi-bin quantity reconciliation once redesigned;
- reservation reduces ATP but not physical on-hand;
- releasing reservation restores ATP;
- quarantine excluded from nettable stock;
- transfer in-transit ownership reconciles;
- reversal creates compensating movement, not destructive history;
- concurrent consumers cannot oversubscribe;
- repeated idempotency key applies exactly once.

## 5. State-machine tests

For each aggregate define an explicit transition matrix.

Examples:

- purchase order;
- shipment task;
- transfer;
- work order;
- NCR;
- RMA;
- quotation;
- service case;
- settlement batch;
- controlled document revision.

Generate positive/negative tests from the transition contract:

```text
state A + command X -> state B
state C + command X -> rejected
```

Permission and state should be tested independently.

## 6. Permission/scope matrix

Build on existing auth-security tests.

For every sensitive command test:

- unauthenticated;
- authenticated without permission;
- permission but wrong warehouse/account;
- explicit deny override;
- allowed actor/scope;
- invalid state;
- idempotent replay;
- audit record.

This suite becomes especially important as `server.py` is modularized.

## 7. Migration tests

Current schema evolution is concentrated in `database.py` with a substantially stale PostgreSQL schema. Add immutable migration fixtures.

Maintain representative previous DB snapshots containing **synthetic/non-sensitive** data.

For each supported upgrade path:

```text
old fixture
 -> run migrations
 -> schema checksum/version
 -> orphan/integrity checks
 -> business invariant tests
 -> application smoke
```

Also test a fresh empty database reaches exactly the same final schema contract.

## 8. SQLite/PostgreSQL parity suite

Do not claim PostgreSQL support from DDL existence.

Eventually run the same domain contract tests against both backends:

- uniqueness/null semantics;
- transactions;
- decimal/date behavior;
- insert/upsert semantics;
- concurrency;
- migration results.

This should be locally executable using a developer/server PostgreSQL instance or disposable local container if the project accepts containers. GitHub Actions is not required.

## 9. Concurrency tests

Deterministic rather than random stress first.

Examples:

```text
Barrier: two threads both attempt to consume last 5 units
Expected: one succeeds according to policy; invariant holds
```

Test:

- shipment vs shipment;
- shipment vs transfer;
- PO receive duplicate;
- transfer partial receive duplicate;
- stock count vs adjustment;
- platform event replay;
- work-order issue later;
- refund/return disposition later.

Record DB lock errors separately from invariant failures.

## 10. Failure-injection tests

High-value reliability scenarios:

- exception after stock movement but before response;
- process killed after local commit before remote sync;
- worker killed after claiming job;
- network timeout during platform call;
- disk/file write fails after metadata insert;
- restore from corrupt backup;
- missing attachment referenced by DB;
- stale/expired job lease.

Business correctness should be proved under partial failure, not only happy path.

## 11. Import/export tests

Every import type should verify:

- malformed rows;
- duplicate within file;
- duplicate against database;
- preview does not mutate;
- confirm uses canonical service;
- partial failure policy;
- file replay/idempotency;
- unknown material/location/warehouse;
- decimal/UOM behavior;
- rollback/reversal where supported.

## 12. Client tests

Existing JS routing tests are useful. Expand incrementally around contracts:

- route/menu permission visibility;
- stale request protection;
- safe rendering/XSS payloads;
- pagination cursor behavior;
- form validation;
- network failure state;
- scan workflow state machine;
- offline conflict UI later.

Do not require a heavy browser stack for every test. Pure JS tests plus targeted browser/device scenarios can coexist.

## 13. Performance tests

Create synthetic datasets and benchmark:

- material/global search;
- inventory by warehouse/location;
- order/ship/transfer lists;
- ledger/history;
- dashboard aggregates;
- platform event import;
- test-result history;
- product analytics.

Use 5k/50k/500k scale tiers relevant to future target size.

Measure p50/p95/p99 and memory, not only “completed successfully”.

## 14. Business audit logs versus technical logs

`operation_logs` answer business questions:

```text
who changed what, before/after, when
```

Technical logs answer different questions:

```text
why did request/job fail, which request/job/trace, latency, dependency error
```

Keep them separate but correlate them.

Do not fill immutable business audit logs with noisy debug output.

## 15. Structured application logging

Introduce a standard logger with JSON or consistently parseable records.

Recommended fields:

```text
timestamp
level
service/process
request_id
user_id (when safe)
route/action
object_type/id
job_id/attempt
platform_account_id
error_code
latency_ms
message
```

Never log:

- passwords;
- raw session tokens;
- API secrets;
- unnecessary customer PII;
- whole OCR/platform payloads by default.

## 16. Request correlation

Generate a request ID at HTTP ingress and propagate it through:

- application logs;
- error responses;
- operation/audit metadata where useful;
- outbox/job creation;
- worker logs.

Then a user report such as “shipment failed” can be traced across request, DB event and background sync.

## 17. Metrics

Start small with operationally useful counters/gauges/histograms:

### HTTP

- requests by route/status;
- latency;
- unhandled errors;
- active requests.

### Database

- transaction latency;
- lock/busy errors;
- DB size/WAL size;
- connection/operation failures.

### Jobs

- queued/running/retry/dead-letter;
- oldest queue age;
- processing duration;
- attempts;
- worker heartbeat.

### Integrations

- sync lag;
- success/failure/retry;
- rate-limit errors;
- reconciliation mismatches.

### Backup

- last successful/verified backup age;
- restore-drill result.

### Business operational

- stuck shipment/PO/RMA/work-order count.

## 18. Metrics implementation

Do not require Prometheus immediately. Options:

- lightweight `/metrics` endpoint;
- application health JSON endpoint;
- DB-backed operational metrics table;
- structured logs consumed by server-local/external monitor.

Prometheus/OpenTelemetry can be adopted later if operational environment benefits.

The first requirement is that metrics exist and are inspectable independently of GitHub.

## 19. Health versus readiness

Provide distinct concepts:

- liveness: process responds;
- readiness: can execute core DB operations;
- dependency status: platform/OCR/AI may be degraded without making core app unready;
- worker health: heartbeat + backlog age.

Do not mark whole inventory service down because Taobao API is unavailable.

## 20. Error taxonomy

Replace ad-hoc human strings as the only machine signal with stable error codes where automation needs them.

Examples:

```text
AUTH_REQUIRED
PERMISSION_DENIED
WAREHOUSE_SCOPE_DENIED
INVALID_STATE
INSUFFICIENT_STOCK
IDEMPOTENCY_CONFLICT
EXTERNAL_RETRYABLE
EXTERNAL_PERMANENT
VALIDATION_ERROR
```

Human-readable Chinese message remains useful, but clients/tests/metrics should not parse text to determine behavior.

## 21. Alerts

Alert on actionable conditions, not every exception log.

Initial alerts:

- service unavailable;
- sustained DB lock errors;
- disk critical;
- backup stale/unverified;
- worker heartbeat missing;
- queue oldest-age over policy;
- integration dead-letter backlog;
- repeated unhandled server error;
- security login anomaly if justified.

Business todos such as one stock shortage belong in the app exception queue, not necessarily pager-style infrastructure alerting.

## 22. Release gate

Define one repository-local command such as:

```text
python3 tools/run_release_checks.py
```

which orchestrates required fast suites:

- syntax/import;
- DB fresh/migration fixture;
- core contracts;
- auth/permissions;
- client routing/safe rendering;
- backup smoke;
- selected concurrency/idempotency.

Long stress/recovery tests can be separate but documented.

GitHub Actions may optionally invoke the exact same command, but the command itself is the release contract.

## 23. Test data policy

Use deterministic synthetic fixtures.

Never commit production:

- customer names/phones/addresses;
- API keys;
- auth tokens;
- production DB backups;
- proprietary customer files unless explicitly sanitized/authorized.

Create a fixture builder that can generate realistic orders, parts, warehouses and RF products without private data.

## 24. Priority roadmap

### P0

1. inventory of existing tests and map to business invariants;
2. one local release-check runner;
3. state-transition contract tests;
4. permission/scope matrix;
5. deterministic concurrency/idempotency suite;
6. immutable migration fixtures;
7. structured technical logger + request ID;
8. health/worker/backup metrics;
9. alert on service/disk/backup/worker failure.

### P1

1. failure injection;
2. production-scale synthetic performance suite;
3. SQLite/PostgreSQL parity suite;
4. browser safe-render/network tests;
5. integration contract simulators;
6. metrics endpoint/exporter;
7. error-code taxonomy.

### P2

1. distributed tracing/OpenTelemetry if multi-process/integration complexity justifies it;
2. automated performance regression baselines;
3. richer SLO/error-budget reporting.

## 25. Acceptance signals

- a fresh checkout can execute one documented local release suite;
- migration fixtures prove old DBs upgrade safely;
- concurrency tests prove stock invariants under races;
- every critical aggregate has allowed/denied transition tests;
- application errors include request/job correlation IDs;
- operators can see queue age, worker health, DB/write failures and backup verification age;
- technical logs contain no raw secrets by default;
- integration outage is distinguishable from core service outage;
- test fixtures contain no production PII/secrets;
- no required release gate, monitor or test depends on GitHub Actions.

## 26. Core recommendation

Do not treat testing and observability as separate cleanup projects. Turn the existing strong local scripts into a **business-contract release suite**, then instrument the same transaction/job boundaries with structured logs and a small set of health metrics. This creates a reliable feedback loop for the much larger manufacturing/commerce expansion planned in W3/W4.