# TASK_INV_IMPL_E03 — Warehouse Locations, Receiving, Putaway, Scan and Count

## Status

`DESIGN_READY_BLOCKED_BY_E02_FOUNDATION`

E03 is a design package only. It does not authorize production runtime changes while E00/E01/E11/E02 gates remain open.

## 1. Objective

Turn the existing warehouse/location/count/scan features into a coherent lightweight WMS execution spine without introducing enterprise-WMS complexity.

Target operating chain:

```text
Inbound receipt
 -> Receiving / staging location
 -> Putaway task
 -> Final storage bin

Reserved outbound demand
 -> Exact bin allocation
 -> Scan source location
 -> Scan material
 -> Confirm quantity
 -> Pick / dispatch staging

Count policy / manual count
 -> Count task
 -> Physical observation
 -> Variance review
 -> E02 movement adjustment
```

The warehouse execution layer must sit on top of E02 stock truth. It must not invent a second inventory balance engine.

## 2. Existing capability to preserve

The current system already has useful warehouse primitives:

- `warehouses`;
- `warehouse_locations` with zone / shelf / box structure;
- `warehouse_layout_items` for a visual layout;
- `shipment_scan_logs`;
- `inventory_count_sessions` / `inventory_count_items`;
- shipment, transfer and purchase workflows;
- a strong material matching / alias / barcode / QR matcher;
- `InventoryCountService` already separates count creation from later approval and posts approved differences through `InventoryService.adjust_inventory` rather than directly editing a number.

These are assets, not throw-away code.

## 3. Core architectural rule

E03 owns **warehouse execution evidence**.

E02 owns **stock truth**.

```text
E03 task / scan / observation
 -> validates execution
 -> calls E02 movement/reservation APIs
 -> E02 posts authoritative stock movement/projection
```

Never create an E03-only quantity field that becomes a second source of truth.

## 4. Scope boundaries

### Included in E03

- stable location identity;
- receiving/staging locations;
- putaway task;
- typed scan resolution;
- exact bin allocation for picking;
- scan-first receive/putaway/pick/transfer/count flows;
- count observation + variance review;
- cycle-count policy;
- simple preferred-bin and pick-sequence rules;
- mobile/handheld guided flow;
- operational timestamps for warehouse KPIs.

### Explicitly deferred

To E07:

- lot/batch identity;
- serial genealogy;
- quarantine / accepted / rejected quality-state authority;
- IQC/NCR/MRB;
- calibration/test genealogy.

To later WMS optimization:

- wave picking;
- cluster picking;
- slotting optimization;
- cartonization;
- conveyor/MFC/PLC integration;
- complex capacity optimization.

## 5. Location model

The current flat tuple:

```text
warehouse_id + zone_name + shelf_code + box_no
```

should remain readable for compatibility, but every executable stock location needs a stable canonical identity.

Recommended additive fields / concepts:

```text
warehouse_locations
  id
  warehouse_id
  location_code          stable human-readable code
  location_type          receiving|storage|dispatch_staging|virtual
  parent_location_id     optional hierarchy
  zone_name              compatibility/display
  shelf_code             compatibility/display
  box_no                 compatibility/display
  scan_code              optional dedicated barcode/QR identity
  pick_sequence          simple route ordering
  putaway_enabled
  pick_enabled
  count_enabled
  enabled
```

Do not use display title as identity.

`location_code` must be unique within a warehouse and must not silently change merely because the visual layout is rearranged.

## 6. Receiving/staging principle

Physical receipt and final putaway are different facts.

Preferred flow:

```text
PO / Transfer inbound document
 -> physical receive
 -> E02 movement into receiving/staging stock position
 -> create putaway task
 -> operator chooses/suggests destination bin(s)
 -> scan/confirm
 -> E02 location-to-location movement
```

This avoids forcing the receiver to know final storage at the instant a parcel arrives.

E07 can later add IQC/quality-state controls between receipt and putaway without changing this execution model.

## 7. Putaway tasks

Suggested additive objects:

```text
putaway_tasks
  id
  warehouse_id
  source_location_id
  source_document_type
  source_document_id
  status
  assigned_user_id
  created_at
  started_at
  completed_at

putaway_task_lines
  id
  task_id
  material_id
  source_position_id
  expected_quantity
  destination_location_id
  confirmed_quantity
  status
```

One received quantity may be split across multiple destination bins through multiple task lines or child allocations.

Completion posts E02 movement(s); the task itself never edits stock balance.

## 8. Typed scan resolver

Scanning is not string search plus automatic action.

Target contract:

```text
resolve_scan(raw, execution_context)
 -> typed candidate(s)
 -> explanation
 -> permitted contextual next actions
```

Initial E03 types:

```text
MATERIAL
LOCATION
SHIPMENT_TASK
TRANSFER
PURCHASE_ORDER / RECEIPT
PUTAWAY_TASK
COUNT_TASK
UNKNOWN
```

Future types such as LOT, SERIAL, WO and RMA are reserved for later epics.

### Safety rules

- exact typed identity outranks fuzzy text;
- multiple candidates require explicit selection;
- detailed/variant material code never silently falls back to a parent material;
- scan resolution itself never mutates stock;
- task action still passes Action Policy, permission, warehouse scope, state and idempotency;
- duplicate active scan identity is a master-data error, not “choose newest”.

## 9. Scan identifier registry

A generic registry is useful if kept small and typed:

```text
scan_identifiers
  id
  namespace
  code_value
  entity_type
  entity_id
  active
  source
  created_at

UNIQUE(namespace, code_value)
```

Initial namespaces should be internal and deterministic. Supplier/manufacturer formats must not be globally assumed unique.

The existing `materials.barcode`, `materials.qr_code`, aliases and material matching behavior should be bridged into the resolver rather than duplicated.

## 10. Outbound exact-bin allocation

E02 Reservation answers:

```text
which material / warehouse quantity is committed?
```

E03 allocation answers:

```text
which concrete bin should the operator pick from?
```

Suggested objects:

```text
pick_tasks
pick_task_lines
```

A pick line should identify:

- shipment/task reference;
- material;
- source location;
- expected quantity;
- confirmed quantity;
- operator;
- timestamps;
- mismatch/exception outcome.

The first version uses simple deterministic selection:

1. eligible/reserved stock only;
2. preferred storage location when configured;
3. lower `pick_sequence` first;
4. minimize unnecessary split picks.

Lot/serial/expiry/quality policy is added later when those dimensions exist.

## 11. Guided scan state machine

Outbound example:

```text
scan shipment task
 -> load expected lines/reservation
 -> show suggested source bin
 -> scan source location
 -> scan exact material
 -> confirm quantity
 -> server validates
 -> mark pick line complete
 -> final shipment action consumes reservation/posts movement
```

A wrong location/material is an explicit exception, never an implicit correction.

## 12. Count model

The current count workflow is a strong starting point but is warehouse/material aggregate oriented.

E03 should make the evidence location-aware and observation-oriented.

Recommended model:

```text
inventory_count_sessions
  existing header retained/extended

inventory_count_observations
  session_id
  location_id
  material_id
  observed_quantity
  observed_by
  observed_at
  scan/source metadata
  remark

inventory_count_variances
  session/location/material
  expected_quantity snapshot
  observed_quantity
  difference
  review status / reviewer / reason
  adjustment_movement_operation_id
```

A physical count observation never directly changes balance.

Approved variance calls the E02 movement kernel using an explicit count-adjustment business operation.

## 13. Blind count

Support a session policy:

```text
blind_count = true|false
```

When blind:

- operator does not see expected balance while observing;
- supervisor/reviewer can see expected vs observed later;
- variance is calculated server-side.

This is optional policy, not a mandatory mode for every count.

## 14. Cycle count

Simple initial policy:

```text
location_count_policy
  location_id
  interval_days
  enabled
  last_completed_at
  next_due_at
```

No AI and no advanced ABC engine are required initially.

Later scheduling can use value/risk/movement frequency once those metrics are trustworthy.

## 15. Putaway / pick policy scope

P0 policy should remain explainable:

### Putaway

- explicit preferred bin for material;
- same-material bin preference;
- location enabled/putaway-enabled;
- deterministic fallback by location code/order.

### Pick

- exact eligible material;
- preferred/pick-enabled location;
- simple path sequence;
- minimize split picks.

Do not build a generic BPM/rules designer in E03.

## 16. Existing warehouse layout

`warehouse_layout_items` is useful as a presentation/layout layer.

It must not become stock truth.

Target relation:

```text
warehouse_locations = canonical operational location identity
warehouse_layout_items = optional visual projection of those locations
```

Moving a rectangle on the layout does not automatically rename/re-key a stock location.

## 17. Migration policy

Exact migration numbers are intentionally **not assigned now**.

E01/E02 migrations must merge first; E03 then receives the next contiguous immutable migration numbers from current `main`.

Do not reserve migration numbers on a design branch because that creates avoidable collisions.

Legacy location migration rules:

- preserve all existing IDs where practical;
- derive proposed location codes deterministically and report conflicts before applying;
- never merge two legacy locations silently;
- inventory rows with missing/invalid location remain explicit reconciliation exceptions;
- layout items remain linked by known location IDs where valid.

## 18. Runtime entry gate

Pure/additive location metadata and scan-resolver infrastructure may be implemented only after E02 stock identity is frozen and merged.

Any E03 flow that posts stock movements must wait until the relevant E02 Movement/Balance contracts are authoritative and locally verified.

Preferred conservative rule:

```text
E02 authoritative cutover PASS
 -> E03 stock-mutating warehouse execution enabled
```

## 19. Required tests

### Location

- stable unique location code per warehouse;
- disabled/non-pickable location rejected by pick action;
- location belongs to the task warehouse;
- layout movement cannot mutate identity.

### Scan

- exact material/location/task resolution;
- ambiguous result requires selection;
- wrong type/context rejected;
- duplicate active scan identity rejected;
- scan alone never changes stock.

### Putaway

- receiving stock exists before putaway;
- partial putaway supported;
- split destination bins supported;
- retry does not double-move stock;
- source insufficient blocks completion.

### Pick

- allocated bin contains enough eligible stock;
- wrong location/material blocked;
- partial pick state explicit;
- shipment completion cannot consume more than picked/reserved policy allows.

### Count

- observation does not change balance;
- blind count hides expected quantity from operator response;
- review computes variance from authoritative E02 projection;
- approved adjustment posts exactly once;
- rejected count posts nothing;
- recount preserves prior observation evidence.

## 20. Definition of done

E03 is complete only when:

- stock locations have stable operational identities;
- inbound stock can remain in staging and be put away separately;
- outbound execution can allocate and scan exact bins;
- scan resolution is shared/typed and never directly mutates stock;
- physical count is observation -> variance -> controlled E02 adjustment;
- cycle count has a simple schedulable policy;
- existing warehouse layout and material matcher are preserved/reused;
- no required runtime/scheduling path depends on GitHub Actions;
- no lot/serial/quality history is fabricated ahead of E07.
