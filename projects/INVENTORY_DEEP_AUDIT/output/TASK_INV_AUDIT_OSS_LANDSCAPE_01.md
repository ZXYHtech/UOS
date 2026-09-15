# TASK_INV_AUDIT_OSS_LANDSCAPE_01 — Open-source inventory / ERP / WMS / electronics / commerce landscape

## 1. Purpose

This landscape is not a replacement shortlist. It is an evidence pool for deciding what Inventory Lite should:

- implement itself;
- borrow as a design pattern;
- integrate through APIs/plugins;
- deliberately not build;
- or, only if scale eventually justifies it, delegate to a larger external ERP / commerce / manufacturing system.

Research refresh date: **2026-09-11**.

Current Inventory Lite audit snapshot: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

## 2. Executive conclusion

No single open-source project is a perfect model for the target business of **electronics product R&D + component inventory + procurement + light manufacturing + warehouse execution + multi-channel e-commerce + sales + after-sales**.

The strongest pattern is a composite benchmark:

- **InvenTree + Part-DB** for electronic part / supplier / manufacturer / stock / BOM semantics.
- **ERPNext + Odoo Community + Dolibarr** for integrated purchasing, inventory, manufacturing, sales and business workflows.
- **OpenBoxes** for warehouse / stock movement discipline.
- **Tryton** for strict modular domain boundaries and workflow design.
- **OpenPnP** as a downstream SMT / machine integration reference rather than an ERP replacement.
- **Saleor + Medusa** for modern channel / API / webhook / extensible commerce architecture.
- **iDempiere / Apache OFBiz / metasfresh** as larger-system references for scalability, extensibility and mature enterprise domain decomposition, but they are likely too heavy to use as the immediate product model for Inventory Lite.

The current strategic default should remain **incremental modularization + selective feature absorption + adapter integration**, not a big-bang rewrite or wholesale migration.

## 3. Candidate landscape

| System | Category | Current activity evidence | License | Architecture / strongest pattern | Relevance to Inventory Lite | Primary caution |
| --- | --- | --- | --- | --- | --- | --- |
| InvenTree | Parts / inventory / BOM / orders / builds | Official org showed core updated Jul 30 2026; 1.4.0 changelog Jun 24 2026 | MIT | Python/Django backend, REST API, plugin ecosystem, mobile app; strong low-level stock and part tracking | **Very High** — closest benchmark for electronics-oriented stock, parts, supplier/manufacturer links, BOM/build and plugin APIs | Not a full accounting/CRM/e-commerce ERP; should not be treated as complete business OS |
| Part-DB | Electronic component inventory | Current docs/repo active in 2026 | AGPL-3.0-or-later | Symfony/PHP + modern API stack; electronic component metadata, inventory and category-centric UX | **Very High** for MPN/manufacturer/supplier/parameter/datasheet/location ideas | AGPL implications make direct code copying undesirable without license review; use conceptual/model reference |
| ERPNext | Full ERP / manufacturing | Official repo active; current GitHub page shows large ongoing community | GPL-3.0 | Frappe full-stack Python/JS framework; accounting, procurement, stock, order management, manufacturing, subcontracting, projects/assets | **Very High** for end-to-end procurement→stock→manufacturing→sales→cost/accounting process reference | Much broader/heavier than Inventory Lite; avoid reproducing framework-scale complexity prematurely |
| Odoo Community | Modular ERP / WMS / manufacturing / commerce | Official branch 19.0; >200k commits visible on current repo | LGPL-3.0 for core Community repository (module licenses must be checked individually) | Highly modular app/add-on architecture; strong WMS, manufacturing, CRM, e-commerce and UI workflows | **Very High** for UX patterns, search/actions, modular apps, state-driven workflows, extensibility | Community vs Enterprise feature/licensing boundary must be checked per feature; framework is large |
| Dolibarr | SME ERP / CRM | Official repo updated Sep 10 2026 in current GitHub org view | GPL-3.0-or-later | PHP modular ERP; products, warehouses, inventory, lots/serials, BOM, manufacturing orders, sales, purchasing, tickets | **High** — good lightweight integrated-SME comparison | Some domain sophistication is below ERPNext/Odoo; direct GPL code reuse requires license review |
| Tryton | Modular ERP framework | Official GitHub mirror updated May 10 2026 | GPL-3.0 | Python modular packages, strict domain separation, strong accounting/stock/purchase/sale/production building blocks | **High** for architecture, module boundaries, state machines and clean model separation | Less polished consumer UX; GitHub is a mirror of canonical Tryton sources |
| OpenBoxes | WMS / supply-chain inventory | Latest release v0.9.7-hotfix1 Apr 23 2026 | EPL-1.0 | Grails/Groovy + React-oriented stack; warehouse movements, shipments, stock and low-resource reliability | **High** for warehouse movement discipline, receiving/shipping, stock status and audit concepts | Healthcare origin means some workflows are domain-specific; not electronics/manufacturing-native |
| OpenPnP | SMT manufacturing equipment | Official project updated Jul 3 2026; project describes itself as stable and under heavy development | GPL-3.0 | Java desktop machine-control ecosystem for SMT pick-and-place | **High as integration target**, not as ERP — useful for component matching, feeders, placement jobs, production trace bridge | Machine-control domain is specialized; should be connected through an adapter, not merged into business core |
| iDempiere | Enterprise ERP / CRM / MFG / SCM / POS | Official org core updated Jul 27 2026 | GPL-2.0-or-later | Java/OSGi enterprise suite; application dictionary and plugin-oriented extension model | **Medium-High** for mature enterprise process/domain references, MRP and extensibility | Heavy implementation/administration footprint for current small-team target |
| Apache OFBiz | ERP / commerce framework | Current Apache docs list active `release24.09` and Java 17 development path | Apache-2.0 | Java entity/service framework with extensible ERP/e-commerce plugins | **Medium-High** for entity/service decomposition, order/fulfilment/commerce architecture | More framework than finished small-team product; high learning/implementation cost |
| metasfresh | ERP for industry/trade | Official org core updated Jul 31 2026 | GPL-2.0 family in distribution repositories; exact component license must be checked | Java + PostgreSQL, REST API, React/Redux web UI, large monorepo | **Medium** for scalable trade/manufacturing workflow and API/UI separation reference | Large enterprise codebase; public release/version signals are less straightforward than active commit stream |
| Saleor | Headless commerce | Official core updated Sep 10 2026; current releases visible Sep 2026 | BSD-3-Clause | Python/Django GraphQL-native headless commerce, apps, webhooks, extension points, commerce-as-code | **High for e-commerce/channel architecture**, not ERP | Does not solve manufacturing/warehouse master-data needs; cloud/open-source boundaries should be evaluated separately |
| Medusa | Modular commerce framework | Official org/core active Sep 10 2026 | MIT core; identified Enterprise components have separate commercial terms | TypeScript commerce modules, workflows, integrations, B2B/DTC/marketplace primitives | **High for adapter/workflow/module patterns** and future multi-channel order integration | Open-core boundary; commerce-first rather than ERP/manufacturing |

## 4. Detailed relevance notes

### 4.1 InvenTree — highest-priority technical benchmark

Why it matters:

- Explicit part-centric model rather than generic retail SKU only.
- Strong stock item tracking and hierarchical locations.
- Supplier/manufacturer relationships fit electronic component sourcing.
- BOM/build/order structures are closer to physical electronics production than ordinary e-commerce inventory tools.
- REST API + plugin system provides a concrete model for keeping the core small while enabling EDA, sourcing, forecasting and external integration.
- Official ecosystem includes mobile and forecasting/order-history plugins.

What Inventory Lite should study deeply:

1. Part vs stock-item separation.
2. Manufacturer Part / Supplier Part modeling.
3. Part parameters/templates and metadata.
4. BOM lines, build orders and build outputs.
5. Stock status, batch/serial ownership and location hierarchy.
6. Purchase/Sales/Return order model separation.
7. Plugin hooks and background task APIs.
8. Label/report template model.
9. API bulk update and import patterns.

Source evidence:
- https://github.com/inventree/InvenTree
- https://inventree.org/about/
- https://github.com/inventree/InvenTree/blob/master/CHANGELOG.md

### 4.2 Part-DB — strongest component-master-data reference

Why it matters:

Part-DB explicitly targets **electronic components**, so it should be used to challenge Inventory Lite's current generic material model. Key concepts to investigate include manufacturer data, component categories, parameters, attachments/datasheets, storage locations and supplier information.

Recommended use:

- borrow data-model and UX ideas;
- compare component-field completeness;
- do not copy AGPL implementation code without deliberate license/legal review.

Source evidence:
- https://github.com/Part-DB/Part-DB-server
- https://docs.part-db.de/

### 4.3 ERPNext — end-to-end business-process benchmark

ERPNext is particularly useful for testing whether Inventory Lite can grow from stock execution to a connected operating system. Its public feature model explicitly spans accounting, procurement/order management, stock, manufacturing, subcontracting, assets and projects.

Study:

- Item and warehouse ledger semantics.
- Purchase Request / Purchase Order / Receipt / Invoice separation.
- Material Request / stock transfer patterns.
- BOM + Work Order + Job Card / operation concepts.
- Material consumption and subcontracting.
- batch / serial traceability.
- valuation and landed cost.
- role/workflow/audit integration.

Use it as a **process completeness benchmark**, not as a target for one-to-one cloning.

Source evidence:
- https://github.com/frappe/erpnext

### 4.4 Odoo Community — UX + modular application benchmark

Odoo's repository describes a suite of integrated open-source apps spanning CRM, e-commerce, warehouse, project, accounting, POS, HR and manufacturing.

Study:

- add-on/module boundaries;
- menu/action/search/filter architecture;
- list/form/kanban state transitions;
- WMS location/routes/picking concepts;
- manufacturing work-order concepts;
- extension rather than core patching;
- activity/chatter-style operational history where appropriate.

Inventory Lite should borrow the **interaction grammar** and module isolation principles much more than Odoo's overall implementation scale.

Source evidence:
- https://github.com/odoo/odoo
- https://github.com/odoo/odoo/blob/19.0/LICENSE

### 4.5 Dolibarr — useful lightweight integrated-business comparison

Dolibarr currently advertises stock/warehouse, barcodes, batches/lots/serials, BOM, manufacturing orders, sales, purchasing, shipping, customer invoices and ticketing in one modular SME system.

This makes it especially useful to ask: which capabilities can remain simple without becoming a full enterprise implementation?

Source evidence:
- https://github.com/Dolibarr/dolibarr

### 4.6 Tryton — architecture discipline benchmark

Tryton is valuable less for UI imitation and more for how it decomposes business capabilities into modules. Inventory Lite's huge `services.py`, `server.py`, PC `app.js` and mobile `app.js` should be compared against Tryton's domain/module boundaries before deciding how to split the codebase.

Source evidence:
- https://github.com/tryton/tryton

### 4.7 OpenBoxes — warehouse execution benchmark

OpenBoxes is a focused stock movement / WMS reference. Its healthcare roots are not directly transferable, but its receiving, warehouse movement, shipment tracking and low-resource operational reliability are relevant.

Inventory Lite should compare:

- receiving state and discrepancy handling;
- stock status/quarantine ideas;
- movement auditability;
- replenishment concepts;
- picking/shipping separation;
- stock card/history usability.

Source evidence:
- https://github.com/openboxes/openboxes

### 4.8 OpenPnP — manufacturing-machine integration benchmark

Inventory Lite already contains an `OpenPnP物料搜索匹配移植说明.md`. The next audit should go beyond search matching and evaluate a clean production adapter boundary:

`Inventory/BOM revision -> production job -> machine program/job reference -> feeder/component usage -> completion/exception -> material consumption/trace evidence`.

OpenPnP should remain an **external production system/device adapter**, not a source of ERP truth.

Source evidence:
- https://github.com/openpnp/openpnp
- https://openpnp.org/

### 4.9 iDempiere — mature enterprise workflow reference

Its current project description explicitly covers ERP/CRM/MFG/SCM/POS. It is relevant for later-stage requirements such as accounting integration, enterprise workflows, extensibility and mature manufacturing/SCM abstractions.

Use it as a high-complexity upper-bound reference.

Source evidence:
- https://github.com/idempiere/idempiere
- https://idempiere.org/source-code/

### 4.10 Apache OFBiz — service/entity architecture benchmark

OFBiz is a useful architecture reference because it separates business entities/services/plugins and supports ERP + commerce domains. The Apache project currently documents separate framework/plugins repositories and a stable release branch.

Best use: study extensible service boundaries, order/party/product/facility concepts and plugin packaging.

Source evidence:
- https://ofbiz.apache.org/developers.html
- https://ofbiz.apache.org/source-repositories.html

### 4.11 metasfresh — scaled trade/manufacturing system reference

The current public project presents a Java/PostgreSQL ERP with REST API and React/Redux web frontend, aimed at industry/trade. Active 2026 commits indicate it remains a useful large-system reference.

Study only where scale requires it: event/API boundaries, large data operation patterns and separation of backend/web frontend.

Source evidence:
- https://github.com/metasfresh/metasfresh

### 4.12 Saleor — modern headless/channel architecture reference

Saleor is not an inventory/manufacturing replacement. Its value is modern commerce architecture:

- GraphQL API;
- apps/integrations;
- many webhooks;
- channel model;
- extension mount points;
- configuration-as-code concepts.

For Inventory Lite, the lesson is to make marketplace/platform integrations adapters around stable internal order/inventory contracts rather than embedding Taobao-specific rules throughout the core.

Source evidence:
- https://saleor.io/open-source
- https://github.com/saleor/saleor

### 4.13 Medusa — commerce modules/workflow reference

Medusa's current public description emphasizes modular commerce building blocks, extensibility and B2B/DTC/marketplace use cases. Its architecture is relevant to future platform adapters, workflow orchestration and feature modules.

Source evidence:
- https://github.com/medusajs/medusa

## 5. Cross-system pattern matrix

Legend: `+++` primary benchmark, `++` strong secondary, `+` useful reference, `-` not a main reason to study.

| Capability | InvenTree | Part-DB | ERPNext | Odoo | Dolibarr | Tryton | OpenBoxes | OpenPnP | iDempiere | OFBiz | metasfresh | Saleor | Medusa |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Electronic component master data | +++ | +++ | ++ | + | + | + | - | ++ | + | + | + | - | - |
| BOM / build | +++ | + | +++ | +++ | ++ | ++ | - | + | +++ | ++ | +++ | - | - |
| MRP / production | ++ | - | +++ | +++ | ++ | ++ | - | +++ machine side | +++ | ++ | +++ | - | - |
| Warehouse execution | +++ | ++ | +++ | +++ | ++ | ++ | +++ | - | +++ | ++ | +++ | + | + |
| Procurement | ++ | + | +++ | +++ | +++ | +++ | ++ | - | +++ | ++ | +++ | - | - |
| Sales / CRM | ++ | - | +++ | +++ | +++ | +++ | - | - | +++ | ++ | +++ | ++ | ++ |
| E-commerce channels | - | - | + | +++ | + | + | - | - | + | +++ | + | +++ | +++ |
| Plugin / extension model | +++ | ++ | +++ | +++ | ++ | +++ | + | ++ | +++ | +++ | ++ | +++ | +++ |
| Modern API-first integration | +++ | ++ | ++ | ++ | + | + | + | + | + | ++ | ++ | +++ | +++ |
| Lightweight SME fit | ++ | ++ | ++ | + | +++ | ++ | ++ | specialized | - | - | - | ++ commerce | ++ commerce |

## 6. What to borrow first

### Tier A — should influence near-term Inventory Lite design

1. **InvenTree** — part / stock item / manufacturer / supplier / BOM / build / plugin model.
2. **ERPNext** — procurement, stock ledger, manufacturing and traceability process completeness.
3. **Odoo Community** — UX conventions, modular apps, actions/search/batch workflows.
4. **Part-DB** — electronics-specific component fields and documentation/parameter management.
5. **Dolibarr** — practical SME-level integration of stock + sales + purchasing + BOM/MO + support.
6. **Saleor / Medusa** — modern adapter/event/webhook/channel architecture for e-commerce.

### Tier B — use for specialized design decisions

7. **OpenBoxes** — WMS receiving/movement/shipping/replenishment discipline.
8. **Tryton** — code/domain decomposition and workflow boundaries.
9. **OpenPnP** — SMT machine/job/component integration boundary.

### Tier C — enterprise upper-bound references

10. **iDempiere**.
11. **Apache OFBiz**.
12. **metasfresh**.

They should prevent reinvention of mature enterprise concepts, but should not drive near-term complexity unless Inventory Lite's company/process scale requires it.

## 7. Licensing boundary

The audit must distinguish **idea/pattern comparison** from **source-code reuse**.

Low-friction code-study references include permissively licensed systems such as InvenTree (MIT), Saleor (BSD-3-Clause), Apache OFBiz (Apache-2.0) and Medusa core (MIT), though dependencies/components still require their own checks.

Copyleft systems such as ERPNext, Dolibarr, Tryton, OpenPnP, iDempiere and Part-DB have GPL/AGPL family obligations. The safe default for this project is:

- cite and study behavior/data models;
- independently implement desired behavior in Inventory Lite;
- use APIs/adapters where appropriate;
- do not paste or mechanically port source code until a dedicated license-compatibility review says it is acceptable.

Odoo requires module-by-module care because Community core and ecosystem modules can have different licenses. Medusa is open-core, so Enterprise-identified materials must not be assumed to share the core MIT license.

## 8. Implications for the rest of the audit

The following follow-up tasks should use this landscape as evidence:

1. Component/master-data audit → InvenTree + Part-DB.
2. BOM/revision/MRP/manufacturing audit → InvenTree + ERPNext + Odoo + Tryton.
3. Warehouse audit → OpenBoxes + ERPNext + Odoo + InvenTree.
4. Procurement/cost audit → ERPNext + Dolibarr + Tryton + Odoo.
5. E-commerce/channel audit → Saleor + Medusa + Odoo.
6. Architecture/modularity audit → Tryton + InvenTree plugins + OFBiz + Medusa modules.
7. SMT/production integration audit → OpenPnP + InvenTree.
8. Final gap matrix → benchmark against **capability patterns**, not raw feature counts.

## 9. Strong recommendation for Inventory Lite

Do **not** choose one project and imitate it wholesale.

The likely best target architecture is a **small modular business core** with:

- electronics-grade material/part master data;
- inventory as an auditable movement/availability model;
- purchase/sales/manufacturing documents as explicit state machines;
- BOM/revision/change-control separation;
- serial/lot genealogy for finished RF/electronic products;
- background jobs/rules/AI around stable services;
- platform/SMT/EDA/accounting systems connected through adapters;
- PC/mobile clients sharing one API contract and permission model.

Whether that conclusion survives detailed source analysis is deliberately left for the later gap and target-architecture tasks.
