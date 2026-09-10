# TASK_INV_AUDIT_DATA_MODEL_01 — Database Schema, Entity & Lifecycle Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Evidence reviewed:

- `inventory_app/database.py` (`SCHEMA_SQL`, migration path, connection settings)
- `deploy/postgres/schema.sql`
- `inventory_app/server.py` session/scope behavior
- `inventory_app/services.py` entry structure and service invariants
- `docs/应用开发索引.md`
- `docs/architecture.md`
- `docs/迭代执行记录.md`

No GitHub Actions result is used as evidence.

## 1. Executive conclusion

The SQLite model has evolved from an MVP inventory schema into a broad operational schema containing identity, product/catalog, inventory, warehouse, recognition, order fulfilment, transfer, procurement, pricing/cost, stock count, notification and archive concepts.

The model has several strong ideas — especially inventory movement logging, recognition revision evidence, purchase receipts and price revisions — but it now carries architectural debt that will become important if the system expands into electronics manufacturing.

The highest-priority model risks are:

1. **PostgreSQL schema drift is already severe.** The PostgreSQL file represents an older subset and is not a faithful alternative schema for the current SQLite application.
2. **Physical stock location is under-modeled.** `inventory` has one `location_id`, while the unique stock identity excludes location. This cannot naturally represent one material split across multiple bins as independent balances.
3. **Schema-level relational integrity is weak in SQLite.** Many ID relationships are plain integers without declared `REFERENCES`, despite `PRAGMA foreign_keys=ON`.
4. **Nullable uniqueness can permit duplicate logical stock rows.** `UNIQUE(material_id, warehouse_id, platform_account_id)` does not guarantee uniqueness for rows where `platform_account_id IS NULL` under normal SQLite/PostgreSQL NULL uniqueness semantics.
5. **Quantity precision is inconsistent.** purchasing and project BOM support `REAL`, while core inventory and one BOM representation use integer quantities.
6. **Two BOM-like structures exist without revision/effectivity control.** This is acceptable for an MVP but inadequate for controlled electronics manufacturing.
7. **Financial values are stored as floating-point `REAL`.** Application rounding reduces display error but does not create finance-grade decimal semantics.
8. **State values are mostly unconstrained `TEXT`.** Business rules live in services rather than database constraints; this raises migration/manual-write/state-corruption risk.
9. **Credentials are modeled as application database fields.** Secret-at-rest controls require a dedicated security decision.
10. **No lot/serial/work-order/engineering-change genealogy exists in the pinned data model.** This is the largest functional barrier to manufacturing traceability.

## 2. Entity domains

### 2.1 Identity and authorization

Core entities:

- `users`
- `roles`
- `permissions`
- `user_roles`
- `role_permissions`
- `user_permission_overrides`
- `warehouse_users`
- `auth_sessions` (created through migration path)
- `auth_login_attempts` (migration path)

Strengths:

- role and permission are separate concepts;
- user-specific allow/deny overrides exist;
- warehouse-user membership is explicit;
- session tokens are hashed before persistence;
- sessions support idle expiry, absolute expiry and revocation.

Debt:

- identity relationships in the SQLite schema are mostly not protected by declared foreign-key references;
- authorization scope is therefore primarily an application invariant, not a database invariant;
- session tables being migration-created rather than visibly co-located with the initial core schema increases schema-evolution complexity.

### 2.2 Product and material master

Core entities:

- `materials`
- `product_categories`
- `material_aliases`
- `material_usage_types`
- `material_usage_assignments`
- `material_scope_categories`
- `material_specifications`
- `material_resources`
- `dead_stock`

This is a good base for an electronics item master, but current first-class fields are still generic. Electronics-specific manufacturer/MPN/package/lifecycle/compliance/supplier-part relationships are not first-class model concepts.

`material_specifications` can temporarily carry parametric attributes, but generic key/value specifications alone do not replace controlled electronic-part identity and lifecycle fields.

### 2.3 BOM and operation/cost primitives

The pinned schema contains at least two BOM-like representations:

- `material_bom`
  - `sales_material_id`
  - `component_material_id`
  - `component_quantity INTEGER`
- `project_bom_lines`
  - `sales_material_id`
  - optional component ID plus component code/name/model snapshots
  - `component_quantity REAL`
  - `import_batch`

And operation costing:

- `labor_cost_profiles`
- `bom_operations`

Strengths:

- enough structure exists to model a simple product bundle/assembly and estimated labor operation cost;
- imported project-BOM lines can preserve source text when a component is not yet normalized.

Major manufacturing gaps:

- no BOM header/version/revision entity;
- no effective-from/effective-to or effectivity by serial/date/order;
- no approved/released/frozen status;
- no reference designator;
- no find-number/line identity suitable for engineering change;
- no alternate/substitute/AVL relation;
- no explicit EBOM vs MBOM relation;
- no where-used revision impact model;
- no routing/work-center entity beyond cost-operation primitives.

### 2.4 Procurement and landed cost

Entities:

- `suppliers`
- `purchase_orders`
- `purchase_order_items`
- `purchase_receipts`
- `purchase_receipt_items`
- `material_purchase_prices`

Strengths:

- supplier is independent from PO;
- PO has approval metadata and expected date;
- line received quantity exists;
- receipts are explicit objects;
- landed allocated cost and purchase-price history are captured.

Gaps:

- no first-class supplier-item/manufacturer-part linkage;
- no MOQ, order multiple, standard lead time, preferred supplier/AVL state;
- no supplier quotation/RFQ history in the audited schema;
- receiving is not linked to IQC lot status;
- receipt has no supplier batch/date-code/COC/inspection identity;
- PO lines do not identify BOM demand, work-order demand or MRP pegging.

### 2.5 Pricing and commercial history

Entities:

- `price_lists`
- `material_prices`
- `material_price_revisions`
- `pricing_rules`
- `order_item_price_revisions`

Strengths:

- channel and customer-group dimensions exist;
- quantity threshold and validity concepts exist;
- price changes have revision records and reasons;
- order item price snapshots/revisions can preserve commercial history.

Risk:

- currency/amounts are represented with floating-point types rather than fixed decimal semantics;
- operational pricing is not the same as accounting revenue/cost recognition.

### 2.6 Inventory and warehouse

Entities:

- `inventory`
- `inventory_logs`
- `warehouse_locations`
- `warehouse_layout_items`
- `inventory_count_sessions`
- `inventory_count_items`

Current balance dimensions:

`material + warehouse + platform account` with columns:

- `quantity_available`
- `quantity_locked`
- `quantity_on_transfer`
- `safety_stock`
- `location_id`

#### Critical modeling issue A — bin/location identity

The unique key is:

`UNIQUE(material_id, warehouse_id, platform_account_id)`

`location_id` is not part of the stock identity. Therefore one row cannot naturally express separate balances for the same material in multiple bins under the same warehouse/account.

For a real WMS/electronics store room, desired identity is closer to:

`material + warehouse + location + stock_status + lot/batch (+ owner/account when necessary)`

or a balance projection derived from an immutable stock ledger.

#### Critical modeling issue B — nullable account uniqueness

`platform_account_id` is nullable. Standard UNIQUE semantics treat NULL values as distinct, so schema-level uniqueness does not guarantee one row for `(material, warehouse, NULL-account)`.

Even if `InventoryService` currently queries/upserts safely, the schema itself does not fully protect the invariant. Recommended designs include:

- normalize the no-account dimension to a non-null scope key;
- a generated/sentinel scope value;
- a partial unique index for `platform_account_id IS NULL` plus another for non-null values;
- or redesign inventory identity around a non-null stock-owner/scope entity.

#### Critical modeling issue C — movement detail

`inventory_logs` records warehouse/account, movement type, delta, balance-after, reference and reason, but does not show first-class source/destination `location_id`, lot/batch, serial, stock-status or quality-status dimensions in the audited definition.

That means the existing ledger is useful for aggregate inventory audit, but insufficient for manufacturing genealogy or robust bin-level WMS audit.

### 2.7 Recognition / image evidence

Entities include:

- `attachments`
- `attachment_derivatives`
- `image_derivative_jobs`
- `recognition_tasks`
- `recognition_corrections`
- `recognition_revisions`

This is a comparatively mature data area.

Positive patterns:

- original attachment identity is distinct from derivatives;
- derivative generation has a durable job table and status/attempt/error model;
- human corrections preserve before/after values;
- revision numbers and change source are explicit;
- image hash is available for deduplication/evidence linkage.

This pattern should be reused elsewhere: future BOM/ECN, platform sync, test records and automation should favor durable state + revision/event evidence rather than hidden background side effects.

### 2.8 Orders, shipment and transfer

Core entities:

- `orders`
- `order_items`
- `shipment_tasks`
- `shipment_scan_logs`
- `transfer_orders`
- `transfer_items`
- `transfer_receipt_events`
- `pending_import_orders`
- `shipment_task_archives`

Strengths:

- formal order and shipment task are separate;
- platform synchronization status is explicit on orders;
- scan logs exist;
- transfers support received quantity and receipt events;
- exception metadata exists on transfers;
- completed shipment archival has file hash/size metadata.

Gaps for scale:

- order-item reservation/allocation is not represented as a first-class reservation entity;
- no canonical parcel/package/carton entity;
- no first-class return/RMA relationship;
- no lot/serial allocation to shipment lines;
- `pending_import_orders` uses nullable fields in a logical uniqueness area and deserves duplicate/idempotency testing;
- generic status TEXT values are not database constrained.

## 3. SQLite relational integrity audit

`PRAGMA foreign_keys = ON` is enabled, but many SQLite table definitions use integer relationship columns without explicit `REFERENCES` clauses. Enabling foreign keys does nothing for a relationship that was never declared.

Examples visible in the initial schema include relationship/junction fields in:

- `user_roles`
- `role_permissions`
- `warehouse_users`
- `material_bom`
- purchasing tables
- pricing tables
- inventory tables
- order/shipment/transfer tables

The application service layer may correctly maintain these relationships in normal operation, but database-level guarantees are incomplete.

Recommendation:

1. inventory every logical relationship;
2. classify delete policy (`RESTRICT`, `CASCADE`, `SET NULL`, archive-only);
3. add constraints in a staged migration;
4. run orphan-detection queries before enabling constraints;
5. keep service checks even after constraints are added.

## 4. SQLite versus PostgreSQL drift

The current `deploy/postgres/schema.sql` contains only the older foundational entities: users/roles/permissions, warehouses, platform accounts, materials, basic inventory/logs, attachments/recognition, orders/items, shipments, transfers, operation logs and settings.

Compared with the current SQLite schema, the PostgreSQL file is missing or materially behind on many later concepts, including examples such as:

- user permission overrides and current auth/session controls;
- product categories and material usage scopes;
- aliases;
- BOM/project BOM/operation costing;
- suppliers, purchase orders, receipts and purchase price history;
- pricing lists/rules/revisions;
- material specifications/resources;
- warehouse locations/layout;
- attachment derivative/job model;
- recognition corrections/revisions;
- notifications;
- transfer partial-receipt/exception event detail;
- stock count;
- shipment scan/archive;
- and many migrated columns added after the early schema.

**Conclusion:** PostgreSQL is currently a design placeholder/legacy migration target, not a drop-in database backend for the pinned application.

Do not start a production PostgreSQL migration by applying the existing SQL file to live data.

## 5. Type and precision audit

### 5.1 Quantity mismatch

Examples:

- inventory quantities: INTEGER
- order/shipment quantities: INTEGER
- `material_bom.component_quantity`: INTEGER
- purchase quantities: REAL
- `project_bom_lines.component_quantity`: REAL

This can become problematic for electronics-related non-piece materials such as cable length, solder paste, adhesives, heat-shrink, sheet material, chemicals or other fractional UOMs.

Recommendation: introduce a unit-of-measure policy before manufacturing expansion. Quantity representation should support decimal precision by UOM rather than assuming all stock is integer pieces.

### 5.2 Money mismatch

Costs and prices use `REAL`. `services.py` has application rounding helpers, but IEEE floating point remains inappropriate as the long-term source of truth for precise monetary aggregation.

Recommended future model:

- fixed decimal semantics in application layer;
- database NUMERIC/DECIMAL when PostgreSQL is introduced;
- explicit currency precision;
- stored money values and quantity values separated from display rounding.

## 6. State-machine integrity

Many entities use `status TEXT` with service-layer transition rules. This keeps the MVP flexible, but as workflows multiply it creates several risks:

- migration can introduce unknown status values;
- typo/manual SQL can bypass state machine;
- UI, service and reporting can drift on status vocabulary;
- cross-domain automation can trigger from a state that one module no longer recognizes.

Do not solve this only with database CHECK constraints. Recommended pattern:

1. one canonical state vocabulary per aggregate;
2. transition function/table in the domain module;
3. tests generated from allowed transitions;
4. database CHECK/enum only after vocabulary stabilizes;
5. event/audit record for consequential transitions.

All tests must be runnable outside GitHub Actions.

## 7. Manufacturing data-model delta

To support electronic product development and production, the following new aggregates are likely required eventually.

### Part engineering

- Manufacturer
- ManufacturerPart / MPN
- SupplierPart
- ApprovedVendor/ApprovedManufacturer relation
- Alternate/Substitute relation
- lifecycle/EOL/NRND status
- compliance/doc links

### Controlled BOM/change

- BOM header
- BOM revision
- BOM line
- reference designator
- release/effectivity state
- ECN/ECO
- change approvals
- where-used impact
- EBOM-to-MBOM mapping

### Planning and production

- demand/supply projection
- MRP run/result
- planned order / purchase suggestion
- production/work order
- work-order material requirement
- issue/return/scrap transaction
- operation/routing/work center
- WIP and completion transaction

### Traceability and quality

- stock lot/batch
- serial number
- stock status (available/hold/quarantine/reject/etc.)
- genealogy links component-lot -> work order -> finished serial
- inspection plan/result
- NCR/deviation/rework
- test station/equipment/calibration
- test result linked to serial/batch/product revision/firmware

### Aftersales

- customer/account lightweight entity
- RMA
- returned serial
- fault/repair action
- warranty decision
- replacement shipment

## 8. Recommended target inventory kernel

Do not replace `inventory` immediately. Migrate in stages.

A stronger target model is:

```text
stock_location
stock_lot / serial
stock_balance (projection)
stock_reservation
stock_movement
stock_movement_line
```

Where a movement line can capture:

```text
material
from_location / to_location
warehouse
lot/batch
serial (when serialized)
stock_status
quantity + UOM
reference document
business event id / idempotency key
actor
occurred_at
```

`stock_balance` should be a fast projection/cache of movement truth, with reconciliation tools able to prove balance from ledger history where practical.

## 9. Migration priorities

### P0 — before adding major manufacturing features

1. define canonical stock identity and multi-bin behavior;
2. protect null-scope stock uniqueness;
3. add relational-integrity inventory and orphan checks;
4. freeze a versioned SQLite schema specification;
5. stop treating the current PostgreSQL SQL as deployment-equivalent;
6. define decimal/UOM policy;
7. introduce idempotency keys for irreversible stock-changing operations.

### P1 — manufacturing foundation

1. electronic part/manufacturer/supplier-part model;
2. controlled BOM revision model;
3. lot/batch and serial entities;
4. stock status/quarantine;
5. work-order model;
6. MRP demand/supply model;
7. inspection/test genealogy.

### P2 — advanced operating model

1. EBOM/MBOM transformation;
2. subcontract/consigned stock;
3. actual cost rollup by production batch/serial;
4. RMA genealogy;
5. richer planning/forecasting.

## 10. Verification requirements without Actions

Every schema evolution should be verifiable from a fresh checkout using repository-contained commands, for example:

- initialize a brand-new SQLite DB;
- migrate a fixture DB from representative old schema versions;
- run orphan/constraint checks;
- replay inventory movement scenarios;
- test concurrent idempotent stock updates;
- export schema metadata and compare to the versioned model;
- when PostgreSQL becomes real, run the same domain test suite against both backends from local/server CLI.

A GitHub Actions workflow may optionally call these commands, but the workflow must never be the only place where the verification logic exists.

## 11. Immediate follow-up questions for later tasks

- Does `InventoryService` manually guarantee the null-account uniqueness invariant under concurrency?
- Can one material be practically stored in two physical locations today, and what does the UI show?
- What exactly increments/decrements `quantity_locked` and is it tied to an order reservation record?
- Is `quantity_on_transfer` a derived value or mutable balance, and how is it repaired after abnormal transfer flows?
- Which stock-changing endpoints have idempotency/replay protection?
- Which historical migrations would be unsafe once foreign keys are made explicit?

These are mandatory inputs to the stock-model, transfer, warehouse-location, concurrency and database-migration tasks.