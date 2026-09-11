# TASK_INV_AUDIT_UX_HEURISTICS_01 — Desktop UX and Information-Architecture Audit

## 0. Scope and evidence boundary

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed PC application architecture, prior frontend journey audit, page/menu breadth, operational dashboard behavior and source-size/maintainability findings.

This is a **static heuristic review**. It identifies structural friction and testable UX hypotheses; it does not claim to replace observation of warehouse/sales/admin users performing real tasks.

## 1. Executive conclusion

The desktop product is feature-rich and has already accumulated practical workflow refinements. Its next UX problem is no longer “missing screens”; it is **information architecture, context switching and safe high-frequency interaction** as domain breadth grows.

The highest-value direction is:

```text
Find the business object quickly
 -> see its complete context
 -> understand current state and next valid actions
 -> perform action with preview/validation
 -> receive an auditable result
```

rather than continuing to add menu pages.

Preliminary maturity:

- feature breadth: 4/5
- operational edge-case attention: 4/5
- navigation scalability: 3/5
- entity-centered context: 2/5
- bulk/high-frequency efficiency: 2.5/5
- consistency across growing domains: 2.5/5
- error prevention/action receipts: 3/5
- accessibility/keyboard evidence: 2/5 pending hands-on validation.

## 2. Heuristic: match the system to the user's work

Current architecture is page/domain oriented. Real tasks cross domains.

Examples:

### Procurement shortage

Current mental journey can span:

```text
inventory warning -> material -> supplier -> purchase history -> PO -> receive
```

Target workspace should preserve the shortage context while opening supplier/PO decisions.

### Customer shipment

```text
order -> stock availability -> warehouse/location -> scan/pick -> logistics -> platform sync
```

The user should not manually rediscover the same order/material context on every page.

### Engineering part

```text
material -> specs -> BOM uses -> supplier/price -> stock -> docs -> revisions
```

This strongly argues for entity-centered workspaces/drawers.

## 3. Information architecture

Recommended top-level navigation remains:

```text
Today / My Work
Orders & Fulfilment
Inventory & Warehouse
Purchasing
Products & Engineering
Production
Quality & Traceability
Sales & Aftersales
Business Analysis
Master Data
System
```

Only show future groups when corresponding features exist.

The key is not exact labels. The key principle is to separate:

- task execution;
- business object management;
- analysis;
- configuration/master data.

Avoid mixing settings/master-data pages into everyday transaction flows.

## 4. Role-tailored home pages

Do not create entirely different applications per role. Use one shell with tailored starting views.

### Warehouse

- pending shipment/pick;
- transfer receive;
- count tasks;
- stock/location exceptions.

### Procurement

- shortages/replenishment suggestions;
- POs awaiting action;
- overdue supply;
- supplier exceptions.

### Sales/support

- inquiries/quotes/follow-ups;
- order/RMA/customer cases;
- sample/evaluation status.

### Owner/admin

- cross-domain critical exceptions;
- approvals;
- inventory cash/profit/product health.

Permissions determine data/actions server-side; role home only improves navigation.

## 5. Global search as primary navigation

A user should not need to know which module contains an identifier.

Global search should support:

- material/enterprise SKU;
- name/model/spec;
- manufacturer/MPN;
- alias;
- barcode/QR;
- order number;
- logistics number;
- PO/transfer/work-order number;
- supplier/customer;
- serial/lot;
- RMA/case;
- warehouse/location.

Results should show type/status/context and open the correct workspace directly.

## 6. Entity workspace pattern

### Material / part

Tabs/sections:

```text
Overview
Stock & Locations
Movements
Purchasing / Suppliers
BOM / Where-used
Pricing / Sales
Specifications
Documents
Revisions / Changes
Quality / Test later
```

### Order

```text
Overview
Customer/address snapshot
Lines/pricing
Reservation/allocation
Shipment/packages
Platform sync
Refund/RMA
Activity/audit
```

### Serial

```text
Configuration
Manufacturing genealogy
Test history
Shipment/customer
RMA/repair
```

This reduces repeated modal/page lookup.

## 7. Visibility of system status

Every long-running or cross-system action needs explicit state.

Examples:

- platform sync: queued / processing / succeeded / retrying / manual review;
- OCR: uploaded / recognizing / needs confirmation / failed;
- import: preview / confirming / completed / partial errors;
- backup: running / created / verified / failed;
- report: stale / calculating / current;
- future MRP: input snapshot / running / recommendation ready.

Avoid generic spinners with no object/state identity.

## 8. User control and reversibility

For consequential actions distinguish:

### Reversible

Can offer undo through a compensating business transaction.

### Correctable but not undoable

Require a correction/reversal workflow.

### Destructive administrative

Require typed/object-specific confirmation and clear impact.

Never imply that deleting a transaction history row is normal undo.

The current transfer/shipment reversal patterns should become UI conventions.

## 9. Error prevention before validation after failure

High-value preflight patterns:

- show available/reserved/required quantity before shipment/issue;
- show affected rows before bulk import;
- validate duplicate material/order identities before save;
- show old/new price and margin impact;
- preview transfer receive discrepancies;
- warn if document/BOM revision is obsolete;
- block unapproved substitute;
- display exact warehouse/location scope.

Use warnings only when the user can legitimately proceed; otherwise block with a clear remediation path.

## 10. Confirmation quality

Avoid generic:

```text
确定吗？
```

Use action-specific confirmation:

```text
Confirm receipt of 48 pcs into East Warehouse / A-03?
PO remaining after receipt: 12 pcs.
```

For stock/money/customer-impact actions show:

- object;
- quantity/value;
- from/to state/location;
- irreversible consequence;
- reason field when exceptional.

## 11. Action receipts

After mutation, show compact receipt:

```text
Shipment completed
Order: ...
Stock deduction: ...
Warehouse: ...
Platform sync: queued
Operation ID: ...
```

This builds operator trust and gives support a reference when something goes wrong.

## 12. Search/filter behavior

List pages should converge on a consistent pattern:

- global keyword;
- structured filters;
- active filter chips;
- clear reset;
- stable sort;
- cursor pagination;
- result count when affordable;
- saved views;
- URL/deep-link state where practical.

Do not implement different filter semantics on every page.

## 13. Saved views

High-value examples:

- `My overdue POs`;
- `Production parts below cover`;
- `Orders waiting > 24h`;
- `Unmapped marketplace SKUs`;
- `Quarantine stock`;
- `RMA awaiting diagnosis`;
- `EOL parts with open demand`;
- `Negative-margin orders`.

Saved views are often more useful than another dashboard card.

## 14. Bulk actions

Desktop should exploit dense-screen advantage.

Useful bulk operations:

- assign tasks;
- approve/reject where policy allows;
- print labels/documents;
- add category/lifecycle metadata;
- create replenishment/PO draft from suggestions;
- export selected records;
- acknowledge alerts.

Safety contract:

```text
select -> preview impact -> validate all -> show failures -> explicit commit -> result receipt
```

Never partially apply dangerous bulk stock actions without a clear per-row result and transaction policy.

## 15. Keyboard efficiency

High-frequency office/admin flows should support:

- predictable tab order;
- Enter to submit only where safe;
- Escape to close non-destructive modal;
- keyboard focus after dialog;
- shortcuts for global search;
- copy identifiers;
- arrow/table navigation if implemented accessibly.

Do not add dozens of hidden shortcuts. Start with search, save/submit and common list navigation.

## 16. Density and progressive disclosure

ERP-like systems fail when every field is shown at once.

Recommended information layers:

- list: identity + state + one or two decision metrics;
- workspace header: critical context/alerts/actions;
- details/tabs: full information;
- advanced/raw/audit sections: secondary.

For RF part records, a summary might show MPN, package, lifecycle, stock/shortage and preferred supplier before detailed parametric attributes.

## 17. Terminology consistency

Create one shared vocabulary for:

- available / physical / reserved / in-transit;
- shipment task vs order;
- material vs product vs SKU vs MPN;
- quote vs order;
- refund vs return vs RMA;
- standard cost vs estimated cost vs actual cost;
- margin vs markup;
- draft/released/obsolete revision.

The W2 pricing audit already found a `margin_percent` semantic risk; UI wording must not perpetuate model ambiguity.

## 18. Empty states

Good empty state answers:

- what this page contains;
- why there may be no records;
- what the next allowed action is;
- whether filters are hiding records.

Examples:

`No overdue purchase orders` is success, not an error.

`No materials found because warehouse filter excludes them` should show the filter context.

## 19. Loading and stale-data states

For dense operational pages:

- keep previous content visibly stale while refreshing where safe;
- show last updated time for external/analytical data;
- prevent stale request from overwriting a newly navigated page;
- require fresh server confirmation before consequential writes;
- show optimistic UI only for actions that can safely roll back.

Prior mobile work already addresses stale-response navigation; apply the same principle broadly.

## 20. Cross-window/deep-link behavior

Identifiers should support copyable links so support/engineering can share exact object context.

Deep links should preserve:

- entity ID;
- relevant tab;
- optional safe filter;

Avoid requiring colleagues to say “go to Inventory, then search X, then click second row.”

## 21. Accessibility

Static source review cannot prove accessibility. Add hands-on checks for:

- visible focus;
- keyboard-only completion of major PC flows;
- semantic buttons/labels;
- contrast;
- status not encoded by color alone;
- zoom/text scaling;
- screen-reader labels for critical forms if required;
- confirmation/error messages associated with fields.

Treat accessibility as usability infrastructure, not a late cosmetic pass.

## 22. Performance perception

Large client files and broad pages can increase perceived latency even when server is fast.

UX performance goals:

- shell renders quickly;
- page requests are cancellable/ignored when stale;
- lists use cursor pagination;
- heavy analysis loads on demand;
- entity summary does not fetch every tab before display;
- actions acknowledge quickly with durable queued state for slow background work.

## 23. Onboarding and in-context help

For infrequent/complex functions use contextual guidance:

- what `available/reserved` means;
- why a shipment is blocked;
- why an alternate needs engineering approval;
- what a price-cost basis means;
- why a returned unit is quarantined.

Prefer concise help near the decision over a giant manual.

## 24. Measurement plan

Run timed task studies with actual roles.

Example tasks:

- find stock/location of a part;
- receive a partial PO;
- complete a shipment;
- find reason an order is blocked;
- find latest supplier price;
- identify product test report by serial;
- create quote from inquiry;
- handle RMA.

Measure:

- completion time;
- navigation count;
- typing count;
- error/recovery count;
- help requests;
- abandonment;
- confidence/ambiguity notes.

Use the results to rank UX changes.

## 25. Priority roadmap

### P0

1. global cross-entity search;
2. entity workspace pattern;
3. consistent filter/list/pagination language;
4. action-specific confirmation + mutation receipts;
5. role-tailored `My Work` starting views;
6. shared terminology/status dictionary;
7. safe bulk-action preview/result convention;
8. keyboard/focus baseline tests.

### P1

1. saved views;
2. deep links;
3. contextual action drawer;
4. cross-domain exception context;
5. approval center;
6. engineering/product workspace;
7. management cockpit separation.

### P2

1. command palette;
2. customizable workspace/dashboard;
3. AI-assisted navigation/query;
4. advanced user personalization after core IA stabilizes.

## 26. Acceptance signals

- a user can locate an arbitrary known identifier without knowing its module;
- material/order/serial workspaces expose cross-domain context without repeated manual searches;
- high-risk actions show object/quantity/state impact before commit;
- every mutation returns a clear result/operation reference;
- list filters/pagination behave consistently;
- top warehouse/admin tasks are keyboard/touch efficient for their device class;
- stale network responses cannot overwrite current navigation state;
- role home pages reduce irrelevant menu scanning without weakening server authorization;
- UX improvements are verified with timed real-user scenarios, not only screenshots;
- no required UX/browser validation depends on GitHub Actions.

## 27. Core recommendation

Stop treating navigation growth as a menu-search problem alone. The desktop UX should evolve from **page-centric administration to entity- and task-centric workspaces**, with global search, persistent context, consistent state/action language and auditable action receipts. That will make the planned manufacturing/CRM/quality expansion usable without making the system feel like a traditional overloaded ERP.