# TASK_INV_IMPL_E05_S03 — MBOM Derivation and Manufacturing Differences

## Status

`DESIGN_READY_BLOCKED_BY_E05_S02`

## Objective

Create a released Manufacturing BOM that explicitly derives from a released EBOM and records manufacturing-specific additions/removals/changes instead of silently duplicating design structure.

## Suggested model

Reuse controlled `bom_revisions` / `bom_lines` with:

```text
bom_type='manufacturing'
based_on_bom_revision_id=<released EBOM>
```

Additional MBOM line semantics may include:

```text
line_type
  component
  subassembly
  phantom
  consumable
  packaging
  label
  process_material

scrap_factor
manufacturing_note
source_ebom_line_id
change_reason
```

## Required ancestry

Normal MBOM creation path:

```text
released EBOM revision
 -> derive draft MBOM revision
 -> manufacturing review/diff
 -> release MBOM
```

A legacy MBOM migration without exact ancestry must be explicitly flagged as `legacy_source_unknown`; do not fabricate a source EBOM.

## Diff classification

Every difference against source EBOM should be explainable as one of:

```text
inherited
added_for_manufacturing
removed_from_manufacturing
quantity_changed
line_type_changed
packaging_added
consumable_added
subassembly_transformed
```

Each non-inherited change carries a reason.

## Typical RF-module additions

- shielding cover;
- enclosure;
- screws;
- connectors/cables not represented in board EBOM;
- labels;
- packaging;
- process consumables where controlled;
- manufacturing subassembly/panelization representation.

## DNF / optional behavior

MBOM must explicitly resolve how EBOM DNF/optional lines are treated for the released manufacturing configuration.

Do not rely on UI hiding to remove a component from demand.

## MRP contract

E08 MRP explodes only a released effective MBOM revision for production demand.

Never explode:

- `material_bom` sales bundle;
- mutable draft EBOM;
- draft MBOM;
- ambiguous “latest BOM”.

## Cost contract

MBOM can feed standard manufacturing estimate later.

Cost output must identify the exact `bom_revision_id` and must not overwrite historical actual work-order cost.

## Tests

- MBOM requires released source EBOM in normal path;
- source ancestry immutable after MBOM release;
- manufacturing-only line carries reason/source classification;
- EBOM future revision does not mutate old MBOM;
- draft source cannot become released MBOM ancestry accidentally;
- DNF/optional handling deterministic;
- released MBOM immutable;
- MRP query rejects draft/non-manufacturing BOM.

## Acceptance

Manufacturing can release a BOM that is traceably based on one engineering revision while explicitly documenting process/packaging/consumable differences, giving E06/E08 one stable production contract.
