# E02 Slice A Execution Packet — Canonical Stock Identity / Quantity / UOM

## Status

`READY_TO_IMPLEMENT_AFTER_E11_EARLY_BRIDGE`

This packet turns `TASK_INV_IMPL_E02_S01.md` into a code-level implementation handoff.

## Entry gate

Do not implement until:

```text
E00 merged
AND E01 A-F required foundations merged
AND E11 Slice A/B merged
AND migration 6 applied successfully
AND current main passes tools/verify_release.py
```

Recommended branch:

```text
impl/e02-stock-identity
```

## Slice objective

Answer one question with a deterministic, testable contract:

> What exact dimensions identify one physical stock position?

This slice does **not** change production stock writes, balances, reservations or ATP.

## Confirmed current code facts

Current legacy balance uniqueness:

```text
UNIQUE(material_id, warehouse_id, platform_account_id)
```

while the same row also contains:

```text
location_id
quantity_available
quantity_locked
quantity_on_transfer
safety_stock
```

Current core mutation primitive defaults:

```python
platform_account_id=None
```

and core workflow tests usually query company/no-account rows using:

```text
platform_account_id IS NULL
```

Therefore a non-null `platform_account_id` must **not** automatically be promoted into physical ownership identity without evidence.

Current `location_id` is mutable metadata but is not part of the unique balance key.

## Migration ownership

### Slice A migration

```text
NONE
```

This slice is code-contract + deterministic mapping/report only.

After E11 Migration 6, reserve:

```text
Migration 7 = E02 Movement Ledger (Slice B / S02)
```

Do not create speculative stock tables in Slice A merely to reserve architecture.

## Target module boundary

Create the initial stock domain without changing production authority:

```text
inventory_app/domains/stock/
  __init__.py
  identity.py
  quantity.py
  legacy_mapping.py
```

Optional tests:

```text
tools/test_stock_identity.py
tools/test_stock_legacy_mapping.py
```

No `server.py` write route is migrated in this slice.

## Canonical physical position identity v1

Conceptual dimensions:

```text
material_id
warehouse_id
location_scope
owner_scope
stock_status
```

### v1 defaults

```text
owner_scope = COMPANY
stock_status = AVAILABLE
```

Lot/serial are deliberately excluded until E07.

Marketplace/channel account is not included in physical identity unless a later evidence-backed decision proves the stock is legally/physically separately owned.

## Location scope

Use an explicit non-null scope representation:

```text
UNASSIGNED
LOCATION:<location_id>
```

Rules:

- real location must exist;
- location.warehouse_id must equal position.warehouse_id;
- missing historical location maps to `UNASSIGNED`;
- never invent shelf/bin names;
- E03 may later move `UNASSIGNED` stock to real locations through explicit stock movements.

## Owner scope

Use explicit normalized v1 scope:

```text
COMPANY
```

Do not encode `NULL` as business meaning in the new identity.

### Legacy non-null platform_account_id

Mapping rule:

```text
platform_account_id IS NULL
 -> physical owner scope COMPANY

platform_account_id IS NOT NULL
 -> produce review flag LEGACY_PLATFORM_ACCOUNT_SCOPE
 -> preserve source account metadata
 -> do not silently split or merge physical stock
```

Before later opening-balance migration, an operator/data review must classify each non-null legacy row as one of:

```text
COMMERCIAL_ONLY_SCOPE
TRUE_SEPARATE_OWNERSHIP
DATA_ERROR / DUPLICATE
OTHER_EXPLICIT_POLICY
```

If evidence is insufficient, cutover remains blocked.

## Stock status v1

Initial canonical status:

```text
AVAILABLE
```

Reason: legacy field is explicitly `quantity_available`.

Do not invent historical quarantine/inspection/reject states that were never recorded.

E07 later introduces quality-aware status semantics through explicit movements/dispositions.

## Canonical position key

Provide one stable serializer, for example:

```text
v1|m=<material_id>|w=<warehouse_id>|loc=<UNASSIGNED|id>|owner=COMPANY|status=AVAILABLE
```

Properties:

- deterministic;
- non-null dimensions;
- versioned format;
- generated only from validated IDs/scopes;
- never used as authorization evidence;
- never parsed from arbitrary client input without validation.

Recommended API:

```python
@dataclass(frozen=True)
class StockPositionIdentity:
    material_id: int
    warehouse_id: int
    location_scope: str
    owner_scope: str = "COMPANY"
    stock_status: str = "AVAILABLE"

    def key(self) -> str: ...
```

## Quantity contract

New authoritative E02 quantity math must not depend on binary float accumulation.

Use application-level `decimal.Decimal` for canonical quantity parsing/math.

Recommended normalized representation:

```text
Decimal in memory
canonical decimal string at evidence/storage boundaries
```

### UOM v1 vocabulary

Start small:

```text
EA       piece/count
LENGTH
MASS
VOLUME
```

Do not build arbitrary conversion graphs in Slice A.

### EA policy

For piece-count inventory:

```text
scale = 0
fractional EA rejected
```

Examples:

```text
"10"  -> valid
10     -> valid
"10.0" -> normalize to 10 if exact integral
"10.5" -> reject for EA
```

### Non-EA policy

For future fractional materials, define deterministic configurable precision but do not migrate current integer inventory automatically.

Initial helper contract may accept a scale policy supplied by material/UOM configuration later.

## Legacy unit mapping

Current `materials.unit` is free text and may contain legacy values such as `pcs`.

Slice A should provide a conservative normalization map for known exact aliases, e.g.:

```text
pcs / pc / piece / 件 -> EA
```

Unknown unit text:

```text
-> UOM_REVIEW_REQUIRED
```

Never guess that an unknown unit is EA just because quantity happens to be integer.

## Legacy mapping report

Create a deterministic command/tool, e.g.:

```text
tools/report_stock_identity_mapping.py
```

Read-only input:

```text
inventory
materials
warehouses
warehouse_locations
platform_accounts
```

Output per legacy row:

```text
legacy_inventory_id
material_id/material_code
warehouse_id/warehouse_code
legacy_location_id
legacy_platform_account_id
legacy_quantity_available
legacy_unit
normalized_uom
proposed_position_key
review_flags[]
```

### Review flags

At minimum:

```text
MISSING_MATERIAL
MISSING_WAREHOUSE
INVALID_LOCATION
LOCATION_WAREHOUSE_MISMATCH
LEGACY_PLATFORM_ACCOUNT_SCOPE
UNKNOWN_UOM
DUPLICATE_PROPOSED_POSITION
CONFLICTING_LEGACY_ROWS
```

## Duplicate-collapse rule

If multiple legacy rows map to the same proposed physical key:

```text
DO NOT SUM AUTOMATICALLY
```

Report every source row and mark:

```text
DUPLICATE_PROPOSED_POSITION
```

Later migration requires an explicit reviewed resolution.

This prevents nullable-unique legacy behavior from hiding duplicate company rows.

## Existing production semantics remain untouched

Forbidden in Slice A:

- changing `InventoryService.adjust_inventory()`;
- changing shipment deduction;
- changing transfer receipt/issue;
- changing purchase receipt;
- changing `inventory` uniqueness;
- changing `quantity_available` type;
- creating reservations;
- making new position key drive API output;
- deleting/merging legacy rows.

## Tests

### Identity tests

Prove:

1. same validated dimensions produce identical key;
2. different real locations produce different keys;
3. no-location produces deterministic `UNASSIGNED`;
4. cross-warehouse location is rejected;
5. missing location/material/warehouse is rejected or report-flagged according to API contract;
6. key format is versioned and deterministic.

### Owner/account tests

Prove:

7. null platform account maps to company scope;
8. non-null platform account generates review evidence and is not silently included/excluded as physical ownership;
9. two legacy NULL rows collapsing to one physical key are reported, never silently summed.

### Quantity/UOM tests

Prove:

10. EA integer round-trip is exact;
11. fractional EA is rejected;
12. Decimal serialization is stable;
13. known legacy UOM alias maps deterministically;
14. unknown UOM requires review;
15. no float accumulation is used in new canonical helper tests.

### Mapping report tests

Prove:

16. same fixture generates same ordered report;
17. no source inventory row disappears;
18. invalid location/warehouse relationship is visible;
19. conflicting source rows block clean status;
20. full `tools/verify_release.py` passes.

## Report exit states

Summary should produce:

```text
CLEAN
REVIEW_REQUIRED
BLOCKED
```

Suggested meaning:

```text
CLEAN:
  every row maps uniquely and only accepted aliases/defaults were used

REVIEW_REQUIRED:
  non-destructive ambiguity exists, e.g. platform-account scope/unknown UOM

BLOCKED:
  broken references, cross-warehouse location, duplicate collapse or impossible quantity
```

Do not call S01 production-ready merely because most rows are clean.

## Rollback

Pure/additive code and reporting only.

Rollback removes unused helper/report code if necessary; production inventory remains unchanged.

No data rollback is required because Slice A performs no production mutation.

## Review checklist

- [ ] no production stock route changed;
- [ ] no DB migration created;
- [ ] location participates in proposed identity;
- [ ] NULL is not used as new business identity;
- [ ] platform account ownership is not guessed;
- [ ] Decimal/UOM rules are explicit;
- [ ] no legacy row is silently merged;
- [ ] report is deterministic/read-only;
- [ ] full Release Gate passes.

## Exit gate

Slice A is complete when every current legacy `inventory` row can be mapped to one proposed canonical stock identity or an explicit review/block condition, with exact quantity/UOM handling and zero production behavior change.

Then unlock:

```text
E02 Slice B / Migration 7 — immutable Stock Movement Ledger
```
