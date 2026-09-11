# TASK_INV_AUDIT_AVL_SUBSTITUTE_01 — AVL, Alternate Parts & Substitution Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Static code/schema search found no dedicated AVL/substitute domain. This report therefore evaluates the gap relative to the existing material/supplier/BOM foundation.

## 1. Executive conclusion

Approved alternates are currently a missing first-class capability. Aliases are not substitutes, and multiple generic material records are not an AVL.

For electronics manufacturing, substitution must answer two distinct questions:

```text
Is this manufacturer part approved for this internal part?
Can this different internal part replace another internal part in this design/revision/context?
```

These require controlled relationships, evidence and effectivity.

## 2. Terminology

### AML / approved manufacturer list

For one internal part, which manufacturer + MPN combinations are approved?

### Supplier source list

Which suppliers may supply each approved manufacturer part, with supplier SKU, MOQ, lead time and commercial terms?

### Alternate/substitute part

A different internal part that can replace another, potentially only under specific engineering conditions.

### Equivalent versus compatible

Do not use one boolean `is_substitute` for all cases. RF/electronics substitutions can be:

- form/fit/function equivalent;
- electrically compatible but package differs;
- footprint compatible with derated performance;
- temporary engineering deviation;
- purchasing-only alternate for the same exact MPN.

## 3. Why aliases cannot solve this

Current `material_aliases` helps search/recognition. It should remain a naming concept.

Treating an alias as an alternate would incorrectly imply:

```text
same name/search token = approved replacement
```

which is unsafe for production.

## 4. Recommended model

### Approved manufacturer part

```text
material_id
manufacturer_part_id
approval_status
approved_by
approved_at
qualification_reference
valid_from / valid_to
remarks
```

### Substitute relationship

```text
source_material_id
target_material_id
substitution_class
scope: global | BOM_revision | work_order | deviation
condition_text/structured constraints
approval_status
engineering_change_id
valid_from/to
priority
```

### Supplier source

Associate supplier-part records with approved manufacturer parts rather than only supplier + generic material.

## 5. RF-specific substitution concerns

For RF modules, “same package and similar description” is especially insufficient. Controlled substitution may need limits for:

- frequency range
- gain/NF/P1dB/OIP3
- insertion loss/isolation
- bias voltage/current
- logic/control interface
- temperature range
- package/footprint
- matching network impact
- calibration impact
- firmware/register differences

The parametric system should help identify candidates, but engineering approval should authorize them.

## 6. BOM relationship

A BOM line should normally reference the internal engineering part requirement. AVL resolves approved manufacturer parts beneath it.

For true alternate internal parts, the BOM revision/deviation should declare whether substitution is allowed.

This prevents purchasing from silently swapping a part merely because inventory is available.

## 7. Shortage workflow

Recommended shortage behavior:

```text
MRP shortage
 -> exact approved sources available?
 -> approved AML sources available?
 -> pre-approved alternate internal part available?
 -> engineering review required?
 -> temporary deviation/ECN if accepted
```

Every replacement used in production must remain traceable to the work order/lot/serial genealogy.

## 8. Lifecycle/EOL integration

AVL becomes especially valuable when an MPN is:

- NRND
- EOL
- obsolete
- allocation constrained
- supplier-discontinued

Do not automatically replace EOL parts. Create sourcing/engineering tasks based on approved alternatives and risk.

## 9. Priorities

### P0

1. manufacturer/MPN model from PART_PARAMETRIC task;
2. approved manufacturer-part relationship;
3. supplier-part relationship;
4. explicit alternate/substitute table;
5. engineering approval/audit fields.

### P1

1. BOM-revision scoped alternates;
2. deviation/temporary substitution;
3. shortage candidate suggestion;
4. lifecycle/EOL flags and evidence;
5. production trace of actual approved part used.

### P2

1. rules-assisted alternate ranking;
2. parametric comparison UI;
3. external lifecycle monitoring.

## 10. Acceptance signals

Local tests should prove:

- alias does not grant substitution authority;
- unapproved MPN cannot be selected as production source where approval is required;
- alternate can be valid for one BOM revision and invalid for another;
- expired/obsolete approval is not silently used;
- actual substituted lot remains traceable.

## 11. Preliminary maturity

- alias/search support: 3.5/5
- supplier foundation: 2.5/5
- AML/AVL: 0.5/5
- controlled substitutes: 0.5/5
- engineering approval/effectivity: 0.5/5
- shortage substitution workflow: 0.5/5

## 12. Core recommendation

Build AVL as a controlled relationship beneath the existing material master, not as extra text fields. Keep search aliases, approved manufacturer sources and engineering substitutes as three separate concepts.