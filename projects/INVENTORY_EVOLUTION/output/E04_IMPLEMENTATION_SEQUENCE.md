# E04 Implementation Sequence — Identity Before Approval, Evidence Before Automation

## Status

`READY_AFTER_E03_GATE`

## Entry condition

Runtime implementation starts only after:

```text
E00 complete
E01 complete
E11-S01/S02 complete
E02 authoritative stock kernel complete
E03 warehouse execution gate complete
current-main Release Gate PASS
```

Branch each slice from then-current `main`.

## Slice A — Internal Part Compatibility Contract

Suggested branch:

```text
impl/e04-internal-part-contract
```

Scope:

- E04-S01;
- freeze `materials.id` / `material_code` semantics;
- legacy model/MPN candidate report;
- no canonical manufacturer assignment yet.

Gate:

- existing relations unchanged;
- channel SKU/BOM/pricing/procurement references intact;
- no ambiguous auto-migration;
- full Release Gate.

## Slice B — Manufacturer + MPN Identity

Suggested branch:

```text
impl/e04-manufacturer-mpn
```

Scope:

- E04-S02;
- manufacturers / aliases;
- manufacturer-part exact identity;
- normalization rules;
- no production approval relation yet.

Gate:

- duplicate rules;
- manufacturer namespace tests;
- canonical display preservation;
- existence != approval.

## Slice C — Supplier Part Identity

Suggested branch:

```text
impl/e04-supplier-part
```

Scope:

- E04-S03;
- supplier SKU namespace;
- exact/unresolved resolution states;
- MOQ/order multiple/lead time basics;
- PO snapshot compatibility design.

Gate:

- supplier namespace identity;
- conflicting identity blocked;
- unresolved source cannot act approved.

## Slice D — Package / Footprint

Suggested branch:

```text
impl/e04-package-footprint
```

Scope:

- E04-S04;
- package identity;
- CAD/library footprint identity;
- controlled relation;
- migration candidates from legacy text only.

Gate:

- package != footprint contract;
- relation approval explicit;
- no silent text merging.

## Slice E — Typed Parametric Engine

Suggested branch:

```text
impl/e04-parametrics
```

Scope:

- E04-S05;
- typed definitions/values;
- canonical units;
- requirement vs manufacturer-source scopes;
- legacy-spec migration candidates;
- structured filters.

Gate:

- unit conversion tests;
- raw value preserved;
- ambiguous legacy rows remain unconverted;
- parametric match cannot authorize substitution.

## Slice F — Lifecycle / Evidence / Compliance

Suggested branch:

```text
impl/e04-engineering-evidence
```

Scope:

- E04-S07;
- evidence/provenance;
- lifecycle assertions;
- datasheet/compliance linkage;
- provider-imported vs verified states.

Gate:

- history/supersession preserved;
- provider refresh cannot silently overwrite verified truth;
- unknown/stale states explicit.

## Slice G — AML / AVL / Substitutes

Suggested branch:

```text
impl/e04-avl-substitute
```

Scope:

- E04-S06;
- material <-> manufacturer-part approvals;
- global-scope internal substitutes;
- approval/suspension/effectivity evidence;
- procurement eligibility contract.

Gate:

- alias != approval;
- MPN existence != approval;
- supplier preferred != approval;
- directional substitution;
- expired/suspended blocked;
- full Release Gate.

BOM-revision-scoped substitute authority remains blocked until E05 provides released BOM revision identities.

## Slice H — Component Search / Workspace / Provider Staging

Suggested branch:

```text
impl/e04-component-workspace
```

Scope:

- E04-S08;
- exact cross-identity search;
- component workspace;
- provider candidate/diff staging;
- extend E03 scan/global resolver.

Gate:

- exact MPN ranking;
- supplier namespace disambiguation;
- approval badges/status accurate;
- provider conflicts require review;
- workspace does not duplicate stock/pricing authority.

## Migration-number rule

No E04 migration number is reserved in design.

At implementation time each slice:

```text
reads latest merged migration
 -> takes next contiguous number
 -> immutable checksum
 -> E00 pre/post integrity
 -> full Release Gate
```

## Stop conditions

Stop the slice if:

- a second canonical internal-part master is accidentally introduced;
- MPN identity is inferred from ambiguous `model` data;
- supplier source bypasses engineering approval;
- package/footprint is collapsed into free text;
- provider data overwrites verified values silently;
- parametric similarity grants substitute authority;
- alias becomes equivalent to AVL.

## Completion rule

E04 completes only when identity, sourcing, approval, parametrics, provenance and search all agree on one controlled component master, while historical/current material IDs remain stable.
