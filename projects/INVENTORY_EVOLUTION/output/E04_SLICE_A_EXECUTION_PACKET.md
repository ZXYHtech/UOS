> Execution target: **ZXYHtech/inventory-Pro** only. Read [repository isolation](../REPOSITORY_ISOLATION.md) before acting; old production/PR instructions below are superseded.

# E04 Slice A Execution Packet — Internal Part Compatibility Contract

## Status

`READY_AFTER_E03_GATE`

## Entry gate

Requires E03 execution foundation merged and current-main Release Gate PASS.

Branch:

```text
impl/e04-internal-part-contract
```

Migration:

`NONE expected`

## Purpose

Freeze the enterprise-internal part identity before adding Manufacturer/MPN/Supplier identities.

Canonical rule:

```text
materials.id = stable internal part identity
materials.material_code = stable enterprise-visible internal code
```

Do not introduce a second canonical internal-part master.

## Existing relations to preserve

Current `materials` rows are already referenced by inventory, orders, BOMs, purchase data, pricing, specifications/resources, aliases, platform SKU mapping and warehouse workflows.

E04-A must preserve all of those FKs/references.

## Identity separation contract

From this slice onward, explicitly distinguish:

```text
Internal Part      = materials.id/material_code
Manufacturer Part  = manufacturer + exact MPN
Supplier Part      = supplier + supplier SKU
Channel SKU        = platform account + external product/SKU identity
Alias/Search Term  = lookup aid only
```

None is silently interchangeable with another.

## Legacy candidate audit

Generate a read-only report for current materials fields that may contain manufacturer/MPN-like text:

```text
material_id/material_code
model
spec
material_name
legacy/enterprise SKU fields
aliases
possible manufacturer token
possible MPN token
confidence/reason
```

This report produces candidates only.

Do not write canonical Manufacturer/MPN from `model`, `material_name` or alias without explicit deterministic evidence/review.

## Material code policy

Internal material code remains stable through supplier/manufacturer changes.

Do not encode future logic that renames the internal material merely because:

- preferred supplier changed;
- manufacturer merged/renamed;
- orderable MPN suffix changed;
- platform listing SKU changed.

A deliberate internal-code rename, if ever allowed, requires separate alias/history policy and must not break historical references.

## Search compatibility

Existing search/alias behavior remains available. E04 later enriches exact cross-identity search rather than removing current material lookup.

Alias must remain:

```text
search hint / alternate naming
```

not:

```text
approved engineering substitute
```

## Expected code touchpoints

Likely additive domain boundary:

```text
inventory_app/domains/components/internal_parts.py
```

Existing material CRUD stays functional while identity semantics are documented/tested.

## Tests

1. current material IDs/codes remain unchanged;
2. existing order/inventory/BOM/procurement/pricing references still resolve;
3. platform SKU mapping still points to same internal material;
4. aliases remain lookup aids only;
5. candidate audit never mutates canonical material;
6. ambiguous `model/spec/name` text is reported as ambiguous, not auto-converted;
7. supplier or platform identifier cannot overwrite material_code;
8. full Release Gate passes.

## Rollback

Pure contract/report work. No data migration expected.

## Stop conditions

Stop if:

- implementation creates a parallel canonical part table and migrates references into it;
- material IDs/codes are bulk-rewritten from inferred MPNs;
- alias begins granting engineering substitution approval.

## Exit / unlock

Internal part identity is frozen and every later E04 object attaches to `materials.id` without replacing it. Unlocks E04-B Manufacturer+MPN.