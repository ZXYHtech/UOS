# TASK_INV_IMPL_E05_S01 — Product / Part Revision Identity and Release State

## Status

`DESIGN_READY_BLOCKED_BY_E04_GATE`

## Objective

Introduce immutable released product/part revision identities so later EBOM, MBOM, documents, firmware, work orders and test records can reference an exact historical configuration.

## Suggested object

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
  withdrawn_at
  change_reference
```

## Status vocabulary

```text
draft
review
released
obsolete
withdrawn
```

## Rules

- revision code unique within `material_id`;
- draft may be edited by authorized engineering users;
- released revision is immutable under ordinary workflow;
- correction creates a new revision or explicit withdrawal/supersession;
- obsolete/withdrawn revisions remain historically queryable;
- one material may have multiple historical released revisions;
- default-current resolution is a query/policy, not “overwrite old row”.

## Relationship to material master

`materials.id` remains internal part identity from E04.

`part_revisions` represents controlled configuration versions of that part/product, not a new material number.

Do not clone material inventory/pricing rows per revision.

## Release evidence

Release records:

- actor;
- time;
- change reason/reference;
- applicable review policy/result;
- linked change record when E05-S06 is used.

## Effectivity

P0 may record simple effective-from metadata, but final default-effective resolution is implemented with E05-S05 so revision release and effectivity remain distinct concepts.

## Tests

- duplicate revision code for same material rejected;
- same revision code on different materials allowed if policy permits;
- released revision edit rejected;
- superseding revision does not delete old revision;
- obsolete/withdrawn remains historically resolvable;
- user without release permission cannot release via API;
- operation/audit evidence records release transition.

## Acceptance

The system has a stable immutable revision identity that future BOM/work-order/test/document records can reference instead of following mutable current material state.
