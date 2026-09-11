# TASK_INV_IMPL_E05 — Controlled Product Revision, EBOM/MBOM, ECN/ECO and Documents

## Status

`DESIGN_READY_BLOCKED_BY_E04_GATE`

E05 is design-only while earlier runtime gates remain open.

## 1. Objective

Create a small engineering configuration-control layer so the system can answer:

```text
What exact released hardware/BOM/doc/firmware/test configuration was effective for this build?
```

without turning Inventory Lite into a full enterprise PLM suite.

## 2. Existing concepts to preserve

Keep current useful domains in their existing roles:

```text
material_bom
  = sales / fulfilment bundle explosion

project_bom_lines
  = project/import/cost-oriented component list and staging evidence

material_resources
  = flexible reference links/resources
```

Do not silently reinterpret any of these as a released production BOM or controlled document repository.

## 3. Required configuration layers

```text
Internal Material / Product
 -> Product / Part Revision
 -> Released EBOM Revision
 -> Released MBOM Revision based on EBOM
 -> Controlled Document / Firmware / Test Release Package
 -> Work Order snapshots exact released configuration (E06)
```

Engineering changes create new revisions/effectivity; historical released revisions remain immutable.

## 4. Product / part revision

Suggested object:

```text
part_revisions
  id
  material_id
  revision_code
  status
  description
  supersedes_revision_id
  created_by
  created_at
  submitted_at
  released_by
  released_at
  obsolete_at
```

Status:

```text
draft
review
released
obsolete
withdrawn
```

A released revision is immutable under ordinary workflow.

## 5. BOM model

New controlled BOM model initially supports only:

```text
engineering
manufacturing
```

Sales/kit BOM remains separate.

Suggested objects:

```text
bom_revisions
  id
  parent_material_id
  part_revision_id
  bom_type              engineering|manufacturing
  revision_code
  status
  based_on_bom_revision_id
  effective_from
  effective_to
  supersedes_bom_revision_id
  created_by/at
  released_by/at

bom_lines
  id
  bom_revision_id
  line_no
  component_material_id
  quantity
  uom
  line_type
  dnf
  optional
  variant_condition
  scrap_factor
  notes

bom_line_refdes
  bom_line_id
  refdes
```

## 6. EBOM semantics

EBOM defines engineering design intent.

Each released line may carry:

- exact internal component requirement;
- quantity;
- refdes;
- optional/DNF state;
- engineering note;
- variant applicability;
- approved MPN/alternate policy through E04 relationships, not free-text substitutions.

Reference designators belong to the BOM placement/design context, not inventory identity.

## 7. MBOM semantics

MBOM is manufacturing planning/execution truth.

It may include items not present in the EBOM:

- panel/substrate handling;
- shielding cover;
- screws/enclosure;
- labels;
- packaging;
- controlled consumables;
- manufacturing subassemblies;
- process-specific additions;
- scrap/yield factor where justified.

Every MBOM revision should explicitly identify:

```text
based_on_bom_revision_id = released EBOM revision
```

unless it is a controlled legacy migration exception.

## 8. EBOM -> MBOM transformation

Do not copy once and lose ancestry.

For each MBOM revision preserve a diff/explanation against its source EBOM:

```text
inherited
added_for_manufacturing
removed_with_reason
quantity_changed_with_reason
line_type_changed
```

Start simple. Many small RF modules may initially have EBOM ≈ MBOM; the system should represent that explicitly rather than assuming they are the same object.

## 9. Multilevel BOM

Controlled BOM explosion must support:

- multilevel subassemblies;
- revision selection;
- cycle prevention;
- quantity propagation;
- phantom/subassembly line types when introduced;
- effective released revision selection.

MRP E08 explodes a released effective MBOM, never the sales BOM or mutable draft EBOM.

## 10. Effectivity

P0 effectivity:

```text
date/time
explicit work-order selection (E06)
```

Future effectivity may include lot/serial range after E07.

Rules:

- at most one default effective released revision for a product/configuration/time where policy requires it;
- historical WO references never float to a newer revision;
- future effective revision may coexist with current released revision;
- withdrawal/obsolete state remains historically resolvable.

## 11. EDA import staging

EDA import never edits released BOM directly.

Target:

```text
Altium/KiCad/export file
 -> parse staging rows
 -> normalize refdes/value/package/MPN
 -> E04 identity match
 -> unresolved/ambiguous review
 -> compare with selected prior EBOM revision
 -> draft new EBOM revision
 -> engineering review
 -> release
```

Suggested staging objects can preserve:

- original row text;
- source project/file/hash;
- import time/operator;
- matched material/MPN;
- match reason/confidence;
- unresolved reason;
- proposed refdes/quantity/value/package.

Never discard unresolved source text.

## 12. BOM diff

Review should explain changes between revisions:

```text
added line/refdes
removed line/refdes
quantity changed
component changed
DNF/optional changed
refdes moved
variant applicability changed
```

Release is based on explicit diff, not an invisible overwrite.

## 13. Engineering Change aggregate

Suggested:

```text
engineering_changes
  id
  change_no
  change_type          ECN|ECO|deviation|waiver
  title
  reason
  status
  requested_by/at
  reviewed_by/at
  approved_by/at
  effective_rule
  summary

engineering_change_objects
  engineering_change_id
  entity_type
  before_entity_id
  after_entity_id
  action
  disposition
  notes
```

Do not implement a generic BPM engine.

## 14. Change impact checklist

Before an ECO release, collect explicit impact decisions for applicable areas:

- EBOM/MBOM;
- E04 AVL/substitutes;
- existing inventory disposition;
- open procurement;
- WIP/work orders;
- firmware;
- fixtures/tools;
- test procedure/limits;
- labels/manuals/customer documents.

Unknown impact is a visible unresolved item, not silently assumed “none”.

## 15. Existing-stock disposition

ECO may classify affected existing stock:

```text
use_as_is
use_until_exhausted
rework
hold_for_review
return_supplier
scrap
not_affected
```

E05 records the decision/evidence.

Actual inventory quality/status execution integrates with E07/E02 rather than E05 directly editing stock.

## 16. Deviation / waiver

Temporary deviation is not a permanent BOM rewrite.

It records:

- scope;
- reason;
- approved exception;
- start/end or quantity/work-order limit;
- affected part/BOM;
- approval;
- expiration/closure.

E06 work order can reference an active approved deviation.

## 17. Controlled documents

Keep `material_resources` for informal/reference resources.

Add separate controlled identity/revisions:

```text
controlled_documents
  id
  document_no
  document_type
  title
  owner_user_id
  status

controlled_document_revisions
  id
  document_id
  revision_code
  status
  attachment_id
  checksum_sha256
  effective_from/to
  supersedes_revision_id
  change_reason
  created_by/at
  released_by/at
```

Released artifact bytes/checksum are immutable.

A correction creates a new revision or explicit withdrawal/supersession event.

## 18. Document applicability

Use explicit controlled links rather than free-text scope:

```text
document_revision_applicability
  document_revision_id
  entity_type
  entity_id
```

Initial entity types:

```text
material
part_revision
bom_revision
```

E06/E07 later add work-order/test-specific links.

## 19. Release packages

A product release package can coordinate multiple released artifacts:

- schematic;
- PCB fabrication package;
- pick-and-place;
- assembly drawing;
- EBOM/MBOM export;
- firmware;
- work instruction;
- RF test procedure/limit set;
- mechanical drawing.

Suggested objects:

```text
release_packages
release_package_items
```

Manufacturing should consume one coherent package/version rather than manually mixing file revisions.

## 20. Firmware release identity

Suggested:

```text
firmware_releases
  id
  firmware_code
  version
  build_id
  source_revision/git_commit
  binary_attachment_id
  checksum_sha256
  hardware_revision applicability
  configuration_schema_version
  release_notes
  status
  released_by/at
```

Filename is not identity.

E07 serialized test/build records later capture exact installed firmware release.

## 21. Test procedure / limit set

Test procedure and limit-set changes must be revisioned controlled artifacts.

Historical test runs later reference exact released:

```text
procedure revision
limit-set revision
station software/script version
fixture/de-embedding configuration when controlled
```

Never recompute historical pass/fail using today’s limits without explicitly labeling re-analysis.

## 22. Release immutability

For controlled revisions:

```text
draft    editable
review   restricted changes / review flow
released immutable
obsolete retained, excluded from new default use
withdrawn retained with warning
```

No normal API performs hard delete on released engineering evidence.

## 23. Existing BOM compatibility

### `material_bom`

Retain as sales/fulfilment BOM until its own migration is explicitly justified.

Shipment behavior must not change merely because EBOM/MBOM exists.

### `project_bom_lines`

May seed EDA/project staging or draft EBOM candidates after review.

Do not automatically declare historical project BOM rows released.

### CostService

Every future cost query must name its source:

```text
sales BOM estimate
EBOM engineering estimate
MBOM standard estimate
actual WO cost (E06/E11)
```

Do not keep a generic ambiguous `total_cost` label across these semantics.

## 24. Where-used

Controlled BOM data must support deterministic where-used:

```text
component material
 -> released/draft EBOM/MBOM revisions containing it
 -> parent products/revisions
```

Engineering change impact analysis depends on this.

## 25. Variant scope

P0 supports simple explicit line applicability metadata and released product/SKU configuration references.

Do not build a full configurable-product engine.

A variant rule must remain inspectable and deterministic.

## 26. Migration strategy

No current mutable BOM is silently labelled “released”.

Migration:

```text
existing sales BOM stays unchanged
project/engineering-like rows -> staging candidate
engineering review
 -> draft controlled EBOM
 -> explicit release
 -> MBOM derived/reviewed/released
```

No historical revision/effectivity is fabricated.

Exact migration numbers are assigned only from the then-current merged `main`.

## 27. Required tests

### Revision/release

- released part/BOM/document revision rejects edit;
- new revision supersedes without deleting old;
- withdrawn/obsolete remains historically resolvable;
- effective revision resolution deterministic.

### BOM

- sales BOM changes do not alter released EBOM/MBOM;
- EBOM refdes preserved and unique by defined rules;
- multilevel cycle blocked;
- MBOM ancestry to EBOM retained;
- EDA import creates staging/draft only;
- BOM diff explains changes.

### ECN/ECO

- affected objects list before/after identities;
- release blocked when required impact item unresolved;
- deviation expires/limits scope;
- stock disposition record does not directly rewrite inventory.

### Documents

- released file checksum immutable;
- Rev B release keeps Rev A downloadable historically;
- applicability points to exact configuration;
- unauthorized release API blocked;
- backup/recovery validates controlled artifact presence/checksum.

## 28. Definition of done

E05 is complete only when:

- product/part revisions exist;
- released EBOM/MBOM revisions are immutable;
- MBOM ancestry to released EBOM is explicit;
- refdes is first-class;
- EDA imports stage/diff/review rather than overwrite;
- effectivity is deterministic;
- ECN/ECO/deviation records control changes;
- existing-stock impact is explicitly decided;
- controlled documents/firmware/test specs have immutable revisions/checksums;
- sales BOM remains semantically separate;
- future E06 work orders can reference one exact released manufacturing configuration;
- no required release/runtime path depends on GitHub Actions.
