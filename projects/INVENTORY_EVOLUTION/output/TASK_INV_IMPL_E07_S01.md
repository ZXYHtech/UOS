# TASK_INV_IMPL_E07_S01 — Traceability Policy and Lot/Serial Identity

## Status

`DESIGN_READY_BLOCKED_BY_E06_E02`

## Objective

Introduce risk-based traceability policy plus first-class lot/serial identities without forcing every material into costly per-unit tracking.

## Trace policy

Per material/product/category policy:

```text
NONE
LOT
SERIAL
LOT_AND_SERIAL
```

Optional flags:

```text
supplier_lot_required
manufacturer_lot_required
date_code_required
expiry_required
certificate_required
finished_serial_required
final_test_required
```

Policy is explicit master data, not inferred from category names at transaction time.

## Lot identity

Suggested:

```text
stock_lots
  id
  material_id
  internal_lot_no
  supplier_id
  supplier_part_id
  manufacturer_part_id
  supplier_lot_no
  manufacturer_lot_no
  date_code
  manufactured_at
  expiry_at
  source_receipt_id
  created_at
  retired_at
```

One receipt line may create multiple lots.

A lot is identity/provenance; current quantity and quality eligibility resolve through E02 stock positions/movements.

## Serial identity

Suggested:

```text
serial_units
  id
  material_id
  serial_no
  lot_id
  product_revision_id
  work_order_id
  created_at
  retired_at
```

For internally generated finished-product serials prefer globally unique serial numbers unless a documented namespace scheme is selected.

Never recycle a serial.

## Identity invariants

- lot/serial material cannot silently change after transaction history exists;
- serial uniqueness enforced at DB level under chosen namespace;
- serial/lot existence does not imply ACCEPTED quality state;
- lot/serial barcode resolves canonical entity through E03 scan resolver;
- static label does not carry mutable quality state as truth.

## Legacy boundary

Do not invent lots/serials for old stock.

Migration may classify existing stock as:

```text
LEGACY_UNTRACED
```

or an equivalent explicit evidence boundary when policy begins after cutover.

## Tests

- NONE policy permits untracked movement where allowed;
- LOT policy requires lot on new controlled receipt/issue;
- SERIAL policy requires unique serial for serialized output;
- one receipt line may split multiple lots;
- duplicate serial rejected;
- retired/shipped/scrapped serial cannot be re-created/recycled;
- material identity immutable after history;
- legacy migration does not fabricate source lot/date code/serial;
- scan label resolves DB identity but cannot mutate quality/stock by itself.

## Acceptance

The system can state exactly which materials/products require no trace, lot trace or serial trace, and new controlled transactions enforce that policy without falsifying historical evidence.
