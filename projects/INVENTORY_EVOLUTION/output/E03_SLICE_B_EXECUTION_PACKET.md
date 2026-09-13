# E03 Slice B Execution Packet — Typed Scan Resolver

## Status

`READY_AFTER_E03_A`

## Entry gate

Requires E03-A stable location identity merged. No E02 authority cutover is required because this slice is read/resolve only.

Branch:

```text
impl/e03-scan-resolver
```

Migration:

```text
NEXT_CONTIGUOUS only if `scan_identifiers` registry is introduced
otherwise NONE
```

## Purpose

Create one server-side resolver for scanned text so desktop/mobile/handheld flows do not each implement different matching logic.

```text
raw scan
 -> normalize
 -> resolve typed candidate(s)
 -> return canonical ID + match explanation
 -> task/domain command separately validates context and authority
```

Resolver itself performs zero consequential writes.

## Existing behavior to preserve

Current system already stores:

- `materials.material_code`;
- `materials.barcode`;
- `materials.qr_code`;
- `material_aliases`;
- shipment scan logs with raw `scanned_code` and matched/unmatched evidence.

Existing shipment scanning must remain functional during migration.

Do not create a second material matching truth that disagrees with current exact/alias/variant protections.

## Target API contract

```python
resolve_scan(conn, raw_value, context=None) -> ScanResolution
```

Result:

```text
raw
normalized
entity_type
entity_id
warehouse_id if relevant
match_reason
match_class: exact | alias | contextual | ambiguous | unknown
active
context_compatible
candidates[] when ambiguous
```

Initial entity types:

```text
MATERIAL
LOCATION
SHIPMENT_TASK
TRANSFER
PURCHASE_ORDER
PURCHASE_RECEIPT
PUTAWAY_TASK
COUNT_TASK
UNKNOWN
```

Reserved only, not implemented in E03:

```text
LOT
SERIAL
WORK_ORDER
RMA
PACKAGE
```

## Optional identifier registry

If existing columns cannot safely express cross-entity scan identity, add:

```text
scan_identifiers
  id
  namespace
  code_value
  normalized_value
  entity_type
  entity_id
  active
  source
  created_at
  retired_at
UNIQUE(namespace, normalized_value)
```

Do not assume all supplier/manufacturer barcodes are globally unique. Namespace/parser policy must be explicit.

Existing material barcode/QR fields may remain canonical sources and be projected/bridged into the resolver rather than immediately migrated.

## Ambiguity / safety rules

- two active exact identities in the same applicable namespace = master-data defect and block;
- alias/fuzzy match never triggers stock-changing action automatically;
- detailed material code cannot silently degrade to a parent/base item;
- unknown scans are returned as UNKNOWN, not auto-created as material/location;
- retired identifiers remain historical evidence but are invalid for new execution;
- scan confidence never bypasses Action Policy, warehouse scope, task state or E02 balance/reservation rules.

## Context examples

### Shipment/pick

Correct material but wrong warehouse/bin remains context-incompatible.

### Putaway

Resolver may identify any location globally, but command accepts only destination locations in the task warehouse with `putaway_enabled`.

### Count

Resolution identifies location/material observation target only; it does not adjust stock.

## Expected code touchpoints

Suggested module:

```text
inventory_app/domains/warehouse/scans.py
```

Compatibility adapters:

- existing shipment scan route calls resolver for identity;
- existing scan log format remains available;
- mobile/web clients consume one `/api/scan/resolve`-style contract or equivalent bounded endpoint.

Do not move shipment stock effect into resolver.

## Tests

1. exact material code resolves correct material;
2. barcode and QR resolve same canonical material;
3. alias resolution identifies reason/class and never impersonates exact match;
4. exact location code resolves location + warehouse;
5. duplicate active identifier is rejected/preflight-fails;
6. ambiguous alias returns candidates and no write;
7. retired identifier cannot authorize new action;
8. wrong entity type for task context rejected;
9. correct material in wrong location remains context incompatible;
10. unknown scan creates no master data;
11. resolver invocation changes no stock/task state;
12. current shipment scan regression remains green;
13. desktop/mobile use same server result contract;
14. full Release Gate passes.

## Rollback

Pure resolution/optional additive registry. Revert callers to old scan matcher while retaining identifier records if already created; do not delete historical identifier provenance.

## Stop conditions

Stop if:

- existing barcode/alias data contains unresolved duplicate exact identities;
- resolver would need fuzzy auto-selection to keep current workflow functioning;
- client-side code remains capable of authorizing a stock write without server revalidation.

## Exit / unlock

A single typed scan contract is available for putaway, picking, transfer and count flows. Unlocks E03-C/D/E/G execution work.