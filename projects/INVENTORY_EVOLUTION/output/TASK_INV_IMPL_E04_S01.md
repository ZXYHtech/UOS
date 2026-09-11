# TASK_INV_IMPL_E04_S01 — Internal Part Identity Compatibility Contract

## Status

`DESIGN_READY_BLOCKED_BY_E03_GATE`

## Objective

Freeze the meaning of the existing material master before adding electronics identities so later MPN/supplier/AVL work does not accidentally create competing part masters.

## Canonical decision

```text
materials.id            = internal engineering/business part identity
materials.material_code = canonical internal part number
```

This remains true through E04.

Do not create a second row-for-row `parts` table.

## Compatibility rules

Existing fields remain readable:

- `material_name`;
- category;
- `model`;
- spec;
- unit;
- barcode/QR;
- aliases;
- specifications/resources;
- platform/channel mappings.

But after E04:

```text
materials.model != authoritative manufacturer MPN
```

unless a separately confirmed manufacturer-part link proves the relation.

## Engineering classification

If additional internal-part metadata is required, add controlled additive fields/relations rather than changing `material_code` meaning.

Possible future concepts:

```text
engineering_class
lifecycle policy
lot/serial policy
inspection policy
storage handling class
```

Some belong to later epics; do not pre-implement them merely because they are listed.

## Migration report

Before introducing MPN authority, produce a read-only candidate report for legacy values that look like MPN/model data:

```text
material_id
material_code
model
aliases
resources/datasheets
possible manufacturer text
confidence/reason
```

Report only. No automatic canonical assignment.

## Tests

- existing material IDs/codes unchanged;
- duplicate internal material codes remain prohibited;
- existing API/search can still retrieve old fields;
- no migration auto-creates manufacturer/MPN from ambiguous `model`;
- channel SKU mappings remain attached to same material IDs;
- BOM/procurement/pricing relations remain intact.

## Acceptance

Every later E04 object can point back to one stable internal material identity without breaking existing e-commerce, inventory, BOM, pricing or procurement references.
