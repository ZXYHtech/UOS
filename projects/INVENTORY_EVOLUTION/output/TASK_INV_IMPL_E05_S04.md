# TASK_INV_IMPL_E05_S04 — EDA Import Staging, Identity Resolution and BOM Diff

## Status

`DESIGN_READY_BLOCKED_BY_E04_E05_S02`

## Objective

Allow Altium/KiCad/other EDA BOM exports to accelerate EBOM creation while guaranteeing that an import can never silently rewrite a released engineering BOM.

## Pipeline

```text
EDA export/source
 -> import session
 -> raw staging rows
 -> normalize refdes/value/package/manufacturer/MPN
 -> E04 identity resolution
 -> unresolved/ambiguous review
 -> compare with selected previous EBOM revision
 -> create/update draft EBOM only
 -> explicit engineering review/release
```

## Suggested objects

```text
eda_import_sessions
  id
  source_type
  source_file_name
  source_hash
  source_project_ref
  imported_by
  imported_at
  target_material_id
  compare_bom_revision_id
  status

eda_import_rows
  id
  session_id
  source_row_no
  raw_json
  refdes_raw
  value_raw
  package_raw
  manufacturer_raw
  mpn_raw
  quantity_raw
  matched_material_id
  matched_manufacturer_part_id
  resolution_status
  resolution_reason
  reviewed_by/at
```

## Source preservation

Raw row/source text must be retained even after successful normalization so engineers can audit what the EDA export actually contained.

## Identity resolution

Use E04 exact identity services:

1. exact internal part number if present;
2. exact manufacturer + MPN;
3. approved mapping/alias where controlled;
4. candidate list requiring review.

Fuzzy text never auto-resolves a production EBOM line.

## RefDes normalization

Parser may split/group refdes but preserves original source representation.

Duplicate refdes, invalid format or one refdes resolving to multiple materials blocks automatic draft generation for affected rows.

## BOM diff

Against a selected prior EBOM revision classify:

```text
unchanged
added
removed
component_changed
quantity_changed
refdes_added
refdes_removed
DNF_changed
package/MPN_source_changed
unresolved
```

Diff is review evidence, not release authority.

## Draft generation

Only resolved/reviewed rows may populate a draft EBOM automatically.

Unresolved rows remain explicit blockers/warnings according to release policy.

No import operation may target a released BOM row for in-place edit.

## Tests

- source file hash/session recorded;
- import preserves raw values;
- exact MPN/internal part match deterministic;
- ambiguous match requires review;
- duplicate refdes detected;
- diff classifications deterministic;
- import creates draft only;
- released EBOM remains unchanged;
- repeated same import can be recognized/idempotent without duplicate draft lines;
- unresolved rows visible in release preflight.

## Acceptance

EDA exports can efficiently produce reviewed draft EBOM revisions and clear diffs while released production configuration remains protected from automated overwrite.
