# E01 Execution Packets Index

## Status

`ALL_E01_EXECUTION_PACKETS_READY_BLOCKED_BY_E00_GATE`

This is the handoff index for actual E01 implementation after E00 is verified and merged.

## Entry gate

Do not start runtime E01 work until:

```text
Inventory PR #3 exact head checked out
 -> python3 tools/verify_release.py = PASS
 -> python3 tools/verify_release.py --require-bash = PASS on Linux release host
 -> no unresolved PR blocker
 -> E00 merged to main
```

Every E01 branch starts from the then-current main, never from the pre-E00 baseline.

## Packet chain

### Slice A — Shared Context + Action Policy

File:

`E01_SLICE_A_EXECUTION_PACKET.md`

Branch:

`impl/e01-platform-policy`

Scope:

- RequestContext;
- shared errors/responses;
- static Action Policy registry;
- preserve current auth/permission/warehouse semantics;
- no DB migration;
- no production write-route migration.

Exit unlocks Slice B.

### Slice B — Business Operation Idempotency

File:

`E01_SLICE_B_EXECUTION_PACKET.md`

Branch:

`impl/e01-idempotency`

Migration:

`2 = business_operations`

Scope:

- canonical request fingerprint;
- operation key validation;
- atomic-local exactly-once business execution primitive;
- synthetic/isolated concurrency/replay tests first;
- no real stock route migrated yet.

Exit unlocks Slice C.

### Slice C — Consequential Pilot Actions

File:

`E01_SLICE_C_EXECUTION_PACKET.md`

Preferred branches:

```text
impl/e01-pilot-transfer-receive
impl/e01-pilot-purchase-receive
impl/e01-pilot-shipment-complete
```

Order:

```text
transfer.receive
 -> purchase.receive
 -> shipment.complete
```

Preserve existing permissions, warehouse scope, state machines, stock semantics and service-owned audit.

Each pilot gets its own full Release Gate.

Exit unlocks Slice D.

### Slice D — Durable Jobs / Worker / Retry

File:

`E01_SLICE_D_EXECUTION_PACKET.md`

Branch:

`impl/e01-durable-jobs`

Migration:

`3 = jobs + job_attempts`

Scope:

- short `BEGIN IMMEDIATE` claim;
- lease/owner/generation fencing;
- attempt history;
- bounded retry/dead-letter/manual-review taxonomy;
- repository/server-local worker CLI/service;
- first adopter non-stock-mutating;
- existing OCR queue remains unchanged initially.

Exit unlocks Slice E.

### Slice E — Transactional Outbox + Correlation

File:

`E01_SLICE_E_EXECUTION_PACKET.md`

Branch:

`impl/e01-outbox-correlation`

Migrations:

```text
4 = outbox_events
5 = operation_logs.correlation_id
```

Scope:

- local business commit atomically creates owed external effect + delivery job;
- network I/O happens later in worker;
- provider acknowledgement/reconciliation evidence;
- correlation trace across request/operation/audit/outbox/job;
- first delivery proof low-risk/test-oriented, not omnichannel redesign.

Exit unlocks Slice F.

### Slice F — Bounded Domain Extraction

File:

`E01_SLICE_F_EXECUTION_PACKET.md`

Branches:

```text
impl/e01-domain-backup
impl/e01-domain-pricing
impl/e01-domain-procurement
impl/e01-domain-integrations
```

Scope:

- behavior-preserving modular-monolith extraction;
- compatibility re-export only where needed;
- no duplicate implementation;
- no Inventory/Stock extraction;
- no pricing semantic fix hidden inside move.

After pricing extraction, execute the prepared early E11 bridge:

```text
E11_SLICE_A_EXECUTION_PACKET.md
 -> E11_SLICE_B_EXECUTION_PACKET.md
 -> E02
```

The bridge index is:

`E11_EARLY_EXECUTION_PACKETS_INDEX.md`

Then continue remaining bounded extraction as scheduled and complete E01.

## Migration chain after E01

```text
1 baseline_current_schema_20260810       E00
2 business_operations                    E01-B
3 jobs + job_attempts                    E01-D
4 outbox_events                          E01-E
5 operation_logs.correlation_id          E01-E
```

The mandatory early E11 bridge then reserves:

```text
6 pricing.floor_override permission      E11-B
```

Therefore E02 must begin at migration 7 unless an explicitly approved intervening migration changes the sequence.

All migrations are contiguous, immutable, checksummed and pass E00 pre/post integrity semantics.

## Merge discipline

Every packet/slice follows:

```text
branch from current main
 -> focused deterministic tests
 -> existing regression tests
 -> full tools/verify_release.py
 -> PR review clean
 -> merge
 -> next branch from new main
```

Do not accumulate A-F on one long-lived unmerged implementation branch.

## Global stop conditions

Stop and split work if a slice begins to require:

- E02 Stock/Reservation semantic redesign;
- E09 omnichannel business redesign;
- broad frontend rewrite;
- external network call inside local SQLite business transaction;
- new authorization model replacing current truth;
- generic workflow/rules engine;
- Redis/Kafka/microservices solely to implement E01;
- destructive deletion of operational/audit evidence.

## E01 completion

E01 is complete only when A-F are individually merged with full Release Gate evidence.

Then mandatory bridge:

```text
E11-S01
 -> E11-S02
 -> E02
```

Do not jump directly from E01 to E02.
