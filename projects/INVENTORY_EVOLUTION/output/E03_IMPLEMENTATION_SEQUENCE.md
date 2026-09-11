# E03 Implementation Sequence — Location First, Execution After Stock Truth

## Status

`READY_AFTER_E02_FOUNDATION`

## Entry rules

E03 design is complete enough to implement later, but runtime entry is staged.

### Additive infrastructure may start only when

```text
E00 complete
E01 complete
E11-S01/S02 complete
E02 stock identity + movement/balance contracts merged and stable
current-main Release Gate PASS
```

### Stock-mutating E03 execution may be enabled only when

```text
E02 authoritative stock cutover PASS
reconciliation clean
current-main Release Gate PASS
```

This prevents E03 from creating a second warehouse truth while E02 is still shadowing legacy balances.

## Slice A — Stable Location Identity

Suggested branch:

```text
impl/e03-location-identity
```

Scope:

- E03-S01;
- stable `location_code` and execution metadata;
- compatibility migration/report for zone/shelf/box;
- preserve location IDs/layout links;
- no stock movement behavior change.

Gate:

- deterministic mapping of all existing locations;
- duplicate/conflict preflight report;
- cross-warehouse integrity tests;
- full Release Gate.

Rollback: additive metadata can be ignored; never destroy historical location IDs.

## Slice B — Typed Scan Resolver

Suggested branch:

```text
impl/e03-scan-resolver
```

Scope:

- E03-S03;
- shared typed scan resolver;
- optional `scan_identifiers` registry;
- bridge existing material code/alias/barcode/QR matcher;
- location/task scan support;
- no stock mutation.

Gate:

- exact/alias/ambiguous/duplicate tests;
- task-context mismatch tests;
- proof that resolver performs no consequential write;
- desktop/mobile clients share the same contract.

## Slice C — Receiving Staging + Putaway

Suggested branch:

```text
impl/e03-putaway
```

Entry:

E02 movement kernel authoritative for the pilot warehouse/path.

Scope:

- E03-S02;
- receiving/staging location;
- putaway task/lines;
- one inbound pilot only;
- E02 location-to-location movement.

Preferred pilot order:

```text
controlled/manual fixture
 -> transfer inbound
 -> purchase receipt
```

Gate:

- partial/split putaway;
- exact-once replay;
- wrong warehouse/bin rejection;
- staging + destination reconcile exactly;
- full Release Gate.

## Slice D — Exact Bin Picking

Suggested branch:

```text
impl/e03-bin-picking
```

Scope:

- E03-S04;
- pick task/lines;
- deterministic source-bin suggestion;
- source-location + material scan proof;
- one shipment pilot.

Gate:

- reservation-to-bin allocation deterministic;
- wrong bin/material blocked;
- partial pick explicit;
- concurrent operators cannot over-pick;
- shipment consumption remains E02 authority;
- full Release Gate.

## Slice E — Location-aware Counting

Suggested branch:

```text
impl/e03-count-observation
```

Scope:

- E03-S05;
- location-aware observations;
- blind-count option;
- variance/review evidence;
- approved reconciliation through E02 adjustment movement;
- compatibility with current count UI/API during migration.

Gate:

- observation never changes balance;
- recount preserves previous evidence;
- approve exact-once;
- reject posts nothing;
- whole warehouse retains per-location identity;
- full Release Gate.

## Slice F — Cycle Count + Simple Location Policies

Suggested branch:

```text
impl/e03-warehouse-policy
```

Scope:

- E03-S06;
- location count intervals;
- preferred material locations;
- pick sequence;
- deterministic putaway/pick suggestion;
- scheduling through E01 Durable Jobs/server-owned scheduler.

Gate:

- no duplicate due tasks;
- policy change does not mutate stock/history;
- disabled/cross-warehouse targets rejected;
- no GitHub Actions runtime dependency.

## Slice G — Mobile / Handheld Guided Scan UX

Suggested branch:

```text
impl/e03-mobile-scan-ux
```

Scope:

- E03-S07;
- shared mobile task state machine;
- putaway/pick/transfer/count scan flows;
- feedback/haptic/audio where useful;
- safe task prefetch/cache;
- no authoritative offline stock writes.

Gate:

- duplicate camera frame does not double-submit;
- stale task/client cache cannot authorize command;
- reconnect does not blindly replay succeeded operation;
- existing mobile functionality remains usable;
- full client-routing + repository Release Gate.

## Migration-number rule

Do not reserve numeric migrations in this design document.

At implementation time:

```text
read latest merged migration from main
 -> assign next contiguous number
 -> immutable checksum definition
 -> migration pre/post integrity
```

This avoids collisions with E01/E02/E11 implementation branches.

## E03 rollout stop conditions

Stop expansion if any of these occurs:

- location migration cannot map a legacy row deterministically;
- E02 vs E03 execution creates stock divergence;
- scan resolver returns ambiguous identity but workflow attempts automatic action;
- staging/putaway retry can duplicate movement;
- pick task can consume more than reservation/available position;
- count observation directly changes balance;
- mobile offline queue can replay consequential write without server idempotency.

Fix the invariant before moving to the next slice.

## Explicitly not in E03

```text
lot / serial
quality/quarantine authority
IQC / NCR / MRB
FEFO based on expiry
wave / cluster picking
cartonization
slotting AI
MFC / PLC automation
```

Those require later authoritative domains and measured business need.

## Completion rule

E03 completes only after every enabled warehouse execution path uses stable location identity, typed scan validation and E02 stock truth, with count observations and putaway/pick evidence independently auditable.
