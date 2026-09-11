# TASK_INV_AUDIT_TARGET_ARCHITECTURE_01 — Target Architecture Options for Inventory Lite Evolution

## 0. Executive decision

Three architecture options are evaluated:

1. **Option A — Minimum-change hardening**: keep current source shape, repair critical invariants and add a small worker.
2. **Option B — Modular monolith (recommended default)**: one deployable business application, explicit domain packages, one primary DB, durable worker/outbox, stable provider/API contracts.
3. **Option C — Larger-scale platform**: PostgreSQL + stronger process separation + optional dedicated services/caches/event infrastructure only when measured scale/organizational needs justify them.

### Recommendation

Adopt **Option B**, reached incrementally through Option A-compatible steps.

Do **not** perform a big-bang rewrite and do **not** introduce microservices now.

The architecture should evolve as:

```text
Current useful monolith
 -> harden tests/migrations/security/ledger
 -> split into domain-owned modular monolith
 -> add manufacturing/quality/economics modules
 -> scale selected infrastructure only after metrics prove the need
```

Required correctness, scheduling, backup, worker execution and tests must remain independent of GitHub Actions.

## 1. Current architecture baseline

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Current strengths:

- simple Python deployment;
- SQLite WAL operational simplicity;
- real RBAC/warehouse-scope controls;
- strong order/fulfilment/transfer workflows;
- useful pricing/procurement capabilities;
- durable OCR worker precedent;
- broad repository-local regression scripts;
- PC + mobile operator surfaces.

Current architecture debt:

- very large `services.py`, `server.py`, `app.js`, `mobile/app.js`;
- stock identity too coarse for bin/state/lot/serial;
- reservation not first-class;
- centralized mutable schema/migration logic;
- PostgreSQL schema drift;
- route permission/state/idempotency policy hand-composed;
- background jobs not generalized;
- manufacturing/quality/traceability domains missing.

## 2. Architecture principles that apply to all options

Regardless of option, preserve these invariants:

1. **Domain service owns business mutation.** UI, AI, import and connector code cannot write authoritative tables directly.
2. **Business document != ledger event.** Documents express intent; stock/economic ledgers express effects.
3. **Consequential transitions are explicit.** Released/submitted records are not silently edited.
4. **Idempotency is server-side.** Retry/double-click/network timeout must not duplicate stock/financial effects.
5. **External work is asynchronous where appropriate.** Remote APIs do not participate in local DB transactions.
6. **Compensation preserves history.** Reverse with linked events; do not delete executed history.
7. **AI is assistive, not authoritative.** Deterministic services remain source of truth.
8. **Permissions combine actor + permission + object/warehouse scope + state + idempotency.**
9. **Migrations are versioned and locally testable.**
10. **Runtime does not depend on GitHub Actions.**

## 3. Option A — Minimum-change hardening

### 3.1 Description

Keep the current application layout largely intact for a short stabilization period.

Add only the foundational controls necessary to prevent further architecture debt while existing workflows continue to operate.

### 3.2 Target shape

```text
Current server.py / services.py / app.js
          |
          +-- stronger action helpers
          +-- numbered migrations
          +-- stock operation idempotency
          +-- reservation tables/service
          +-- durable jobs/outbox
          +-- security headers/secrets hardening
          +-- local release/recovery tests
```

### 3.3 What changes

- introduce `schema_version` and numbered migration files;
- inventory all mutating routes/actions;
- add reusable permission/scope/idempotency/audit wrappers;
- add business-operation keys to stock-changing commands;
- introduce reservation as a new service/table even before full stock-position migration;
- extract a generic job runner from OCR patterns;
- implement backup verification and operational health commands;
- fix pricing margin/markup terminology;
- improve CSP/output escaping/upload handling.

### 3.4 Advantages

- fastest risk reduction;
- low deployment disruption;
- preserves current operator behavior;
- creates regression evidence before refactoring.

### 3.5 Disadvantages

- giant files remain a merge/review burden;
- new manufacturing modules would still risk being added into the wrong source locations;
- data-model migration becomes harder if postponed too long.

### 3.6 When this option is justified

Use as **0–3 month transition**, not the long-term target.

It is appropriate while stabilizing behavior and building migration/test safety.

## 4. Option B — Modular monolith (recommended)

### 4.1 Description

One primary deployable application, one primary relational database, explicit internal domain boundaries, one or more worker processes using the same codebase, and provider adapters for external systems.

No internal network boundary is required between domains.

### 4.2 Target deployment

```text
                 Browser PC / Mobile / API clients
                              |
                     HTTPS reverse proxy
                              |
                    inventory-web.service
                              |
+----------------------------------------------------------------+
|                       Modular Monolith                         |
| Identity | Catalog | Inventory | Warehouse | Purchasing        |
| Commerce | Fulfilment | Manufacturing | Quality | Traceability |
| Pricing/Cost | CRM | Aftersales | Integrations | Reporting     |
+----------------------------------------------------------------+
             |                       |
        Primary DB              durable outbox/jobs
             |                       |
       ledgers/state            inventory-worker.service
                                     |
                          marketplace/carrier/AI/EDA/
                          RF-test/machine/file providers

Scheduled maintenance:
  systemd timers / cron -> local commands/jobs

Backups:
  DB + artifacts -> off-host copy -> restore verification
```

### 4.3 Why this is the best fit

It provides:

- strong source ownership;
- single-transaction local invariants;
- simple deployment for a small team;
- manufacturing/quality extension room;
- controlled async external work;
- easy future extraction of a service only if genuinely needed.

It avoids:

- distributed transactions;
- service discovery;
- message-broker operations;
- duplicated auth;
- premature API choreography;
- large DevOps burden.

## 5. Recommended domain boundaries

## 5.1 Identity & Access

Owns:

- users;
- roles/permissions;
- sessions;
- warehouse/site membership;
- action-policy evaluation helpers;
- service/API credentials references, not provider-specific business logic.

Must not own business-state transitions.

## 5.2 Catalog / Engineering Part Master

Owns:

- internal part/material;
- manufacturer;
- manufacturer part / MPN;
- supplier part identity references;
- aliases;
- typed parameters;
- lifecycle/compliance;
- AVL/substitute relationships;
- part documents metadata.

External distributor data enters through provider adapters and retains provenance.

## 5.3 Inventory Kernel

Owns:

- stock positions/balances;
- stock movement ledger;
- reservations;
- stock status/quality availability flags;
- lot/serial identities where physical stock semantics require them;
- reconciliation/invariant checks.

No other domain writes stock balances directly.

## 5.4 Warehouse Execution

Owns:

- warehouse/location/bin hierarchy;
- receiving staging;
- putaway;
- allocation/pick tasks;
- transfer execution;
- cycle count tasks;
- scan operations;
- packaging later.

Calls Inventory Kernel for actual stock effects.

## 5.5 Purchasing

Owns:

- suppliers;
- supplier-part commercial data;
- purchase orders;
- approvals;
- receipts as business documents;
- price history;
- supplier performance;
- sourcing/RFQ later.

Receipt posts stock through Inventory Kernel and quality workflow.

## 5.6 Commerce / Sales Orders

Owns:

- canonical order;
- channel/platform account context;
- order line commercial snapshots;
- cancellation/backorder/commercial status;
- external-order linkage IDs.

Does not own physical shipment execution or marketplace API client code.

## 5.7 Fulfilment

Owns:

- shipment tasks;
- allocations;
- pick/pack/parcel state;
- logistics data;
- shipment completion/reversal;
- exact serial association when required.

Consumes reservations through Inventory Kernel.

## 5.8 Manufacturing

Owns:

- released production order/work order;
- MBOM snapshot;
- routing/operation basics;
- required/reserved/issued/returned/scrapped material;
- WIP/completion;
- subcontract operational order linkage.

Calls Inventory Kernel for material/output movement.

## 5.9 Engineering Change / BOM Control

Can be a Catalog submodule initially, but owns:

- BOM header/revision/line;
- sales vs EBOM vs MBOM type;
- refdes/variant/DNF;
- effectivity;
- release/supersession;
- ECN/ECO/change approval;
- EBOM→MBOM relationship.

MRP/WO may reference only released effective MBOM.

## 5.10 Quality

Owns:

- inspection plan/control points;
- IQC/IPQC/FQC/OQC results;
- NCR;
- MRB/disposition;
- rework/scrap approval;
- supplier-quality cases.

Quality state changes call Inventory Kernel and can affect nettable/ship-able stock.

## 5.11 Traceability & Test

Owns:

- genealogy links;
- finished serial identity lifecycle;
- component lot/serial usage links;
- RF/electrical test specifications/limit sets;
- test runs/measurements;
- raw artifact references;
- equipment/calibration records;
- firmware/config provenance.

Can begin as Quality submodules if team size remains small.

## 5.12 Pricing & Cost

Owns:

- price lists;
- pricing rules;
- price revisions;
- engineering/reference cost;
- standard cost version;
- actual WO cost aggregation later.

Does not own channel settlement transaction ingest.

## 5.13 CRM & Aftersales

Owns:

- customer/account;
- inquiry/opportunity;
- quotation/revision;
- technical requirement context;
- sample/loan records;
- support case;
- RMA/warranty/repair/replacement lifecycle.

Links to order/serial/test evidence through stable references.

## 5.14 Integrations

Owns provider/adapter code and external sync state:

- marketplace connector;
- carrier connector;
- settlement connector;
- part-data provider;
- EDA adapter;
- AI provider;
- RF test/machine adapter;
- notification provider.

It must not own canonical business objects.

## 5.15 Automation

Owns:

- durable jobs;
- outbox;
- rule definitions;
- scheduled evaluation;
- retry/dead-letter;
- approval requests for automated proposals.

Actions always go through owning domain service.

## 5.16 Reporting

Owns:

- read models;
- metric definitions/lineage;
- cached aggregates;
- management views;
- product scorecards.

It does not mutate transaction truth.

## 6. Source tree target

A practical Python structure without mandatory framework change:

```text
inventory_app/
  bootstrap/
    server.py
    config.py
  core/
    db.py
    errors.py
    auth.py
    action_policy.py
    idempotency.py
    jobs.py
    events.py
    audit.py
  domains/
    catalog/
    inventory/
    warehouse/
    purchasing/
    commerce/
    fulfilment/
    bom_change/
    manufacturing/
    quality/
    traceability/
    testing/
    pricing_cost/
    crm/
    aftersales/
    integrations/
    automation/
    reporting/
  migrations/
    0001_...
    0002_...
  static/
    js/core/
    js/pages/
  mobile/
```

Do not require a frontend bundler simply to modularize; browser-native ES modules are sufficient if desired.

## 7. Database strategy

## 7.1 Near term — keep SQLite, fix semantics

SQLite should remain supported while:

- write concurrency remains modest;
- one primary application/server owns writes;
- DB fits comfortably on one host;
- WAL/checkpoint/backup metrics are healthy;
- local concurrency tests prove business invariants.

### Required SQLite improvements

- numbered migrations;
- explicit foreign-key constraints where safe;
- non-null/partial unique strategy for stock scope;
- decimal/UOM policy;
- transaction-level idempotency;
- shorter, explicit write transactions;
- invariant/reconciliation commands;
- backup/restore drills.

## 7.2 PostgreSQL adoption criteria

Move only when one or more are demonstrated:

1. sustained write contention exceeds acceptable latency despite transaction optimization;
2. multiple independent worker processes need higher concurrent write throughput;
3. reporting/transaction workload requires stronger concurrency isolation;
4. operational requirements demand PostgreSQL HA/PITR/tooling;
5. dataset/query scale produces measured SQLite limits;
6. multi-site architecture requires a server database with mature replication options.

### Migration rule

The existing `deploy/postgres/schema.sql` is not an authoritative migration path.

Use:

```text
canonical numbered schema migrations
 -> backend compatibility layer where needed
 -> SQLite fixture upgrade tests
 -> PostgreSQL schema parity tests
 -> data copy/reconciliation rehearsal
 -> cutover only after parity proof
```

## 8. Ledger strategy

## 8.1 Stock movement ledger

Target movement line fields:

```text
operation_id / idempotency_key
material_id
from/to warehouse/location
from/to stock status
lot/serial where applicable
quantity + UOM
business reference type/id
actor
occurred_at
reversal_of
reason
```

A balance table may remain a fast projection.

## 8.2 Reservation ledger

Separate from physical movement:

```text
reservation
  reference type/id/line
  material / optional stock position
  quantity
  status: active/released/consumed
  purpose: sales/WO/project/sample/etc.
  timestamps
  idempotency key
```

## 8.3 Economic events

Channel/order economics should use additive events/snapshots rather than rewriting master cost:

```text
sale revenue
promotion/discount
platform fee
payment fee
freight
seller-borne tax
refund
return loss
replacement/warranty cost
COGS basis
```

## 9. Job / event architecture

### Synchronous path

Use for local invariant changes that must commit atomically.

Example:

```text
confirm shipment
 -> validate state/scope
 -> consume reservation
 -> post stock movement
 -> change shipment state
 -> add outbox event
COMMIT
```

### Asynchronous path

Worker later handles:

```text
outbox event
 -> platform API
 -> ack/retry
 -> reconciliation status
```

### Do not

- call remote platform API inside stock transaction;
- use in-memory background threads as sole durable ownership;
- use GitHub Actions as runtime scheduler;
- create a general message broker before needed.

## 10. Event taxonomy

Three categories:

### Domain events

Persisted/semantic:

- OrderConfirmed;
- ReservationCreated;
- ShipmentCompleted;
- PurchaseReceiptPosted;
- WorkOrderReleased;
- MaterialIssued;
- ProductSerialCompleted;
- QualityDispositionChanged;
- RmaReceived;
- SettlementImported.

### Integration events

Outbox entries for external side effects.

### Technical telemetry

Logs/metrics/traces for request/worker/DB/provider performance.

Do not mix them into one generic event table without semantics.

## 11. Provider and adapter contracts

Recommended first-class interfaces:

```text
CommerceConnector
CarrierProvider
SettlementConnector
PartDataProvider
AIProvider
ArtifactStore
NotificationProvider
EDAAdapter
TestEquipmentAdapter
ManufacturingMachineAdapter
```

Every provider should expose:

- configuration/availability validation;
- bounded timeout/retry behavior;
- provenance/external IDs;
- masked secret handling;
- health/status;
- deterministic local result schema.

## 12. API strategy

Keep REST unless a real integration need proves otherwise.

Required improvements:

- route/action registry;
- typed request/response schemas;
- stable status/error codes;
- explicit pagination/filter syntax;
- idempotency-key support on consequential commands;
- API version/deprecation policy;
- generated reference documentation where feasible;
- object/warehouse scope always server-side.

### Command/query distinction

Conceptually distinguish:

```text
GET/query -> read model
POST command -> business action/state transition
```

Avoid generic CRUD for consequential workflow objects.

## 13. Permission architecture

Each action definition should bind:

```text
authenticated actor
required permission(s)
object/warehouse scope resolver
allowed source state
business preconditions
idempotency class
audit policy
```

Example:

```text
shipment.complete
  permission: shipment.process
  scope: task.warehouse_id
  state: processing/waiting_logistics -> shipped/completed
  idempotency: required
  audit: ledger-derived + operation log
```

UI capability checks remain convenience only.

## 14. Reporting/read architecture

Do not run every executive KPI as an expensive multi-domain live query forever.

Stages:

1. direct queries while volume is small;
2. domain query services/views;
3. cached aggregate/read-model tables updated by local jobs/events;
4. external BI/read replica only if later justified.

Every KPI needs:

- definition;
- source fields/events;
- denominator;
- time basis;
- scope;
- freshness;
- known limitations.

## 15. Client architecture

### PC

Target dense management/review work:

- global search;
- entity workspace;
- saved views;
- bulk preview/validation;
- keyboard support;
- analytical drilldown.

### Mobile

Target physical execution:

```text
scan task
 -> scan location
 -> scan item/lot/serial
 -> quantity
 -> validate
 -> server-confirmed action receipt
```

### Shared contract

PC/mobile share:

- identifiers;
- status vocabulary;
- actions;
- API error semantics;
- permission-driven capabilities;
- scan payload rules.

They do not need identical layouts.

## 16. Offline architecture decision

Current online PWA static-cache behavior and legacy `mobile-offline` local business store are fundamentally different products.

Recommended near-term decision:

### Default

Online authoritative writes, with:

- cached static assets;
- optional read cache;
- clear network failure states;
- retriable non-mutating work where safe.

### True offline writes only if explicitly funded

Then require:

```text
operation UUID
base server version
local pending queue
server conflict detection
per-domain merge/compensation policy
device/user identity
sync receipt
```

Do not allow generic last-write-wins inventory mutation.

## 17. Testing architecture

Repository-local release contract:

```text
1. syntax/import checks
2. migration upgrade fixtures
3. domain unit/state-transition tests
4. stock/financial invariant tests
5. idempotency/concurrency tests
6. permission/object-scope matrix
7. connector replay tests
8. backup/restore drill
9. client routing/critical workflow checks
10. performance smoke benchmarks
```

A shell/Python command should run this directly on a developer machine/server.

CI may call the same command, but required correctness cannot rely on GitHub Actions.

## 18. Observability architecture

Add correlation identifiers:

```text
request_id
actor_id
business_operation_id
job_id
external_object_id
```

Structured technical logs should report:

- route latency/error;
- DB lock wait/transaction duration;
- worker queue depth/age;
- retries/dead letters;
- connector latency/error classes;
- backup age/restore verification status;
- disk/database size;
- OCR/AI resource pressure.

Business audit remains in operation/ledger tables, not only logs.

## 19. Migration sequence from current source

### Stage 0 — characterize

- pin fixtures;
- freeze current regression suite;
- add one aggregate release command;
- backup/restore rehearsal.

### Stage 1 — extract shared primitives

- DB connection/migration;
- errors/API response;
- auth/scope;
- action policy;
- idempotency;
- operation audit;
- jobs/outbox.

No business behavior redesign yet.

### Stage 2 — split low-risk domains

Suggested source extraction order:

1. pricing/cost;
2. procurement;
3. backup/settings;
4. catalog categories/resources;
5. integrations/notifications.

### Stage 3 — stock kernel migration

- introduce new stock-position/reservation/ledger structures;
- dual-read/reconcile during migration if necessary;
- cut individual commands to new service;
- prove balance equivalence;
- retire obsolete quantity mutation paths.

### Stage 4 — commerce/fulfilment adaptation

- order reservation;
- exact allocation/bin scan;
- external-object sync/outbox;
- shipment idempotency.

### Stage 5 — engineering configuration

- part/MPN/supplier part;
- AVL;
- EBOM/MBOM/revisions;
- ECN/docs/firmware.

### Stage 6 — manufacturing/quality/traceability

- WO;
- IQC/NCR;
- lot/serial;
- RF test evidence;
- subcontract.

### Stage 7 — planning/economics/CRM

- MRP;
- standard/actual cost;
- channel settlement;
- CRM/quote/RMA;
- executive read models.

### Stage 8 — automation/AI optimization

Only after trusted data/commands exist.

## 20. Option C — Larger-scale platform

### 20.1 Description

Retain domain architecture from Option B but strengthen infrastructure:

- PostgreSQL primary;
- multiple web/worker processes;
- centralized object/blob storage;
- optional Redis for cache/locks/queue acceleration;
- optional event/message broker;
- dedicated reporting store/read replica;
- selected service extraction where organization/scale requires it.

### 20.2 Important rule

**Option C is not a different business model.** It is Option B with stronger infrastructure boundaries.

If Option B domain ownership is poor, Option C only distributes the mess.

### 20.3 Triggers for Option C

At least one measurable condition should exist:

- sustained DB write contention;
- high worker concurrency;
- multi-site/HA requirements;
- very large traceability/test/ledger volumes;
- independent teams needing separate deploy cadence;
- integrations requiring isolation/SLA;
- advanced analytics load harming transactions;
- automated warehouse/equipment fleet needing dedicated services.

## 21. Potential service extraction order later

If scale proves necessary, extract only stable boundaries, likely:

1. artifact/test-file storage processing;
2. platform connector workers;
3. reporting/analytics read service;
4. machine/test-equipment gateway;
5. notification service.

Avoid extracting inventory transaction truth first; it is highly coupled to reservations, warehouse and manufacturing invariants.

## 22. Architecture option comparison

| Criterion | Option A Minimum-change | Option B Modular monolith | Option C Larger scale |
|---|---|---|---|
| near-term delivery speed | **Best** | Good | Poor |
| maintainability after many new domains | Weak/Medium | **Best for target** | Good if well operated |
| deployment simplicity | **Best** | **Very good** | Complex |
| local transaction consistency | Good | **Best** | More complex if services split |
| manufacturing extension | Medium | **Best** | Strong but expensive |
| small-team fit | **Strong** | **Strongest balance** | Weak |
| scalability ceiling | Medium | High enough for likely next stage | Highest |
| operational burden | Low | Moderate | High |
| migration risk | Low short-term | Moderate/incremental | High |
| recommendation | bridge only | **Default target** | conditional future |

## 23. Decisions that should be made now

1. modular monolith is the target architecture;
2. SQLite remains supported until measured thresholds trigger migration;
3. stock/reservation ledger becomes the core invariant owner;
4. background work uses DB-backed durable jobs/outbox;
5. required scheduling uses systemd/cron/application worker, not GitHub Actions;
6. business-document state machines replace arbitrary status editing;
7. external providers are adapters, not business authority;
8. released engineering configuration becomes first-class;
9. PC/mobile share contracts but remain task-specialized;
10. AI cannot bypass domain services.

## 24. Decisions intentionally deferred

Do not decide yet:

- exact PostgreSQL cutover date;
- Redis adoption;
- event broker technology;
- microservice boundaries;
- full offline-first synchronization;
- wave/cluster WMS;
- generic plugin marketplace;
- generic workflow designer;
- full accounting platform.

Measure first.

## 25. Core recommendation

The target is not “a bigger inventory app.” It is a controlled operating backbone for a small electronics/RF company:

```text
Commerce demand
      |
Reservation / ATP
      |
Inventory/Warehouse truth
      |
Engineering revision -> Manufacturing -> Quality/Test -> Finished serial
      |                                      |
Purchasing/MRP                         Aftersales/RMA
      |                                      |
Cost / Channel economics / Product intelligence
```

Implement that inside a **modular monolith with one authoritative transaction database and a durable worker layer**. This is the highest-value balance of control, simplicity, extensibility and future scale.