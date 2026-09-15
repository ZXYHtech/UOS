# TASK_INV_AUDIT_ROADMAP_01 — 0–3–6–12–24 Month Product & Technical Roadmap

## 0. Roadmap intent

This roadmap sequences the deep-audit recommendations without a big-bang rewrite.

The governing order is:

```text
Protect existing behavior
 -> establish stock/data/security truth
 -> establish engineering configuration truth
 -> establish manufacturing/quality truth
 -> automate commerce/planning/economics
 -> optimize analytics/AI/scale
```

Calendar bands are planning horizons, not promises. A stage advances only when its measurable gate is met.

Required tests, jobs, scheduling, backup and production correctness remain independent of GitHub Actions.

## 1. North-star outcome at 24 months

Inventory Lite should evolve into a lightweight operating backbone capable of supporting:

- multi-channel e-commerce orders and stock publication;
- precise warehouse/bin execution;
- electronics part/MPN/AVL management;
- released EBOM/MBOM and controlled engineering change;
- work orders and material planning;
- lot/serial genealogy;
- RF/electrical test evidence and quality release;
- supplier/procurement control;
- technical CRM, sample and RMA workflows;
- standard/actual cost and channel contribution margin;
- exception-first management reporting;
- deterministic rules plus assistive AI;
- simple deployment with measured path to PostgreSQL/scale later.

The system should remain purpose-built rather than expanding into HR/payroll/general accounting/storefront CMS.

## 2. Phase 0 — Immediate stabilization (0–4 weeks)

### Objective

Make current behavior reproducible and stop architecture debt from increasing while larger migrations are prepared.

### Technical work

1. create one repository-local release/verification entry point;
2. freeze representative deterministic fixture databases;
3. inventory all stock-changing and externally replayable commands;
4. introduce schema version and numbered migration framework;
5. add DB integrity/orphan/preflight checks;
6. establish backup-to-temp restore verification;
7. add server/action correlation IDs;
8. define route/action policy metadata shape;
9. fix `margin_percent` naming/formula semantics;
10. security quick wins: CSP/security headers, secret masking review, upload/path checks, default-credential deployment check.

### Product/UX work

- add clear action receipts for critical stock/order operations;
- remove ambiguous destructive confirmation text;
- document online vs legacy offline client authority;
- avoid adding new business domains to giant files unless behind new module boundaries.

### Measurable outcomes

- fresh checkout can run a documented local verification command;
- current core/auth/client/OCR tests remain green;
- at least representative old DB fixtures migrate reproducibly;
- a test backup restores into a separate DB and passes integrity/smoke checks;
- every known stock-changing command has an owner, transaction boundary and replay-risk classification;
- margin/markup regression tests distinguish the formulas.

### STOP / GO gate

**GO** only if current business behavior is reproducible enough to detect regressions.

**STOP** structural data migration if backup/restore and fixture migration cannot be proven locally.

## 3. Phase 1 — Foundation hardening (month 1–3)

### Objective

Build the infrastructure and stock kernel needed by every later feature.

## 3.1 Domain/source modularization foundation

Extract shared primitives first:

- DB/migrations;
- API errors/response schema;
- auth/scope/action policy;
- idempotency;
- audit;
- jobs/outbox;
- provider interfaces.

Then begin low-risk domain extraction:

- pricing/cost;
- procurement;
- backup/settings;
- catalog categories/resources;
- integrations/notifications.

Do not redesign all UI simultaneously.

## 3.2 Durable job/outbox platform

Generalize the good OCR pattern into reusable persisted jobs:

- claim/lease;
- retry classes;
- next retry;
- dead-letter/manual review;
- idempotency;
- result/error evidence;
- worker health.

Runtime:

```text
inventory-web.service
inventory-worker.service
systemd timer / cron for scheduled enqueue/maintenance
```

## 3.3 Stock kernel v1

Introduce target stock concepts behind migration/feature flags:

- stock position by warehouse/location/state;
- reservation object;
- movement operation/idempotency key;
- compensating reversal;
- reconciliation between old balance and new projection during transition.

First business path to adopt reservation: confirmed sales orders/shipments.

## 3.4 Global search/identifier registry

Extract current mature material matching into a shared service:

- internal code;
- aliases;
- barcode/QR;
- model/MPN later;
- duplicate scan-code prevention;
- explainable match rank.

### Measurable outcomes by month 3

- new job framework can survive worker restart without duplicate execution;
- same business-operation key cannot post stock twice;
- two competing orders cannot both reserve the same insufficient ATP;
- same material can be represented in more than one bin/state in the new model;
- current shipment flow works through reservation without losing existing scan/reversal behavior;
- route/action matrix tests auth + permission + warehouse scope + state + idempotency;
- backup health and worker health are observable.

### STOP / GO gate

Do not automate channel stock publication or begin MRP until ATP/reservations reconcile correctly under concurrency tests.

## 4. Phase 2 — Engineering configuration control (month 3–6)

### Objective

Turn generic materials/BOM/resources into a controlled electronics engineering foundation.

## 4.1 Electronics part master

Implement:

```text
Internal Part
 -> Manufacturer Part / MPN
 -> Supplier Part / SKU
 -> typed parameters
 -> lifecycle/compliance
 -> aliases/barcodes
```

Maintain provenance for externally imported distributor data.

## 4.2 AVL/substitutes

Add:

- approved/conditional/rejected states;
- applicability/effectivity;
- qualification reason/evidence;
- priority/preferred status;
- no silent substitution from parametric similarity.

## 4.3 Revisioned BOM

Separate:

- sales/kit BOM;
- EBOM;
- MBOM.

Add:

- header/revision;
- line identity;
- reference designators;
- quantity/UOM;
- variant/optional/DNF;
- release status/effective dates;
- based-on relationship from MBOM to EBOM.

## 4.4 ECN/ECO and controlled documents

Minimum viable controlled change:

```text
change request
 -> impact/where-used
 -> approval
 -> new draft revision
 -> release
 -> supersede old revision
```

Controlled documents/firmware/test specs gain:

- document number;
- revision;
- status;
- checksum;
- applicability;
- effective/superseded relation.

## 4.5 EDA staging

Build safe import flow:

```text
EDA export
 -> normalize MPN/refdes/value/package
 -> deterministic match
 -> unresolved review
 -> draft EBOM
 -> diff
 -> release
```

### Measurable outcomes by month 6

- one internal part can link multiple approved suppliers without losing MPN identity;
- parametric search works without parameters becoming substitution authority;
- released EBOM is immutable;
- MBOM explicitly records source EBOM revision;
- refdes is preserved;
- change impact/where-used can be reviewed before release;
- released WO/test later can reference exact document/firmware revision;
- EDA import cannot silently rewrite released production BOM.

### STOP / GO gate

Do not build production planning on mutable project BOM or commerce kit BOM. Manufacturing proceeds only once one released MBOM path is proven end-to-end.

## 5. Phase 3 — Manufacturing, quality and traceability MVP (month 6–9)

### Objective

Create a small, auditable manufacturing spine rather than a full MES.

## 5.1 Work order

Minimum lifecycle:

```text
Draft
 -> Released
 -> Material Reserved
 -> In Progress
 -> Partially Completed
 -> Completed
with Hold/Cancel/Close paths
```

Release freezes product/MBOM revision.

## 5.2 Material execution

Support:

- requirement snapshot;
- reserve/allocate;
- kit/pick;
- issue;
- overissue with reason;
- return;
- scrap;
- output receipt;
- partial completion;
- cancellation disposition.

## 5.3 Quality stock state

At minimum:

- pending inspection;
- accepted;
- quarantine;
- rejected;
- rework;
- scrap.

Quality state must affect ATP/MRP/pick.

## 5.4 IQC/NCR

Implement:

- receipt inspection;
- partial acceptance/rejection;
- configurable inspection plan;
- NCR;
- disposition/MRB-lite;
- supplier link;
- rework/retest.

## 5.5 Lot/serial genealogy

Risk-based policy:

- none;
- lot;
- serial.

Trace:

```text
supplier receipt/lot
 -> stock position
 -> WO issue
 -> finished lot/serial
 -> shipment/customer
```

### Measurable outcomes by month 9

- one released WO can reserve, issue, return/scrap and receive output without generic inventory adjustment;
- quarantine stock never becomes allocatable by accident;
- selected finished serial can trace back to consumed lot(s);
- cancelled/reversed production events preserve history;
- WO remaining qty and partial output reconcile;
- production transactions survive retry without duplicate movement.

### STOP / GO gate

Do not claim manufacturing traceability until at least one representative RF module serial is traceable from receipt through build to shipment using actual system records.

## 6. Phase 4 — Test evidence, subcontract and RMA (month 9–12)

### Objective

Close the product-quality lifecycle from incoming component to shipped unit and aftersales.

## 6.1 RF/electrical test system

Implement:

- test procedure/spec revision;
- limit-set revision;
- test run;
- scalar measurements;
- raw artifacts such as Touchstone/spectrum/NF data;
- pass/fail from deterministic limits;
- operator;
- equipment/calibration;
- firmware/config/test-script version.

Rendered screenshots/PDFs become evidence views, not sole source data.

## 6.2 Final quality release

Finished serial/lot can be ship-able only when required tests/inspections are valid.

## 6.3 Subcontract/external WIP

Support:

- company-owned material sent out;
- external WIP location/state;
- supplier accountability;
- consumed/returned/scrapped variance;
- processing cost;
- received output quality gate.

## 6.4 RMA/repair

Implement serial-aware lifecycle:

```text
request/authorization
 -> return received
 -> inspect/diagnose
 -> warranty decision
 -> repair/rework/retest
 -> return/replacement/refund
 -> close
```

Physical return, financial refund and restock eligibility remain separate.

### Measurable outcomes by month 12

- shipped serial links exact product revision, firmware and required test evidence;
- test result can be regenerated/read from structured/raw source, not only image;
- expired/unqualified test equipment is visible and policy-controlled;
- RMA serial timeline reaches original shipment/build/test evidence;
- subcontract material balance reconciles sent = consumed + returned + approved loss/scrap + variance.

### STOP / GO gate

Do not automate final release solely from AI interpretation or uploaded screenshot presence. Deterministic required-test/status rules must be authoritative.

## 7. Phase 5 — Planning, omnichannel and economics (month 12–18)

### Objective

Use now-trustworthy stock/manufacturing data to automate planning and commerce.

## 7.1 MRP v1

Daily time-bucket planning is sufficient initially.

Inputs:

- released MBOM dependent demand;
- WOs/customer/project demand;
- qualified on-hand;
- active reservations;
- open POs/transfers/WO receipts;
- lead time/MOQ/order multiple;
- safety policy;
- yield/scrap assumptions where justified.

Outputs are recommendations first, not silent POs/WOs.

## 7.2 Omnichannel worker

Evolve platform integration to:

- external-object ledger;
- cursor/checkpoint;
- overlap/replay safety;
- durable retries;
- outbound fulfilment outbox;
- ATP-based stock publication;
- refund/return reconciliation;
- periodic full reconciliation.

## 7.3 CRM/quote/sample

Add lightweight technical sales flow:

- inquiry/customer;
- requirements;
- quote revisions;
- technical attachments;
- sample/loan/gift;
- conversion/follow-up.

## 7.4 Channel economics

Capture additive order economics:

- revenue;
- discounts;
- product COGS basis;
- marketplace fee;
- payment fee;
- freight;
- seller-borne tax;
- refund/return/replacement cost.

Add settlement import/reconciliation.

## 7.5 Standard/actual manufacturing cost

After WO actual material events exist:

- standard cost versions;
- actual material/labor/overhead/subcontract/scrap;
- variance;
- unit/product profitability.

### Measurable outcomes by month 18

- MRP recommendation explains demand/supply pegging;
- channel published stock equals documented ATP policy;
- connector retries after restart without duplicate canonical orders;
- remote/local fulfilment mismatch appears in reconciliation queue;
- completed historical order retains its cost/economic snapshot;
- contribution margin by SKU/channel is reproducible;
- quote revision that converted to order remains immutable.

### STOP / GO gate

Do not auto-create procurement or production orders until recommendation precision and operator override reasons have been measured over a representative period.

## 8. Phase 6 — Management intelligence and safe automation (month 18–24)

### Objective

Turn reliable transactional data into management leverage rather than adding more manual reports.

## 8.1 Reporting read models

Create metric lineage registry and views for:

### Daily

- exceptions;
- overdue work;
- stock shortage;
- quality blocks;
- sync failures.

### Weekly

- fulfilment cycle;
- purchase lead time;
- production throughput;
- first-pass yield/rework;
- stockouts;
- RMA/support trend.

### Monthly

- revenue/contribution;
- inventory turns/aging;
- cash tied in stock;
- product/channel/customer profitability;
- supplier performance;
- forecast/MRP accuracy;
- product portfolio scorecard.

## 8.2 Deterministic rules automation

Introduce controlled rules for:

- replenishment suggestion;
- shortage routing;
- overdue PO;
- quarantine aging;
- connector retry/escalation;
- repeated OCR/master-data correction;
- RMA recurrence;
- slow stock review;
- product/lifecycle review.

Every rule declares safety class and audit behavior.

## 8.3 AI Copilot

Prioritize assistive use cases:

- permission-aware natural-language query;
- part/SKU candidate matching;
- EDA/document extraction;
- support/RMA summarization;
- anomaly explanation;
- purchase/MRP explanation;
- management report drafting.

AI only calls approved read/action tools and cannot directly write DB business state.

### Measurable outcomes by month 24

- every management KPI exposes source, time basis and freshness;
- safe rules reduce manual exception checking without hiding failures;
- AI answers can link the records/metrics used;
- high-risk actions still require deterministic validation/approval;
- product portfolio decisions can combine real contribution, stock health, support burden, supplier/lifecycle risk and inquiry demand.

## 9. Scale decision checkpoint — around month 12 and month 24

Do not migrate infrastructure based on roadmap age alone.

Measure:

- DB size;
- write-lock wait;
- p95/p99 API latency;
- concurrent writers;
- worker queue age/depth;
- trace/test event volume;
- backup/restore time;
- reporting query impact;
- server CPU/memory/disk;
- number of active sites/users.

### PostgreSQL GO conditions

Consider migration when measured SQLite contention, HA/PITR requirements or data/reporting volume justify it.

### PostgreSQL STOP conditions

Stay on SQLite if:

- contention is negligible;
- backups/restores meet business targets;
- one server remains appropriate;
- query latency is healthy;
- operational simplicity is more valuable than hypothetical scale.

## 10. Product-scope guardrails through all phases

Do not accidentally turn the roadmap into a generic ERP rebuild.

Remain out of scope unless a later explicit business case appears:

- HR/payroll;
- general ledger/accounting suite;
- storefront CMS/cart engine;
- generalized project-management suite;
- enterprise BPM designer;
- arbitrary third-party plugin marketplace;
- complex finite-capacity MES scheduler;
- automated warehouse MFC;
- generic data lake.

Integrate with specialist systems where that is cheaper and safer.

## 11. Rollout strategy for every major domain

Use the same controlled pattern:

```text
1. schema/migration behind feature flag
2. fixture/reconciliation tests
3. read-only visibility
4. limited pilot actor/product/warehouse
5. dual validation against current process
6. controlled write enablement
7. monitor exceptions and rollback path
8. expand scope
9. retire old path only after reconciliation
```

Avoid irreversible cutovers where a shadow/pilot approach is possible.

## 12. Decision cadence

At the end of each phase, review:

- defects/regressions;
- operator task time;
- stock reconciliation variance;
- exception volume;
- adoption of new workflow;
- data completeness;
- automation false-positive/override rate;
- infrastructure metrics;
- whether the next phase's prerequisites are actually true.

A roadmap date must never override a failed dependency gate.

## 13. Top outcome metrics by horizon

| Horizon | Primary outcomes |
|---|---|
| 0–1 month | reproducible tests/migrations/recovery/security baseline |
| 1–3 months | authoritative reservation/idempotency + stock-position foundation + durable jobs |
| 3–6 months | electronic part/AVL/released EBOM/MBOM/ECN/document control |
| 6–9 months | WO + quality state + lot/serial genealogy MVP |
| 9–12 months | RF test/calibration + final release + subcontract/RMA |
| 12–18 months | MRP + durable omnichannel + CRM + channel/actual cost economics |
| 18–24 months | executive read models + product intelligence + safe rules + AI Copilot |

## 14. Core recommendation

The roadmap deliberately delays the most attractive automation until the underlying truth is reliable.

The strategic order is:

```text
Correct state
 -> controlled workflow
 -> complete traceability
 -> reliable automation
 -> trustworthy analytics/AI
```

If this sequence is maintained, Inventory Lite can grow from a strong lightweight warehouse/e-commerce tool into an electronics R&D/manufacturing operating platform without a disruptive rewrite.