# E07 Implementation Sequence — Trace Honestly, Release with Evidence

## Status

`READY_AFTER_E06_GATE`

## Entry condition

Do not create E07 runtime implementation until:

```text
E00 complete
E01 complete
E11-S01/S02 complete
E02 authoritative stock kernel
E03 warehouse execution stable
E04 electronics identity/AVL complete
E05 controlled configuration complete
E06 work-order execution complete
current-main Release Gate PASS
```

Branch every slice from then-current `main`.

## Slice A — Trace Policy + Lot/Serial Identity

Suggested branch:

```text
impl/e07-trace-identity
```

Scope:

- E07-S01;
- NONE/LOT/SERIAL/LOT_AND_SERIAL policy;
- lot/serial identities;
- legacy-untraced evidence boundary;
- E03 scan resolver extension.

Gate:

- serial uniqueness/non-reuse;
- policy enforcement;
- no historical genealogy fabrication;
- full Release Gate.

## Slice B — Lot-aware Receipt + Quality Stock States

Suggested branch:

```text
impl/e07-quality-stock
```

Scope:

- E07-S02;
- multi-lot receipt;
- E02 quality-state dimension;
- pending/accepted/quarantine/rejected/rework/scrap eligibility;
- one controlled receipt pilot.

Gate:

- lot totals reconcile receipt;
- pending/quarantine excluded from ATP/reservation;
- quality transition uses E02 movement, not in-place status edit;
- full Release Gate.

## Slice C — Inspection Plan / IQC / FQC

Suggested branch:

```text
impl/e07-inspection
```

Scope:

- E07-S03;
- released inspection plan/characteristics;
- IQC first, FQC second;
- partial acceptance/rejection;
- separation-of-duty policy.

Gate:

- historical plan/limit snapshot immutable;
- partial disposition exact;
- required characteristic/evidence enforced;
- no quality release through UI-only shortcut.

## Slice D — NCR / MRB-lite / Rework / Scrap

Suggested branch:

```text
impl/e07-ncr-rework
```

Scope:

- E07-S04;
- NCR/dispositions;
- rework/retest linkage;
- scrap/RTV/use-as-is controls.

Gate:

- affected quantity bounded;
- authority by disposition;
- original failure retained;
- stock movement exact-once.

## Slice E — Manufacturing Genealogy

Suggested branch:

```text
impl/e07-genealogy
```

Scope:

- E07-S05;
- output lot/serial generation;
- actual issue movement -> output genealogy;
- explicit capture granularity;
- reverse trace queries.

Gate:

- no theoretical BOM-only genealogy;
- WO/output-lot scope not misrepresented as per-serial;
- supplier lot -> affected output query deterministic.

## Slice F — Released Test Spec / Limit Execution

Suggested branch:

```text
impl/e07-test-limits
```

Scope:

- E07-S06;
- structured released limit sets linked to E05 documents;
- deterministic evaluation;
- historical snapshots.

Gate:

- draft limits rejected;
- current limit change leaves historical result unchanged;
- override retains original deterministic result.

## Slice G — Test Run / Measurement / Raw RF Artifacts

Suggested branch:

```text
impl/e07-rf-test-record
```

Scope:

- E07-S07;
- DUT test runs;
- scalar/structured measurements;
- Touchstone/spectrum/raw artifacts + hashes;
- retest chain;
- station-local upload API/CLI where useful.

Gate:

- raw artifact immutable/hash-checked;
- run exact DUT/config/limit identity;
- failed run retained after retest;
- ingestion idempotent;
- no GitHub Actions runtime path.

## Slice H — Equipment / Calibration / Setup Provenance

Suggested branch:

```text
impl/e07-equipment-calibration
```

Scope:

- E07-S08;
- instrument master;
- calibration records;
- run-equipment join;
- optional VNA calibration/de-embedding setup evidence.

Gate:

- calibration validity calculated at test time;
- later calibration does not rewrite old run;
- invalid-window impact query works.

## Slice I — Final Quality Release / Shipment Trace

Suggested branch:

```text
impl/e07-quality-release
```

Scope:

- E07-S09;
- required evidence gate;
- accepted/saleable quality transition;
- shipment serial/lot assignment;
- recall impact queries.

Gate:

- missing/fail evidence blocks normal release;
- override separately authorized;
- serial cannot double-ship;
- serial/customer/supplier-lot/equipment-impact trace deterministic.

## Storage/recovery gate

Before Slice G/H/I becomes production authority, extend E00 recovery tests so referenced retained test artifacts/certificates are included and checksum-verifiable.

A DB-only restore is not accepted when release-critical raw RF evidence is missing.

## Migration-number rule

Do not reserve numeric migrations in this design. Every implementation slice uses the next contiguous migration from merged main and passes the E00 migration/integrity/recovery gate.

## Stop conditions

Stop rollout if:

- uninspected stock can become usable by changing location/row text;
- a serial can be reused;
- legacy stock receives invented lot/serial history;
- genealogy claims finer granularity than captured;
- failed test is overwritten by passing retest;
- current limits/calibration rewrite historical evidence;
- raw artifact can be replaced without hash/revision evidence;
- final quality release can bypass mandatory evidence.

## Completion rule

E07 completes when a trace-controlled finished RF serial can be followed from source/component evidence through WO/configuration, test/quality/rework and final customer shipment, with honest evidence boundaries and reproducible raw test evidence.
