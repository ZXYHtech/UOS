> Execution target: **ZXYHtech/inventory-Pro** only. Read [repository isolation](../REPOSITORY_ISOLATION.md) before acting; old production/PR instructions below are superseded.

# E03 Slice A Execution Packet — Stable Warehouse Location Identity

## Status

`READY_AFTER_E02_LOCATION_FOUNDATION`

## Entry gate

Start only after E02 stock identity/movement/balance contracts are merged and stable. Stock-mutating E03 behavior remains disabled until E02 authority cutover.

Branch:

```text
impl/e03-location-identity
```

Migration:

```text
NEXT_CONTIGUOUS after final E02 migration
expected 10 if E02-J needs no additional structural migration
```

Do not publish a migration number until branch is based on current merged `main`.

## Confirmed legacy model

Current `warehouse_locations` uses:

```text
id
warehouse_id
zone_name
shelf_code
box_no
remark
enabled
```

with legacy uniqueness based on warehouse + zone/shelf/box.

`warehouse_layout_items.location_id` references those rows for layout rendering.

Static source review found two lifecycle risks in the current route layer:

1. deleting a layout `box` can directly delete the corresponding `warehouse_locations` row;
2. editing a location can directly change its `warehouse_id`.

Once E02 movement/balance/count evidence references stable location IDs, both behaviors are unsafe.

## Purpose

Make a warehouse location a durable business identity independent of layout drawing coordinates or labels.

Additive location metadata:

```text
location_code
location_type
parent_location_id NULL
scan_code NULL
pick_sequence
putaway_enabled
pick_enabled
count_enabled
archived_at NULL (or equivalent lifecycle evidence)
```

Initial location types:

```text
RECEIVING
STORAGE
DISPATCH_STAGING
VIRTUAL
```

Do not encode quality meaning such as ACCEPTED/QUARANTINE/REJECTED in `location_type`; E07 owns quality state.

## Stable identity rule

`warehouse_locations.id` remains the canonical internal FK identity.

`location_code` is a human/scan-friendly stable code unique within one warehouse.

Changing display data such as zone/shelf/box or layout coordinates must not change historical references.

### Warehouse immutability after use

Once a location has any historical/active reference from stock, movement, count, putaway/pick task or other execution evidence:

```text
warehouse_id is immutable
```

A location cannot be reassigned from warehouse A to warehouse B by editing the row.

Correct cross-warehouse change is:

```text
create/identify destination location in warehouse B
 -> move stock through E02 transfer/movement semantics
 -> archive/disable old location when appropriate
```

A never-used draft location may be corrected through an explicit safe-edit path only if reference checks prove zero business evidence.

## Migration preflight

Before UNIQUE enforcement, produce a deterministic report for every existing location:

```text
location_id
warehouse_id
zone/shelf/box
proposed location_code
layout reference count
current inventory reference count
historical movement/count/task reference counts where available
conflict flags
```

Generated code must be deterministic and collision-safe. If two legacy rows generate the same code, stop migration and report both IDs; never merge automatically.

Preserve all existing location IDs.

## Layout decoupling — mandatory correction

After this slice:

```text
layout delete != location delete
```

Deleting/rebuilding a visual layout node may unlink/archive the layout representation, but a location that has ever been referenced by stock, movements, count observations, putaway/pick tasks or historical layout evidence must not be physically deleted.

Recommended server behavior:

```text
if location referenced:
  disable/archive location or unlink layout item
else:
  hard delete only through an explicit safe-delete path
```

A disabled/archived location remains readable historically and cannot be selected for new putaway/pick/count unless a controlled re-enable action occurs.

## Permissions / scope

Reuse current warehouse/location management semantics:

```text
location.manage OR warehouse.manage
+ authoritative warehouse scope
```

No new broad permission is required in this slice.

Client-supplied warehouse ID does not establish authority; the server reloads the location and validates its warehouse.

Changing `warehouse_id` for a referenced location is rejected even for an administrator; admin authority does not rewrite historical identity.

## Expected code touchpoints

Likely additive domain boundary:

```text
inventory_app/domains/warehouse/locations.py
```

Bounded compatibility edits:

```text
inventory_app/server.py
inventory_app/database.py / numbered migration
warehouse layout APIs
```

E02 position identity must continue to reference location ID rather than display coordinates.

## Tests

Required deterministic tests:

1. every existing location gets one deterministic proposed code;
2. duplicate generated code blocks migration;
3. `location_code` unique within warehouse but scan/UI remains warehouse-disambiguated;
4. same location ID survives zone/shelf/box rename;
5. layout move/coordinate change does not affect location identity;
6. deleting a referenced layout box does **not** delete the referenced location;
7. referenced location cannot change warehouse_id;
8. never-used draft location warehouse correction follows explicit zero-reference safe path;
9. disabled/archived location cannot receive new putaway/pick/count execution;
10. historical movement/balance/count references remain queryable;
11. cross-warehouse location use is rejected;
12. migration repeat is a no-op and full Release Gate passes.

## Rollback

Additive metadata may be ignored by prior compatible code before E03 stock execution is enabled.

Do not roll back by deleting locations created/referenced after deployment. Preserve identity/evidence and disable new E03 behavior instead.

## Stop conditions

Stop this slice if:

- legacy locations cannot be assigned deterministic codes without operator choice;
- a location row points to another warehouse through existing inventory/layout evidence;
- hard-delete behavior remains reachable for historically referenced locations;
- referenced location warehouse_id can still be edited;
- E02 position identity would need rewriting merely because a display label changed.

## Exit / unlock

Slice A completes when warehouse locations have stable operational identity, warehouse membership cannot be rewritten after use, and layout rendering is no longer the owner of location lifecycle.

Unlocks E03-B typed scan resolution and later location-aware execution.