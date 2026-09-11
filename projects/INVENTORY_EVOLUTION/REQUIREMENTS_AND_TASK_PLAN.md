# INVENTORY_EVOLUTION — Requirements & Execution Plan

## 1. Purpose

This project executes the completed `INVENTORY_DEEP_AUDIT` recommendations against `ZXYHtech/inventory` in dependency order.

Audit source:

- UOS audit PR: `ZXYHtech/UOS#1`
- completed audit head: `8287a98328d9409e6a1051194e9dcb9a052b9a74`
- inventory implementation baseline/current main: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`

The implementation goal is **more capability with fewer hidden assumptions**, not more screens.

## 2. Architecture decision

Default target:

```text
Modular Monolith
 + one authoritative relational database
 + DB-backed durable worker/outbox
 + provider/connector interfaces
 + versioned domain APIs
 + deterministic local release gate
```

SQLite remains the primary database until measured write contention, HA/PITR, dataset scale, multi-site or reporting pressure justifies PostgreSQL.

## 3. Non-negotiable implementation rules

1. No big-bang rewrite.
2. No required GitHub Actions dependency.
3. Consequential writes require deterministic domain-service validation.
4. Stock/external replay operations require server-side idempotency.
5. Executed history is corrected through compensating/reversal events, not deletion.
6. Released engineering/manufacturing records are immutable; change creates a new controlled revision or reversal.
7. AI/rules do not bypass normal permission/state/idempotency gates.
8. Historical lot/serial/BOM/cost evidence is never fabricated during migration.
9. Every story has local test evidence and explicit coexistence/rollback behavior.
10. Implementation changes occur on dedicated `ZXYHtech/inventory` branches/PRs; UOS stores orchestration/evidence/status artifacts.

## 4. Epic sequence

### E00 — Release safety, schema migration and recovery foundation

Stories:

- E00-S01 schema version + numbered immutable migration runner
- E00-S02 representative old-DB fixtures
- E00-S03 pre/post migration integrity + orphan checks
- E00-S04 one local `verify_release` command
- E00-S05 restore-to-temporary verification
- E00-S06 full backup manifest/checksums
- E00-S07 off-host copy hook + backup health record

**Gate:** must complete before major schema domains.

### E01 — Core modularization, action policy and durable jobs

Action registry, idempotency/business operation IDs, generalized durable jobs, retries/dead-letter, outbox, correlation IDs and first low-risk module extraction.

### E02 — Stock position, movement ledger and reservation kernel

Canonical stock dimensions, idempotent movement operation/lines, explicit reversals, first-class reservations, ATP, order/shipment reservation integration and migration reconciliation.

### E03 — Warehouse locations, receiving, putaway, scan and count

Zone/bin hierarchy, staging, putaway, scan-first pick, count observation/reconciliation, cycle count and simple path ordering.

### E04 — Electronics part master, parameters, MPN and AVL

Manufacturer/MPN/supplier part, typed parameters, lifecycle/compliance, AVL/substitutes, provider/provenance, component workspace and global part search.

### E05 — Revisioned EBOM/MBOM, ECN/ECO and controlled documents

Typed/revisioned BOMs, refdes, effectivity, ECN/ECO, where-used, EDA staging/diff, controlled docs and firmware/test-spec revisions.

### E06 — Work order and manufacturing execution spine

WO lifecycle, requirement snapshot, reservation/allocation, kitting, issue/return/scrap, partial output, cancel/hold and optional labor actuals.

### E07 — Quality, lot/serial genealogy and RF test evidence

Risk-based trace policy, lots/serials, genealogy, quality states, IQC/NCR/MRB-lite, structured RF tests, equipment/calibration, firmware/test provenance and final release.

### E08 — Procurement planning, MRP and subcontract

Lead time/MOQ/order multiple, planning views, released-MBOM MRP, pegging/explanation, recommendation review and subcontract/external WIP.

### E09 — Omnichannel connector, ATP publication and reconciliation

External-object ledger, standardized connector interface, durable Taobao sync, cursor/replay safety, fulfilment outbox, channel ATP and reconciliation.

### E10 — CRM, quotation, samples, support and RMA

Lightweight customer/opportunity, technical requirements, immutable quote revisions, sample flow, support case and serial-aware RMA/repair/retest.

### E11 — Pricing safety, channel economics and manufacturing cost

Margin/markup correction, floor approval, order economics ledger, settlement reconciliation, standard cost, WO actual cost and variance/contribution reporting.

### E12 — KPI lineage, executive reporting and product intelligence

Metric lineage, lifecycle timestamps, daily/weekly/monthly management views, inventory/supplier/profitability metrics and explainable product scorecards.

### E13 — Rules automation and exception routing

Notify/suggest/reversible/approval-required rule classes, dedupe/cooldown, routing, simulation and rule-quality metrics.

### E14 — Evidence-bound AI Copilot

Permission-aware read tools, evidence links, part/document/RMA/MRP/report assistants, proposal-to-action handoff, model/evaluation/privacy governance.

### E15 — Conditional scale-up / PostgreSQL

Only starts after measured entry criteria; canonical migrations and identical business contract tests must drive any backend migration.

## 5. First implementation tranche

The first tranche is intentionally narrow:

```text
E00 release safety
 -> E01 action/idempotency/jobs
 -> E11-S01/S02 margin formula safety
 -> E02 stock/reservation kernel
 -> E03 scan resolver
 -> E04 part identity schema design
 -> E05 BOM revision schema design
```

MRP, AI, large dashboards and advanced WMS remain blocked until their truth dependencies exist.

## 6. Story Definition of Done

A story is complete only when applicable evidence covers:

1. schema migration;
2. domain/service contract;
3. permission/object scope;
4. state transition/preconditions;
5. idempotency;
6. operation/ledger audit evidence;
7. deterministic local test;
8. rollback/compensation;
9. docs/operator note;
10. old-path retirement or explicit coexistence.

## 7. Immediate E00 execution plan

### E00-S01

Introduce a non-destructive migration registry around the existing schema bootstrap. The current schema becomes a verified baseline migration marker rather than being replayed as new destructive DDL.

### E00-S02/S03

Build old-schema fixture generators and validation queries. Verify baseline adoption, repeat-run no-op, required objects, integrity and orphan checks.

### E00-S04

Create one local release command that orchestrates existing repository tests plus migration/recovery checks. CI may call this later, but it is not authoritative.

### E00-S05–S07

Strengthen backup from “file exists” to “recoverable”: isolated restore verification, manifest/checksum, off-host copy adapter and health record.

## 8. Business/operator decisions tracked separately

Implementation must expose rather than guess decisions including:

- RPO/RTO and off-host backup policy;
- stock status taxonomy and legacy-bin policy;
- part numbering/MPN conventions and AVL authority;
- BOM revision/effectivity naming;
- traceability policy by product/component family;
- RF test suite/raw-data retention;
- channel ATP buffers/caps;
- warranty/quote-floor/contribution-margin policies;
- AI provider/privacy boundaries;
- PostgreSQL scale triggers.
