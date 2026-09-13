# E04 Slice C Execution Packet — Supplier Part Identity

## Status

`READY_AFTER_E04_B`

## Entry gate

Requires Manufacturer+MPN identity merged and current-main Release Gate PASS.

Branch:

```text
impl/e04-supplier-part
```

Migration:

```text
NEXT_CONTIGUOUS
= supplier_parts + indexes
```

## Purpose

Represent the exact supplier catalogue/source identity used by purchasing without confusing it with the internal material or Manufacturer+MPN.

Canonical identity:

```text
supplier_id + normalized_supplier_sku
```

The same supplier SKU text from two suppliers is not the same source.

## Schema

```text
supplier_parts
  id
  supplier_id
  supplier_sku
  normalized_supplier_sku
  manufacturer_part_id NULL
  material_id NULL
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
UNIQUE(supplier_id, normalized_supplier_sku)
```

Resolution states:

```text
UNRESOLVED
INTERNAL_PART_ONLY
EXACT_MANUFACTURER_PART
CONFLICT
RETIRED
```

## Relationship rules

Preferred electronics path:

```text
Supplier Part
 -> exact Manufacturer Part
 -> E04-G approved relation
 -> Internal Material
```

For commodity/non-MPN items, direct supplier-part -> internal material is allowed only as an explicit exception.

If both `material_id` and `manufacturer_part_id` are present, their later approved relation must be consistent. Until E04-G exists, this consistency is a review condition rather than implied approval.

## Commercial planning fields

P0 only:

- MOQ;
- order multiple;
- standard lead time;
- packaging;
- currency;
- enabled/preferred.

Do not duplicate transactional purchase-price history. Existing purchase receipt/price history remains transaction truth.

## Historical PO snapshot boundary

Future PO lines should snapshot source identity/display where known:

```text
supplier_part_id
supplier_sku
manufacturer_part_id
manufacturer + MPN display
```

Changing supplier-part master later must not rewrite historical PO evidence.

## Provider import boundary

Distributor/provider results enter staging/unresolved state.

Provider availability/price/confidence does **not**:

- mark source preferred automatically;
- approve Manufacturer Part for production;
- create substitute authority.

## Tests

1. supplier SKU uniqueness scoped to supplier;
2. same SKU under two suppliers allowed;
3. unresolved source cannot present itself as exact MPN;
4. conflicting material/Manufacturer Part mapping blocked/reviewed;
5. retired/disabled source excluded from new sourcing suggestions;
6. preferred flag does not grant engineering approval;
7. provider result stays staged until review;
8. source master changes do not rewrite historical PO snapshot;
9. full Release Gate passes.

## Rollback

Additive sourcing identity may remain inert. Do not delete rows referenced by purchase evidence.

## Stop conditions

Stop if supplier availability or preferred status bypasses engineering approval, or if historical purchase identity would be recalculated from current master data.

## Exit / unlock

Purchasing can name the exact supplier source/SKU while internal part and manufacturer identity remain distinct. Unlocks sourcing/planning and later AVL enforcement.