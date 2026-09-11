# TASK_INV_IMPL_E04_S04 — Package and Footprint Identity

## Status

`DESIGN_READY_BLOCKED_BY_E04_S02`

## Objective

Separate physical component package identity from PCB footprint/library identity so MPN, BOM and EDA integration do not rely on one overloaded free-text package field.

## Core distinction

```text
Package
 = physical body / leads / mechanical package family

Footprint
 = PCB land-pattern / CAD-library identity
```

They are related but not identical.

## Suggested objects

```text
packages
  id
  package_code
  package_name
  package_family
  body_dimensions metadata
  pin_count
  pitch
  status
  source/evidence

footprints
  id
  footprint_code
  cad_system
  library_name
  footprint_name
  revision
  status
  source/evidence

package_footprint_relations
  package_id
  footprint_id
  approval_status
  qualification_reference
```

## Rules

- one package may have multiple approved footprints;
- one footprint may support more than one package variant only when explicitly qualified;
- free-text `materials.model/spec` does not become package authority automatically;
- manufacturer part may reference a package identity;
- E05 BOM line / EDA import can reference approved footprint/library identities later;
- relation existence is not equivalent to BOM approval/effectivity.

## Migration

Legacy package-like text from material specs/OpenPnP imports is staging evidence only until matched/confirmed.

Do not auto-merge package strings merely because punctuation or dimensions appear similar.

## Search

Support exact package/footprint identities and aliases, while retaining canonical display values.

## Tests

- package code unique under defined namespace;
- footprint identity includes CAD/library namespace;
- package and footprint cannot be silently conflated;
- manufacturer part can link package without forcing one footprint;
- unapproved package-footprint relation cannot be treated as qualified;
- legacy free-text package candidate remains reviewable without rewriting source text.

## Acceptance

Mechanical package and EDA footprint become explicit reusable identities suitable for manufacturer-part data, BOM/EDA workflows and controlled compatibility decisions.
