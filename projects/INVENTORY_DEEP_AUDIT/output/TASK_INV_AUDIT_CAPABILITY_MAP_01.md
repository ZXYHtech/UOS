# TASK_INV_AUDIT_CAPABILITY_MAP_01 — Current Capability & Workflow Matrix

## 0. Scope and evidence boundary

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

This is a static source audit. It does not infer runtime correctness from documentation alone and does not use GitHub Actions as evidence. A capability is classified as implemented only when multiple implementation anchors exist (schema/service/API/UI/tests or equivalent). Runtime verification remains a separate later step and must be executable from local/server commands without GitHub Actions.

Classification:

- **IMPLEMENTED** — concrete source path exists across enough layers to represent a real workflow.
- **IMPLEMENTED / NEEDS DEPTH AUDIT** — real implementation exists but business completeness is not yet proven.
- **PARTIAL** — useful primitives exist but the end-to-end business capability is incomplete.
- **DOCUMENTED / PLANNED** — mentioned by docs but no sufficient source evidence for a complete capability.
- **NOT FOUND IN PINNED SOURCE** — searched in the pinned tree and no relevant implementation was found.

## 1. Executive capability position

Inventory Lite is no longer only an inventory counter. The pinned source contains a credible lightweight operations platform with identity/permissions, multi-warehouse inventory, order recognition, order/fulfilment, transfer, procurement, pricing/cost, stock count, product classification/profile data, platform adapters, backup, notifications, PC/mobile clients and audit records.

However, it is not yet a manufacturing ERP/MRP/PLM system. The largest missing chain is:

`engineering item/revision -> controlled BOM revision -> MRP -> work order -> kitting/issue -> WIP -> lot/serial genealogy -> test/quality record -> finished-goods serial -> RMA history`

The source has several foundations for that future chain, but not the chain itself.

## 2. Capability matrix

| Domain | Static status | Strongest evidence | Current behavior / boundary | Next depth audit |
|---|---|---|---|---|
| Authentication | IMPLEMENTED | `server.py`, `database.py`, `tools/test_auth_security.py` | salted PBKDF2 hashes, durable sessions, revoke on password reset, login-attempt controls | threat model, session fixation/CSRF/upload exposure |
| Roles & permissions | IMPLEMENTED / NEEDS DEPTH AUDIT | roles/permissions/user_roles/role_permissions/user overrides; `require_perm` | server-side permission checks exist; per-user overrides supported | route-by-route permission completeness |
| Warehouse data scope | IMPLEMENTED / NEEDS DEPTH AUDIT | `warehouse_scope`, `require_warehouse_access`, filtering helpers | non-admin warehouse scope enforced in server helpers; product inventory read has special broader visibility | prove no route bypasses scope |
| Users / warehouses | IMPLEMENTED | schema + APIs + PC UI documented in development index | CRUD and warehouse-user relationships | lifecycle/delete/reference rules |
| Product/material master | IMPLEMENTED / NEEDS DEPTH AUDIT | `materials`, category tables, aliases, specs/resources, services/UI | SKU/material code, model/spec/unit, barcode/QR, category, aliases, resources exist | electronics parametric completeness, lifecycle states |
| Product classification | IMPLEMENTED | `product_categories`, audit status, CategoryService, PC UI | three-level category model with audit workflow | governance, code/prefix collisions, bulk change safety |
| Material usage separation | IMPLEMENTED / PARTIAL | `material_usage_types`, assignments, scope categories | distinguishes product/production/project usage | whether this becomes true item-domain separation or only filtering |
| BOM / bundle | PARTIAL | `material_bom`, `project_bom_lines`, `bom_operations` | component relations and operation cost primitives exist | revision, effectivity, alternates, refdes, EBOM/MBOM |
| Product resources/docs | IMPLEMENTED / PARTIAL | `material_resources`, attachments | links/files can be associated with a material | controlled revision/approval/effectivity not established |
| Inventory balance | IMPLEMENTED / NEEDS DEPTH AUDIT | `inventory`, `InventoryService`, inventory logs | available/locked/on-transfer counters and safety stock exist | reservation semantics, atomicity, bin split, lot/serial |
| Inventory ledger | IMPLEMENTED | `inventory_logs` and service-layer invariant | movements record delta, after-balance, reference/reason/user | immutability, reconciliation, location/lot dimensions |
| Stock count | IMPLEMENTED / NEEDS DEPTH AUDIT | `inventory_count_sessions/items`, test scripts | count session and review fields exist | freeze/snapshot race, recount, blind count, bin-level count |
| Warehouse locations | IMPLEMENTED / PARTIAL | `warehouse_locations`, `warehouse_layout_items` | zone/shelf/box and visual layout concepts exist | multi-bin quantity, putaway/pick path/scan confirmation |
| Procurement supplier master | IMPLEMENTED | `suppliers`, ProcurementService/API/UI | supplier records with payment/tax/contact fields | supplier item, lead-time, MOQ, approved supplier list |
| Purchase order | IMPLEMENTED / NEEDS DEPTH AUDIT | `purchase_orders/items`, service/API | draft/submit/approval/completion fields and line quantities/costs | cancellation, change control, partial close, expected-vs-actual |
| Purchase receiving | IMPLEMENTED / NEEDS DEPTH AUDIT | `purchase_receipts/items`, received quantity | partial quantity primitive exists and landed allocation field exists | IQC/hold/reject, batch/lot capture, discrepancy workflow |
| Purchase price history | IMPLEMENTED | `material_purchase_prices` | receipt-linked purchase/landed price history | currency conversion, supplier quotation history |
| Labor/operation cost | PARTIAL | `labor_cost_profiles`, `bom_operations` | setup/run time, workers, fixed cost and overhead-rate primitives | routing/work-center/actual time/variance |
| Price lists | IMPLEMENTED | `price_lists`, `material_prices` | currency/channel/customer group, quantity and validity fields | precedence conflicts, channel publication |
| Pricing rules | IMPLEMENTED / NEEDS DEPTH AUDIT | `pricing_rules`, `PricingService` | rule-based price calculation primitives exist | deterministic rule engine and explainability |
| Price audit/revisions | IMPLEMENTED | material/order item revision tables | before/after and reason are stored | append-only protection and finance-grade audit |
| Order ingest adapters | IMPLEMENTED / PARTIAL | `OrderAdapter`, Website/Taobao/PDD/Manual adapters | common normalized order shape exists | real connector coverage, retries, webhooks, reconciliation |
| OCR/image order recognition | IMPLEMENTED / NEEDS DEPTH AUDIT | `recognition.py`, queue, tasks, corrections/revisions, stress tests | asynchronous OCR queue, human correction evidence, derivatives | accuracy metrics, provider fallback, privacy/cost controls |
| Human confirmation before order | IMPLEMENTED | docs + service flow + recognition revision model | recognition result is reviewed before formal order | edge-case bypass review |
| Orders | IMPLEMENTED / NEEDS DEPTH AUDIT | `orders`, `order_items`, OrderService/API/UI | platform/order key, receiver, status, sync status, item lines | reservation, split/backorder, cancellation/refund integrity |
| Shipment task | IMPLEMENTED | `shipment_tasks`, scan logs, ShipmentService | assignment, logistics, scan evidence, completion | pack/label/carton, partial shipment, multi-package |
| Inventory deduction at completion | IMPLEMENTED | service-layer business invariant | source docs and services treat completion as stock-deduction point | concurrent completion/idempotency |
| Inter-warehouse transfer | IMPLEMENTED / NEEDS DEPTH AUDIT | transfer orders/items/receipt events, service + extensive iteration history | source/destination, transit, partial receive, exception workflow | exact stock semantics and rollback/idempotency |
| Exception management | IMPLEMENTED / PARTIAL | ExceptionService, transfer exception fields, UI index | exception primitives and workflow exist | unified exception taxonomy/SLA/escalation |
| Notifications | IMPLEMENTED / PARTIAL | `app_notifications`, NotificationService, Feishu notifier | in-app notification and Feishu integration primitives | durable delivery/retry/escalation independent of Actions |
| Unified todo | IMPLEMENTED / NEEDS DEPTH AUDIT | `UnifiedTodoService` imported by server | work aggregation layer exists | coverage, ownership, due dates, SLA |
| Voice documents | IMPLEMENTED / PARTIAL | `voice_documents`, VoiceDocumentService, server production inbound path | speech-derived draft/confirm workflows can create business actions | command safety, confirmation, supported document families |
| Platform account / SKU mapping | IMPLEMENTED / NEEDS DEPTH AUDIT | account/credential/mapping tables + PlatformAccountService | account and product/SKU mapping data exists | credential safety, actual sync, conflict/retry/reconcile |
| Taobao integration | PARTIAL TO IMPLEMENTED | Taobao adapter/client docs and source references | more than a placeholder, but external reliability not proven here | API coverage, auth renewal, sync reconciliation |
| Pinduoduo adapter | PARTIAL | `PddOrderAdapter` normalized shape | adapter class exists | actual remote client/webhook/sync path not yet proven |
| Website adapter | PARTIAL | `WebsiteOrderAdapter` | normalized ingestion contract exists | authentication/webhook/idempotency contract |
| Backup / restore | IMPLEMENTED / NEEDS DEPTH AUDIT | BackupService and `/api/backups*` documented | create/list/download/delete/restore paths exist | crash consistency, off-host copy, encryption, restore drill |
| Import/export | IMPLEMENTED / NEEDS DEPTH AUDIT | ExcelImportService/ImportService/CSV endpoints | precheck/import/export foundations exist | schema versioning, rollback, massive file behavior |
| PC web client | IMPLEMENTED | `inventory_app/static/app.js` and styles | broad administrative/operations UI | monolith UI debt and task efficiency |
| Mobile online PWA | IMPLEMENTED | `mobile/` | server-backed mobile workflows | feature parity, weak-network behavior, scan flow |
| Android wrapper | IMPLEMENTED | `android-offline-app` README/Java project | current behavior is online WebView despite legacy directory name | naming/build cleanup and release signing |
| iOS wrapper | IMPLEMENTED / PARTIAL | `ios-app` WKWebView + share extension | online mobile wrapper and image sharing | distribution/signing/runtime parity |
| Browser offline inventory | IMPLEMENTED / ISOLATED | `mobile-offline/` | local browser data + sync package concept | conflict model, authority and future support decision |
| Production material inbound | PARTIAL | server voice path uses `movement_type=production_inbound` | production-tagged stock movement exists | no production-order genealogy established |
| Work orders / manufacturing orders | NOT FOUND IN PINNED SOURCE | no `work_order` result in pinned code search | no canonical production order entity found | design required |
| MRP / shortage explosion | DOCUMENTED / NOT IMPLEMENTED | MRP appears in design/reference docs; old OSS plan explicitly deferred complex MRP | no material requirements planning engine found | design required |
| Lot/batch genealogy | NOT FOUND IN PINNED SOURCE | no lot-number entity found | current inventory is aggregate balance | design required |
| Finished-goods serial genealogy | NOT FOUND IN PINNED SOURCE | no serial-number entity found | cannot prove unit-level traceability | design required |
| Engineering revision / ECN/ECO | NOT FOUND IN PINNED SOURCE | no ECN entity found | price revisions exist, but not engineering change control | design required |
| EBOM -> MBOM | NOT FOUND AS CONTROLLED FLOW | two BOM-like structures exist | no controlled conversion/effectivity flow found | design required |
| Incoming/in-process/final QC | NOT FOUND AS COMPLETE DOMAIN | receiving/exception primitives exist | no IQC/IPQC/FQC/OQC domain model found | design required |
| RF/electrical test genealogy | NOT FOUND AS COMPLETE DOMAIN | material resources can hold files | no serial/lot-linked test-result entity found | design required |
| RMA / repair / warranty | NOT FOUND AS COMPLETE DOMAIN | order/shipment history exists | no RMA/repair/warranty entity found in W1 evidence | design required |
| CRM/quote/sample pipeline | NOT FOUND AS COMPLETE DOMAIN | customer_group exists in pricing | no customer/opportunity/quotation/sample state model established | design required |
| Finance/general ledger | INTENTIONALLY ABSENT | old OSS plan explicitly deferred full accounting | operational cost/pricing is not financial accounting | integration boundary decision later |

## 3. Workflow chains already credible

### 3.1 OCR-to-fulfilment

`image -> recognition task/queue -> normalized result -> human confirmation -> order/order items -> shipment task -> scan/logistics -> completion -> inventory movement + operation log`

This is one of the system's strongest differentiated chains and should be preserved during future modularization.

### 3.2 Inter-warehouse transfer

`create -> approve/confirm as applicable -> source shipment -> in transit -> receive/partial receive -> discrepancy/exception -> completion -> dual-side inventory/log evidence`

Iteration history shows this workflow has received repeated edge-case work, including undoing shipment and cumulative partial receiving.

### 3.3 Purchase-to-cost

`supplier -> purchase order -> approval -> receipt -> received quantity -> landed purchase price history -> material/product cost calculation`

The foundation is useful, but the manufacturing side is incomplete because there is no production order consuming these costs into actual unit/batch genealogy.

## 4. High-value capability gaps for an electronics business

### P0 / structural correctness before scaling

1. Make stock-location semantics capable of multiple bins per material and auditable bin-level movement.
2. Define reservation/allocation semantics separately from simple locked quantity.
3. Eliminate SQLite/PostgreSQL schema drift before claiming database portability.
4. Establish strict idempotency rules for remote order sync, shipment completion, transfer receive and purchase receive.
5. Strengthen schema-level relational integrity instead of relying primarily on service code.

### P1 / electronics R&D and manufacturing

1. Electronic part master: manufacturer, MPN, package, lifecycle, parametric fields, datasheet, supplier part number.
2. AVL/AML and alternates/substitutes.
3. BOM revision/effectivity + reference designator.
4. ECN/ECO approval and where-used impact analysis.
5. MRP/shortage explosion.
6. Work order/kitting/issue/return/scrap/completion.
7. Lot/serial genealogy.
8. IQC and final/test record linkage.

### P1 / commerce & after-sales

1. durable platform sync job/retry/reconciliation layer;
2. returns/refunds/RMA;
3. customer/quote/sample lightweight flow;
4. real contribution margin including platform fee, payment fee, shipping, refund and warranty cost.

## 5. Architecture signal

The product is already beyond the scale where all business growth should continue by appending logic to four very large central files. The correct near-term response is **not** a microservice rewrite. It is a controlled modular-monolith split around domain boundaries while preserving existing service invariants and local deployability.

Candidate domain packages for later design:

- identity_access
- catalog_parts
- inventory_warehouse
- purchasing
- sales_orders
- fulfilment
- transfers
- pricing_cost
- recognition
- integrations
- manufacturing
- quality_traceability
- aftersales
- reporting_automation

## 6. No-GitHub-Actions compliance

All later validation must have a repository-local or server-local command. Recommended future examples include `tools/test_all.py`, deterministic migration checks, local API smoke tests, and server-side worker/service health checks. CI may call these commands, but CI cannot own the commands or the correctness model.

## 7. Next tasks unlocked by this map

- `TASK_INV_AUDIT_DATA_MODEL_01`
- `TASK_INV_AUDIT_API_PERMISSION_01`
- `TASK_INV_AUDIT_FRONTEND_UX_MAP_01`
- `TASK_INV_AUDIT_CODE_ARCHITECTURE_01`
- `TASK_INV_AUDIT_DOC_TRUTH_01`

The capability map should be revised only when new code evidence changes a classification; absence statements above are scoped strictly to the pinned commit.