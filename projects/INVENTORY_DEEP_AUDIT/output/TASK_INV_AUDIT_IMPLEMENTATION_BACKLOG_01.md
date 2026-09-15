# TASK_INV_AUDIT_IMPLEMENTATION_BACKLOG_01 — Implementation-ready Epics & Stories

## 0. Purpose

This backlog converts the audit roadmap into implementation packages that can be executed incrementally against Inventory Lite.

Pinned baseline remains:

`ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`

The backlog is intentionally ordered by dependency. New business modules should not be implemented on top of known-weak stock/revision/migration invariants merely because their screens are attractive.

Required validation and runtime jobs must be executable locally/on the server without GitHub Actions.

## 1. Epic E00 — Release safety, schema migration and recovery foundation

### Objective

Make every future structural change reversible, testable and reproducible.

### Stories

- **E00-S01** Add `schema_version` and numbered immutable migration runner.
- **E00-S02** Create representative old-database fixtures from known schema eras.
- **E00-S03** Add pre/post migration integrity and orphan checks.
- **E00-S04** Create one local `verify_release` command that runs deterministic server/domain/client tests.
- **E00-S05** Create restore-to-temporary-DB verification command.
- **E00-S06** Define full backup manifest: DB, attachments/artifacts, config metadata and checksums.
- **E00-S07** Add off-host backup copy hook/command and health record.

### Data changes

- `schema_migrations` or equivalent;
- backup verification/history metadata;
- optional deployment/runtime version metadata.

### API/UI touchpoints

- admin health/backup page shows last successful backup and last verified restore;
- no destructive restore without explicit confirmation and compatibility checks.

### Migration

First migration must adopt the current SQLite schema **without replaying old DDL destructively**. It should record current baseline version after verifying required objects.

### Tests

- upgrade every fixture to current schema;
- re-run migration is no-op;
- corrupt/incompatible backup rejected;
- restore copy boots and performs login/read/write smoke test.

### Rollout

Deploy before other major schema work.

### Acceptance

A fresh checkout and a restored backup can be verified with documented local commands.

### Operator decisions

- target RPO/RTO policy;
- off-host backup destination/retention;
- maintenance window expectations for destructive restore.

---

## 2. Epic E01 — Core modularization, action policy and durable jobs

### Objective

Create shared infrastructure that prevents every new feature from expanding `server.py`/`services.py` with bespoke permissions, retries and background loops.

### Stories

- **E01-S01** Extract common DB/error/API response helpers.
- **E01-S02** Create action registry metadata: auth, permission, scope, state, idempotency, audit.
- **E01-S03** Migrate representative high-risk routes to action wrapper.
- **E01-S04** Add `business_operation_id`/idempotency utility.
- **E01-S05** Generalize OCR-style DB-backed job claim/lease/attempt model.
- **E01-S06** Add worker CLI/service entry point.
- **E01-S07** Add job retry class, next-attempt, dead-letter/manual-review state.
- **E01-S08** Add outbox helper committed in same DB transaction as business state.
- **E01-S09** Add structured correlation IDs across request/action/job/external event.
- **E01-S10** Begin domain-module extraction with pricing/procurement/backup/integrations.

### Data changes

Suggested generic tables:

```text
jobs
job_attempts
outbox_events
business_operations / idempotency_records
```

### API/UI touchpoints

- admin job/failed-job inspection page later;
- existing APIs preserve behavior during extraction.

### Migration

Add infrastructure tables independently; migrate routes/domain code one path at a time.

### Tests

- two claims cannot own same job;
- worker restart leaves job recoverable;
- same idempotency key returns original result/no duplicate effect;
- wrong warehouse/permission/state is rejected;
- outbox exists iff business transaction commits.

### Rollout

Pilot with non-critical report/notification job, then platform sync.

### Acceptance

At least three distinct background workloads use one job framework without duplicating queue logic.

### Operator decisions

- default retry policy and dead-letter ownership;
- operational supervisor choice: systemd recommended, cron acceptable for enqueue-only jobs.

---

## 3. Epic E02 — Stock position, movement ledger and reservation kernel

### Objective

Make inventory semantics trustworthy enough for omnichannel, WMS, MRP and manufacturing.

### Stories

- **E02-S01** Define canonical stock dimensions: material, warehouse, bin/location, stock state, owner/class, lot/serial optional.
- **E02-S02** Add stock-position/balance projection table.
- **E02-S03** Add movement operation + movement-line ledger with idempotency key.
- **E02-S04** Add explicit compensating reversal relation.
- **E02-S05** Add first-class `stock_reservation` with purpose/reference/status.
- **E02-S06** Implement ATP calculation query/service.
- **E02-S07** Migrate order confirmation to reserve rather than only check stock later.
- **E02-S08** Consume/release reservation through shipment lifecycle.
- **E02-S09** Add reconciliation comparing old inventory balance to new projection during migration.
- **E02-S10** Retire direct balance writes not routed through Inventory domain.

### Data changes

Conceptual tables:

```text
stock_positions
stock_movement_operations
stock_movement_lines
stock_reservations
```

Stock status vocabulary must at least allow normal/engineering/quarantine/rejected/external-WIP separation, even if some states are activated by later epics.

### API/UI touchpoints

- inventory detail shows physical, reserved, ATP and state breakdown;
- order/shipment detail shows reservation reference;
- audit receipt links movement operation.

### Migration

- seed new positions from old balances;
- use deterministic synthetic default location/status only as migration marker, not fictional physical history;
- dual-reconcile while old model remains readable;
- never fabricate lots/serials for historical stock.

### Tests

- two simultaneous orders competing for 5 units cannot both reserve 4;
- repeated shipment command posts movement once;
- cancellation releases reservation;
- reversal restores correct state only once;
- same material can exist in multiple bins/statuses;
- ATP excludes quarantine/engineering states when activated.

### Rollout

Start one warehouse/order workflow, shadow-reconcile, then expand.

### Acceptance

Physical stock, reservation and ATP are explainable from durable records and survive retry/concurrency.

### Operator decisions

- initial default stock-status taxonomy;
- whether platform/account represents ownership, channel allocation or only commercial context;
- how legacy inventory without physical bin should be represented until counted/put away.

---

## 4. Epic E03 — Warehouse locations, receiving, putaway, scan and count

### Objective

Turn location metadata into reliable physical warehouse execution.

### Stories

- **E03-S01** Define warehouse→zone→bin/location hierarchy and status.
- **E03-S02** Add receiving/staging locations.
- **E03-S03** Add putaway task after PO/transfer/RMA receipt.
- **E03-S04** Add preferred-bin/location policy.
- **E03-S05** Extract unified material/location/order/serial scan resolver.
- **E03-S06** Enforce unique/collision-safe barcode/QR identifiers.
- **E03-S07** Add scan-first pick flow: task→source bin→item/lot/serial→qty.
- **E03-S08** Add count observation separate from adjustment.
- **E03-S09** Add variance review/reconciliation action.
- **E03-S10** Add cycle-count policy/schedule.
- **E03-S11** Add simple pick-path ordering.

### Data changes

- location hierarchy/type/policy;
- putaway tasks/lines;
- count observation/reconciliation metadata;
- identifier registry if needed.

### API/UI touchpoints

PC: workload/location/count planning.

Mobile: guided scan execution with immediate mismatch block.

### Migration

Map existing `warehouse_locations` into new hierarchy without assuming existing `inventory.location_id` is a complete physical truth.

### Tests

- wrong bin/item scan blocks action;
- putaway splits received qty across bins;
- count observation preserves expected and observed values;
- adjustment is compensating ledger event;
- duplicate scan code cannot silently resolve to wrong object.

### Rollout

Pilot labels/scan in one warehouse and selected high-frequency SKUs.

### Acceptance

A picker can complete a representative shipment without typing a material code and the system proves source bin + item + qty.

### Operator decisions

- physical bin coding convention;
- preferred label size/printer;
- blind vs assisted cycle counts;
- whether receiving staging is per shipment or shared zone initially.

---

## 5. Epic E04 — Electronics part master, parameters, MPN and AVL

### Objective

Create controlled electronic-component identity usable by engineering, purchasing and BOM workflows.

### Stories

- **E04-S01** Add manufacturer master.
- **E04-S02** Add manufacturer-part/MPN entity linked to internal part.
- **E04-S03** Add supplier-part entity linked to supplier + MPN/internal part.
- **E04-S04** Migrate generic `model`/supplier information into controlled fields where mapping is unambiguous.
- **E04-S05** Add typed parameter templates with units and searchable values.
- **E04-S06** Add lifecycle/compliance fields and evidence/provenance.
- **E04-S07** Add approved alternate/substitute relationship with status/effectivity.
- **E04-S08** Add component-centric workspace.
- **E04-S09** Add PartDataProvider interface with source/provenance.
- **E04-S10** Extend global search across internal code/MPN/supplier SKU/alias/parameters.

### Data changes

```text
manufacturers
manufacturer_parts
supplier_parts
parameter_templates
part_parameter_values
part_substitutes / approved_sources
```

### API/UI touchpoints

Material/Part workspace tabs:

- identity;
- parameters;
- suppliers;
- alternates;
- stock;
- BOM where-used;
- docs/lifecycle.

### Migration

Do not auto-convert every existing `model` string into MPN. Create review queue for ambiguous rows.

### Tests

- one internal part may have multiple suppliers;
- same MPN cannot silently map to conflicting manufacturer identities;
- parameter unit conversions/search are deterministic;
- parametric similarity cannot make an alternate approved.

### Rollout

Pilot on a representative set: IC, resistor/capacitor, RF MMIC, connector, PCB/finished product.

### Acceptance

A buyer/engineer can search MPN and reach one controlled internal part with sources/stock/BOM context.

### Operator decisions

- internal part-number convention;
- required parameter templates per component category;
- lifecycle vocabulary;
- AVL approval roles.

---

## 6. Epic E05 — Revisioned EBOM/MBOM, ECN/ECO and controlled documents

### Objective

Establish configuration control before production automation.

### Stories

- **E05-S01** Introduce typed BOM header: sales/engineering/manufacturing.
- **E05-S02** Add BOM revision lifecycle draft/review/released/obsolete.
- **E05-S03** Add line identity, qty/UOM, refdes, optional/DNF, variant and notes.
- **E05-S04** Add MBOM `based_on` EBOM revision.
- **E05-S05** Add release/effectivity model.
- **E05-S06** Add ECN/ECO/change request + impact/approval.
- **E05-S07** Add where-used query by exact revision.
- **E05-S08** Add EDA staging/import/match/diff flow.
- **E05-S09** Add controlled document/document revision model with hash.
- **E05-S10** Add firmware release metadata and hardware applicability.
- **E05-S11** Link test specification/procedure revisions.

### Data changes

```text
bom_headers
bom_revisions
bom_lines
engineering_changes
engineering_change_impacts
controlled_documents
controlled_document_revisions
firmware_releases
```

### API/UI touchpoints

- BOM compare/release page;
- ECN impact/approval page;
- document current/effective/superseded state;
- EDA unresolved-match review.

### Migration

Keep existing `material_bom` for sales-kit behavior during transition. Convert project BOMs into draft engineering BOMs only when semantics are known.

### Tests

- released revision cannot be edited;
- new revision preserves old where-used/history;
- BOM cycle prevention;
- EDA ambiguous match blocks release;
- WO later resolves exact released MBOM revision.

### Rollout

Start with one finished RF module and one simple assembly.

### Acceptance

A production user can answer: “Which exact BOM/drawing/firmware revision is currently released for this product?” without interpreting free text.

### Operator decisions

- revision naming scheme;
- approval roles;
- effective-date vs explicit serial/WO effectivity policy;
- required release-package files.

---

## 7. Epic E06 — Work order and manufacturing execution spine

### Objective

Add controlled production without creating a full MES.

### Stories

- **E06-S01** Add WO header/state machine and product/MBOM snapshot.
- **E06-S02** Generate material requirement lines from released MBOM.
- **E06-S03** Reserve/allocate qualified stock.
- **E06-S04** Add kitting/pick execution.
- **E06-S05** Post issue transaction to WIP.
- **E06-S06** Support controlled overissue with reason.
- **E06-S07** Support material return.
- **E06-S08** Support scrap transaction/disposition.
- **E06-S09** Support partial finished output receipt.
- **E06-S10** Support hold/cancel/close with remaining material disposition.
- **E06-S11** Capture basic operation/labor actuals where useful.

### Data changes

```text
work_orders
work_order_materials
work_order_operations
work_order_outputs
```

Movement truth remains in Inventory Kernel.

### API/UI touchpoints

- WO release/readiness;
- shortages/reservation;
- mobile kitting/issue/return;
- partial completion;
- audit timeline.

### Migration

No attempt to fabricate historical WOs from old cost/BOM records.

### Tests

- release freezes revision;
- repeated issue/output is idempotent;
- reservation/issue/return reconcile;
- partial completion leaves correct remaining requirement;
- cancellation cannot orphan reserved/WIP stock.

### Rollout

Pilot on manual/low-risk assembly before high-volume SMT integration.

### Acceptance

One representative product can be built from released MBOM to finished receipt using only controlled WO material transactions.

### Operator decisions

- WO numbering;
- whether labor actual capture is manual, standard-only or time-based initially;
- WIP location semantics;
- overissue/scrap approval thresholds.

---

## 8. Epic E07 — Quality, lot/serial genealogy and RF test evidence

### Objective

Prove what material/product was used, whether it passed required controls and how it reached the customer.

### Stories

- **E07-S01** Add risk-based trace policy per material/product.
- **E07-S02** Add stock lot/batch entity and receipt capture.
- **E07-S03** Add finished/component serial entity where required.
- **E07-S04** Add genealogy links from issued stock to WO output.
- **E07-S05** Add quality stock-state transitions.
- **E07-S06** Add inspection order/result model.
- **E07-S07** Add IQC partial accept/reject.
- **E07-S08** Add NCR + disposition/MRB-lite.
- **E07-S09** Add test specification/limit-set revision.
- **E07-S10** Add test run/measurement/raw artifact model.
- **E07-S11** Add equipment/calibration records.
- **E07-S12** Capture firmware/test script/config provenance.
- **E07-S13** Add final quality release rule.
- **E07-S14** Add backward/forward genealogy browser.

### Data changes

```text
stock_lots
serial_numbers
genealogy_links
inspection_orders
inspection_results
ncr_cases
test_specs / limit_sets
test_runs
test_measurements
equipment
calibration_records
```

### API/UI touchpoints

- receive with lot/date-code;
- QC queue;
- serial/product timeline;
- test upload/station API;
- trace report.

### Migration

Legacy stock/shipments remain explicitly untraced where evidence does not exist. Never invent lot/serial genealogy.

### Tests

- quarantine cannot allocate/ship;
- serial uniqueness;
- one issued lot can trace to finished serials;
- failed required test blocks release;
- historical test retains old limit revision;
- calibration status recorded with test run.

### Rollout

Enable serial/test policy first for finished RF modules; lot trace selected critical components next.

### Acceptance

Given a shipped serial, system can show product revision, build, consumed traced components where required, firmware, test result and customer shipment.

### Operator decisions

- which product/component classes require lot vs serial;
- required final tests by product family;
- calibration warning vs hard-block policy;
- retention period for raw RF data.

---

## 9. Epic E08 — Procurement planning, MRP and subcontract

### Objective

Convert stock/engineering/manufacturing truth into controlled supply planning.

### Stories

- **E08-S01** Extend supplier parts with lead time/MOQ/order multiple/preferred status.
- **E08-S02** Add demand/supply planning views.
- **E08-S03** Implement released-MBOM explosion.
- **E08-S04** Add MRP run snapshot and recommendation lines.
- **E08-S05** Add pegging/explanation to source demand/supply.
- **E08-S06** Add recommendation review/override reason.
- **E08-S07** Generate draft PO/WO only after explicit approval.
- **E08-S08** Add supplier on-time/price/quality metrics.
- **E08-S09** Add subcontract order/external-WIP flow.
- **E08-S10** Reconcile consigned sent/consumed/returned/scrap/variance.

### Data changes

```text
planning_policies
mrp_runs
mrp_recommendations
subcontract_orders
subcontract_material_lines
```

### API/UI touchpoints

- planning workbench;
- shortage pegging;
- supplier comparison;
- subcontract WIP/reconciliation.

### Migration

No auto-generation of historical planning records.

### Tests

- MRP excludes quarantine/non-nettable stock;
- uses released effective MBOM only;
- open PO/WO supply not double-counted;
- recommendation replay is stable;
- subcontract ownership remains company asset where appropriate.

### Rollout

Advisory-only MRP for a period before any draft creation automation.

### Acceptance

Planner can explain every recommendation by dated demand, qualified supply and policy.

### Operator decisions

- planning horizon/bucket;
- safety-stock/service-level policy;
- default lead-time source;
- auto-draft threshold, if ever enabled.

---

## 10. Epic E09 — Omnichannel connector, ATP publication and reconciliation

### Objective

Evolve current Taobao/operator-sync foundation into durable channel synchronization without weakening local stock truth.

### Stories

- **E09-S01** Create external-object observation/import ledger.
- **E09-S02** Standardize connector interface: authenticate/test/pull orders/push fulfilment/publish inventory/reconcile.
- **E09-S03** Migrate Taobao sync to durable job/checkpoint model.
- **E09-S04** Add cursor/overlap/replay-safe ingestion.
- **E09-S05** Add canonical channel/shop/external order identity.
- **E09-S06** Add outbound fulfilment outbox + remote acknowledgement.
- **E09-S07** Add ATP publication policy and channel caps/buffers.
- **E09-S08** Add stock publication result/version history.
- **E09-S09** Add cancellation/refund observation handling.
- **E09-S10** Add periodic full reconciliation.
- **E09-S11** Extend additional marketplaces only through same contract.

### Data changes

```text
external_objects
connector_checkpoints
sync_operations
channel_inventory_publications
```

### API/UI touchpoints

- account sync health;
- mapping conflicts;
- reconciliation exception queue;
- last published ATP/remote ack.

### Migration

Keep existing account/SKU mapping; backfill external object IDs only where evidence is unambiguous.

### Tests

- replay same remote order does not duplicate;
- changed remote version is detected;
- checkpoint advances after durable process;
- local shipment commits even if remote push fails;
- publish uses ATP, not raw balance.

### Rollout

Taobao first, manual compare to current operator flow, then enable scheduled sync.

### Acceptance

Normal transient connector failures recover without manual duplicate repair; persistent mismatch appears as one actionable reconciliation item.

### Operator decisions

- per-channel stock buffer/cap;
- synchronization cadence;
- which remote fields are authoritative before fulfilment;
- manual-review thresholds.

---

## 11. Epic E10 — CRM, quotation, samples, support and RMA

### Objective

Extend order-centric operations into customer lifecycle without implementing a heavyweight CRM.

### Stories

- **E10-S01** Add lightweight customer/account identity.
- **E10-S02** Add inquiry/opportunity with owner/next action.
- **E10-S03** Capture structured technical requirements + attachments.
- **E10-S04** Add quotation header/lines and immutable revisions.
- **E10-S05** Link accepted quote revision to order.
- **E10-S06** Add sample/loan/gift transaction with stock classification.
- **E10-S07** Add customer support case/ticket with SLA/owner.
- **E10-S08** Link case to order/shipment/serial/RMA.
- **E10-S09** Add RMA authorization/reason/status.
- **E10-S10** Add return receipt + quality disposition.
- **E10-S11** Add diagnosis/repair/retest actions.
- **E10-S12** Add warranty decision, replacement/refund linkage and closure.

### Data changes

```text
customers
opportunities
quotations / quotation_revisions
sample_transactions
support_cases
rmas / rma_items / repair_actions
```

### API/UI touchpoints

- customer timeline;
- technical quote workspace;
- support/RMA serial timeline.

### Migration

Do not force existing order receiver data into deduplicated customer master automatically; use candidate matching/review.

### Tests

- quote history immutable;
- sample removes saleable ATP by correct state;
- refund and physical restock are independent;
- RMA received serial validates against history where available;
- repaired unit requires defined retest before release.

### Rollout

Start with quotations/samples and RMA for highest-support product families.

### Acceptance

Support can navigate customer→order→shipped serial→build/test→RMA without manual file hunting.

### Operator decisions

- customer dedupe rules;
- quotation approval/floor-price rules;
- warranty policy categories;
- case SLA targets and escalation ownership.

---

## 12. Epic E11 — Pricing safety, channel economics and manufacturing cost

### Objective

Separate “what price should we charge?” from “what did this order/product actually earn?”.

### Stories

- **E11-S01** Rename/fix markup vs gross-margin rule semantics.
- **E11-S02** Define canonical price/margin formulas and regression fixtures.
- **E11-S03** Add floor-price policy/override permission/reason.
- **E11-S04** Add order economics event ledger.
- **E11-S05** Capture platform/payment/shipping/tax/refund/replacement cost categories.
- **E11-S06** Add settlement import/reconciliation.
- **E11-S07** Add standard cost version/effectivity.
- **E11-S08** Capture WO actual cost snapshot from material/labor/overhead/subcontract/scrap.
- **E11-S09** Add standard-vs-actual variance.
- **E11-S10** Expose order/SKU/channel contribution margin.

### Data changes

```text
order_economic_events
settlement_batches / settlement_lines
standard_cost_versions
work_order_cost_snapshots
cost_variances
```

### API/UI touchpoints

- pricing calculator shows formula type;
- profitability drill-down explains each cost component;
- settlement mismatch queue.

### Migration

Do not recompute historical realized profit from today's master cost. Historical orders without snapshots remain marked estimated/unknown.

### Tests

- gross margin vs markup math;
- floor override permission;
- cost master changes do not rewrite historical snapshot;
- refund/freight/platform fee change contribution without changing product master cost.

### Rollout

Formula safety first; economics shadow-report next; settlement reconciliation before management KPI publication.

### Acceptance

Management can reproduce contribution profit for a completed order from immutable economic events.

### Operator decisions

- cost basis for historical/unfinished manufacturing periods;
- tax treatment scope;
- advertising attribution inclusion/exclusion;
- contribution-margin approval thresholds.

---

## 13. Epic E12 — KPI lineage, executive reporting and product intelligence

### Objective

Create trustworthy decision support without turning the operational dashboard into a BI wall.

### Stories

- **E12-S01** Create metric registry/lineage definition.
- **E12-S02** Add lifecycle timestamps needed for cycle-time KPIs.
- **E12-S03** Add daily exception/action management view.
- **E12-S04** Add weekly fulfilment/procurement/production/quality flow view.
- **E12-S05** Add monthly inventory/economics view.
- **E12-S06** Add inventory aging/turns/days-of-supply metrics.
- **E12-S07** Add supplier on-time/quality metrics.
- **E12-S08** Add SKU/channel/customer profitability views.
- **E12-S09** Add product scorecard separating measured vs inferred fields.
- **E12-S10** Add drill-through from KPI to underlying records.
- **E12-S11** Add cached read models only where measured query cost warrants them.

### Data changes

- metric definitions;
- optional aggregate/read-model tables.

### API/UI touchpoints

Distinct Daily / Weekly / Monthly management views.

### Migration

Historical KPIs must state data-availability boundaries if required timestamps/economics did not exist.

### Tests

- numerator/denominator fixture tests;
- scope/timezone tests;
- drill-down totals reconcile;
- freshness/definition exposed.

### Rollout

Publish only metrics whose source data is mature enough.

### Acceptance

No management KPI is displayed without a documented definition and reproducible source query/read model.

### Operator decisions

- management KPI shortlist;
- financial reporting period/timezone;
- product-score weighting policy, if a composite score is used.

---

## 14. Epic E13 — Rules automation and exception routing

### Objective

Automate repetitive detection/routing while preserving human control over consequential actions.

### Stories

- **E13-S01** Define rule trigger/condition/action/approval/audit schema.
- **E13-S02** Implement notify-only rules.
- **E13-S03** Implement suggestion/draft rules.
- **E13-S04** Add dedupe/cooldown/escalation semantics.
- **E13-S05** Route outputs into unified todo/support/exception ownership.
- **E13-S06** Add safe connector retry/escalation rule.
- **E13-S07** Add overdue PO/quarantine aging/stock shortage rules.
- **E13-S08** Add slow-stock/product-review rules.
- **E13-S09** Add rule simulation/test mode against fixture data.
- **E13-S10** Add per-rule metrics: firings, suppressions, overrides, false positives.

### Data changes

```text
automation_rules
automation_executions
automation_approvals
```

### API/UI touchpoints

- rule list/status;
- simulation output;
- execution/audit timeline;
- approve/reject proposal.

### Migration

Start with code/config-defined rules if DB rule editor would add premature complexity.

### Tests

- duplicate event does not create duplicate action;
- approval-required action cannot auto-execute;
- disabled rule has no effect;
- rule retry uses idempotent domain command.

### Rollout

Notify-only first; suggestions next; very limited reversible auto-actions last.

### Acceptance

Automation reduces repeated manual checking without creating hidden mutations or alert storms.

### Operator decisions

- thresholds/cooldowns;
- who owns each exception class;
- which safety class may auto-execute.

---

## 15. Epic E14 — Evidence-bound AI Copilot

### Objective

Add AI where it reduces reading/matching/drafting work without granting it database authority.

### Stories

- **E14-S01** Define AI tool permission model matching server actor/scope.
- **E14-S02** Add permission-aware read tools over approved query services.
- **E14-S03** Add structured source citations/record links in AI answers.
- **E14-S04** Add part/MPN candidate matching assistant.
- **E14-S05** Add EDA/document extraction into reviewable staging.
- **E14-S06** Add support/RMA summarization.
- **E14-S07** Add anomaly explanation over KPI/read-model data.
- **E14-S08** Add purchasing/MRP recommendation explanation.
- **E14-S09** Add weekly/monthly narrative report drafting.
- **E14-S10** Add proposal-to-action handoff requiring deterministic validation/approval.
- **E14-S11** Add prompt/model/version/evaluation metadata and PII/privacy controls.
- **E14-S12** Reuse recognition correction/evaluation pattern for AI quality evaluation.

### Data changes

AI run/evaluation records may include:

```text
provider/model/version
actor/scope
input references
output hash/result
proposed action
approval/result
evaluation feedback
```

Do not store unnecessary sensitive prompt content by default.

### API/UI touchpoints

- Copilot side panel/search;
- “show evidence” links;
- review proposal before action;
- feedback/correction controls.

### Migration

None required for business truth; AI tables are additive.

### Tests

- actor cannot retrieve records outside permission/warehouse scope;
- AI cannot call raw SQL mutation;
- proposed high-risk action requires normal domain authorization;
- missing evidence leads to uncertainty, not fabricated answer;
- model/provider failure does not change business state.

### Rollout

Read-only/search/summarization first; draft proposals second; no autonomous high-risk operations.

### Acceptance

AI saves operator analysis time while every authoritative mutation remains attributable to a deterministic service/action and actor/approval.

### Operator decisions

- allowed providers/data residency;
- sensitive fields excluded from external providers;
- which teams get Copilot access;
- retention/evaluation policy.

---

## 16. Epic E15 — Conditional scale-up / PostgreSQL and performance

### Objective

Provide a prepared path to larger scale without turning hypothetical future needs into current infrastructure burden.

### Entry criteria

Do not start migration merely because it appears on a roadmap.

At least one should be measured:

- sustained SQLite write contention;
- unacceptable p95/p99 latency from DB locking;
- worker concurrency growth;
- HA/PITR requirement;
- large test/traceability/ledger dataset pressure;
- reporting workload harms operations;
- multi-site deployment need.

### Stories

- **E15-S01** Create DB compatibility test matrix from canonical migrations.
- **E15-S02** Remove SQLite-specific SQL assumptions from domain layer where practical.
- **E15-S03** Generate/apply equivalent PostgreSQL schema via migrations, not stale legacy SQL.
- **E15-S04** Build data-copy/reconciliation rehearsal.
- **E15-S05** Run dual-environment contract suite.
- **E15-S06** Benchmark representative transaction/read workloads.
- **E15-S07** Define cutover/fallback process.
- **E15-S08** Add PostgreSQL backup/PITR procedures if adopted.

### API/UI touchpoints

None expected; database change should preserve business contracts.

### Tests

Same business fixtures/results on both supported backends.

### Rollout

Isolated staging rehearsal → maintenance cutover → reconciliation → fallback window.

### Acceptance

Migration is justified by measured need and preserves ledger/reservation/order/WO invariants exactly.

### Operator decisions

- whether HA/PITR is a hard business requirement;
- acceptable maintenance window;
- operations ownership for PostgreSQL.

---

## 17. Cross-epic dependency map

```text
E00 Release Safety
  -> E01 Core/Jobs/Action Policy
       -> E02 Stock Kernel
            -> E03 Warehouse/Scan
            -> E09 Omnichannel
            -> E06 Work Order
                 -> E07 Quality/Trace/Test
                 -> E08 MRP/Subcontract
                 -> E11 Actual Cost

E04 Part Master
  -> E05 BOM/ECN/Docs
       -> E06 Work Order
       -> E08 MRP

E09 Commerce + E10 CRM/RMA + E11 Economics
  -> E12 Reporting/Product Intelligence
       -> E13 Rules Automation
       -> E14 AI Copilot

E15 Scale-up is conditional and depends on E00/E01 architectural cleanup, not calendar date.
```

## 18. Suggested first implementation tranche

A practical first tranche should contain only high-leverage foundations:

1. E00 migration/recovery/release safety;
2. E01 action policy/idempotency/jobs;
3. E11-S01/S02 margin terminology/formula fix;
4. E02 reservation/idempotent stock operations;
5. E03 unified identifier/scan resolver;
6. E04 part identity schema design;
7. E05 BOM revision schema design.

Do not start MRP, AI or a large new dashboard in the first tranche.

## 19. Definition of Done for every story

A story is not done when the UI renders. Minimum completion evidence:

1. schema migration where applicable;
2. domain/service contract;
3. permission/object-scope check;
4. state transition/preconditions;
5. idempotency if consequential;
6. operation/ledger audit evidence;
7. local deterministic test;
8. rollback/compensation behavior;
9. docs/operator note;
10. old path retirement or explicit coexistence status.

## 20. Decisions requiring business/operator input

Before or during implementation, operators must explicitly decide:

- stock status taxonomy and legacy-bin policy;
- part-number/manufacturer/MPN conventions;
- AVL approval authority;
- BOM revision/effectivity conventions;
- quality/lot/serial policy by product/component family;
- required RF test suite and raw-data retention;
- planning policies, lead times and safety stock ownership;
- channel stock caps/buffers and source-of-truth rules;
- quote floor/approval and warranty policies;
- contribution-margin definitions;
- KPI shortlist;
- automation thresholds/safety classes;
- external AI provider/privacy policy;
- RPO/RTO and off-host backup strategy;
- PostgreSQL/scale trigger thresholds.

These should be configuration or documented operating policy, not guessed by developers.

## 21. Core recommendation

Execute epics in dependency order and preserve the current system's strongest workflows while replacing weak invariants underneath them.

The implementation goal is:

```text
more capability with fewer hidden assumptions
```

not simply more tables and screens. Every new domain should strengthen auditability, explainability and operator speed while keeping one clear source of business truth.