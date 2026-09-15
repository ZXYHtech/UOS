# TASK_INV_AUDIT_CODE_ARCHITECTURE_01 — Source Architecture & Maintainability Hotspots

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

This audit is intentionally framework-neutral and does not recommend GitHub Actions as an architectural dependency.

## 1. Current architecture in one sentence

Inventory Lite is a **server-centric modular-in-concept but file-monolithic implementation**: business responsibilities are named as services and the data model has meaningful domain concepts, but a large fraction of HTTP routing, business logic and UI behavior is concentrated in a few extremely large files.

## 2. Major source hotspots

Pinned tree sizes:

- `inventory_app/static/app.js` ≈ 664 KB
- `inventory_app/services.py` ≈ 419 KB
- `mobile/app.js` ≈ 305 KB
- `inventory_app/server.py` ≈ 278 KB
- `inventory_app/recognition.py` ≈ 113 KB
- `inventory_app/database.py` ≈ 78 KB
- `inventory_app/static/styles.css` ≈ 54 KB

These sizes do not automatically mean bad code, but combined with the number of domains now present they are strong maintainability signals.

`server.py` imports many services at once, including inventory, order, shipment, transfer, procurement, cost, pricing, backup, recognition-related configuration, category, exception, notifications/todo and voice-document services. The central Handler then performs auth, scope checks, route matching, request parsing and domain delegation.

`services.py` contains adapter code, recognition correction helpers and multiple major business services in the same module.

`app.js` acts as a large PC application shell, navigation registry, state/cache layer, view renderer, forms/dialogs and API interaction layer.

## 3. What is good and should be preserved

### 3.1 Business logic is conceptually centralized

The development index explicitly says inventory changes should go through service methods rather than direct UI/route SQL. This is the right invariant.

### 3.2 Service names already reveal natural module boundaries

The code already has conceptual boundaries such as:

- InventoryService
- OrderService
- ShipmentService
- TransferService
- ProcurementService
- CostService
- PricingService
- BackupService
- CategoryService
- ExceptionService
- NotificationService
- UnifiedTodoService
- VoiceDocumentService

The system therefore does not need a conceptual redesign from zero. It needs to turn existing conceptual boundaries into physical source boundaries.

### 3.3 Durable job/revision patterns already exist

OCR/image processing uses persisted task/job/revision/correction records. That pattern is valuable and should be generalized to future integrations/automation rather than adding hidden background threads with no durable state.

### 3.4 Existing deployment simplicity has business value

Python + SQLite + native JS keeps deployment lightweight. For the current team, preserving simple deployment is a real feature. Modularization must not automatically imply containers, Kubernetes, service mesh or microservices.

## 4. Main architecture risks

### R1 — `server.py` route concentration

Impact:

- permission/scope checks are easy to omit on a new branch;
- route-specific parsing and business orchestration can mix;
- code review becomes difficult because unrelated APIs share one large file;
- merge conflicts increase;
- Agent changes require loading excessive context.

Target:

`server.py` becomes transport/bootstrap only. Route groups move to domain modules while shared auth/scope helpers remain reusable.

### R2 — `services.py` domain concentration

Impact:

- unrelated business rules share imports/global helpers;
- changing one domain has a wider regression surface;
- module-level search is noisy;
- large-context AI/Agent edits are more error-prone;
- unit testing a service can drag unrelated dependencies.

Target:

Split by domain without changing external behavior first.

Example:

```text
inventory_app/domain/
  inventory.py
  warehouse.py
  catalog.py
  procurement.py
  pricing.py
  orders.py
  fulfilment.py
  transfers.py
  recognition.py
  integrations.py
  notifications.py
```

Then manufacturing/quality/aftersales can be added as new modules instead of further expanding the mega-file.

### R3 — PC `app.js` mega-file

Impact:

- page registry, fetch logic, local cache, render HTML, dialogs and business-specific interaction are tightly co-located;
- duplicate helper patterns accumulate;
- XSS review is harder because many HTML construction sites exist;
- individual feature ownership is difficult;
- testability is limited.

Target without mandatory bundler:

Browser-native ES modules are sufficient:

```text
static/js/
  core/api.js
  core/auth.js
  core/router.js
  core/state.js
  core/ui.js
  pages/inventory.js
  pages/orders.js
  pages/shipments.js
  pages/transfers.js
  pages/materials.js
  pages/procurement.js
  pages/pricing.js
  pages/settings.js
```

This preserves zero-build deployment if desired.

### R4 — PC and mobile duplicate business presentation logic

`inventory_app/static/app.js` and `mobile/app.js` are separate large clients. This is understandable because mobile workflow differs, but business validation/display vocabulary can drift.

Do not force one responsive client immediately. First extract shared contracts:

- status metadata;
- permission/page capability mapping;
- API schema expectations;
- error codes/messages where practical;
- barcode/scanning event schema;
- formatting helpers.

### R5 — legacy/duplicate mobile surfaces

The repository contains:

- `mobile/` online PWA;
- `mobile-offline/` browser-local offline app;
- `android-offline-app/` whose README now says it is an online WebView app;
- Android assets still include a copy of the offline web files with the same tree/blob identity as `mobile-offline/` in the pinned tree;
- `ios-app/` online WKWebView wrapper.

This is a classic product-history accumulation risk. The next architecture decision should explicitly classify every client as:

`SUPPORTED / MAINTENANCE_ONLY / MIGRATE / REMOVE`

and rename misleading directories before more automation depends on them.

### R6 — schema evolution centralized in one Python module

`database.py` contains initial schema, compatibility migration logic, seeds and DB helpers. As the schema expands into manufacturing, this will become difficult to reason about and impossible to cleanly mirror to PostgreSQL.

Target:

- immutable numbered migrations;
- one current schema specification;
- fixture upgrades from representative old versions;
- backend-specific DDL adapters only where necessary;
- schema-version table.

No external migration service or GitHub Actions is required.

### R7 — PostgreSQL placeholder can create false confidence

A stale `deploy/postgres/schema.sql` next to a much richer SQLite runtime can encourage an unsafe assumption that database migration is already mostly solved.

Treat PostgreSQL as **not supported for current production behavior** until parity tests exist.

### R8 — background work needs a general durable job model

The OCR derivative queue is already moving in the right direction. Future platform sync, report generation, backups, search indexing, MRP, notifications and AI tasks should not each invent their own ad-hoc loop.

Recommended internal primitive:

```text
jobs
job_attempts
job_locks/lease
job_result
job_dead_letter
```

or domain-specific outboxes feeding worker processes.

The worker must run under systemd/CLI and remain independent of GitHub Actions.

## 5. Recommended architecture style

### Now: modular monolith

Best fit for current stage:

- one deployable application;
- one primary database;
- explicit domain modules;
- internal service interfaces;
- durable job worker as a second process only when needed;
- shared repository-local tests;
- optional online/offline/mobile clients.

### Not recommended now: microservices

Microservices would add:

- distributed transactions;
- deployment and observability burden;
- API version coordination;
- more failure modes;
- duplicated auth and data contracts.

There is no evidence that current scale justifies that cost.

## 6. Target boundaries for electronics-company evolution

### Catalog / Part Master

Owns:

- item identity
- manufacturer/MPN
- aliases
- specifications
- lifecycle
- documents
- substitutes/AVL

### Inventory / Warehouse

Owns:

- locations
- stock balance
- reservations
- movements
- counts
- transfer stock state
- lot/serial/status later

### Purchasing

Owns supplier, supplier-part, PO, receipt, purchase cost and replenishment execution.

### Sales / Commerce

Owns platform order normalization, customer/quote/sample later, channel mapping and commercial status.

### Fulfilment

Owns allocation, pick/pack/ship, logistics and shipment confirmation.

### Manufacturing

Future owner of BOM release, MRP demand, work order, issue/return/scrap/WIP/completion.

### Quality / Traceability

Future owner of lot/serial genealogy, inspection, NCR, test evidence and calibration link.

### Pricing / Cost

Owns price lists/rules, landed cost, standard/estimated cost and later actual cost aggregation.

### Integration

Owns remote credentials, adapter contracts, sync cursor, webhook/event ingestion, retry/dead-letter and reconciliation.

### Automation / Reporting

Owns durable rules/jobs, KPI projections, notifications and AI assistant operations.

## 7. Refactor sequence designed to avoid a big-bang rewrite

### Step 1 — characterize current behavior

Before moving code, produce local regression commands for core workflows.

### Step 2 — extract pure/shared primitives

Move constants, serializers, status vocabularies, permission helpers and API response utilities with no behavior change.

### Step 3 — split one low-risk domain at a time

Suggested order:

1. pricing/cost;
2. procurement;
3. backup/settings;
4. categories/catalog profile;
5. transfers;
6. orders/fulfilment;
7. inventory last, because it is the highest-risk invariant owner.

### Step 4 — split routes after services

Route modules should call already-extracted domain services.

### Step 5 — split PC JavaScript by page/domain

Maintain the same DOM/UI first; do not redesign UX during the extraction.

### Step 6 — add new manufacturing modules only after foundation stabilizes

Do not add MRP/work orders directly into the old mega-files if modularization is already planned.

## 8. Source-size guardrails

Do not use arbitrary line-count limits as hard quality gates, but add review signals such as:

- a file repeatedly touched by unrelated domains;
- a module importing most of the application;
- tests unable to instantiate one domain without global setup;
- merge conflicts in unrelated work;
- duplicated status/permission definitions across clients;
- a route handler performing SQL + permission + business transition + formatting in one block.

These are stronger refactor triggers than a simple “500 lines is too many” rule.

## 9. No-Actions operational architecture

Required execution paths:

```text
Developer/fresh checkout
  -> python/node repository-local checks

Linux server
  -> systemd service for web API
  -> systemd service for worker(s)
  -> systemd timer or cron for maintenance where needed

Database
  -> durable job/outbox state
  -> backup/restore scripts

Monitoring
  -> application health endpoint/log/metrics
  -> external or server-local checker
```

GitHub may host code, but GitHub Actions must not own production execution.

## 10. Preliminary architecture score

0–5 static architecture maturity:

- domain concepts: **4/5**
- physical module boundaries: **2/5**
- deploy simplicity: **4.5/5**
- test entry points: **3.5/5**
- DB portability: **1.5/5**
- background-work foundation: **3/5** (strong OCR precedent, not yet general)
- mobile/client portfolio clarity: **2.5/5**
- suitability for controlled manufacturing extension today: **2/5**
- suitability for incremental modular-monolith evolution: **4/5**

## 11. Core recommendation

Do **not** rewrite Inventory Lite and do **not** move to microservices.

The best technical strategy is:

`preserve current business behavior -> create local reproducible regression suite -> split domain modules -> repair data model invariants -> add durable job/integration primitives -> then add electronics manufacturing/traceability domains`

This creates room for much deeper functionality while retaining the lightweight operating model that is currently one of the system's advantages.