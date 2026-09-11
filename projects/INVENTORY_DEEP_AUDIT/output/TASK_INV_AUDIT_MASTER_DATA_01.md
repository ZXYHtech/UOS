# TASK_INV_AUDIT_MASTER_DATA_01 — Product Master Data, Aliases, Categories, Units & Lifecycle Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed material/category/alias/spec/resource/platform-SKU schemas and current material-related source/document evidence. No GitHub Actions result is used.

## 1. Executive conclusion

Inventory Lite's material master has already evolved beyond a simple `code + name + stock` table. Current source contains concepts for category hierarchy, aliases, SPU/product line, management/lifecycle state, physical-SKU flag, master/enterprise/legacy SKU codes, naming/configuration metadata, specifications, resources and platform SKU mappings.

That makes it a credible product/master-data base for the company's e-commerce catalog.

It is **not yet a complete electronics part master**. The biggest missing distinction is between:

- internal item/part identity;
- manufacturer;
- manufacturer part number (MPN);
- supplier part number/source;
- package/footprint;
- controlled technical parameters;
- approved/substitute relationships;
- lifecycle/compliance evidence.

A generic `model/spec` plus key/value specifications can help, but it is not sufficient for engineering procurement and BOM control.

## 2. Existing strengths

### Material identity and commerce fields

Current/migrated material fields include examples such as:

- material code/name;
- model/spec/unit;
- category;
- barcode/QR;
- safety stock;
- SPU;
- product line;
- manage status;
- physical SKU flag;
- sales category;
- master material code;
- enterprise SKU code;
- legacy SKU code;
- category prefix;
- lifecycle status;
- naming rule;
- configuration dimensions;
- platform-stock related metadata.

This shows the current system has already recognized the difference between internal master identity and marketplace presentation identity.

### Aliases

`material_aliases` supports alternate names with confidence metadata. This is useful for OCR/search/import matching.

### Specifications/resources

`material_specifications` supports grouped key/value/unit attributes.

`material_resources` can attach/link resources to materials.

These are good primitives for datasheets, drawings, product images and structured technical attributes.

### Platform SKU mapping

`platform_sku_mappings` separates platform product/SKU identity from internal material identity, which is the correct long-term direction for multi-channel commerce.

## 3. Electronics-part identity gap

A repository search found manufacturer/MPN concepts in an OpenPnP migration/reference document, but not as established first-class current source entities.

Recommended distinction:

```text
InternalPart
  internal_part_no
  description
  category
  base_uom
  lifecycle

Manufacturer

ManufacturerPart
  manufacturer_id
  mpn
  package
  datasheet
  lifecycle
  compliance

SupplierPart
  supplier_id
  manufacturer_part_id
  supplier_sku
  packaging
  MOQ
  order_multiple
  lead_time
  price breaks
```

One internal part may have one preferred MPN or several approved interchangeable MPNs depending on engineering rules.

## 4. Lifecycle semantics

A `lifecycle_status` field already exists, which is valuable. It should be converted from free-form metadata into a controlled vocabulary appropriate to both products and components.

Possible states:

```text
DRAFT
ACTIVE
PREFERRED
NRND
EOL
OBSOLETE
BLOCKED
```

Do not force exactly these labels without reviewing current data. The important requirement is explicit transition meaning and effect on:

- new BOM use;
- purchasing;
- new product creation;
- existing production;
- substitution;
- inventory disposition.

## 5. Category versus engineering taxonomy

The current category hierarchy is useful for product navigation and enterprise coding. Electronics engineering often needs overlapping taxonomies:

- commercial/product category;
- engineering component type;
- commodity group;
- sourcing category;
- storage/handling category.

Do not overload one three-level category tree to perform all four jobs.

Recommendation: retain the current product category model and introduce tagged/typed classifications only where business need appears.

## 6. Parametric data

Generic `material_specifications` is a useful start, but engineering search needs typed values.

Example resistor fields:

```text
resistance: DECIMAL + ohm
power: DECIMAL + W
tolerance: DECIMAL + %
tempco: DECIMAL + ppm/C
package: ENUM/REFERENCE
voltage_rating: DECIMAL + V
```

RF amplifier example:

```text
frequency_min/max
small_signal_gain
noise_figure
p1db
ip3
supply_voltage/current
package
```

A text-only key/value model makes sorting/range search and unit normalization unreliable.

### Recommended design

Use category/type schemas:

```text
attribute_definitions
  code
  value_type
  canonical_unit
  allowed_units
  searchable/filterable

part_attribute_values
  material_id
  attribute_definition_id
  numeric_value / text_value / bool_value
  unit
  source/evidence
```

Do not migrate all existing specs at once. Start with high-value electronic component categories.

## 7. Unit-of-measure gap

`materials.unit` is currently a string and different quantity paths use integer or floating-point values.

Future master data should define:

- base UOM;
- purchase UOM;
- packaging conversion where needed;
- quantity precision;
- allowed conversions.

Examples:

- pcs;
- reel -> pcs conversion;
- m/mm;
- g/kg;
- ml/L.

Avoid arbitrary conversion for items where packaging has lot/traceability implications.

## 8. Naming and coding

Current naming/category-prefix/master-SKU work is useful and should remain separate from external MPN identity.

Rule:

**internal code is an enterprise identifier, not a substitute for manufacturer identity.**

A resistor or Mini-Circuits component should not lose MPN/manufacturer traceability because it received a ZXYH internal code.

Recommended UI always shows:

```text
Internal PN | MPN | Manufacturer | Description
```

for production materials.

## 9. Duplicate and merge governance

As OCR/import/platform data increases, duplicate master records become a major risk.

Before creating a new electronics part, matching should examine:

- exact internal code;
- exact MPN + manufacturer;
- supplier SKU;
- normalized model;
- aliases;
- barcode;
- technical fingerprint.

Merge must preserve:

- inventory movements;
- BOM references;
- purchase history;
- platform mappings;
- documents;
- audit trail;
- old identifiers as aliases.

Never hard-delete a referenced part just to remove duplication.

## 10. Document/resource control

`material_resources` can attach useful files/URLs, but engineering needs revision-aware document control for:

- datasheet;
- schematic;
- PCB/Gerber;
- assembly drawing;
- mechanical drawing;
- firmware;
- calibration/test procedure;
- product manual.

A material resource link should eventually carry:

```text
document type
revision/version
approval/release state
checksum
valid/effective state
supersedes relation
```

This is addressed more deeply in the document-control task.

## 11. Search requirements

Future global part search should support:

- internal code;
- legacy code;
- enterprise SKU;
- manufacturer;
- MPN;
- supplier SKU;
- model/name;
- alias;
- category;
- barcode/QR;
- parametric ranges.

Ranking should prefer exact identifiers over fuzzy matches.

OCR fuzzy correction must never silently substitute one engineering part for another when multiple plausible candidates exist.

## 12. Master-data governance

Recommended state flow:

```text
candidate/imported
 -> needs review
 -> approved/active
 -> controlled change
 -> deprecated/EOL
 -> obsolete/blocked
```

High-impact fields should record revision/change reason:

- internal code;
- MPN/manufacturer;
- base UOM;
- lifecycle;
- category if it affects coding;
- BOM substitution class;
- safety/compliance classification.

## 13. Automation opportunities without Actions

Application/server jobs can:

- detect duplicates;
- flag missing MPN/manufacturer;
- flag missing datasheet;
- normalize units;
- identify EOL/NRND parts from approved external data sources;
- detect platform SKU mappings with no internal material;
- propose category/attributes from OCR/import;
- flag parts used in BOM but disabled/obsolete.

Automations should produce review queues rather than silently rewrite controlled engineering master data.

Run via independent worker/systemd timer/cron with durable DB job state; never require GitHub Actions.

## 14. Priority roadmap

### P0

1. define canonical internal-part identity and source-of-truth rules;
2. define UOM/precision policy;
3. make lifecycle vocabulary controlled;
4. preserve current platform-SKU separation;
5. implement duplicate/orphan integrity checks.

### P1

1. manufacturer + MPN entities;
2. supplier-part relation;
3. package/footprint fields;
4. typed parametric attributes for priority component categories;
5. AVL/substitute links;
6. revision-aware document resources.

### P2

1. external lifecycle/availability data enrichment;
2. parametric comparison and alternate suggestion;
3. component risk scoring;
4. preferred-part program.

## 15. Local verification — no Actions

Recommended direct checks:

```bash
python3 tools/check_master_data.py
python3 tools/test_part_matching.py
python3 tools/test_material_merge.py
```

Verify:

- no duplicate active internal codes;
- manufacturer+MPN uniqueness policy;
- no orphan BOM/inventory/platform references;
- unit changes cannot invalidate stock silently;
- merge preserves all references;
- lifecycle transition rules;
- exact identifier search outranks fuzzy candidate;
- ambiguous OCR match requires human confirmation.

## 16. Static maturity score

0–5:

- e-commerce product master: **4/5**
- category/coding governance: **4/5**
- aliases/search foundations: **4/5**
- specs/resources foundation: **3.5/5**
- platform SKU separation: **4/5**
- UOM governance: **2/5**
- electronics MPN/manufacturer model: **1/5**
- supplier-part sourcing model: **1/5**
- typed parametric search: **1.5/5**
- engineering lifecycle/change governance: **2/5**

## 17. Core judgment

The current material master is good enough to evolve; it should not be replaced.

The key transition is:

`commerce-oriented material/SKU master`

->

`enterprise internal part master + explicit manufacturer/MPN/supplier identities + typed engineering attributes`,

while preserving the platform mapping, classification and OCR/search strengths already present.