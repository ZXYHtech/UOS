# TASK_INV_AUDIT_OSS_ARCH_PATTERN_01 — Reusable Open-source Architecture & Extension Patterns

## 0. Scope

This synthesis consumes the current W6 peer benchmarks completed on 2026-09-11:

- `TASK_INV_AUDIT_OSS_ERP_01.md`
- `TASK_INV_AUDIT_OSS_ELECTRONICS_01.md`
- `TASK_INV_AUDIT_OSS_WMS_01.md`
- `TASK_INV_AUDIT_OSS_COMMERCE_01.md`

Inventory Lite evidence remains pinned to `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

The goal is not to imitate a particular framework. The goal is to extract architecture patterns that repeatedly appear in mature ERP, electronics inventory, WMS and commerce systems, then decide which are portable to Inventory Lite and which would be premature complexity.

## 1. Executive conclusion

The peer systems converge on a surprisingly consistent architecture:

```text
Business document/state machine
  -> domain service validates transition
  -> authoritative ledger / reservation / state event
  -> durable outbox/job for side effects
  -> provider/connector executes external work
  -> reconciliation/compensation records outcome
```

They also converge on **modularity without necessarily requiring microservices**. ERPNext/Frappe, Odoo, Dolibarr, Tryton, InvenTree, Medusa and Sylius all demonstrate strong module/domain ownership while remaining deployable as one primary application platform.

For Inventory Lite, the most appropriate target remains a **modular monolith with a small durable worker**, one primary database, explicit domain ownership and strongly controlled cross-domain contracts.

The largest architecture upgrade is therefore not “change framework” or “move to distributed services.” It is to make business truth explicit: stock identity, reservations, released documents, state transitions, idempotency, revision/effectivity, durable jobs and integration provenance.

## 2. Pattern 1 — domain ownership inside one deployable system

### Evidence across peers

- Tryton decomposes stock, stock-lot, production, quality, sales and opportunity into modules.
- Medusa decomposes product, pricing, inventory, order, fulfilment, payment, promotion, sales channel and tax into commerce modules.
- Odoo and ERPNext use broad domain applications/modules while still operating as integrated business platforms.
- Dolibarr emphasizes custom modules instead of repeatedly editing core.

### Portable Inventory Lite rule

Each domain should own:

```text
models / tables
state vocabulary
service / commands
routes / API
migrations
business events
local tests
```

Recommended ownership:

```text
catalog/
inventory/
warehouse/
purchasing/
commerce/
fulfilment/
manufacturing/
quality/
traceability/
pricing_cost/
crm/
after_sales/
integrations/
automation/
reporting/
identity/
```

### Cross-domain rule

A module must not reach into another module's tables merely because it can.

Preferred options:

1. call the owning service;
2. use a stable ID/reference;
3. consume an event/outbox record;
4. build a read projection for reporting.

### Do not copy

Do not create network microservices for these boundaries at current scale. Source ownership and transaction boundaries provide most of the benefit without distributed-system cost.

## 3. Pattern 2 — authoritative business documents with controlled lifecycle

ERPNext submitted documents, Odoo/Sylius state machines and Tryton workflows all reinforce this pattern:

```text
Draft
 -> reviewed/approved/released
 -> execution
 -> immutable authoritative history
 -> cancel/reverse/supersede rather than silent rewrite
```

Apply it to:

- PO and receipt;
- shipment;
- transfer;
- work order;
- quality inspection/NCR disposition;
- return/RMA;
- EBOM/MBOM release;
- firmware/test-spec release;
- settlement reconciliation.

### Inventory Lite rule

Consequential records should declare:

```text
status
allowed transitions
actor/permission
preconditions
effectivity/version
side effects
reversal/compensation path
audit event
```

This is stronger than generic `status TEXT` plus scattered conditionals.

## 4. Pattern 3 — source document is not the stock ledger

ERPNext stock ledger, Odoo stock moves, OpenBoxes stock movements and InvenTree stock-item/build allocation all point to the same architecture.

Business documents express **intent**; stock ledger events express **physical/ownership/state truth**.

Target:

```text
shipment / receipt / transfer / WO / RMA / adjustment
            |
            v
stock movement operation
            |
            v
immutable movement line(s)
            |
            v
balance / availability projection
```

Do not allow each feature to invent a different quantity mutation mechanism.

## 5. Pattern 4 — logical Part is distinct from physical Stock Position

InvenTree provides the strongest direct evidence:

```text
Part = logical/catalog identity
Stock Item = physical inventory instance/position
```

OpenBoxes and WMS peers reinforce that physical stock identity includes location/bin, lot and state.

Target Inventory Lite distinction:

```text
Internal Part / Material
  manufacturer + MPN
  engineering parameters
  lifecycle / revision / AVL

Stock Position
  warehouse + bin
  material
  lot/batch/serial where required
  quality state
  ownership/classification
  receipt/build provenance
  quantity
```

This is more robust than forcing all distinctions into one `(material, warehouse, platform)` row.

## 6. Pattern 5 — stocked, reserved, incoming and usable are separate concepts

Medusa's explicit `stocked_quantity`, `reserved_quantity`, `incoming_quantity` and `ReservationItem` model strongly validates the audit's earlier stock redesign.

A correct availability model is conceptually:

```text
qualified physical stock
- reservations/allocations
- non-saleable/engineering commitments
- quarantine/rejected state
- policy/safety buffer
= ATP / publishable / allocatable stock
```

Reservations require their own identity:

```text
reservation_id
business reference
material/stock position
quantity
status
created/released/consumed timestamps
idempotency key
```

A cached `quantity_locked` may remain a projection, but it must not be the only business evidence.

## 7. Pattern 6 — receiving staging before putaway

OpenBoxes demonstrates a clean operational boundary:

```text
Receipt
 -> receiving/staging bin
 -> inspection if required
 -> putaway task
 -> final bin
```

This avoids forcing the receiving operator to decide permanent storage immediately and creates a natural IQC/quarantine boundary.

For Inventory Lite, the same concept can support:

- PO receiving;
- transfer receipt;
- RMA return receipt;
- subcontract return;
- production output waiting inspection.

## 8. Pattern 7 — risk-based lot/serial policy

Odoo, ERPNext, InvenTree and Tryton all treat traceability as configurable rather than universally serializing everything.

Recommended policy:

```text
NONE
LOT
SERIAL
LOT_AND_SERIAL (only when genuinely needed)
```

RF modules/instruments and critical assemblies can use serial traceability; low-cost generic components can stay lot or quantity-only.

This keeps the system usable while enabling full genealogy where business value justifies it.

## 9. Pattern 8 — build/WO allocation to concrete qualified stock

InvenTree Build Orders and WMS allocation patterns demonstrate that a build should not merely deduct arbitrary BOM quantities at completion.

Target:

```text
released MBOM revision
 -> WO material requirement snapshot
 -> reservation
 -> allocate exact qualified stock position/lot
 -> pick/issue
 -> consume/return/scrap
 -> finished output receipt
```

This is the backbone linking MRP, traceability, quality and actual cost.

## 10. Pattern 9 — workflow + durable job + compensation

Medusa provides the clearest modern pattern; OCR in Inventory Lite already supplies a local precedent.

Use synchronous database transactions for local invariants, then durable jobs/outbox for remote/slow work.

```text
local business transaction
 -> outbox/job row committed
 -> worker claims with lease
 -> idempotent handler
 -> success / retry / manual review
 -> compensation/reconciliation if required
```

Suitable domains:

- marketplace order/fulfilment sync;
- inventory publication;
- RF report generation;
- large imports;
- backup verification;
- settlement ingest;
- MRP runs;
- AI analysis;
- notifications;
- external machine/test station integration.

### Required job fields

At minimum:

```text
job_type
payload/reference
status
attempt_count
next_attempt_at
lease/locked_by
idempotency_key
last_error
result/reference
created/started/completed timestamps
```

### Project constraint

Required jobs and schedules must run through the application/server/worker plus systemd/cron/timer where appropriate. GitHub Actions is not a runtime scheduler or correctness dependency.

## 11. Pattern 10 — domain events are not technical events

Dolibarr triggers, Medusa workflow events and OpenPnP machine events illustrate different event purposes.

Inventory Lite should distinguish:

### Business event

Examples:

- `OrderConfirmed`
- `StockReserved`
- `ShipmentCompleted`
- `PurchaseReceiptAccepted`
- `WorkOrderReleased`
- `QualityDispositionApproved`
- `RmaClosed`

Used for automation/integration/reporting.

### Technical event

Examples:

- request failed;
- worker retry;
- DB lock wait;
- OCR timeout;
- remote API latency.

Used for observability.

### Machine/external event

Examples:

- SMT job started;
- feeder fault;
- test station completed run.

Must be translated through adapters into controlled domain commands before changing authoritative business state.

## 12. Pattern 11 — provider/connector interfaces with provenance

Saleor apps, Medusa modules/providers, Part-DB providers and InvenTree plugins all support provider boundaries.

Recommended provider contracts:

```text
CommerceConnector
PartDataProvider
CarrierProvider
Payment/SettlementConnector
ArtifactStore
NotificationProvider
AIProvider
TestEquipmentAdapter
ManufacturingMachineAdapter
```

External data should retain:

```text
provider
external ID
observed version/time
payload hash/provenance
mapping status
last sync result
```

Never treat distributor or AI-provided data as automatically approved engineering truth.

## 13. Pattern 12 — external object ledger before omnichannel automation

Modern commerce systems separate canonical objects from integration observations.

Inventory Lite should maintain durable external identity such as:

```text
platform_account_id
external_object_type
external_object_id
external_version_or_modified_at
payload_hash
first_seen_at
last_seen_at
processing status
canonical_object_id
```

This supports:

- replay safety;
- dedupe;
- update detection;
- reconciliation;
- source-of-truth analysis.

It is superior to relying on recognition raw text as long-term connector state.

## 14. Pattern 13 — pricing, promotion and settlement are separate

Medusa explicitly separates Pricing and Promotion; W4 found Inventory Lite already has useful pricing but lacks complete realized economics.

Recommended ownership:

```text
Pricing
 -> list/contract/channel/customer price

Promotion
 -> temporary discount/promotion adjustment when needed

Order snapshot
 -> immutable transaction price basis

Channel economics
 -> platform/payment/freight/tax/refund settlement events
```

Do not turn `PricingService` into accounting.

## 15. Pattern 14 — parametric metadata is not engineering authority

InvenTree explicitly treats parameters as metadata, and Part-DB shows their value for component search.

Use parameters for:

- filtering;
- comparison;
- documentation;
- candidate discovery.

Use controlled objects for:

- approved MPN;
- AVL/substitute eligibility;
- product/BOM revision;
- released firmware/test specification;
- lifecycle/effectivity.

An AI or parametric similarity score may suggest alternates, but cannot silently authorize them.

## 16. Pattern 15 — EDA and machine systems are bounded integrations

Part-DB and OpenPnP show why EDA/import and SMT execution require explicit adapters.

### EDA boundary

```text
KiCad/Altium/EDA BOM
 -> normalize code/MPN/value/package/refdes
 -> match internal parts
 -> unresolved review
 -> draft EBOM
 -> diff
 -> release
```

### Machine boundary

```text
released WO + product revision
 -> machine job package
 -> OpenPnP/test equipment execution
 -> machine evidence/events
 -> controlled domain command
 -> Inventory Lite authoritative state
```

Do not make machine software the enterprise inventory authority.

## 17. Pattern 16 — declarative permission/action policy

Frappe metadata and modern API frameworks demonstrate the benefit of central policy metadata. Inventory Lite already has strong server permission primitives but route coverage is hand-composed in a large handler.

Target action definition:

```text
action/route
  authentication requirement
  permission(s)
  object/warehouse scope resolver
  allowed state transition
  idempotency class
  audit requirement
```

This metadata can generate parts of tests/documentation without becoming a generic low-code platform.

## 18. Pattern 17 — API schema/version/deprecation governance

InvenTree's documented/versioned API, Saleor's API-first contract and newer Odoo/Tryton APIs show that integration surfaces need governance independent of UI code.

Inventory Lite should establish:

- stable object IDs;
- explicit request/response schemas;
- documented error codes;
- pagination contract;
- version/deprecation policy;
- permission/scope behavior;
- idempotency semantics for commands.

REST remains sufficient; GraphQL is not required.

## 19. Pattern 18 — controlled plugin evolution, not arbitrary hooks

Dolibarr demonstrates upgrade-friendly hooks; Medusa distinguishes modules and plugins.

Inventory Lite should evolve in stages:

### Stage A — internal modules

First create clean domain boundaries inside the repository.

### Stage B — provider interfaces

Allow configured implementations for commerce, part data, notifications, AI and equipment.

### Stage C — packaged extensions

Only when interfaces are stable, permit reusable extension packages with:

- declared dependencies;
- version compatibility;
- migrations;
- permissions;
- settings schema;
- startup/health validation.

### Avoid

- arbitrary plugin SQL access;
- arbitrary code hooks at every line of core execution;
- a third-party plugin marketplace before core contracts stabilize.

## 20. Pattern 19 — read models/reporting separated from transaction truth

Mature business systems often expose dashboards/reporting across many domains, but the transactional schema should not become optimized solely for analytics.

Recommended Inventory Lite pattern:

```text
transaction/domain tables
 -> event/lifecycle data
 -> query/read model / cached aggregates
 -> KPI/reporting layer
```

Every management KPI should declare lineage and freshness.

Examples:

- ATP from reservation/stock state;
- order cycle time from lifecycle timestamps;
- inventory turns from movement/economic data;
- contribution margin from immutable order economics events;
- product scorecard from measured source metrics.

## 21. Pattern 20 — migration/version discipline

All mature peers depend on repeatable upgrades. Inventory Lite's current centralized migration logic and stale PostgreSQL schema are not sufficient for future manufacturing expansion.

Target:

```text
schema_version
numbered immutable migrations
representative old-version fixtures
preflight integrity checks
migration rollback/recovery strategy
SQLite parity tests
PostgreSQL compatibility only when explicitly supported
```

Do not maintain two manually drifting schemas.

## 22. Pattern 21 — task-centric warehouse UI over generic CRUD

Odoo Barcode, OpenBoxes putaway and current Inventory Lite operator work all reinforce a guided execution model:

```text
Task
 -> expected location/item
 -> scan
 -> validate
 -> quantity
 -> next item
 -> exception or finish
```

Desktop can remain dense and comparative; mobile should optimize physical execution.

The same API/state vocabulary must back both.

## 23. Pattern 22 — compensation, never history deletion

OpenBoxes rollback events, ERP-style cancel/reversal and Inventory Lite's existing shipment/transfer reversal direction all support:

```text
incorrect executed event
 -> compensating event
 -> linked reversal reason
 -> preserved original history
```

This should be universal for stock, quality, settlement and cost corrections.

## 24. Architecture patterns to adopt by phase

### P0 — portable now

1. domain module ownership;
2. explicit business state machines;
3. authoritative stock movement ledger;
4. first-class reservations;
5. part vs stock-position separation;
6. bin/location/quality dimensions;
7. numbered migrations;
8. idempotency keys for consequential commands;
9. durable job/outbox worker;
10. provider/connector interfaces;
11. declarative action permission/scope policy;
12. API schema/error/idempotency contract;
13. compensation/reversal pattern;
14. server-local regression suite and recovery checks.

### P1 — after foundation

1. released BOM/ECN/document modules;
2. WO/build allocation;
3. lot/serial genealogy;
4. quality control points/NCR;
5. EDA provider/import staging;
6. RF test evidence graph;
7. external-object sync ledger;
8. settlement/economics event model;
9. reporting read models/KPI registry;
10. packaged provider implementations.

### P2 — business volume dependent

1. generalized multi-step workflow engine;
2. advanced WMS route/removal policies;
3. wave/cluster picking;
4. large-scale cache/lock infrastructure;
5. PostgreSQL migration;
6. richer plugin packaging;
7. advanced AI agents.

## 25. Explicit over-engineering boundary

| Idea | Why peers use it | Inventory Lite decision now |
|---|---|---|
| Microservices | organizational/scale isolation | **Do not adopt**; modular monolith first |
| Kafka/general event bus | huge distributed event volume | **Do not adopt**; DB outbox/jobs sufficient |
| Redis as mandatory infrastructure | cache/locks/queues at scale | **Do not require** until measured need |
| Generic BPM/workflow designer | arbitrary enterprise processes | **Do not build**; explicit domain state machines |
| Generic low-code model builder | framework/platform business | **Do not build** |
| Full accounting/GL | ERP suite scope | **Integrate/export** rather than rebuild |
| HR/payroll/project ERP | broad enterprise scope | **Out of scope** |
| Shop-floor MES scheduler | complex factories | **Later only if real production requires it** |
| Wave/cluster WMS | high-volume picking | **Later, volume-triggered** |
| GraphQL migration | large composable commerce API | **No need**; governed REST is sufficient |
| Third-party plugin marketplace | mature ecosystem | **Later only after stable extension contracts** |
| Offline multi-master inventory | field/offline-first operations | **Avoid unless explicit conflict semantics are funded** |

## 26. Target reference architecture

```text
                         PC / Mobile / Integrations
                                  |
                         Versioned domain API
                                  |
+----------------------------------------------------------------+
|                       Modular Monolith                         |
|                                                                |
| Identity | Catalog | Inventory/WMS | Purchasing | Commerce     |
| Pricing  | Fulfilment | Manufacturing | Quality | Aftersales   |
| Integrations | Automation | Reporting                          |
+----------------------------------------------------------------+
          |              |                    |
   primary DB       durable job/outbox     artifact store
          |              |
 stock ledger       independent worker
 reservation        systemd/cron/timer
 revisions               |
          |          external providers
          |          marketplace/carrier/AI/EDA/equipment
          v
 reporting/read projections
```

The design intentionally keeps local invariants in one database transaction while isolating slow/remote work through durable jobs.

## 27. Acceptance against task requirement

This synthesis explicitly covers:

- plugin/provider patterns;
- domain module ownership;
- workflow/state-machine patterns;
- event/job/outbox patterns;
- permission/action policy;
- reporting/read models;
- migration/versioning;
- API contracts;
- customization/extension seams;
- portable ideas versus premature complexity.

No required execution path depends on GitHub Actions.

## 28. Core recommendation

Borrow the **discipline** of mature open-source ERP/WMS/electronics/commerce systems without inheriting their full size.

The right Inventory Lite evolution is:

```text
large but useful monolith
 -> explicit domain-owned modular monolith
 -> authoritative stock/reservation/revision state
 -> durable worker + provider boundaries
 -> manufacturing/traceability/economics modules
 -> scale infrastructure only when measured constraints require it
```

This gives the company most of the architectural benefits of mature ERP systems while preserving the current product's lightweight deployment and operator-focused speed.