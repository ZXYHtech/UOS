# TASK_INV_AUDIT_OSS_WMS_01 — Warehouse Management System Deep Benchmark

## 0. Scope and freshness

Research date: **2026-09-11**.

Inventory Lite evidence remains pinned to `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Benchmarks:

- OpenBoxes 0.9.8;
- Odoo 19 Inventory / Barcode patterns;
- ERPNext Stock patterns;
- OpenWMS.org as an architecture contrast for larger automated warehouses.

This report focuses on warehouse process design, not general ERP replacement.

## 1. Current maintenance / license snapshot

| System | Current evidence | License | Relevance |
|---|---|---|---|
| OpenBoxes | `v0.9.8` released 2026-06-13; active 2026 docs/release/security fixes | EPL-1.0 | Strong receiving/putaway/bin/stock-movement model, pragmatic WMS reference |
| Odoo Inventory 19 | Current 19.0 docs | LGPL-3 core/community code; feature edition must be checked | Rich routes, reservations, putaway/removal, cycle count, batch/wave/cluster/barcode patterns |
| ERPNext Stock | Actively maintained v15/v16 | GPL-3.0 | Stock ledger, warehouse, pick list, stock reconciliation, serial/batch, barcode scan |
| OpenWMS.org | Current repository builds on Spring Boot 3.x/JDK 25; latest tagged root release shown as 3.0.0 | Apache-2.0 | Automated/manual WMS + MFC architecture; useful as a complexity ceiling, not target stack |

## 2. OpenBoxes — strongest direct WMS reference

OpenBoxes is specifically designed around inventory and stock movement, and its current documentation shows operational concepts directly relevant to Inventory Lite.

### 2.1 Receiving has real state

OpenBoxes receiving distinguishes statuses such as:

```text
Pending
Shipped
Partial Received
Received
```

Only a shipped or partially received movement can be received; a fully received shipment is not simply received again.

This validates Inventory Lite's existing transfer/receipt state-machine direction: warehouse actions need valid source-document states, not generic quantity edits.

## 3. OpenBoxes receiving -> putaway boundary

One of OpenBoxes' most portable patterns is a **receiving staging location**.

Current docs describe:

```text
Inbound shipment
 -> Receiving Bin (R-<shipment>)
 -> Putaway task
 -> physical Bin Location(s)
```

Putaway can:

- display receiving candidates;
- group by stock movement or product;
- filter by lot;
- use preferred bin;
- split one received quantity across several bins;
- generate a putaway list;
- complete the move only after final review.

### Inventory Lite implication

Do not require the receiver to know the permanent bin at the moment the truck/package is received.

Target:

```text
physical receipt / quality state
 -> receiving/staging stock position
 -> putaway task
 -> final bin positions
```

This also aligns naturally with IQC quarantine.

## 4. OpenBoxes inventory item + bin + lot

Putaway API examples expose:

- inventory item;
- lot number;
- expiration date;
- current facility/location/bins;
- destination putaway location;
- quantity.

This reinforces the W3/W6 electronics conclusion that bin/lot/quality differences belong below aggregate material/warehouse quantity.

A warehouse row should not carry one optional `location_id` while its uniqueness remains at warehouse/account level.

## 5. OpenBoxes stock movement as workflow aggregate

OpenBoxes `StockMovement` is a business object connecting origin, destination, line items and workflow status.

Its status API demonstrates transitions such as:

```text
REVIEWING -> PICKING -> PICKED -> ...
```

and can generate pick-list suggestions. Picking records concrete inventory item + bin + quantity, and rejects quantity beyond on-hand.

### Portable pattern

Separate:

```text
Demand/transfer/shipment document
 -> warehouse execution task
 -> pick allocation
 -> physical movement ledger
```

Inventory Lite's current shipment task is already moving this direction. Extend it consistently to PO putaway, WO kitting and RMA receipt.

## 6. OpenBoxes rollback events

OpenBoxes 0.9.8 release notes explicitly include shipment rollback events. This is important because mature WMS products generally correct executed movements through explicit reversal/rollback semantics rather than deleting history.

Inventory Lite's own transfer/shipment reversal behavior is therefore a strength to standardize.

## 7. OpenBoxes product/security caution

The same 0.9.8 release also fixed serious security issues involving:

- Zebra template rendering;
- caller-supplied document URLs / SSRF;
- role/privilege escalation.

Portable lesson:

WMS extensions such as label templates, remote documents and role administration are real security boundaries. Inventory Lite's future label/scan/document framework must use constrained templates, allowlisted fetch behavior and server-side permission checks.

## 8. Odoo — strongest warehouse-strategy catalogue

Odoo 19 Inventory documentation provides a broad set of warehouse algorithms and process patterns.

### Storage / inbound

- locations;
- multi-step routes;
- putaway rules;
- storage categories;
- one-/two-/three-step receipt;
- consignment;
- dropshipping.

### Reservation / outbound

- reserve at confirmation;
- manual reservation;
- reserve before scheduled date;
- one-/two-/three-step delivery.

### Picking optimization

- piece picking;
- batch picking;
- cluster picking;
- wave transfers.

### Removal strategies

- FIFO;
- LIFO;
- FEFO;
- closest location;
- least packages.

### Inventory control

- lot/serial;
- expiration;
- cycle counts;
- barcode operations;
- packages.

## 9. Odoo lesson: policy belongs on location/product, not hard-coded flow

Removal and putaway strategies can be configured by location/category/context.

Inventory Lite should eventually support a small policy layer:

```text
location_policy
  putaway strategy
  pick/removal strategy
  allowed material/category
  capacity constraints
  cycle-count frequency
```

Do not hard-code one FIFO algorithm globally.

For RF/electronics, useful early policies are much simpler than food/pharma:

- preferred bin;
- oldest accepted lot first;
- same-part consolidation;
- ESD/controlled area;
- quarantine never pickable;
- serial/lot-required product policy.

## 10. Odoo lesson: wave/batch only when volume needs it

Batch and wave picking optimize picker travel at high order volume. They are **not** the right P0 for a two-person/small warehouse.

Inventory Lite should first optimize:

1. reliable reservation;
2. exact bin allocation;
3. scan-first pick;
4. ordered pick path;
5. multi-order batch only once enough simultaneous shipments exist.

A useful future threshold is measured picker travel/task volume, not a desire to “look like a WMS.”

## 11. Odoo barcode lesson

Odoo Barcode workflows require scanning source location, product/package and can process batch/wave/cluster transfers.

This supports W5's proposed scan pattern:

```text
Task
 -> source location scan
 -> material/lot/serial scan
 -> quantity validation
 -> destination/package
 -> server-confirmed transaction
```

The barcode app is not merely a search shortcut; it is a guided state-machine UI.

## 12. Odoo cycle-count lesson

Cycle count is configured by location and schedules future counts. This is more useful than one annual `adjust inventory` page.

Inventory Lite target:

```text
count policy
 -> count task
 -> blind/assisted observation
 -> variance
 -> approval/disposition
 -> adjustment ledger
 -> next count date
```

High-risk/high-value bins can have more frequent count policy.

## 13. ERPNext — useful stock-ledger and reconciliation patterns

ERPNext provides:

- Stock Ledger;
- Warehouses;
- Pick List;
- Stock Reconciliation;
- Serial/Batch Bundles;
- barcode scanning in reconciliation.

Its Stock Reconciliation workflow can use scan mode to accumulate observed counts and then submit a controlled reconciliation.

### Portable lesson

A physical count is an **observation + reconciliation transaction**, not a direct editable balance cell.

Inventory Lite should keep:

```text
expected balance
observed count
variance reason/approval
adjustment ledger
```

as distinct evidence.

## 14. ERPNext Pick List lesson

ERPNext Pick List selects stock based on warehouse/availability and uses FIFO logic, with expiry-aware selection for batched items.

Inventory Lite should similarly separate:

- allocation algorithm suggestion;
- concrete picker-confirmed stock/lot/bin;
- final consumption/ship transaction.

The algorithm can suggest; scan/validation proves execution.

## 15. OpenWMS.org — useful as a complexity boundary

OpenWMS.org describes itself as an extensible WMS with a Material Flow Control system for automatic and manual warehouses. Its project is decomposed into business services/repositories and common event types.

This architecture is appropriate for automated material handling, conveyors, PLC/MFC integration and multi-service deployment—not for Inventory Lite's current scale.

### Portable ideas

- explicit transport/order concepts;
- device/material-flow boundary;
- event contracts;
- separate automation adapter from warehouse business state.

### Do not copy

- microservice topology;
- distributed messaging infrastructure;
- MFC abstractions without automated warehouse hardware;
- operational complexity requiring many deployable services.

Inventory Lite should remain a modular monolith.

## 16. Capability comparison

| Capability | OpenBoxes | Odoo 19 | ERPNext | OpenWMS.org | Inventory Lite target |
|---|---|---|---|---|---|
| Receipt states | Strong | Strong | Strong | Strong domain | Strengthen existing PO/transfer state |
| Receiving staging | Strong explicit Receiving Bin | Multi-step receipt | Warehouse/receipt flow | Strong | Add staging + IQC |
| Bin locations | Strong | Strong | Warehouse hierarchy / bins depending design | Strong | Make bin part of stock identity |
| Putaway | Strong task | Strong rules | Simpler | Strong | Preferred/rule-based P1 |
| Reservation | Movement/pick workflow | Strong configurable | Pick/allocation flows | Strong | P0 authoritative ledger |
| Picking | Strong | Strong | Pick List | Strong | Scan-first exact allocation |
| Batch/wave | Less central | Strong | More basic | Enterprise | P2 only when volume proves need |
| Removal strategy | FEFO-oriented | Very strong | FIFO/batch-aware | Configurable | Simple policy first |
| Cycle count | Current OpenBoxes supports cycle-count surfaces | Strong | Reconciliation | Strong | Task + observation + variance |
| Lot/serial | Strong inventory-item lot | Strong | Strong | Domain dependent | Risk-based W3 model |
| Barcode/mobile | Operational support | Strong Barcode app | Barcode scan | Device integration | Shared scan resolver |
| Reversal | Current rollback events | Reverse/cancel flows | Cancel/reconciliation | State/event model | Standard compensating ledger |
| Automation hardware | No core MFC focus | Limited | No | Core MFC strength | External adapter only |

## 17. Target Inventory Lite WMS model

The benchmark converges on this structure:

```text
Warehouse
  -> Zone / structural location
    -> Bin / stock location
      -> Stock Position
         material
         lot/serial
         quality state
         owner/reservation
         quantity
```

Business workflows:

```text
PO/Transfer/RMA receipt
 -> staging/receiving
 -> IQC if required
 -> putaway

Sales/WO demand
 -> reservation
 -> allocation
 -> pick
 -> pack/issue
 -> ship/consume

Count policy
 -> count task
 -> observation
 -> variance
 -> adjustment/review
```

This should be the WMS kernel before wave picking or route optimization.

## 18. Picking priority for RF/electronics

Suggested initial rule order:

1. qualified/accepted stock only;
2. exact reserved material/approved alternate only;
3. required lot/serial policy;
4. non-expired/released stock;
5. preferred location/shortest simple path;
6. oldest receipt/lot first where appropriate;
7. minimize split picks when equivalent.

Make policy explicit and explain suggested allocation.

## 19. Putaway priority for RF/electronics

Useful rule inputs:

- default/preferred part bin;
- available bin capacity;
- same material/lot already present;
- ESD area requirement;
- high-value locked area;
- quarantine/inspection state;
- package/reel dimensions later;
- pick frequency / fast-moving zone later.

Do not require AI for this. A deterministic rule engine is better initially.

## 20. WMS UX priorities

Mobile/handheld:

1. scan task;
2. scan source/destination location;
3. scan material/lot/serial;
4. enter/scan quantity;
5. immediate mismatch feedback;
6. server-confirmed receipt.

Desktop:

- workload/exception planning;
- location map/status;
- putaway/pick batch planning;
- cycle-count configuration;
- discrepancy resolution;
- productivity/aging analytics.

## 21. WMS KPIs worth adding

Only after the underlying timestamps/states exist:

- dock/receipt-to-putaway time;
- location accuracy;
- pick accuracy;
- order lines/hour or task duration;
- stockout due to misplaced stock;
- cycle-count variance;
- quarantine age;
- transfer discrepancy;
- stale receiving-bin stock;
- split-pick frequency;
- bin utilization where capacity modeled.

Do not optimize worker speed while compromising scan/traceability quality.

## 22. Recommended scope decisions

### Build now / P0

- stock-position identity by bin/state;
- receiving/staging location;
- authoritative reservation;
- exact pick allocation;
- scan-first receipt/pick/transfer/count;
- count observation + reconciliation;
- quality-state exclusion;
- compensating reversals.

### P1

- putaway rules/preferred bins;
- pick/removal strategies;
- cycle-count schedules;
- package/reel metadata;
- ordered pick path;
- warehouse productivity metrics.

### P2

- batch/cluster/wave picking;
- slotting optimization;
- hardware automation/MFC adapters;
- capacity optimization.

## 23. Sources

Current evidence consulted 2026-09-11:

### OpenBoxes

- Releases: https://github.com/openboxes/openboxes/releases
- Repository/license: https://github.com/openboxes/openboxes
- 0.9.8 release notes: https://community.openboxes.com/t/openboxes-v0-9-8-release-notes-june-2026/2032
- Receiving: https://help.openboxes.com/article/48-receiving
- Receiving/Putaway: https://help.openboxes.com/article/297-receiving-putaway
- Putaway API: https://docs.openboxes.com/en/docs-update-release-process/api-guide/putaway/
- Stock Movement: https://docs.openboxes.com/en/latest/api-guide/outbound/stockMovement/
- Stock Movement Item/Picking: https://docs.openboxes.com/en/develop/api-guide/outbound/stockMovementItem/

### Odoo 19

- Inventory: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory.html
- Putaway: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/shipping_receiving/daily_operations/putaway.html
- Locations/cycle counting: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/inventory_management/use_locations.html
- Cycle counts: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/inventory_management/cycle_counts.html
- Removal strategies: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/shipping_receiving/removal_strategies.html
- Batch picking: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/shipping_receiving/picking_methods/batch.html
- Wave transfers: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/shipping_receiving/picking_methods/wave.html
- Barcode batch transfers: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/barcode/operations/process_transfers.html

### ERPNext

- Stock reconciliation: https://docs.frappe.io/erpnext/stock-reconciliation
- Pick List: https://docs.frappe.io/erpnext/pick-list

### OpenWMS.org

- Repository/license: https://github.com/openwms/org.openwms
- Releases: https://github.com/openwms/org.openwms/releases

## 24. Acceptance signals

- OpenBoxes and multiple maintained WMS references are compared;
- receiving, putaway, bins, picking, replenishment/reservation, stocktake, lot/serial, transfers, barcode, batch/wave and analytics are covered;
- advanced WMS functionality is prioritized by measured business volume rather than copied wholesale;
- OpenWMS microservices/MFC are explicitly treated as over-engineering at current scale;
- every recommended physical transaction remains traceable through state/document/ledger;
- no required WMS operation depends on GitHub Actions.

## 25. Core recommendation

The most valuable WMS upgrade is not wave picking. It is the **receiving staging -> quality -> bin-level stock position -> reservation -> exact scan-confirmed pick -> ledger** chain. OpenBoxes provides the clearest pragmatic receiving/putaway example; Odoo provides a catalogue of strategies to adopt only as scale requires; ERPNext reinforces reconciliation and stock-ledger discipline.