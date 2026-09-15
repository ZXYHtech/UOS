# TASK_INV_AUDIT_PROTOTYPE_SAMPLE_01 — Prototype, Sample and Engineering-stock Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed inventory identity and movement semantics, material master/usage concepts, warehouse/location structures, project BOM lines, order/transfer flows and the absence of first-class prototype/sample/project-stock objects.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The current system can physically increase or decrease stock and can record a free-form movement reason/reference, but it cannot reliably distinguish **commercially available stock** from **engineering-owned, prototype, laboratory, evaluation or giveaway stock**.

That distinction matters for a small electronics/RF company because one physical part may be:

- saleable inventory;
- reserved for a customer order;
- owned by an R&D project;
- issued to an engineer or lab bench;
- consumed by a prototype build;
- temporarily checked out and expected back;
- given to a customer as a sample;
- loaned to a customer for evaluation;
- failed/damaged during engineering work;
- retained as a golden sample/reference unit;
- non-saleable but still financially accountable.

Trying to encode those states only in `reason`, location names, remarks or ad-hoc warehouse conventions will eventually corrupt availability, replenishment, project-cost and accountability decisions.

Preliminary maturity: **1.0/5** for controlled prototype/sample stock management.

## 2. What can be reused

Useful existing foundations include:

- `materials` as a canonical item identity;
- `inventory` as a warehouse-level balance surface;
- `inventory_logs` with movement type, delta, reference type/id, actor and timestamp;
- warehouse and location concepts;
- `project_bom_lines` as evidence that project-oriented component lists already exist;
- operation logging for user-visible mutations;
- order and transfer references that can inspire document-driven movement patterns.

These are good building blocks, but none is currently an authoritative engineering-stock ledger.

## 3. Core semantic gap

The existing `inventory` row exposes quantities such as available/locked/on-transfer, but the service layer does not provide a first-class model for project ownership, engineer custody, sample disposition or prototype consumption.

The system needs to separate four questions that are currently easy to conflate:

1. **Where is the material physically?** — warehouse/bin/lab/custodian.
2. **Who or what owns the demand?** — project, work order, customer sample, internal cost center.
3. **What is its commercial availability?** — saleable, reserved, non-saleable, quarantine, consumed.
4. **What transaction changed the state?** — issue, return, consume, loan, gift, scrap, transfer.

A location such as `R&D shelf` is not an ownership model. A remark such as `for project A` is not a reservation. A zero-value sales order is not a robust sample process.

## 4. Required workflow classes

### 4.1 Project-owned stock

A project must be able to reserve or own quantities without pretending the parts have already been consumed.

Required states:

```text
available
 -> project_reserved
 -> issued_to_engineer / issued_to_build
 -> returned | consumed | scrapped
```

The reservation must reduce ATP/available-to-promise while leaving physical on-hand correct.

### 4.2 Engineering issue and return

A controlled issue should capture:

- project or cost center;
- material and quantity;
- source warehouse/location;
- recipient/custodian;
- purpose;
- issue timestamp and issuer;
- expected return when applicable;
- final disposition.

Returns must reference the original issue and support partial return, consumed remainder and damaged remainder.

### 4.3 Prototype build consumption

Prototype consumption should not be a generic negative stock adjustment. It should reference a build/prototype record and preserve:

- intended BOM/revision or draft BOM snapshot;
- actual issued quantities;
- substitutions used;
- excess issue and return;
- failed/scrapped parts when material;
- assembled prototype identifier where useful.

This becomes the bridge to later work-order and actual-cost control.

### 4.4 Customer samples

At least three distinct dispositions are needed:

- `gifted`: ownership leaves the company permanently;
- `loaned/evaluation`: ownership remains and return is expected;
- `sold_sample`: commercial sale with normal order/revenue semantics.

A sample must not automatically be treated as a normal fulfilled sale because margin, revenue, receivable, inventory and follow-up semantics differ.

### 4.5 Golden samples and lab references

Reference units should be explicitly non-saleable and should have owner/location/status. For serial-controlled finished RF modules, preserve the actual serial number and product revision once serial traceability exists.

## 5. Minimal target data model

Do not create a separate inventory universe. Extend the common stock ledger with typed ownership/reservation/custody.

```text
projects
  id
  project_code
  name
  owner_user_id
  status
  cost_center

stock_reservations
  id
  material_id
  warehouse_id
  location_id
  quantity
  reservation_type: sales | project | work_order | sample
  reference_type
  reference_id
  status
  expires_at

engineering_issues
  id
  issue_no
  project_id
  custodian_user_id
  status: draft | issued | partially_returned | closed | cancelled
  issued_at
  closed_at

engineering_issue_lines
  issue_id
  material_id
  issued_qty
  returned_qty
  consumed_qty
  damaged_qty
  source_location_id

prototype_builds
  id
  project_id
  build_no
  product_material_id
  bom_revision_id
  status
  quantity
  created_by

sample_transactions
  id
  sample_no
  customer_id
  disposition: gift | loan | sold
  status
  expected_return_at
  sales_owner

sample_lines
  sample_id
  material_id
  quantity
  serial_or_lot_link
```

The exact schema can be simplified initially, but the reference must be structured rather than encoded only in remarks.

## 6. Ledger requirements

Every engineering/sample stock mutation should produce an immutable stock-ledger event with:

- material;
- quantity and unit;
- from/to stock state where applicable;
- warehouse/location;
- lot/serial when traceability is enabled;
- authoritative business-document reference;
- actor/time;
- reason/disposition;
- before/after balance or enough information to reconstruct it.

Important invariant:

```text
physical_on_hand = saleable + reserved + engineering + quarantine + other owned states
```

Do not make `available` a synonym for physical on-hand.

## 7. Interaction with MRP and purchasing

Engineering demand needs an explicit planning policy.

Examples:

- prototype reservation may consume current supply immediately;
- planned prototype BOM may create future independent/project demand;
- sample stock may have a dedicated replenishment policy;
- golden samples should normally not count as usable supply;
- loaned samples remain company assets but should not be ATP.

Without this distinction, MRP can falsely conclude parts are available for production or customer orders.

## 8. Interaction with costing

Prototype and sample flows should capture cost without forcing full accounting complexity on day one.

Minimum useful outputs:

- material cost consumed by project;
- prototype build material cost;
- gifted sample cost by customer/opportunity;
- open loaned-sample asset value;
- damaged/scrapped engineering cost;
- variance between planned and actual prototype consumption.

This can initially be analytical cost allocation, later feeding formal cost accounting.

## 9. Permissions and accountability

Recommended control split:

- engineer: request/receive/return assigned material;
- project owner: approve project reservation/consumption above threshold;
- warehouse: execute physical issue/return;
- sales: request sample and record customer purpose;
- finance/admin: report cost and overdue assets;
- admin: configure policy, not silently rewrite closed transactions.

Avoid allowing a user to simply edit an old stock quantity to repair an engineering issue. Correct through a referenced reversal/adjustment.

## 10. UX requirements

High-value screens:

1. **Project material board** — planned, reserved, issued, consumed, shortage.
2. **My checked-out material** — engineer custody and expected returns.
3. **Prototype build page** — BOM snapshot vs actual issue/return.
4. **Sample register** — customer, disposition, owner, due/returned state.
5. **Non-saleable stock view** — engineering, reference, quarantine, damaged.

Barcode/QR scanning should support issue and return, but scanning is only an input method; it must post a typed transaction.

## 11. Priority roadmap

### P0

1. introduce reservation/stock-state semantics separate from physical on-hand;
2. first-class engineering issue/return document;
3. project reference on reservations and consumption;
4. explicit sample disposition (`gift`, `loan`, `sold`);
5. block engineering/non-saleable quantities from sales ATP.

### P1

1. prototype build record with BOM snapshot;
2. partial return/consumption/damage split;
3. custodian and overdue loan/sample alerts;
4. project/sample cost reporting;
5. lot/serial linkage.

### P2

1. automated EDA/BOM-driven prototype reservation;
2. project budget integration;
3. sample-to-opportunity conversion analytics;
4. mobile scan workflow.

## 12. Acceptance signals

- a part reserved for Project A cannot simultaneously be promised to a customer as free stock;
- issuing ten units to an engineer and returning four leaves a traceable six-unit disposition rather than an unexplained adjustment;
- a gifted sample and a loaned evaluation unit have different stock/asset states;
- a prototype build can show planned vs actual consumed material;
- non-saleable/golden-sample stock remains visible but excluded from ATP;
- every mutation resolves to a document/reference and actor;
- no acceptance test requires GitHub Actions.

## 13. Risks if deferred

1. false availability and stockouts during production;
2. R&D consumption hidden as generic shrinkage;
3. sample leakage and overdue evaluation units;
4. inability to explain project material cost;
5. duplicated purchasing because engineering-held stock is invisible;
6. later MRP/work-order implementation forced to unwind ad-hoc conventions.

## 14. Core recommendation

Build engineering/sample stock as a **typed ownership + reservation + transaction layer on top of the common inventory ledger**, not as special warehouse names or free-text reasons. This is the smallest design that will remain compatible with MRP, work orders, traceability and cost accounting.