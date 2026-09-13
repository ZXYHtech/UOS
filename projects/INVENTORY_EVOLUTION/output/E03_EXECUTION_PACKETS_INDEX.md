# E03 Execution Packets Index — Warehouse Execution

## Status

`ALL_E03_EXECUTION_PACKETS_READY_BLOCKED_BY_E02_FOUNDATION_AND_AUTHORITY_GATES`

This is the direct handoff index for implementing E03 after E02 stock truth is sufficiently stable.

## Entry gates

Additive/read-only E03 infrastructure may start only when:

```text
E00 complete/merged
E01 complete/merged
E11 early pricing safety complete
E02 stock identity + movement + balance contracts merged/stable
full current-main Release Gate PASS
```

Stock-mutating E03 execution may be enabled only when the applicable E02 stock authority path is active and reconciliation is clean.

Each slice branches from then-current `main`.

## Migration numbering

E02 prepared migrations are fixed through version 9:

```text
7 movement ledger
8 stock balances
9 stock reservations/events
```

E02-J may still consume the next migration if a separately reviewed final structural constraint is genuinely required.

Therefore E03 does **not** pre-publish numeric migration IDs. For every schema slice:

```text
read latest merged schema_migrations version
 -> assign next contiguous immutable number
 -> checksum + pre/post integrity
```

Expected numbering begins at 10 only if E02-J uses no additional migration.

## Slice A — Stable Location Identity

Packet:

`E03_SLICE_A_EXECUTION_PACKET.md`

Branch:

`impl/e03-location-identity`

Schema:

```text
NEXT_CONTIGUOUS
warehouse_locations additive stable identity/execution metadata
```

Purpose:

- stable `location_code`;
- location type and execution flags;
- preserve location IDs;
- deterministic legacy mapping/conflict report;
- decouple layout lifecycle from business location lifecycle;
- referenced location cannot be hard-deleted or moved to another warehouse.

Critical confirmed legacy risks corrected here:

1. deleting a layout box can currently delete its `warehouse_locations` row;
2. location edit can currently change `warehouse_id`.

After E03-A, layout delete/rename/reposition cannot rewrite historical warehouse-location identity.

Unlocks B and later location-aware execution.

## Slice B — Typed Scan Resolver

Packet:

`E03_SLICE_B_EXECUTION_PACKET.md`

Branch:

`impl/e03-scan-resolver`

Schema:

```text
NONE
or NEXT_CONTIGUOUS = scan_identifiers registry if required by implementation
```

Purpose:

- one shared resolver for material/location/task/document scans;
- reuse material code/barcode/QR/alias semantics;
- return typed canonical identity + match explanation;
- ambiguity blocks auto-action;
- resolver performs zero stock mutation.

Unlocks C/D/E/G.

## Slice C — Receiving Staging / Putaway

Packet:

`E03_SLICE_C_EXECUTION_PACKET.md`

Branch:

`impl/e03-putaway`

Schema:

```text
NEXT_CONTIGUOUS = putaway_tasks + putaway_task_lines
```

Entry additionally requires E02 movement/balance authority for chosen pilot.

Model:

```text
receipt
 -> RECEIVING/STAGING E02 position
 -> putaway task
 -> source/material/destination scans
 -> E02 location-to-location movement
 -> storage bin
```

Partial/split putaway is explicit. Putaway task never owns independent stock truth.

Preferred rollout:

```text
controlled fixture/manual inbound
 -> transfer receipt
 -> purchase receipt
```

Purchase path still honors `PURCHASE_PARTIAL_RECEIPT_LANDED_COST_SAFETY_REVIEW.md` prerequisite from E02-H.

## Slice D — Exact-bin Picking

Packet:

`E03_SLICE_D_EXECUTION_PACKET.md`

Branch:

`impl/e03-bin-picking`

Schema:

```text
NEXT_CONTIGUOUS = pick_tasks + pick_task_lines
```

Entry additionally requires E02 reservation/ATP authority for shipment pilot.

Critical boundary:

```text
pick confirmation = execution evidence
shipment issue = physical E02 movement + reservation consume
```

Do not deduct stock once during pick and again during shipment.

Current `shipment_scan_logs` may be bridged during migration but cannot remain an independent picked-quantity truth indefinitely.

## Slice E — Location-aware Count Observation

Packet:

`E03_SLICE_E_EXECUTION_PACKET.md`

Branch:

`impl/e03-count-observation`

Schema:

```text
NEXT_CONTIGUOUS = inventory_count_observations + inventory_count_variances
```

Preserves current strong count principle:

```text
observation != mutation
approved variance -> E02 count_adjustment movement
```

Adds:

- exact location identity;
- blind count option;
- immutable recount rounds;
- stale-snapshot/movement-after-snapshot detection before approval.

Whole-warehouse count retains distinct bins rather than collapsing by material.

## Slice F — Cycle Count / Simple Location Policies

Packet:

`E03_SLICE_F_EXECUTION_PACKET.md`

Branch:

`impl/e03-warehouse-policy`

Schema:

```text
NEXT_CONTIGUOUS = location_count_policies + material_preferred_locations
```

Purpose:

- recurring count scheduling;
- preferred putaway/pick locations;
- deterministic pick sequence;
- no automatic relocation;
- no AI/opaque slotting.

Scheduler uses E01 Durable Jobs/systemd-owned runtime, never GitHub Actions.

## Slice G — Mobile / Handheld Guided Scan UX

Packet:

`E03_SLICE_G_EXECUTION_PACKET.md`

Branch:

`impl/e03-mobile-scan-ux`

Migration:

`NONE expected`

Shared state machine:

```text
TASK -> LOCATION -> MATERIAL -> QUANTITY -> CONFIRM
```

Client may cache/prefetch display context only. Every consequential command revalidates server-side permission/scope/state/E02 truth/E03 location.

Offline authoritative stock writes remain forbidden. Reconnect checks task/business-operation status before retrying.

## E03-wide invariants

```text
E02 = stock/reservation authority
E03 = location/task/scan execution evidence
layout = presentation/projection only
scan confidence != action authority
observation != stock mutation
pick evidence != physical issue movement
receipt != putaway
```

E03 does not own:

```text
lot/serial
quality/quarantine truth
IQC/NCR/MRB
FEFO
wave/cluster picking
cartonization
AI slotting
PLC/MFC automation
```

## Universal stop conditions

Stop a slice if:

- stable location identity still depends on layout deletion/reparenting;
- referenced location can change warehouse;
- ambiguous scan automatically triggers a stock action;
- putaway or pick tables maintain an independent stock total;
- same retry can move/pick/count-adjust twice;
- pick and shipment both physically deduct the same stock;
- stale count snapshot can apply an old delta without review/recount;
- client/offline cache can authorize stock mutation;
- E02/E03 reconciliation diverges;
- required scheduling depends on GitHub Actions.

## Completion

E03 completes only when enabled warehouse execution paths use stable location identity, shared typed scan validation and E02 stock truth, with receiving/putaway/picking/count evidence independently auditable.

Then E04 electronics component master may proceed according to the master roadmap.