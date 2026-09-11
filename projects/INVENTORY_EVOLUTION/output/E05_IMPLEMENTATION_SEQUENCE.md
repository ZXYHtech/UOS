# E05 Implementation Sequence — Release Baseline Before Manufacturing

## Status

`READY_AFTER_E04_GATE`

## Entry condition

Do not create E05 runtime implementation until:

```text
E00 complete
E01 complete
E11-S01/S02 complete
E02 complete
E03 complete
E04 complete
current-main Release Gate PASS
```

Branch every slice from then-current `main`.

## Slice A — Part Revision Identity

Suggested branch:

```text
impl/e05-part-revision
```

Scope:

- E05-S01;
- part/product revision table;
- draft/review/released/obsolete/withdrawn states;
- release permission/audit;
- no BOM migration yet.

Gate:

- released immutable;
- supersession/history tests;
- API permission tests;
- full Release Gate.

## Slice B — Controlled EBOM + RefDes

Suggested branch:

```text
impl/e05-ebom
```

Scope:

- E05-S02;
- engineering BOM revision/lines/refdes;
- multilevel cycle detection;
- no sales-BOM behavior change.

Gate:

- refdes integrity;
- released immutable;
- sales/EBOM separation;
- exact revision explosion.

## Slice C — EDA Import Staging + Diff

Suggested branch:

```text
impl/e05-eda-staging
```

Scope:

- E05-S04;
- import sessions/raw rows;
- E04 identity matching;
- unresolved review;
- BOM diff;
- draft EBOM generation only.

Gate:

- import cannot edit released BOM;
- source/hash retained;
- ambiguity blocks auto-resolution;
- diff deterministic.

## Slice D — Controlled MBOM

Suggested branch:

```text
impl/e05-mbom
```

Scope:

- E05-S03;
- derive MBOM from released EBOM;
- manufacturing additions/differences;
- line type/scrap-factor semantics;
- no MRP yet.

Gate:

- ancestry preserved;
- differences explainable;
- draft EBOM cannot become released MBOM source;
- released MBOM immutable.

## Slice E — Effectivity Resolution

Suggested branch:

```text
impl/e05-effectivity
```

Scope:

- E05-S05;
- current effective configuration resolver;
- effective-from/to;
- deterministic default configuration.

Gate:

- future/current/historical resolution tests;
- overlap detection;
- historical reference never floats.

## Slice F — ECN/ECO/Deviation

Suggested branch:

```text
impl/e05-engineering-change
```

Scope:

- E05-S06;
- engineering change aggregate;
- affected objects;
- impact checklist;
- stock/WIP disposition decisions;
- deviation/waiver scope.

Gate:

- unresolved impact blocks approval;
- before/after references immutable;
- deviation expiry enforced;
- no direct stock mutation.

## Slice G — Controlled Documents / Firmware / Test Spec

Suggested branch:

```text
impl/e05-controlled-docs
```

Scope:

- E05-S07;
- controlled document/revision;
- immutable SHA-256 release artifact;
- release package;
- firmware release identity;
- test procedure/limit-set revision.

Gate:

- released bytes immutable;
- historical revisions preserved;
- package cannot mix draft required items;
- unauthorized release blocked;
- E00 backup/restore extended to validate artifacts/checksums before production reliance.

## Slice H — Compatibility / Where-used / Cost Source

Suggested branch:

```text
impl/e05-bom-compatibility
```

Scope:

- E05-S08;
- explicit sales/engineering/manufacturing BOM APIs;
- where-used;
- legacy migration report;
- cost source/revision labeling.

Gate:

- shipment sales BOM regression unchanged;
- controlled BOM never modifies legacy sales BOM;
- cost result identifies source/revision;
- legacy candidate never auto-released.

## Migration-number rule

Do not pre-reserve E05 migration numbers.

Each implementation slice takes the next contiguous merged migration number from current `main`, uses an immutable checksum and passes E00 pre/post integrity semantics.

## Stop conditions

Stop if:

- a released object remains mutable;
- EDA import can overwrite production configuration;
- MBOM loses its EBOM ancestry;
- caller uses generic/latest BOM where exact revision is required;
- current effectivity can return two conflicting defaults;
- ECO approves while required impact remains unresolved;
- controlled file can be replaced without new revision/checksum;
- sales BOM behavior changes unintentionally.

## Completion rule

E05 completes only when E06 can create a work order that references one exact released part revision, MBOM revision and coherent release package, and that configuration remains historically immutable.
