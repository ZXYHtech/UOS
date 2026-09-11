# TASK_INV_AUDIT_PART_PARAMETRIC_01 — Electronics Component Parametric Master-Data Fitness

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed material master, specifications/resources, supplier model, project BOM and OpenPnP migration notes.

## 1. Executive conclusion

The current material master is strong for internal SKU/e-commerce management but is not yet a proper electronics component master.

The most important missing concept is separation of four identities:

```text
Internal Part / Enterprise Material
Manufacturer Part (Manufacturer + MPN)
Supplier Part / Supplier SKU
Sales SKU / Channel SKU
```

Today several of these meanings can be placed into `model`, `material_code`, aliases or free-form specifications, but that is insufficient for reliable AVL, sourcing, EOL, BOM and traceability.

## 2. Existing assets to preserve

Current system already has:

- enterprise/internal material code
- legacy SKU/master SKU fields
- category hierarchy
- lifecycle-like status
- arbitrary `material_specifications`
- `material_resources` for datasheets/images/links/attachments
- supplier records
- platform SKU mappings
- aliases
- product/project BOM structures
- barcode/QR

These form a good shell for a richer engineering master-data model.

## 3. Missing first-class electronics identity

Static search did not identify first-class schema for:

- manufacturer
- MPN
- manufacturer-part record
- supplier-part record
- package
- footprint
- datasheet revision/source
- RoHS/REACH status
- lifecycle/EOL evidence

The OpenPnP migration document references manufacturer part number and package, but its mapping suggests extending/using generic fields such as `model`. That is acceptable for import experimentation, not for the canonical engineering model.

## 4. Recommended data model

### Internal part

`parts`

- internal part number
- description
- category
- unit
- lifecycle state
- engineering class
- preferred status
- serialization/lot policy
- inspection policy
- storage/ESD/MSL properties where needed

### Manufacturer

`manufacturers`

- manufacturer ID/name
- aliases
- website
- status

### Manufacturer part

`manufacturer_parts`

- internal part ID
- manufacturer ID
- MPN
- package ID
- lifecycle
- datasheet/resource
- compliance fields
- source/evidence/last verified

Unique identity should normally include manufacturer + normalized MPN.

### Supplier part

`supplier_parts`

- supplier ID
- manufacturer-part/internal-part ID
- supplier SKU
- MOQ
- order multiple
- lead time
- currency
- packaging
- last quoted/purchased price
- enabled/preferred state

Purchase-order lines should eventually snapshot the supplier part used.

### Package / footprint

Keep package and PCB footprint separate:

- package describes component body/lead family;
- footprint describes PCB land pattern/library identity.

One package may map to multiple approved footprints or vice versa depending on design practice.

## 5. Parametric attributes

Keep the current flexible specification table, but add metadata:

- attribute definition
- type: numeric/string/enum/bool
- canonical unit
- searchable/filterable flag
- category applicability
- min/max/tolerance representation
- normalized numeric value for filtering

Do not create one database column for every RF/electronic parameter.

Example RF attributes:

- frequency min/max
- gain
- noise figure
- P1dB
- OIP3
- supply voltage/current
- package

The same engine can support resistors/capacitors/connectors without schema explosion.

## 6. Source provenance

Engineering values should support provenance:

```text
value
source type
source URL/attachment
source revision/date
last verified at
verified by
confidence/status
```

This matters for lifecycle, compliance, RF performance and approved substitution.

## 7. Search requirements

Future material search should resolve:

- internal part number
- MPN
- manufacturer alias
- supplier SKU
- legacy code
- channel SKU
- barcode/QR
- common aliases
- key parametrics

Do not force users to remember which identifier type is stored in `model`.

## 8. Integration with current system

Recommended migration:

1. keep `materials.id` as canonical internal-part identity initially;
2. add manufacturer/manufacturer-part/supplier-part tables referencing material;
3. gradually reinterpret generic `model` as display compatibility, not canonical MPN;
4. migrate known MPN values with review rather than automatic assumptions;
5. preserve existing e-commerce SKU mappings unchanged.

This minimizes breakage.

## 9. Priorities

### P0

1. manufacturer table;
2. manufacturer-part table with MPN;
3. supplier-part table;
4. package/footprint identifiers;
5. canonical identifier search.

### P1

1. typed parametric definitions;
2. lifecycle/EOL evidence;
3. compliance fields where commercially required;
4. supplier MOQ/lead-time/price-break structure;
5. datasheet provenance.

### P2

1. external component-database enrichment adapters;
2. lifecycle monitoring;
3. parametric normalization/duplicate detection.

## 10. Preliminary maturity

- internal SKU master: 4/5
- flexible specifications/resources: 3.5/5
- manufacturer/MPN identity: 1/5
- supplier-part identity: 1.5/5
- package/footprint engineering model: 1/5
- parametric search: 1.5/5
- provenance/lifecycle evidence: 1/5

## 11. Core recommendation

Do not build a separate PLM database first. Extend the existing material identity so one internal part can have many approved manufacturer/supplier identities. This becomes the foundation for AVL, MRP, BOM revision, procurement and traceability.