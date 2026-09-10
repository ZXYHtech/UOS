# TASK_INV_AUDIT_FRONTEND_UX_MAP_01 — PC, Mobile, Offline UX & Journey Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Evidence reviewed from current client trees, development index, Android/iOS wrappers and iteration history. This is a static workflow/interaction audit; it does not pretend that UI source inspection replaces real operator usability testing.

No GitHub Actions dependency is assumed for UX validation.

## 1. Current client portfolio

The repository contains five distinct user-facing surfaces:

1. **PC Web** — `inventory_app/static/`
2. **Mobile online PWA** — `mobile/`
3. **Browser offline PWA** — `mobile-offline/`
4. **Android WebView wrapper** — `android-offline-app/`, now functionally online despite its legacy name
5. **iOS WKWebView wrapper** — `ios-app/`

This is already a multi-client product, not simply a responsive web page.

## 2. Core user journeys

### 2.1 Management / administrator

Typical path:

`dashboard -> exceptions/todos -> orders/inventory/procurement -> product/pricing -> users/settings/logs`

Needs:

- compact exception-first overview;
- cross-warehouse search;
- profitability and stock-risk decisions;
- approval queues;
- drill-down without losing filter state;
- batch operations.

### 2.2 Warehouse operator

Typical path:

`pending shipment -> accept -> locate stock -> scan/pick -> logistics -> complete`

and:

`transfer -> source confirmation -> receive -> discrepancy`

Needs:

- scan-first operation;
- minimal typing;
- very clear current task and next action;
- large touch targets;
- physical location visible before quantity;
- mismatch must stop the flow rather than become a warning buried in text.

### 2.3 Purchasing / supply

Typical path:

`stock warning/replenishment -> supplier -> PO -> approval -> receipt -> price/cost history`

Needs:

- shortage context;
- supplier/price/lead-time comparison;
- partial receive status;
- outstanding quantity;
- exception/late receipt handling;
- future MRP demand linkage.

### 2.4 Product / engineering

Current path is fragmented across:

`materials -> categories -> aliases -> project BOM -> specifications/resources -> cost/pricing`

Needs for electronics expansion:

- one material/part workspace;
- parametric search;
- manufacturer/MPN/supplier part identity;
- BOM where-used;
- revision/status/document control;
- lifecycle/substitute/AVL visibility;
- engineering stock and prototype history.

### 2.5 Customer service / sales

Current useful anchors:

`orders -> recognition history -> shipment/logistics -> pricing -> platform status`

Missing future workspace:

`customer/inquiry/quote/sample -> order -> shipment -> return/RMA -> repair/replacement`

## 3. Strong UX characteristics already present

Iteration history indicates active work on real operator friction rather than decorative dashboards. Examples include:

- cursor pagination for large orders/tasks/transfers/inventory lists;
- mobile weak-network navigation protection so stale requests do not overwrite the current page;
- transfer receive explicitly separates normal versus abnormal receipt;
- cumulative partial receiving and exception reasons;
- undo/retry safety around transfer shipment;
- A4 print workflows and Android native printing;
- search/category/product-management refinements;
- OCR correction workflows based on real error patterns.

This is important: the product already has a culture of solving operational edge cases. Future UX work should preserve that mindset.

## 4. Major UX debt

### U1 — navigation breadth is outgrowing the original application shell

The development index shows many PC page keys and menu groups across orders, shipments, inventory, transfers, purchasing, suppliers, cost, pricing, product data, categories, warehouses, locations, accounts, settings and logs.

The existing feature-map/favorites/menu-search work helps, but the long-term problem is no longer merely “find a menu item.” Users need task-oriented workspaces.

Recommended top-level IA:

```text
Today / 我的工作
Orders & Fulfilment
Inventory & Warehouse
Purchasing
Products & Engineering
Production (future)
Quality & Traceability (future)
Sales & Aftersales (future)
Business Analysis
Master Data
System
```

### U2 — entity information is scattered across pages

A material can participate in inventory, locations, orders, transfers, BOM, purchasing, supplier history, price, specs/resources and future production/quality.

A high-value UX improvement is a universal **entity workspace/drawer**:

`material -> summary / stock / location / movements / purchase / BOM / price / orders / docs / changes`

Future electronics fields fit naturally into the same workspace.

### U3 — page-centric UI should evolve toward task-centric UI

Warehouse users should not navigate multiple management pages to finish one physical task.

Future scan/task UI should use a persistent state machine:

```text
Task
 -> required item/location
 -> scan
 -> validate
 -> quantity
 -> next item
 -> exception or finish
```

The operator should always know:

- what am I doing;
- what is expected now;
- what was scanned;
- what is wrong;
- what is the next safe action.

### U4 — PC and mobile should share domain language, not necessarily layout

Do not force one identical interface. PC is better for dense comparison/batch editing; mobile is better for guided physical execution.

Shared contracts should include:

- status names;
- exception types;
- permission-driven actions;
- scan payload format;
- API errors;
- entity identifiers;
- workflow transitions.

### U5 — offline product direction is unclear

`mobile-offline/` still exists as an independent local-data application while current Android is online-only. This creates a product-strategy choice:

A. retire offline business mutation and keep only offline read/cache;
B. maintain a true offline-first operational client with conflict resolution;
C. keep offline PWA only as an emergency/legacy tool.

Do not continue adding offline capabilities until authority/conflict semantics are explicitly chosen.

## 5. Mobile UX target for warehouse operations

### Scan-first home

Primary actions:

- scan shipment task/logistics code;
- scan material;
- scan location;
- receive transfer;
- stock count;
- quick lookup.

### Contextual action instead of manual menu selection

A scanned code should resolve to candidate actions based on object type and user permissions.

Example:

`scan material -> show stock by location + pending tasks requiring it + move/count options`

`scan transfer -> open receive workflow`

`scan location -> show expected contents + count/move tasks`

### Offline/network states must be explicit

Never silently pretend a write succeeded.

Use states such as:

- submitted and confirmed by server;
- pending local retry;
- failed, operator action required;
- conflict, review required.

## 6. PC UX target

### Global search / command surface

Search across:

- material code/model/name/MPN/alias;
- order number;
- logistics number;
- transfer/PO number;
- warehouse/location;
- supplier;
- future serial number/RMA.

Result should open an entity workspace directly rather than forcing the user to know which module owns it.

### Saved views

Allow users to save filters such as:

- low-stock production parts;
- overdue POs;
- orders waiting > X;
- transfer exceptions;
- materials missing classification;
- future EOL parts with open demand.

### Bulk operation safety

For destructive/stock-changing bulk actions:

1. preview affected records;
2. show validation errors before commit;
3. explicit final confirmation;
4. idempotent server operation;
5. audit receipt/result summary.

## 7. Electronics R&D UX requirements

A future engineering workspace should make the following relationships visible without jumping across many pages:

```text
Internal Part
├─ manufacturer + MPN
├─ parametric attributes
├─ package / footprint
├─ lifecycle / preferred status
├─ suppliers / supplier part numbers / price breaks
├─ substitutes / AVL
├─ datasheet / drawing / test docs
├─ current BOM uses
├─ revisions / ECN history
├─ stock by location/status
└─ open shortage / purchase / production demand
```

For a finished RF module/product:

```text
Product revision
├─ EBOM / MBOM
├─ firmware
├─ drawings
├─ test specification
├─ production batches
├─ serial numbers
├─ measured test reports
└─ customer/RMA history
```

## 8. Reduce repetitive manual input

High-value automation targets:

- remember last warehouse/location within a task session;
- barcode/QR selection instead of typing codes;
- auto-fill supplier/last purchase price with explicit confirmation;
- suggested warehouse based on stock and task scope;
- address/order recognition with confidence and human confirmation;
- batch upload with pre-validation;
- default filters per role;
- one-click exception creation from the current failed operation;
- copy/duplicate BOM/price/PO only through controlled version semantics.

## 9. Feedback design

Every consequential action should return a small receipt:

```text
What changed
Which object
Quantity/value before -> after
Reference document
Operator
Time
Any follow-up task
```

This is more useful than generic “success” to warehouse and admin users.

## 10. Accessibility and error prevention

Future UI review should verify:

- keyboard operation for dense PC workflows;
- visible focus states;
- not relying only on color for status;
- touch targets suitable for mobile warehouse use;
- confirmation wording identifies object and quantity;
- no ambiguous “确定” dialog for irreversible operations;
- long identifiers can be copied/scanned;
- network failure never produces optimistic stock state without server confirmation.

## 11. Suggested UX backlog priorities

### P0

1. entity/global search;
2. material/product unified workspace;
3. task-centric warehouse mobile flow;
4. explicit offline/network write states;
5. shared status/action contract across PC/mobile;
6. client portfolio decision for offline PWA;
7. stock location model fix before advanced location UX.

### P1

1. saved role-specific views;
2. scan-anything contextual action;
3. purchasing shortage workspace;
4. exception inbox with owner/SLA/next action;
5. approval center;
6. engineering part/BOM workspace;
7. global notification/todo action center.

### P2

1. customizable dashboards;
2. command palette;
3. natural-language query/AI copilot;
4. advanced warehouse path optimization;
5. role-level onboarding/walkthroughs.

## 12. UX validation without GitHub Actions

Recommended local/manual test assets:

- repository-contained deterministic demo database generator;
- scripted API fixture setup;
- Playwright or browser test runner executable locally if a browser-test dependency is later accepted;
- otherwise current JS syntax/unit checks + manual scenario checklist;
- Android/iOS device scenario checklist;
- warehouse workflow timed-task study;
- low-bandwidth network simulation;
- 500/5,000/50,000-row synthetic list benchmarks.

GitHub Actions is not required for any of the above.

## 13. Preliminary UX score

0–5 static maturity:

- operational edge-case attention: **4/5**
- PC feature breadth: **4/5**
- mobile operational support: **4/5**
- navigation scalability: **3/5**
- entity-centered information architecture: **2/5**
- scan-first warehouse ergonomics: **2.5/5**
- offline authority/conflict clarity: **2/5**
- engineering/manufacturing UX readiness: **1.5/5**
- cross-client maintainability: **2/5**

## 14. Core recommendation

Do not prioritize cosmetic redesign. The biggest UX gain will come from aligning the interface with real operating objects and tasks:

`find object fast -> see complete context -> perform the next valid action -> scan/validate instead of type -> receive an auditable result -> handle exceptions in place`

That direction also prepares the product for manufacturing without turning it into a cluttered ERP menu tree.