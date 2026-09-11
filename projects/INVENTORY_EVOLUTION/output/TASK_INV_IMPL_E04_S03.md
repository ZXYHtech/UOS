# TASK_INV_IMPL_E04_S03 — Supplier Part and Sourcing Identity

## Status

`DESIGN_READY_BLOCKED_BY_E04_S02`

## Objective

Make supplier SKU/source identity explicit so purchasing can distinguish “which supplier listing/source was used” from the internal part and manufacturer part identities.

## Suggested object

```text
supplier_parts
  id
  supplier_id
  supplier_sku
  normalized_supplier_sku
  manufacturer_part_id
  material_id
  resolution_status
  packaging
  moq
  order_multiple
  standard_lead_time_days
  currency
  enabled
  preferred
  source_url
  last_verified_at
  created_at
  updated_at
```

## Identity rule

Canonical supplier-part identity is scoped by supplier:

```text
UNIQUE(supplier_id, normalized_supplier_sku)
```

The same SKU text from two suppliers is not the same identity.

## Resolution status

Suggested vocabulary:

```text
unresolved
internal_part_only
exact_manufacturer_part
conflict
retired
```

Do not force uncertain supplier catalogue data into an exact MPN mapping.

## Relationship rules

Preferred electronics path:

```text
supplier part
 -> exact manufacturer part
 -> approved manufacturer-part relationship
 -> internal material
```

For commodities with no useful MPN, a supplier part may reference only the internal material, but this exception must be explicit.

If both `material_id` and `manufacturer_part_id` are present, their controlled relationship must be consistent.

## Commercial fields

P0 supports stable planning/source fields:

- MOQ;
- order multiple;
- standard lead time;
- packaging;
- currency;
- preferred/enabled.

Do not duplicate transactional purchase price history; current purchase-price history remains the source for historical transactions.

Future price-break tables may be added only when real sourcing use cases require them.

## Procurement integration

Future PO line should snapshot, where known:

```text
supplier_part_id
manufacturer_part_id
supplier_sku display
manufacturer + MPN display
```

Snapshot preserves what was actually ordered even if master sourcing changes later.

## Provider import boundary

External distributor/provider search may create/update staged supplier-part candidates, but it cannot silently mark them preferred or production-approved.

## Tests

- supplier SKU uniqueness scoped to supplier;
- same SKU under different suppliers allowed;
- unresolved source cannot masquerade as exact MPN;
- conflicting material/manufacturer-part relation blocked;
- disabled/retired source excluded from new sourcing suggestion;
- master source change does not rewrite historical PO snapshot;
- provider result remains staging until deterministic review.

## Acceptance

Purchasing can identify the exact supplier source/SKU used for a part without overloading supplier name, model text or alias fields, and without bypassing engineering approval.
