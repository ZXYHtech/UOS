# TASK_INV_IMPL_E05_S02 — Revisioned EBOM and Reference Designators

## Status

`DESIGN_READY_BLOCKED_BY_E05_S01_E04`

## Objective

Create a controlled Engineering BOM that represents design intent by released revision, with first-class reference designators and no dependence on mutable sales/project BOM rows.

## Suggested objects

```text
bom_revisions
  id
  parent_material_id
  part_revision_id
  bom_type='engineering'
  revision_code
  status
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
  dnf
  optional
  variant_condition
  notes

bom_line_refdes
  bom_line_id
  refdes
```

## Semantics

Each EBOM line references the internal engineering component requirement (`materials.id`).

Approved manufacturer parts/alternates are resolved through E04 controlled relationships; do not store an arbitrary supplier/MPN string as substitute authority on the line.

## RefDes

Reference designators such as:

```text
R1
R2
C7
U3
J1
```

belong to the EBOM placement context.

Rules:

- preserve canonical display text;
- prevent duplicate active refdes within one EBOM revision where applicable;
- quantity/refdes count consistency is validated for fitted discrete placements unless line type/policy allows otherwise;
- DNF lines may retain refdes even though consumed quantity is zero/none by manufacturing policy.

## Line identity

Use a stable line ID + line number within revision.

Do not use refdes itself as the inventory/material identity.

## Draft/release

- draft EBOM editable;
- review/release through Action Policy;
- released EBOM immutable;
- changes create a new revision;
- old released revision remains queryable.

## Multilevel

EBOM lines may reference subassembly internal materials.

Explosion requires explicit revision selection/effectivity and cycle detection.

Do not implicitly use “latest” subassembly revision in historical released builds.

## Sales BOM separation

Current `material_bom` remains fulfilment/sales-kit behavior.

An EBOM release must not change shipment component explosion unless a separate controlled business decision migrates that product's sales BOM semantics.

## Tests

- released EBOM immutable;
- refdes duplicate blocked;
- refdes preserved across revision copy/diff;
- cycle detection prevents recursive BOM loop;
- sales BOM edit does not alter EBOM;
- EBOM edit does not alter sales BOM;
- unapproved MPN cannot be smuggled into line as substitute authority;
- historical revision explosion resolves exact referenced child revisions/effectivity policy.

## Acceptance

Engineering can release a specific design BOM revision with exact internal parts, quantities and PCB reference designators, while sales/fulfilment BOM remains independent.
