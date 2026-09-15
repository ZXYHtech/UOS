# TASK_INV_AUDIT_WAREHOUSE_LOCATION_01 — Multi-Warehouse, Bin, Shelf & Physical Inventory Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Primary evidence comes from the current SQLite schema, inventory/transfer/shipment services, development index, mobile/PC code map and stock-count schema. No GitHub Actions result is part of the acceptance evidence.

## 1. Executive conclusion

Inventory Lite already has useful warehouse concepts: multiple warehouses, warehouse-user scope, zone/shelf/box locations, a warehouse visual-layout model, transfer workflows, shipment scan records and inventory-count sessions. This is substantially more than a simple stock table.

However, the **physical-location model and the stock-balance model are not yet the same thing**. Locations exist as master/layout objects, while stock remains primarily one aggregate row per material + warehouse + platform account. This is the central barrier to calling the current implementation a full WMS.

The result is best described as:

**multi-warehouse inventory with location metadata and warehouse-operation features — not yet true bin-level inventory accounting.**

## 2. Existing warehouse model

### Warehouse master

`warehouses` includes:

- code/name;
- region/province/city;
- manager/contact;
- enabled state.

`warehouse_users` associates users with warehouses and an optional warehouse role.

Server helpers enforce warehouse visibility/access independently of front-end navigation.

### Location master

`warehouse_locations` includes:

- warehouse;
- zone;
- shelf code;
- box number;
- remark;
- enabled state.

Uniqueness is defined across warehouse + zone + shelf + box.

This is appropriate for a small electronics storeroom where a location might map to:

`Warehouse A / Component Zone / Shelf 03 / Box 12`.

### Visual layout

`warehouse_layout_items` adds visual positioning and hierarchy-like fields:

- item type/key/parent key;
- optional location ID;
- title;
- x/y/width/height;
- shape/content/image/z-index.

This can support a useful warehouse map, but it is a presentation/layout model, not stock accounting truth.

## 3. Critical mismatch: one inventory row cannot naturally represent many bins

Current `inventory` contains `location_id`, but its uniqueness is only:

`material + warehouse + platform account`.

If material `R1001` has:

- 200 pcs in Box A;
- 300 pcs in Box B;

there is no natural schema identity for two separate stock balances under the same warehouse/account.

Possible current behaviors would require one of these compromises:

- only one “primary” location on the aggregate row;
- store multiple locations elsewhere but not quantities;
- aggregate all stock and lose exact bin quantity;
- create duplicate logical inventory rows, conflicting with intended aggregate semantics.

None is sufficient for a true WMS.

## 4. Inventory movement lacks location dimensions

The current `inventory_logs` definition records:

- material;
- warehouse;
- platform account;
- movement type;
- quantity delta;
- quantity after;
- business reference;
- reason/actor/time.

It does not make source/destination location first-class in the audited base model.

Consequences:

- an internal move Box A -> Box B cannot be represented as a precise two-location stock movement without extra conventions;
- a warehouse count cannot reliably reconcile each bin from the ledger;
- picking cannot prove which bin supplied a shipment;
- receiving cannot prove which bin stock was put away into;
- later lot/serial genealogy has nowhere natural to attach physically.

## 5. Stock-count granularity

`inventory_count_sessions` is warehouse-based.

`inventory_count_items` uses uniqueness:

`session_id + material_id`

and stores snapshot/count/difference.

Location is not part of the count-item identity in the audited schema.

Therefore current counting is naturally a **warehouse/material count**, not a bin-by-bin cycle count.

For a growing electronics warehouse, that becomes limiting because the same resistor/amplifier/filter may be distributed across receiving, picking, engineering and production locations.

## 6. Shipment scanning

`shipment_scan_logs` records shipment task, material, scanned code, quantity, match result, operator and time.

This is a valuable foundation, but the audited schema does not record an expected/scanned **source location** in the scan log.

A stronger pick flow should prove:

```text
shipment task
 -> expected material
 -> expected source bin
 -> scan bin
 -> scan material
 -> quantity
 -> match
 -> pick confirmation
```

This reduces picking errors and makes warehouse efficiency measurable.

## 7. Transfer workflow versus internal move

The transfer domain is designed for warehouse-to-warehouse movement and has strong document state, partial receiving and exception logic.

A true WMS also needs a lighter internal move:

`same warehouse / source bin -> destination bin`

without creating an inter-warehouse logistics document.

Recommended separate domain action:

- `stock_move` or `bin_transfer`;
- scan source location;
- scan material/lot;
- enter/scan quantity;
- scan destination location;
- atomic movement posting;
- one auditable movement reference.

## 8. Putaway gap

Purchase receipt currently establishes warehouse-level receiving but the data model does not show a controlled putaway task that assigns received stock to one or more locations.

Recommended future receiving chain:

```text
PO receipt
 -> receiving/staging location
 -> IQC status if required
 -> putaway suggestion/task
 -> scan target location
 -> stock movement to storage bin
```

For electronics, putaway rules may consider:

- component category;
- package/reel/tray/tube;
- ESD requirement;
- moisture sensitivity;
- hazardous/chemical storage;
- high-value secure storage;
- picking frequency;
- engineering versus production stock.

Not all need implementation immediately, but the location model should allow them later.

## 9. Picking strategy gap

Current fulfilment can check stock and scan items, but no robust location allocation strategy was established in this audit.

Future strategies may include:

- fixed bin;
- nearest/priority bin;
- FIFO by receipt/lot;
- FEFO for shelf-life items;
- full-reel before cut-reel preference;
- production kitting location;
- quarantine exclusion;
- serial-specific allocation.

The architecture should treat picking strategy as a policy, not hard-code one path into UI.

## 10. Recommended location hierarchy

Do not force only zone/shelf/box columns forever. Introduce a first-class location node that can support different physical structures:

```text
Warehouse
└─ Area
   └─ Aisle / Cabinet
      └─ Shelf
         └─ Bin / Box
```

Suggested model:

```text
stock_locations
  id
  warehouse_id
  parent_id
  location_code UNIQUE within warehouse
  location_name
  location_type
  picking_priority
  allow_mixed_materials
  allow_mixed_lots
  enabled
```

The current zone/shelf/box values can be migrated into generated hierarchical locations.

## 11. Recommended bin-level stock identity

Minimum future balance identity:

```text
material
+ warehouse
+ location
+ stock_status
+ lot/batch when applicable
+ ownership/scope if needed
```

For serialized items, serial identity is better represented as individual stock units/genealogy records rather than a balance quantity >1.

## 12. Warehouse task model

A scalable warehouse experience benefits from one generic task concept covering:

- receive;
- putaway;
- pick;
- pack;
- replenish forward-pick bin;
- internal move;
- count;
- transfer out;
- transfer in;
- exception investigation.

Each task should contain:

- actor/queue;
- warehouse;
- source/destination location where relevant;
- expected object/quantity;
- scan requirements;
- status;
- timestamps;
- exception path;
- business reference.

This should integrate with existing UnifiedTodo/notification ideas rather than create another unrelated dashboard.

## 13. Electronics-specific warehouse requirements

### Component packaging

Useful future attributes:

- reel/tray/tube/bag/loose;
- package quantity;
- manufacturer lot/date code;
- moisture sensitivity / opened-at / bake status where business requires it;
- ESD-controlled location;
- partial-reel remaining quantity.

### High-value RF components

For expensive mixers, PLLs, LNAs, SAW filters or modules, consider:

- controlled storage location;
- mandatory scan;
- serial/lot traceability;
- issue-to-project/work-order;
- return-to-stock inspection.

### Engineering stock

Separate ownership/status is more useful than simply creating arbitrary warehouses for every engineer. Future model can support:

`physical location + stock purpose/owner/status`.

## 14. Warehouse UX priorities

### Mobile

1. scan location first;
2. scan item/lot/serial;
3. show expected versus actual;
4. minimize manual code entry;
5. keep current task persistent across navigation/network interruption;
6. create exception in context;
7. confirm server-posted result before displaying final success.

### PC

1. stock-by-location drilldown;
2. location occupancy and capacity;
3. stale/empty/overfilled bin reports;
4. movement history by location;
5. count variance by location/operator;
6. replenishment queue;
7. warehouse map as navigation, not accounting truth.

## 15. Migration path without disrupting current operations

### Phase 1 — introduce location truth alongside aggregate stock

- create hierarchical locations;
- create bin-level movement lines/balances;
- keep old warehouse aggregate `inventory` as compatibility projection;
- verify sums match.

### Phase 2 — start with low-risk operations

- internal bin move;
- putaway;
- location-level count.

### Phase 3 — connect fulfilment

- order allocation chooses bin;
- pick scan requires bin + material;
- shipment consumes picked stock.

### Phase 4 — connect manufacturing/quality

- lot/status/serial;
- kitting;
- quarantine;
- work-order issue/return.

Only after reconciliation proves parity should the old single-location field be retired.

## 16. Local/server verification — explicitly no Actions

Recommended direct commands:

```bash
python3 tools/test_warehouse_locations.py
python3 tools/test_bin_inventory.py
python3 tools/test_pick_scan.py
python3 tools/check_location_balance.py
```

Required scenarios:

- same material in two bins;
- move partial quantity between bins;
- count one bin without altering another;
- disable/move a non-empty location fails or requires migration;
- concurrent putaway/pick does not lose stock;
- scan wrong bin/item creates no stock mutation;
- sum of location balances equals warehouse projection;
- transfer receive into staging then putaway;
- rollback/retry is idempotent.

These tests must be executable from a developer/server host. GitHub Actions is not part of the required path.

## 17. Static maturity score

0–5:

- multi-warehouse support: **4/5**
- warehouse user scope: **4/5**
- location master/layout: **3.5/5**
- bin-level quantity accounting: **1/5**
- internal location movement: **1.5/5**
- location-level cycle counting: **1/5**
- scan foundation: **3/5**
- guided pick/putaway: **2/5**
- lot/serial physical traceability: **0.5/5**
- WMS readiness overall: **2.5/5**

## 18. Core judgment

The existing warehouse/location work should not be discarded. It is the correct user-facing foundation.

But before calling the system a WMS, stock truth needs to move from:

`material + warehouse balance with optional location metadata`

to:

`auditable stock quantity at real physical locations, connected to putaway/pick/count/move workflows`.
