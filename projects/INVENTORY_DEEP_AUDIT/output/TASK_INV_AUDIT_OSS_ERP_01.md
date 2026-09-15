# TASK_INV_AUDIT_OSS_ERP_01 — Current Open-source ERP Deep Benchmark

## 0. Scope and freshness

Research date: **2026-09-11**.

Inventory Lite evidence remains pinned to `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Benchmark systems:

- ERPNext / Frappe;
- Odoo Community;
- Dolibarr;
- Tryton.

This benchmark is not a recommendation to replace Inventory Lite with one of these systems. Its purpose is to extract proven domain and extension patterns relevant to a small electronics/RF company.

## 1. Current maintenance / license snapshot

| System | Current evidence as of 2026-09-11 | License evidence | Primary architectural character |
|---|---|---|---|
| ERPNext | GitHub release list shows active v15 and v16 lines; latest-labelled release observed `v15.121.2` on 2026-09-09 and v16 releases in the `16.34.x` line | GPL-3.0 | Python/JS Frappe document framework, broad integrated ERP |
| Odoo Community | Official documentation and source branch are on 19.0 | LGPL-3 | Python modular ERP framework with very broad domain modules |
| Dolibarr | Official release table lists `24.0.0` on 2026-08-20 | GPL family (project distribution; verify exact file before code reuse) | PHP modular ERP/CRM, pragmatic module/hook/trigger ecosystem |
| Tryton | 8.0 line released 2026-04-20 and actively patched; PyPI identifies 8.0.9 as newer/current in August 2026 | GPL-3.0-or-later | Python modular business platform, strong model/workflow discipline |

### Important licensing boundary

This report recommends **patterns**, not source-code copying. Inventory Lite must independently review license compatibility before reusing code. In particular GPL/AGPL obligations differ materially from permissive licenses, and Odoo Community/Enterprise feature availability must not be inferred solely from generic Odoo product documentation.

## 2. ERPNext — strongest lesson: submitted business documents + integrated stock/manufacturing ledger

### Current evidence

Official ERPNext/Frappe sources show:

- ERPNext remains actively released across v15/v16 lines;
- ERPNext code is GPL v3;
- Frappe automatically exposes document resources through REST APIs and supports whitelisted RPC methods;
- ERPNext manufacturing centers around BOM, Work Order, Job Card, Workstation, Production Planning, Quality and Inventory;
- official BOM documentation states a submitted BOM cannot simply be edited; users cancel/duplicate and submit another version-like business document;
- multi-level BOM, manufacturing operations, scrap/secondary items and quality-inspection requirements are first-class concepts;
- stock terminology includes Serial Number, Batch, Stock Ledger Entry and Stock Reconciliation.

### What Inventory Lite should learn

#### A. Submitted document immutability

ERPNext's document lifecycle is a strong precedent for:

```text
Draft -> Submitted/Released -> Cancelled/Superseded
```

rather than allowing authoritative BOM/PO/receipt/work-order records to be edited freely after execution.

Inventory Lite should borrow the **principle**, not Frappe's exact DocType implementation.

#### B. One stock movement vocabulary

ERPNext treats a Stock Ledger Entry as the common material-movement evidence created by several source documents. Inventory Lite already has `inventory_logs`; its target should similarly make every authoritative physical/ownership/state change resolve to one ledger contract.

#### C. Manufacturing documents are not generic adjustments

ERPNext's Work Order and Stock Entry separation illustrates the same conclusion reached in W3: production reservation/transfer/consumption/output require explicit documents and state transitions.

#### D. Framework-generated API / metadata

Frappe exposes CRUD around metadata-driven DocTypes. Inventory Lite should not recreate all of Frappe, but it can borrow:

- declarative field metadata;
- consistent validation/permission hooks;
- generated list/detail schemas;
- common audit fields;
- common API behavior.

This would reduce repeated hand-written CRUD in giant server/client files.

### What not to copy now

- full accounting/HR/project breadth;
- generic low-code document designer;
- the full Frappe framework runtime;
- enterprise-style configuration surface before business processes stabilize.

Inventory Lite's advantage is a narrower RF/e-commerce workflow and simpler deployment.

## 3. Odoo Community — strongest lesson: explicit routes, operation types and manufacturing flow composition

### Current evidence

Odoo 19 official documentation describes:

- manufacturing orders;
- one-, two- and three-step manufacturing;
- multi-level BOMs and kits;
- work centers and work-order dependencies;
- scrap, manufacturing backorders, split/merge and unbuild;
- lot/serial manufacturing and lifecycle traceability;
- subcontracting;
- replenishment through reordering rules, make-to-order and master production schedule;
- inventory lot/serial tracking and traceability reports.

Odoo 19 source is LGPLv3. The 19.0 developer docs also introduce an External JSON-2 API, while older XML-RPC/JSON-RPC APIs are scheduled for eventual removal.

### What Inventory Lite should learn

#### A. Warehouse operation types / routes

Odoo's ability to represent:

```text
pick components -> manufacture -> store finished goods
```

as distinct stock operations is directly useful. Inventory Lite should model movement purpose/state explicitly rather than rely on warehouse names or free-text movement reasons.

#### B. Configurable process depth

Odoo supports simple one-step manufacturing and more controlled multi-step flows. This is highly relevant to a small RF company:

- simple prototype build can use a short path;
- controlled production can add picking, quality and finished receipt;
- system should not force maximum process complexity on every product.

#### C. Lot/serial as a product policy

Odoo configures tracking per product rather than assuming every item is serialized. This matches W3's risk-based `NONE / LOT / SERIAL` recommendation.

#### D. Replenishment mechanisms remain distinct

Reordering rule, MTO and MPS are separate concepts. Inventory Lite should similarly distinguish:

- simple min/cover replenishment;
- order/project-driven demand;
- manufacturing MRP;
- forecast planning.

### What not to copy now

- full route/rule engine complexity;
- broad Shop Floor/MES surface;
- every Odoo model/warehouse operation type;
- edition-specific features without checking Community availability;
- Odoo's broad accounting/business suite when Inventory Lite only needs integration boundaries.

## 4. Dolibarr — strongest lesson: extension without core edits

### Current evidence

Dolibarr's official release table lists 24.0.0 dated 2026-08-20. Its developer documentation exposes:

- modular application features;
- ModuleBuilder for rapid module development;
- REST API module;
- **Triggers** for business CRUD/status events;
- **Hooks** as program extension points;
- custom modules that can add APIs, UI and logic without rewriting core files.

The Hooks documentation explicitly states the purpose is to add custom behavior without modifying core code, simplifying upgrades.

### What Inventory Lite should learn

#### A. Stable extension seam

This is one of the most important lessons for the current source architecture.

Instead of adding every new feature to `server.py`, `services.py` and `app.js`, create stable extension seams:

```text
domain command
 -> domain event
 -> registered handler/plugin
```

and UI extension slots where genuinely needed.

#### B. Event versus UI hook distinction

Dolibarr separates business-event triggers from more general hooks. Inventory Lite should make the same conceptual distinction:

- domain event = durable/business semantic;
- UI/render extension = presentation;
- integration outbox = external side effect.

Do not use one generic callback mechanism for all three.

#### C. Module packaging

Future optional domains such as advanced CRM, accounting connector, supplier data providers or AI tools can be modules with declared dependencies and migrations.

### What not to copy now

- arbitrary runtime hooks everywhere;
- unrestricted plugin code with full database access;
- a low-code module generator before core domain boundaries are clean.

Inventory Lite first needs internal modules; a third-party plugin ecosystem can come later.

## 5. Tryton — strongest lesson: small composable modules and business-model rigor

### Current evidence

Tryton 8.0 was released 2026-04-20 and remains actively patched. Official documentation has separate modules for:

- stock;
- stock lot;
- production;
- quality;
- sale;
- sale opportunity;
- purchasing and other business domains.

The stock-lot module provides batch traceability and quantity/location tracking. The quality module introduces control points and inspections. The production module defines BOM and production orders. Tryton 8.0 server release notes include a REST API in addition to RPC capabilities. The server package is GPL-3.0-or-later.

### What Inventory Lite should learn

#### A. Domain modules with explicit dependencies

Tryton's architecture demonstrates that an ERP does not need microservices to be modular.

Target Inventory Lite package structure can remain one deployable application:

```text
inventory/
purchasing/
orders/
manufacturing/
quality/
crm/
after_sales/
pricing/
integrations/
automation/
```

Each module owns models/services/routes/migrations/tests and depends on explicit lower-level contracts.

#### B. Optional capability layers

Stock-lot is an optional module layered on stock. That is a useful precedent for risk-based traceability: basic quantity inventory should not become unusable simply because some products need lots/serials.

#### C. Quality control points

Tryton's control-point idea supports a generic model where inspections are triggered at defined business operations instead of hard-coding separate quality logic into every receipt/work-order screen.

### What not to copy now

- the entire Tryton framework/desktop-client model;
- maximum module granularity;
- generic enterprise configurability before workflows are known.

## 6. Comparative capability view

Legend: `Strong` means the benchmark has a mature first-class concept; it does not mean every feature is in the same open-source edition or equally suitable for Inventory Lite.

| Capability | ERPNext | Odoo 19 | Dolibarr | Tryton 8 | Inventory Lite direction |
|---|---|---|---|---|---|
| Inventory ledger | Strong | Strong | Moderate/Strong | Strong | Strengthen one authoritative ledger |
| Warehouses/locations | Strong | Strong | Moderate | Strong | Fix stock identity at bin/state level |
| Purchase/receipt | Strong | Strong | Strong | Strong | Current base good; add source/quality/MRP |
| BOM | Strong | Strong | Available/modular | Strong | Typed revisioned sales/EBOM/MBOM |
| Work orders | Strong | Strong | More limited/module-dependent | Strong | Add lightweight WO spine |
| MRP/replenishment | Strong | Strong | More limited than ERPNext/Odoo | Modular | Time-phased planning after stock-state fix |
| Lot/serial | Strong | Strong | Available | Strong via stock-lot | Risk-based traceability |
| Quality | Strong | Strong product suite | More limited/module-dependent | Strong modular concept | Quality-state + inspection/NCR |
| CRM/sales | Strong | Strong | Strong | Strong modules | Lightweight technical CRM |
| Accounting | Strong | Strong ecosystem | Strong SME focus | Strong modules | Keep integration boundary, not rebuild now |
| Extensibility | Frappe apps/hooks | Odoo modules | Modules/hooks/triggers | Modules | Internal modular monolith first |
| API | REST/RPC | JSON-2 + legacy RPC | REST module | REST/RPC | Stable versioned domain API |

## 7. Most portable architecture patterns

### Pattern 1 — authoritative business documents

From ERPNext/Odoo/Tryton:

```text
Draft document
 -> validate/approve/release
 -> execute stock/financial effects
 -> immutable history
 -> reversal/cancel/supersession
```

Apply to PO receipt, shipment, transfer, WO, quality disposition, RMA and controlled documents.

### Pattern 2 — stock ledger beneath source documents

A document owns business intent; ledger events own quantity/state evidence.

Do not make balance columns the only history.

### Pattern 3 — process complexity is configurable

Do not force every item through full manufacturing/quality/traceability. Configure policy by product/material/site.

### Pattern 4 — domain modules, not microservices

All four peers demonstrate broad modularity in one business platform. Inventory Lite should split source ownership without introducing network boundaries.

### Pattern 5 — extension/event seams

Use stable domain events, integration outboxes and registered modules instead of direct cross-module calls scattered through handlers.

### Pattern 6 — metadata-driven consistency

Borrow limited metadata patterns for:

- common status/lifecycle fields;
- permission declarations;
- configurable parameters;
- forms/list schemas;
- automation trigger definitions.

Do not build a generic no-code ERP builder.

## 8. Architecture decision for Inventory Lite

The benchmark reinforces the audit's existing direction:

```text
Do not replace Inventory Lite.
Do not copy a full ERP.
Do not split into microservices.

Instead:
1. harden the stock/reservation ledger;
2. split code into domain modules;
3. introduce released business-document state machines;
4. layer optional manufacturing/quality/traceability capabilities;
5. use durable events/outboxes for automation/integration;
6. preserve simple operator workflows;
7. integrate accounting rather than rebuilding a general ledger.
```

This preserves Inventory Lite's current advantage—small-team, purpose-built commerce/warehouse workflows—while importing the architectural discipline proven by larger ERP systems.

## 9. Concrete ideas to borrow first

### P0

1. ERPNext-style submit/release/cancel immutability for consequential documents.
2. Odoo-style separation of simple vs multi-step manufacturing flow.
3. Tryton-style modular domain packages with declared dependencies.
4. Dolibarr-style stable event/extension seams that avoid core edits.
5. common stock ledger contract beneath all documents.
6. risk-based lot/serial policy.
7. quality control points attached to business operations.
8. metadata/declarative route permission and state-transition registry.

### P1

1. configurable routing/operation types;
2. generated API/schema metadata for repetitive CRUD;
3. modular optional functions for quality/CRM/advanced analytics;
4. application-level plugin/provider interfaces;
5. explicit upgrade/migration compatibility contract.

### Avoid for now

1. general accounting suite;
2. HR/payroll/project ERP breadth;
3. generic low-code application builder;
4. microservices/event-bus infrastructure;
5. enterprise shop-floor scheduling complexity;
6. arbitrary third-party code execution inside core process.

## 10. Sources

Current-source references consulted on 2026-09-11:

- ERPNext releases: https://github.com/frappe/erpnext/releases
- ERPNext license: https://frappe.io/erpnext/license-trademark
- Frappe REST API: https://docs.frappe.io/framework/user/en/guides/integration/rest_api
- ERPNext BOM: https://docs.frappe.io/erpnext/bill-of-materials
- ERPNext manufacturing: https://docs.frappe.io/erpnext/manufacturing
- Odoo 19 Manufacturing: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/manufacturing.html
- Odoo 19 Replenishment: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment.html
- Odoo 19 lot tracking: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/product_management/product_tracking/lots.html
- Odoo 19 license: https://github.com/odoo/odoo/blob/19.0/LICENSE
- Odoo 19 JSON-2 API: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
- Dolibarr releases: https://wiki.dolibarr.org/index.php/Releases
- Dolibarr REST API: https://wiki.dolibarr.org/index.php/Module_Web_Services_REST
- Dolibarr ModuleBuilder: https://wiki.dolibarr.org/index.php/Module_ModuleBuilder
- Dolibarr Hooks: https://wiki.dolibarr.org/index.php/Hooks_system
- Dolibarr Triggers: https://wiki.dolibarr.org/index.php/Triggers
- Tryton server releases: https://docs.tryton.org/latest/server/releases.html
- Tryton production: https://docs.tryton.org/latest/modules-production/index.html
- Tryton stock: https://docs.tryton.org/latest/modules-stock/
- Tryton stock lots: https://docs.tryton.org/latest/modules-stock-lot/
- Tryton quality: https://docs.tryton.org/latest/modules-quality/index.html
- Tryton RPC: https://docs.tryton.org/latest/server/topics/rpc.html
- Tryton server package/license metadata: https://pypi.org/project/trytond/

## 11. Acceptance signals

- current versions/releases are dated rather than assumed from model memory;
- license and edition caveats are explicit;
- comparison separates observed peer capability from recommended Inventory Lite scope;
- at least four ERP systems are compared across inventory, purchase, manufacturing, BOM/MRP, sales, APIs and extensibility;
- recommendations identify portable patterns and explicitly reject over-engineering;
- no recommendation requires GitHub Actions.

## 12. Core recommendation

The strongest shared lesson from ERPNext, Odoo, Dolibarr and Tryton is **not feature count**. It is disciplined modular business objects: submitted/released documents, a shared stock ledger, explicit process states, optional modules and stable extension seams. Inventory Lite should adopt those patterns selectively while keeping its deployment and user experience much smaller than a general ERP.