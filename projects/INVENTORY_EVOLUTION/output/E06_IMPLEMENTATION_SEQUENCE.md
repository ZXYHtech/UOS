# E06 Implementation Sequence — Frozen Configuration, Controlled Material, Real Output

## Status

`READY_AFTER_E05_GATE`

## Entry condition

Do not create E06 runtime implementation until:

```text
E00 complete
E01 complete
E11-S01/S02 complete
E02 stock kernel authoritative
E03 warehouse execution stable
E04 electronics identity/AVL complete
E05 released configuration complete
current-main Release Gate PASS
```

Branch every slice from then-current `main`.

## Slice A — WO Header / Lifecycle / Configuration Freeze

Suggested branch:

```text
impl/e06-work-order-core
```

Scope:

- E06-S01;
- WO header/state machine;
- production vs engineering-prototype order type;
- freeze product revision/MBOM/release package;
- no material issue yet.

Gate:

- invalid configuration release rejected;
- frozen IDs immutable;
- transition/permission matrix;
- full Release Gate.

## Slice B — Requirement Snapshot / Reservation

Suggested branch:

```text
impl/e06-wo-requirements
```

Scope:

- E06-S02;
- MBOM explosion at release;
- requirement snapshot;
- E02 work-order reservation;
- shortage/readiness.

Gate:

- snapshot exactly tied to released MBOM;
- later MBOM change no effect;
- reservation/ATP concurrency tests;
- cancellation of unused reservations exact-once.

## Slice C — Kit / Pick / Issue

Suggested branch:

```text
impl/e06-wo-issue
```

Scope:

- E06-S03;
- E03 pick/scan integration;
- E02 issue to WO-owned WIP;
- partial issue.

Gate:

- movement + requirement update atomic;
- no overissue through normal command;
- concurrent issue cannot exceed authority;
- WIP remains attributable to WO/requirement.

## Slice D — Return / Overissue / Scrap

Suggested branch:

```text
impl/e06-material-exceptions
```

Scope:

- E06-S04;
- controlled overissue;
- partial return;
- material scrap;
- WIP equation/reversal.

Gate:

- reasons/permissions;
- bounded return/scrap;
- no planned-requirement rewrite;
- exact-once/reversal tests.

## Slice E — Partial Output / Output Receipt

Suggested branch:

```text
impl/e06-output-receipt
```

Scope:

- E06-S05;
- partial finished output receipts;
- E02 output movement;
- completed quantity/state;
- E07 quality seam only, no fabricated quality data.

Gate:

- partial aggregation;
- replay/reversal;
- frozen output revision;
- closure does not bypass WIP policy.

## Slice F — Hold / Cancel / Disposition

Suggested branch:

```text
impl/e06-wo-disposition
```

Scope:

- E06-S06;
- hold/resume;
- cancel-pending-disposition;
- reservation release;
- WIP return/scrap/close rules.

Gate:

- cancellation cannot strand WIP;
- output history preserved;
- hold blocks new execution without hiding existing stock/evidence.

## Slice G — Controlled Substitute Execution

Suggested branch:

```text
impl/e06-wo-substitution
```

Scope:

- E06-S07;
- E04 approved alternate / AML use;
- E05 deviation/waiver use;
- reservation migration from original to substitute;
- actual-substitute evidence.

Gate:

- similarity/alias/supplier stock cannot authorize;
- scope/effectivity/quantity enforced;
- directionality enforced;
- historical authority retained.

## Slice H — Prototype / Trial-build Mode

Suggested branch:

```text
impl/e06-prototype-build
```

Scope:

- E06-S08;
- engineering prototype mode;
- immutable draft-design snapshot;
- project/custody context;
- non-saleable output default;
- same E02/E03 stock execution.

Gate:

- prototype freedom does not weaken production release rules;
- draft edit does not rewrite old prototype build;
- output excluded from saleable ATP by default;
- cannot convert executed prototype WO into production WO.

## Optional later slice — Operations / labor actuals

Do **not** block E06 completion on full routing/MES.

Only add `work_order_operations` / labor-time capture when operators have a real need for station sequencing or actual labor variance.

Avoid:

- generic MES workflow engine;
- machine integration before hardware need;
- capacity scheduling before reliable timestamps/demand.

## Migration-number rule

No E06 migration numbers are reserved in design.

Each slice takes the next contiguous migration on merged `main` and passes E00 migration/integrity/recovery semantics.

## Stop conditions

Stop expansion if:

- WO config floats to latest BOM/release;
- requirement snapshot is recomputed from current master;
- reservation/issue can double-post;
- issued material loses WO ownership;
- normal issue silently overissues;
- cancel can close with stranded WIP;
- substitute can bypass E04/E05 authority;
- prototype output enters normal ATP without explicit release/disposition.

## Completion rule

E06 completes when one low-volume production WO can be released from an exact E05 configuration, reserve/kit/issue material, handle returns/scrap/substitutes, receive partial finished output and close/cancel without losing any stock or configuration evidence.
