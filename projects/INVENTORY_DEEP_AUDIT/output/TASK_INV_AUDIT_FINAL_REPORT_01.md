# TASK_INV_AUDIT_FINAL_REPORT_01 — Inventory Lite Deep Audit & Strategic Evolution Report

## 0. Report identity

**Audit project:** `INVENTORY_DEEP_AUDIT`  
**Inventory Lite source pinned at:** `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`  
**Audit completion date:** 2026-09-11  
**Audit mode:** source/document/workflow architecture analysis; external repository remained read-only  
**Required-runtime constraint:** GitHub Actions is **not** accepted as a required test, scheduling, synchronization, backup, production-correctness or recovery dependency.

This report synthesizes all completed audit waves, including current-state source review, business-domain audits, electronics/manufacturing fit, commerce/aftersales, platform/security/reliability/UX, automation/AI, current open-source benchmarks and implementation planning.

---

# 1. Executive summary

## 1.1 Core conclusion

Inventory Lite is **worth evolving, not replacing**.

It already contains a meaningful operational core rather than a toy inventory application. The strongest existing areas are:

- order ingestion/confirmation;
- shipment-task execution;
- inter-warehouse transfer handling;
- OCR recognition with human confirmation and durable worker isolation;
- pricing lists/rules/revisions;
- procurement/receipt/landed-cost primitives;
- permissions and warehouse scope;
- inventory operation logging;
- mobile operator workflows;
- SQLite backup using the SQLite backup API;
- a substantial repository-local regression suite.

The system's main limitation is **not missing pages**. It is that several critical concepts needed by an electronics R&D/manufacturing/e-commerce company are not yet authoritative first-class business state.

The most important missing kernels are:

```text
1. Stock truth
   bin/location + quality/state + reservation + idempotent ledger

2. Engineering truth
   internal part + MPN + supplier part + AVL + revisioned EBOM/MBOM + ECN

3. Manufacturing truth
   work order + issue/return/scrap/output + WIP + lot/serial genealogy

4. Product-release truth
   controlled documents/firmware + RF/electrical test + equipment/calibration + final release

5. Commerce/economic truth
   replay-safe external-object sync + ATP publication + RMA + settlement/contribution economics

6. Operational truth
   numbered migrations + security hardening + recovery verification + observability/release gate
```

If these kernels are added in the correct order, Inventory Lite can become a highly capable, lightweight operating backbone for an RF/electronics business without becoming a generic heavyweight ERP.

## 1.2 Strategic recommendation

Adopt a **modular monolith**:

- one main deployable business application;
- one authoritative relational database;
- explicit domain packages;
- one durable DB-backed worker layer;
- provider/connector interfaces;
- stable domain APIs;
- deterministic local tests;
- server-owned schedules via systemd/cron/application worker;
- PostgreSQL only when measured constraints justify migration.

Do **not** perform a big-bang rewrite, and do **not** move to microservices now.

---

# 2. What was audited

The audit covered the system from six perspectives.

## 2.1 Current architecture and source truth

Reviewed:

- database schema/migrations;
- server/API/auth/scope;
- business services;
- PC/mobile/offline clients;
- OCR worker/recognition;
- platform integration;
- local tools/tests;
- deployment/backups;
- documentation-to-code truth alignment.

## 2.2 Core business operations

Reviewed:

- stock semantics;
- warehouses/locations;
- procurement;
- orders/fulfilment;
- transfers;
- master data;
- BOM/cost;
- pricing;
- imports/exports/backups;
- OCR/AI;
- platform connectors;
- dashboards;
- exceptions/audit logs.

## 2.3 Electronics R&D/manufacturing

Reviewed fit for:

- parametric components;
- MPN/manufacturer/supplier identity;
- AVL/substitutes;
- revision/ECN;
- EBOM/MBOM;
- prototype/sample stock;
- MRP;
- work orders;
- lot/serial genealogy;
- QC/NCR;
- test records;
- document control;
- subcontracting;
- actual manufacturing cost.

## 2.4 Commerce/sales/aftersales

Reviewed:

- omnichannel flows;
- CRM/quotation/sample;
- forecast/replenishment;
- returns/RMA;
- customer service;
- channel settlement/economics;
- product intelligence;
- management reporting.

## 2.5 Platform/UX/automation

Reviewed:

- scalability/concurrency;
- security/secrets;
- reliability/disaster recovery;
- testing/observability;
- desktop UX;
- mobile/offline sync;
- global search/scan;
- automation rules;
- AI Copilot opportunities.

## 2.6 Open-source benchmark

Current 2026 references included:

- ERPNext / Frappe;
- Odoo Community;
- Dolibarr;
- Tryton;
- InvenTree;
- Part-DB;
- OpenPnP;
- OpenBoxes;
- OpenWMS.org;
- Saleor;
- Medusa;
- Sylius.

The benchmark extracted design patterns rather than recommending wholesale replacement or code copying.

---

# 3. Current-state verdict by business area

The following 0–5 values are ordinal audit bands, not mathematical precision or operational certification.

| Area | Current fit | Verdict |
|---|---:|---|
| order ingestion / human confirmation | 4.0 | strong |
| shipment/fulfilment execution | 4.0 core | strong, but reservation gap matters |
| transfer workflow | 4.0 | strong relative to current scale |
| OCR worker + human review | 4.0–4.5 | one of the best technical areas |
| pricing engine | 3.5–4.0 | strong, margin terminology needs correction |
| procurement/receiving | 3.0 | useful foundation, electronics sourcing gaps |
| permissions / warehouse scope | 4.0 concept | strong model, route coverage maintainability risk |
| backup implementation | 4.0 DB mechanism / ~2 operational recovery | good backup primitive, weak recovery assurance |
| warehouse/bin execution | ~2.0 | location model not yet authoritative enough |
| reservation / ATP | ~1.5 | major scaling gap |
| electronic part master | ~2.0 | generic material model is useful but insufficient |
| controlled EBOM/MBOM/revision | 0.5–1.0 | major R&D/manufacturing gap |
| work order | ~0.5 | absent as first-class execution domain |
| MRP | ~1.0 | raw inputs exist, trustworthy planning does not |
| lot/serial genealogy | ~0.5 | major traceability gap |
| quality/NCR | 0.5–1.0 | major production-control gap |
| structured RF/electrical test | ~0.5 | attachments possible, evidence graph missing |
| RMA/repair | 0.5–1.0 | aftersales lifecycle incomplete |
| CRM/quotation | 1.0–1.5 | order-centric rather than customer-lifecycle-centric |
| channel contribution economics | ~1.0 | pricing exists; realized profitability does not |
| architecture maintainability | ~2.0 | good concepts, file-monolithic implementation |
| general durable job framework | ~1.0–2.5 | OCR precedent strong; generic platform missing |
| observability | ~1.5–2.0 | business logs better than technical telemetry |
| executive/product intelligence | ~1.0–2.0 | operational dashboard exists; strategic BI incomplete |

---

# 4. Business-fit verdict

## 4.1 E-commerce operations

### Verdict: **good current fit for operator-controlled low/moderate volume; not yet ready for aggressive automated omnichannel stock promise**.

Strong existing capabilities:

- normalized order adapter concept;
- real Taobao synchronization path;
- duplicate/review controls;
- formal shipment tasks;
- scan/logistics/stock deduction flows;
- platform sync status;
- reversal/audit patterns.

Critical missing capability:

**first-class reservation/ATP**.

Current behavior is closer to:

```text
check available stock
 -> later deduct stock
```

A scalable omnichannel model requires:

```text
confirm business commitment
 -> reserve ATP
 -> allocate exact stock
 -> pick/ship
 -> consume reservation
```

Without this, multiple open orders can compete for the same inventory even if final negative-stock protection is correct.

## 4.2 Electronics R&D

### Verdict: **useful generic foundation, insufficient configuration control**.

Useful current concepts:

- materials;
- categories;
- aliases;
- generic specifications;
- resources/attachments;
- project BOM lines;
- purchase history;
- cost/pricing.

Missing electronics-specific truth:

```text
Internal Part
 -> Manufacturer
 -> MPN
 -> Supplier Part
 -> AVL/Substitute
 -> Lifecycle/Compliance
 -> Typed Parameters
 -> Released BOM Revision
 -> ECN/ECO
```

The system should not rely on free-form `model`/specifications or generic project BOM rows for controlled production.

## 4.3 Manufacturing

### Verdict: **not currently sufficient as a controlled manufacturing system**.

A real manufacturing spine requires:

- released MBOM;
- work order;
- material reservation;
- kitting/issue/return/overissue/scrap;
- WIP;
- partial completion;
- finished output receipt;
- lot/serial genealogy;
- quality state;
- RF/electrical test release evidence;
- actual cost capture.

Adding only a “production order” screen would not solve the problem. The source-of-truth keys underneath it must exist first.

## 4.4 Sales / customer lifecycle

### Verdict: **strong order handling, weak pre-sales and aftersales continuity**.

Target lightweight flow:

```text
Inquiry
 -> technical requirements
 -> quotation revision
 -> sample/loan/gift
 -> order
 -> shipment/serial
 -> support case
 -> RMA/repair/retest/replacement
```

A small technical CRM is appropriate; a giant general CRM suite is not required.

## 4.5 Management / profitability

### Verdict: **operational visibility is useful; strategic profitability is incomplete**.

The current dashboard is better treated as an action board than a BI system.

Future management data should be built from reproducible source events:

- stock aging/turns;
- fulfilment cycle;
- supplier delivery/quality;
- production yield/scrap;
- RMA recurrence;
- channel contribution;
- SKU/product profitability;
- inquiry/conversion;
- lifecycle/supplier risk.

---

# 5. Strong findings that should be preserved

## 5.1 Human confirmation around probabilistic recognition

The OCR path correctly separates:

```text
machine recognition
 -> candidate structured data
 -> validation/duplicate checks
 -> human confirmation
 -> canonical business object
```

This is exactly the right pattern for future AI.

## 5.2 Durable OCR worker engineering

The OCR subsystem already demonstrates:

- database-backed task state;
- atomic claim;
- isolated child process;
- timeout;
- memory backpressure;
- interruption handling;
- derivative-image jobs.

This should become the template for a common job/outbox platform, not be discarded for a generic synchronous AI API.

## 5.3 Shipment task separated from order

This is a strong domain boundary. Keep it.

Future reservation, parcel and serial semantics should extend it rather than collapse order and warehouse execution together.

## 5.4 Reversal instead of history deletion

Existing shipment/transfer reversal direction is correct.

Standardize this principle across:

- inventory;
- production;
- quality;
- returns;
- settlement;
- cost corrections.

## 5.5 Pricing and price revision history

Current price-list/rule/revision concepts are valuable and should not be replaced by a generic ERP price field.

## 5.6 Server-side permissions and warehouse scope

The system has real backend authorization controls. UI permissions are not treated as the only boundary.

The next step is to make route coverage more declarative/testable, not redesign RBAC from zero.

## 5.7 Backup API choice

Using SQLite's backup API is a technically sound primitive for an active WAL database.

The missing part is independently scheduled, off-host, verified recovery.

---

# 6. Top risks

## Risk 1 — Stock promise can diverge from physical stock protection

`quantity_locked`/`quantity_on_transfer` fields do not by themselves prove authoritative reservation/in-transit semantics.

Impact:

- oversubscription;
- wrong channel ATP;
- wrong MRP supply;
- manual exception burden.

## Risk 2 — Stock identity is too coarse for a true WMS/manufacturing system

A material cannot naturally exist as independent balances across multiple bins/status/lot/serial dimensions if the balance identity is primarily warehouse/account level.

Impact:

- weak bin accuracy;
- weak quarantine semantics;
- weak traceability;
- limited scan execution.

## Risk 3 — No released engineering configuration baseline

Without authoritative revision/effectivity/refdes/AVL, the system cannot reliably answer what should be built.

## Risk 4 — Work order/manufacturing genealogy absent

No first-class WO spine means production material consumption, WIP, output and actual cost cannot be made trustworthy simply by adding reports.

## Risk 5 — Quality/test evidence is not first-class

For RF products, a screenshot/file attachment alone does not prove:

- which serial was tested;
- against which limit revision;
- with which firmware;
- using which calibrated equipment;
- whether the result authorized shipment.

## Risk 6 — PostgreSQL deployment file can create false confidence

The current PostgreSQL schema is materially behind the current SQLite runtime schema.

It must not be treated as production-equivalent.

## Risk 7 — Large central source files amplify future regression risk

The existing conceptual services are good, but physical code ownership is concentrated in large files.

Adding manufacturing/quality/CRM directly into those files would magnify review, testing and Agent-edit risk.

## Risk 8 — Security consequence grows with integration and AI

Important areas:

- bearer token in browser local storage increases XSS consequence;
- platform/AI credentials require stronger secret-at-rest policy;
- technical file uploads can create XSS/path/content risks;
- object/warehouse authorization must cover every new API/tool;
- backups contain sensitive operational/customer data.

## Risk 9 — Backup existence may be mistaken for recoverability

Recovery requires:

- scheduling proof;
- off-host redundancy;
- integrity checks;
- schema compatibility;
- restore rehearsal;
- RPO/RTO.

## Risk 10 — AI/automation can amplify bad source semantics

Automating replenishment, stock publication or substitution before reservation/revision/quality state is reliable would create faster errors, not better operations.

---

# 7. Open-source benchmark — what should be borrowed

## ERPNext / Frappe

Best lessons:

- submitted/released business-document discipline;
- common stock-ledger concept;
- integrated manufacturing/stock relationships;
- metadata/API consistency.

Do not copy the whole ERP framework or unrelated HR/accounting breadth.

## Odoo

Best lessons:

- configurable one/multi-step warehouse/manufacturing flows;
- routes/operation types;
- lot/serial policy;
- reservation/putaway/removal strategies;
- barcode-guided execution.

Do not copy full warehouse/MES complexity before volume requires it.

## Tryton

Best lesson:

- modular business domains in one integrated platform.

This strongly supports modular-monolith architecture.

## Dolibarr

Best lesson:

- stable extension hooks/triggers/modules that avoid repeated core edits.

Inventory Lite should first build internal modules/provider interfaces before a broad plugin ecosystem.

## InvenTree

Most relevant electronics benchmark.

Best lessons:

```text
Part != Stock Item
Build requirement -> allocate concrete stock -> consume -> output
```

Also strong for:

- MPN/supplier structure;
- parameters;
- substitutes;
- lot/serial/status;
- labels/API/plugins.

## Part-DB

Best lessons:

- component record as a knowledge hub;
- parametric/search/provider data;
- EDA integration;
- labels/barcodes;
- provenance/security concerns around rich component data.

## OpenPnP

Best lesson:

Machine execution is an **adapter boundary**, not inventory authority.

Inventory Lite should export controlled job/BOM/placement context and import execution evidence.

## OpenBoxes

Best warehouse lesson:

```text
receive -> staging/receiving bin -> putaway -> final bin
```

Also strong for stock movement state and reversal patterns.

## Medusa

Most directly relevant modern commerce architecture lesson:

```text
stocked
reserved
incoming
ReservationItem
```

Also valuable for:

- domain modules;
- workflows/compensation;
- provider interfaces;
- channel scope;
- pricing vs promotion;
- returns.

## Saleor / Sylius

Useful for:

- API-first channel boundaries;
- apps/extensions;
- explicit commerce state machines;
- security lessons around object-level authorization.

---

# 8. Target architecture

## 8.1 Recommended target

**Modular monolith + durable worker**.

```text
                 PC / Mobile / Integrations
                           |
                  Versioned domain API
                           |
+---------------------------------------------------------------+
|                     Modular Monolith                          |
| Identity | Catalog | Inventory | Warehouse | Purchasing       |
| Commerce | Fulfilment | BOM/ECN | Manufacturing | Quality     |
| Traceability/Test | Pricing/Cost | CRM/Aftersales             |
| Integrations | Automation | Reporting                         |
+---------------------------------------------------------------+
                |                         |
        Authoritative DB              durable jobs/outbox
                |                         |
   stock/reservation/revision          worker process
   workflow/economic ledgers               |
                                   external providers
                                   marketplace/AI/EDA/
                                   RF test/machine/carrier
```

## 8.2 Why not microservices

The current scale does not justify:

- distributed transactions;
- duplicated authentication;
- service discovery;
- network failure handling between every business domain;
- separate deployment/observability for many services.

The same domain boundaries can be created inside one codebase first.

## 8.3 Database direction

Keep SQLite until measured reasons justify PostgreSQL.

Before any DB migration:

- numbered migrations;
- backend-neutral business contracts;
- concurrency/idempotency tests;
- schema parity tests;
- data-copy rehearsal;
- cutover/reconciliation/fallback plan.

PostgreSQL is a future scale/HA tool, not a prerequisite for correct business semantics.

---

# 9. Core target data model

## 9.1 Part and engineering identity

```text
Internal Part
 ├─ Manufacturer Part / MPN
 ├─ Supplier Parts
 ├─ Typed Parameters
 ├─ Lifecycle/Compliance
 ├─ AVL/Substitutes
 ├─ Documents
 └─ BOM Where-used
```

## 9.2 Stock

```text
Stock Position
  material
  warehouse/bin
  quality/state
  lot/batch
  optional serial
  ownership/class
  receipt/build provenance
  quantity
```

Separate:

```text
physical/stocked
reserved
incoming
non-saleable/engineering
quarantine/rejected
ATP/nettable
```

## 9.3 Movement

Every consequential stock action posts through one movement contract with:

- business operation/idempotency key;
- source/destination state/location;
- material/lot/serial;
- quantity/UOM;
- source document;
- actor/time;
- reversal link.

## 9.4 BOM/configuration

```text
BOM Header
 -> Revision
    -> Lines (refdes, qty, UOM, variant/DNF)
```

Types:

- sales/kit;
- engineering;
- manufacturing.

MBOM explicitly references source EBOM revision.

## 9.5 Manufacturing

```text
Released MBOM
 -> Work Order
 -> Requirement/Reservation
 -> Allocation
 -> Issue/Return/Scrap
 -> Output
 -> Finished Lot/Serial
```

## 9.6 Quality/test

```text
Receipt/WO/Product Serial
 -> Inspection / NCR
 -> Test Spec + Limit Revision
 -> Test Run + Raw Data + Measurements
 -> Equipment/Calibration + Firmware
 -> Release/Disposition
```

## 9.7 Commerce/economics

```text
External observation
 -> Canonical Order
 -> Reservation/ATP
 -> Fulfilment
 -> Remote acknowledgement
 -> RMA/refund
 -> Settlement economic events
 -> Contribution profit
```

---

# 10. Top 20 recommendations

Ordered by dependency and risk rather than UI visibility.

1. **Redesign canonical stock identity** around location/bin/state/lot/ownership dimensions.
2. **Implement first-class reservations** for orders, then WO/project demand.
3. **Require idempotency keys** for all consequential stock/external replay commands.
4. **Standardize compensating reversals** instead of deleting executed history.
5. **Introduce numbered migrations + schema version + old-DB fixtures**.
6. **Create a local release gate** covering state transitions, concurrency, permission, migration and recovery.
7. **Harden security** around CSP/XSS, credentials, uploads, route scope and backup data.
8. **Generalize the OCR worker pattern** into one durable job/outbox platform.
9. **Split source ownership into domain modules** before adding more major domains.
10. **Create internal-part → manufacturer-part → supplier-part identity**.
11. **Add controlled AVL/substitute semantics** separate from parametric similarity.
12. **Implement revisioned released EBOM/MBOM with refdes/effectivity and ECN/ECO**.
13. **Add controlled documents/firmware/test-spec revisions with checksums/applicability**.
14. **Implement lightweight Work Order execution** with reserve/issue/return/scrap/output.
15. **Add quality stock states + IQC/NCR/MRB-lite**.
16. **Add risk-based lot/serial genealogy**.
17. **Build structured RF/electrical test evidence** tied to serial/lot/spec/firmware/equipment calibration.
18. **Implement MRP only after stock/reservation/released MBOM are authoritative**.
19. **Evolve platform connectors** into external-object + durable outbox/reconciliation + ATP publication.
20. **Add RMA/CRM/channel economics/reporting/rules/AI** only on top of the trusted core above.

---

# 11. Recommended implementation order

## Foundation gate

```text
Migrations + tests + security + recovery
            |
       Action policy
            |
     Idempotency/jobs
            |
      Stock kernel
```

## Engineering gate

```text
Part/MPN/Supplier Part
        |
    AVL/Substitute
        |
   EBOM/MBOM Revision
        |
   ECN + Documents
```

## Manufacturing gate

```text
Released MBOM
 -> WO
 -> Quality state
 -> Lot/Serial
 -> RF Test
 -> Final Release
```

## Planning/commerce gate

```text
Trusted inventory/manufacturing
 -> MRP
 -> Omnichannel ATP
 -> RMA
 -> Standard/Actual Cost
 -> Channel Economics
```

## Intelligence gate

```text
Complete event/economic data
 -> KPI read models
 -> Product Intelligence
 -> Rules Automation
 -> AI Copilot
```

---

# 12. 0–24 month roadmap summary

## 0–1 month — stabilize

- migration framework;
- deterministic fixtures/release command;
- backup restore verification;
- security quick wins;
- action/idempotency inventory;
- margin/markup fix.

## 1–3 months — stock/platform foundation

- modular shared primitives;
- durable jobs/outbox;
- stock positions;
- reservations;
- idempotent movement;
- global identifier/search/scan foundation.

## 3–6 months — electronics configuration

- part/MPN/supplier identity;
- typed parameters;
- AVL;
- EBOM/MBOM revisions;
- refdes;
- ECN/ECO;
- controlled docs/firmware;
- EDA staging.

## 6–9 months — manufacturing/quality MVP

- work order;
- kitting/issue/return/scrap;
- quality state;
- IQC/NCR;
- lot/serial genealogy.

## 9–12 months — test/release/aftersales

- structured RF/electrical tests;
- equipment/calibration;
- final release;
- subcontract/external WIP;
- RMA/repair/retest.

## 12–18 months — planning/commerce/economics

- MRP;
- durable marketplace synchronization;
- ATP publication;
- technical CRM/quote/sample;
- settlement economics;
- standard/actual manufacturing cost.

## 18–24 months — management intelligence

- KPI lineage/read models;
- product portfolio intelligence;
- safe rules automation;
- evidence-bound AI Copilot;
- scale decision based on real telemetry.

---

# 13. UX strategy

Do not prioritize cosmetic redesign.

The highest-value UX pattern is:

```text
Find/scan object
 -> see full context
 -> see next valid action
 -> scan/validate instead of retype
 -> commit through domain service
 -> receive audit receipt
 -> handle exception in place
```

## Desktop

Optimize for:

- search;
- comparison;
- saved views;
- batch preview;
- entity workspaces;
- engineering/management analysis.

## Mobile

Optimize for:

- task-first flow;
- source/destination location scan;
- item/lot/serial scan;
- immediate mismatch block;
- explicit network status;
- server-confirmed result.

## Offline

Current online static cache and independent local-data offline app are not the same capability.

Near-term recommendation:

- server-authoritative writes;
- cached assets/read data as appropriate;
- explicit failed/pending network state.

True offline multi-master writes require explicit conflict/version/idempotency design and should be a separate funded decision.

---

# 14. Automation strategy

The detailed backlog identified more than 60 concrete safe-rule opportunities.

Use four safety classes:

### A — notification only

No mutation.

### B — suggestion/draft

Human reviews before consequence.

### C — reversible low-risk automatic action

Only with idempotency/audit.

### D — consequential approval-required

Examples that should not be autonomous by default:

- stock movement;
- BOM release;
- substitute approval;
- quality release;
- refund/write-off;
- WO completion;
- below-floor price;
- destructive restore.

---

# 15. AI strategy

AI should be used where uncertainty is acceptable and review is possible:

- document/OCR extraction;
- candidate part/MPN matching;
- semantic search;
- anomaly explanation;
- support/RMA summary;
- purchase/MRP explanation;
- report drafting;
- knowledge retrieval.

AI should **not** independently establish:

- stock balance;
- reservation truth;
- released BOM revision;
- approved substitute;
- quality release;
- test pass/fail outside deterministic limits;
- settlement truth;
- refund/write-off;
- production completion.

AI action handoff must call the same domain service, permission, state and idempotency checks used by the ordinary application.

---

# 16. Reliability and deployment strategy

## 16.1 Required server processes

Recommended target:

```text
inventory-web.service
inventory-worker.service
```

Optional separate OCR worker may remain if isolation is operationally useful.

## 16.2 Scheduling

Use:

- systemd timers;
- cron;
- durable worker scheduled jobs.

Do not make GitHub Actions a scheduler for:

- backups;
- marketplace sync;
- MRP;
- report generation;
- recovery checks;
- alerts;
- production jobs.

## 16.3 Recovery

A backup is considered operational only after:

- integrity validation;
- schema compatibility check;
- isolated restore;
- application smoke test;
- recorded verification time/result.

At least one production copy should exist outside the primary host/storage failure domain.

---

# 17. Security priorities

## P0

1. CSP/security headers and XSS review, especially given browser bearer-token storage;
2. platform/AI secret-at-rest protection and masking;
3. default-account deployment gate;
4. file upload/path/content-type/size controls;
5. object/warehouse scope matrix for all mutations;
6. idempotency on replayable actions;
7. backup access/encryption/retention policy;
8. formula-injection-safe spreadsheet exports;
9. safe SVG/render/template handling;
10. rate/abuse limits for expensive auth/OCR/AI/sync endpoints where needed.

This is a static audit priority list, not a claim that every item is currently exploitable.

---

# 18. Testing/release strategy

Inventory Lite already has valuable local test assets. Preserve and organize them.

Target local release sequence:

```text
1. import/syntax checks
2. migration fixtures
3. domain/state-machine tests
4. inventory/cost invariant tests
5. idempotency/concurrency tests
6. auth/permission/object-scope matrix
7. connector replay/reconciliation tests
8. backup/restore drill
9. PC/mobile critical-flow checks
10. performance smoke benchmarks
```

One repository command should orchestrate these locally.

A CI system may invoke the same command, but correctness must not depend on one hosted CI provider.

---

# 19. What should explicitly NOT be built now

Avoid scope creep into:

- microservices;
- Kafka/general event bus;
- mandatory Redis;
- Kubernetes;
- generic BPM/workflow designer;
- generic low-code ERP builder;
- full accounting/general ledger;
- HR/payroll;
- storefront CMS/cart/payment orchestration;
- enterprise finite-capacity MES;
- automated warehouse MFC;
- wave/cluster picking before volume proves need;
- third-party plugin marketplace;
- autonomous high-risk AI agents.

These may be valid in other systems; they are not currently the highest-return investments here.

---

# 20. Facts vs inferences vs proposals

## 20.1 Confirmed source facts

Examples from the pinned source/audit evidence:

- the SQLite runtime schema is materially richer than the existing PostgreSQL schema file;
- current `inventory` identity does not make bin/location a full uniqueness dimension;
- `quantity_locked` and `quantity_on_transfer` exist, but core service evidence did not establish them as authoritative reservation/in-transit ledgers;
- current core search did not identify first-class work-order, lot/serial, calibration or subcontract domains;
- `CostService` recursively estimates BOM/purchase/labor/overhead cost but is not an actual WO accounting ledger;
- order/shipment/transfer/OCR/pricing/procurement/auth concepts are materially implemented;
- Taobao integration is materially implemented, while adapter maturity across other channels is uneven;
- OCR uses a durable worker architecture;
- local tools include meaningful core/auth/client/OCR/stress tests;
- online mobile PWA static caching is not the same as offline business synchronization;
- legacy `mobile-offline` keeps independent local business data and exports a package.

## 20.2 Audit inferences

Examples:

- omnichannel automation will become unsafe before reservation/ATP is authoritative;
- manufacturing screens without revision/WO/genealogy keys would create process appearance rather than control;
- source-file concentration will materially increase regression cost as new domains are added;
- SQLite can likely remain adequate for the next stage if transaction semantics are repaired and measured contention stays low;
- a modular monolith is a better fit than microservices for the current product shape.

These are reasoned conclusions, not direct source statements.

## 20.3 Proposed future design

Examples:

- stock-position/reservation/movement tables;
- internal-part/manufacturer-part/supplier-part hierarchy;
- revisioned EBOM/MBOM model;
- work-order/quality/test/RMA schemas;
- durable job/outbox framework;
- action-policy registry;
- order economics event model;
- KPI lineage registry;
- AI tool boundary.

These are recommendations and should be validated through implementation design/pilot testing before being treated as production facts.

---

# 21. Expected business outcomes if roadmap is executed

## Inventory / warehouse

- fewer oversubscription and misplaced-stock failures;
- faster scan-based operations;
- exact bin/status visibility;
- better count accuracy;
- clearer engineering/quarantine/WIP stock.

## R&D / engineering

- controlled MPN/AVL/BOM revisions;
- safer substitutes;
- faster EDA import/review;
- clear document/firmware release state;
- stronger where-used/change impact.

## Manufacturing / quality

- controlled material issue and WIP;
- serial/lot traceability;
- structured RF test evidence;
- faster root cause/RMA;
- actual scrap/yield/cost visibility.

## Purchasing

- better lead-time/source selection;
- MRP-based shortage visibility;
- supplier performance and quality context;
- less emergency procurement.

## E-commerce / sales

- safer channel ATP;
- durable platform synchronization;
- better quotation/sample follow-up;
- controlled refund/RMA;
- real channel contribution margin.

## Management

- less manual information assembly;
- better product portfolio decisions;
- clearer cash tied in stock;
- more trustworthy profitability;
- exceptions surfaced before they become customer problems.

---

# 22. Future vision

The most useful long-term vision is not “ERP replacement.”

It is a **purpose-built RF/electronics operating system** where one product can be followed through its complete lifecycle:

```text
Market inquiry
 -> quotation
 -> product/part engineering
 -> released EBOM/MBOM
 -> material planning/purchase
 -> receiving/IQC
 -> stock/bin/lot
 -> work order
 -> assembly
 -> RF/electrical test
 -> finished serial
 -> channel/order
 -> shipment
 -> customer
 -> RMA/repair
 -> profitability/product intelligence
```

At every step the system should answer:

- what object is this?
- what revision/state is authoritative?
- who changed it and why?
- which physical stock was involved?
- which test/evidence supports the decision?
- which customer/product/channel did it affect?
- what is the next valid action?

This is the differentiating value Inventory Lite can provide that a generic inventory package or generic ERP often cannot provide without substantial customization.

---

# 23. Final recommendation

## Keep

- current lightweight deployment philosophy;
- operator-first workflow mindset;
- shipment/transfer execution concepts;
- OCR durable worker + human review;
- pricing/procurement foundations;
- RBAC/warehouse scope;
- operation logs/reversal principles;
- repository-local testing culture.

## Repair first

- stock identity;
- reservations/ATP;
- idempotency;
- migrations;
- security hardening;
- recovery proof;
- source modularity.

## Build next

- electronics part/MPN/AVL;
- revisioned EBOM/MBOM/ECN/docs;
- work orders;
- quality/lot/serial;
- RF test evidence;
- MRP;
- durable omnichannel;
- RMA/CRM;
- standard/actual/channel economics.

## Optimize later

- product intelligence;
- advanced forecast;
- automated rules;
- AI Copilot;
- PostgreSQL/scale infrastructure when measurement supports it.

### Final verdict

**Inventory Lite already has enough operational substance to justify continued investment.** Its next step should not be feature accumulation. It should be a controlled transition from an effective small-team operational application into a modular, auditable system whose stock, engineering configuration, manufacturing, quality and economics are explicit first-class truth.

That path offers the highest probability of supporting e-commerce + electronics R&D + production + sales/aftersales while preserving the speed and simplicity that are already strengths of the current product.