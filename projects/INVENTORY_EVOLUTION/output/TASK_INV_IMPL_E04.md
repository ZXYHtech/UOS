# TASK_INV_IMPL_E04 — Electronics Part Master, MPN, Supplier Part, Parametrics and AVL

## Status

`DESIGN_READY_BLOCKED_BY_E03_GATE`

E04 is design-only while earlier runtime gates remain open.

## 1. Objective

Evolve the existing `materials` master from a strong internal/e-commerce SKU catalogue into a reliable electronics engineering part master without creating a separate parallel PLM database.

Canonical identity layers must be explicit:

```text
Internal Part / Material
Manufacturer Part = Manufacturer + MPN
Supplier Part / Supplier SKU
Sales / Channel SKU
```

These are related identities, not aliases of one another.

## 2. Existing assets to preserve

The current system already has:

- `materials.id` + enterprise/internal `material_code`;
- categories;
- model/spec text;
- `material_aliases`;
- `material_specifications`;
- `material_resources`;
- suppliers;
- platform SKU mappings;
- barcode/QR;
- BOM/project-BOM relationships;
- pricing/purchase history;
- strong material search/matching behavior.

Do not replace these wholesale.

## 3. Canonical internal-part decision

For the first controlled evolution:

```text
materials.id = canonical internal part identity
materials.material_code = canonical internal part number
```

Do **not** introduce a second `parts` table that duplicates every material row.

New electronics tables reference `materials.id`.

Generic `materials.model` remains compatibility/display data but is no longer authoritative MPN identity once E04 data is available.

Known legacy MPN-like values must be migrated through review/staging, not blindly assumed from `model`.

## 4. Manufacturer identity

Suggested objects:

```text
manufacturers
manufacturer_aliases
manufacturer_parts
```

### manufacturers

```text
id
manufacturer_name
normalized_name
website
status
created_at
updated_at
```

### manufacturer_parts

Manufacturer part identity should stand on its own:

```text
id
manufacturer_id
mpn
normalized_mpn
package_id
lifecycle_status
status
created_at
updated_at
```

Recommended unique identity:

```text
manufacturer_id + normalized_mpn
```

Do not make “row exists” mean “approved for production”. Approval is a separate controlled relationship.

## 5. Internal Part ↔ Manufacturer Part approval

Suggested object:

```text
material_manufacturer_approvals
  id
  material_id
  manufacturer_part_id
  approval_status
  approval_class
  qualification_reference
  valid_from
  valid_to
  approved_by
  approved_at
  suspended_reason
  remark
```

This is the AML/approved-manufacturer-source relationship.

Possible status vocabulary:

```text
draft
under_review
approved
suspended
rejected
expired
```

Existence of an MPN record does not grant procurement/production authority.

## 6. Supplier Part / sourcing identity

Suggested object:

```text
supplier_parts
  id
  supplier_id
  supplier_sku
  manufacturer_part_id
  material_id
  source_resolution_status
  packaging
  moq
  order_multiple
  standard_lead_time_days
  currency
  enabled
  preferred
  last_verified_at
  created_at
  updated_at
```

Rules:

- supplier SKU identity is scoped to supplier;
- exact MPN linkage is preferred when known;
- generic/internal-material-only source may exist for non-MPN commodities but must be explicit;
- unresolved supplier catalogue rows remain staging/unresolved, not silently production-approved;
- purchasing eligibility is evaluated through supplier source + AML/approval rules, not supplier-part existence alone.

PO lines should later snapshot the actual supplier part / manufacturer part used when known.

## 7. Package and footprint

Package and PCB footprint are separate engineering identities.

Suggested objects:

```text
packages
footprints
package_footprint_relations
```

Examples:

- package: QFN-24 4x4 mm body/lead family;
- footprint: specific KiCad/Altium land-pattern/library identity.

Do not equate a package text label with one globally approved footprint.

E05 controlled BOM/EDA integration will later use these identities.

## 8. Typed parametric attributes

Preserve the flexibility of current `material_specifications`, but add typed definitions.

Suggested model:

```text
part_attribute_definitions
  id
  attribute_code
  name
  data_type
  canonical_unit
  category applicability
  searchable
  filterable
  enum/schema metadata

part_attribute_values
  definition_id
  owner scope
  raw/display value
  normalized numeric/text value
  min/max/tolerance where applicable
  source/evidence
  verification state
```

Supported data types should cover:

```text
numeric
range
string
enum
boolean
```

Do not add one database column for every RF parameter.

RF examples:

- frequency min/max;
- gain;
- NF;
- P1dB;
- OIP3;
- supply voltage/current;
- insertion loss/isolation;
- impedance;
- package.

Passive examples:

- value;
- tolerance;
- voltage rating;
- dielectric;
- package.

## 9. Requirement values vs source values

An internal part can represent an engineering requirement while a manufacturer part represents one real source implementation.

Therefore parametric architecture must be capable of distinguishing:

```text
internal requirement / nominal attributes
manufacturer-part datasheet attributes
```

Do not overwrite one with the other merely because values are similar.

Initial implementation may phase these scopes, but the data contract must not preclude the distinction.

## 10. Provenance

Engineering data needs evidence.

Suggested reusable evidence object/concepts:

```text
entity type/id
value/evidence type
source URL or attachment
source/provider
source document revision/date
retrieved_at
last_verified_at
verified_by
verification_status
```

Use for:

- datasheets;
- lifecycle state;
- RoHS/REACH/compliance evidence;
- RF performance values;
- package/footprint evidence;
- external provider enrichment.

Unknown or stale evidence must be distinguishable from verified current data.

## 11. Lifecycle and compliance

Initial lifecycle vocabulary should be explicit and configurable, for example:

```text
active
NRND
EOL
obsolete
unknown
```

Never auto-substitute merely because a source becomes EOL.

Lifecycle changes create sourcing/engineering attention; they do not silently modify BOM or production choices.

Compliance should be evidence-bound. Do not infer RoHS/REACH purely from category/manufacturer.

## 12. AVL / AML vs substitutes

Keep three concepts separate:

```text
Alias
  = another identifier/name for the same canonical object

Approved Manufacturer Part
  = an MPN allowed to fulfil one internal part

Internal-part Substitute
  = a different internal part that engineering allows to replace another under conditions
```

Never let alias/search similarity grant substitution authority.

## 13. Internal-part substitution

Suggested object:

```text
material_substitutions
  id
  source_material_id
  target_material_id
  substitution_class
  scope
  conditions
  approval_status
  valid_from
  valid_to
  approved_by
  approved_at
  priority
  engineering_reference
```

Initial classes:

```text
form_fit_function
conditional
purchasing_only
engineering_deviation
```

Initial scope may support `global` only; E05 later adds BOM-revision/effectivity scope and ECN/ECO authority.

Do not fake E05 effectivity fields before that domain exists.

## 14. RF/electronics substitution safety

Similarity is only candidate discovery.

Engineering approval may need to consider:

- frequency range;
- gain/NF/P1dB/OIP3;
- insertion loss/isolation;
- control interface;
- voltage/current;
- temperature;
- package/footprint;
- matching network impact;
- calibration impact;
- firmware/register behavior.

A parametric comparison UI can help reviewers but cannot approve a replacement automatically.

## 15. Search / component workspace

E04 expands E03/global search identity coverage to:

- internal part number;
- manufacturer + exact MPN;
- manufacturer aliases;
- supplier SKU;
- legacy aliases;
- channel SKU;
- barcode/QR;
- package/footprint;
- typed parametric filters.

Search result must explain why it matched.

Suggested component workspace centers on one `materials.id` and shows:

```text
internal identity
approved manufacturer parts
supplier sources
parametric requirements/values
package/footprint
resources/datasheets
lifecycle/compliance evidence
stock summary
pricing/purchase context
future BOM where-used
```

## 16. Provider/enrichment boundary

External component-data providers may:

- search candidates;
- return manufacturer/MPN/package/parametric/lifecycle/document data;
- attach source/provenance;
- create staging suggestions.

They may **not** directly:

- approve an MPN;
- create an engineering substitute;
- overwrite verified canonical values silently;
- change BOMs;
- place purchase orders.

Provider result -> staged candidate -> deterministic validation/review -> canonical data.

## 17. Migration strategy

Do not guess existing `materials.model` values into canonical MPNs.

Migration phases:

```text
additive identity tables
 -> exact high-confidence staging candidates
 -> review report
 -> operator/engineering confirmation
 -> canonical links
 -> compatibility display remains
```

No historical manufacturer/MPN/AVL identity is fabricated.

Exact numbered migrations are assigned only after current merged E03/E02 history is known.

## 18. Required tests

### Identity

- manufacturer + normalized MPN unique;
- different manufacturers may legitimately use same MPN text;
- aliases do not merge manufacturer identity automatically;
- legacy `model` remains compatible but non-authoritative.

### Supplier source

- supplier SKU unique within supplier namespace;
- source linked to wrong internal/MPN context rejected;
- unresolved source cannot become approved production source accidentally.

### AVL

- manufacturer-part existence != approval;
- suspended/expired approval not eligible;
- approval history/evidence preserved;
- alias never grants AVL status.

### Substitute

- candidate similarity does not authorize substitution;
- unapproved alternate blocked;
- expired conditional approval blocked;
- directionality explicit; A->B does not imply B->A unless separately approved.

### Parametrics

- numeric units normalize deterministically;
- incompatible units rejected;
- raw/source value retained;
- requirement vs source value not conflated;
- filters return explainable exact constraints.

### Search

- exact MPN outranks fuzzy text;
- supplier SKU scoped to supplier;
- ambiguous candidates require explicit selection;
- search never mutates canonical master data.

## 19. Definition of done

E04 is complete only when:

- internal part, MPN, supplier part and channel SKU identities are explicit;
- `materials.id` remains a stable canonical internal-part anchor;
- manufacturer-part existence is distinct from engineering approval;
- supplier sourcing is tied to controlled identity;
- package and footprint are separate;
- typed parametrics have unit/provenance semantics;
- lifecycle/compliance evidence is not guessed;
- AVL/substitutes are controlled relationships, not aliases;
- exact MPN/supplier/parametric search is available;
- external provider enrichment is staging/evidence-bound;
- no required runtime depends on GitHub Actions.
