# Post-E00 Runtime Execution Handoff

## Status

`READY_TO_EXECUTE_AFTER_E00_REAL_GATE`

This is the shortest operational handoff for moving from the current E00 draft implementation into actual post-E00 business/runtime development.

## Current E00 external state

Inventory PR:

```text
repo: ZXYHtech/inventory
PR: #3
branch: impl/e00-release-safety
head: 0e0870499f7e8b5e68a308231eae954f106bd5aa
state: open
Draft: true
mergeable: true (informational only)
merged: false
```

`mergeable=true` is not completion evidence.

## Mandatory E00 gate

From a real checkout of the exact PR head:

```bash
git fetch origin
git switch impl/e00-release-safety
git pull --ff-only origin impl/e00-release-safety
git rev-parse HEAD
python3 tools/verify_release.py
python3 tools/verify_release.py --require-bash
```

Required:

```text
exact tested head recorded
both required commands exit 0 / PASS
no unresolved review blocker
```

Then merge PR #3.

Before any production server cutover, independently run fresh pre-change protection:

```text
exact deployed-code snapshot
+ production DB consistent backup
+ isolated restore verification
+ manifest/checksums
+ off-host Recovery Bundle when configured
```

Do not reuse an old development/test backup as production rollout proof.

# Runtime execution chain after E00 merge

## E01-A — Shared Context / Action Policy

Packet:

`E01_SLICE_A_EXECUTION_PACKET.md`

Branch:

`impl/e01-platform-policy`

Migration:

`NONE`

No production write semantics change.

## E01-B — Business-operation idempotency

Packet:

`E01_SLICE_B_EXECUTION_PACKET.md`

Branch:

`impl/e01-idempotency`

Migration:

```text
2 = business_operations
```

No real stock route migrated yet.

## E01-C — real consequential pilots

Packet:

`E01_SLICE_C_EXECUTION_PACKET.md`

Branches / order:

```text
impl/e01-pilot-transfer-receive
 -> impl/e01-pilot-purchase-receive
 -> impl/e01-pilot-shipment-complete
```

Each pilot runs the full gate before the next.

## E01-D — Durable Jobs

Packet:

`E01_SLICE_D_EXECUTION_PACKET.md`

Branch:

`impl/e01-durable-jobs`

Migration:

```text
3 = jobs + job_attempts
```

Single worker first; lease generation/fencing required; OCR remains unchanged initially.

## E01-E — Transactional Outbox / Correlation

Packet:

`E01_SLICE_E_EXECUTION_PACKET.md`

Branch:

`impl/e01-outbox-correlation`

Migrations:

```text
4 = outbox_events
5 = operation_logs.correlation_id
```

External network calls occur only after local commit through worker delivery.

## E01-F — bounded modular extraction

Packet:

`E01_SLICE_F_EXECUTION_PACKET.md`

Small branches:

```text
impl/e01-domain-backup
impl/e01-domain-pricing
impl/e01-domain-procurement
impl/e01-domain-integrations
```

No Stock semantics in this refactor.

Pricing extraction must preserve behavior before E11.

# Mandatory early E11 bridge

Index:

`E11_EARLY_EXECUTION_PACKETS_INDEX.md`

## E11-A — pricing semantics

Packet:

`E11_SLICE_A_EXECUTION_PACKET.md`

Branch:

`impl/e11-pricing-semantics`

Migration:

`NONE`

Hard invariant:

```text
historical margin_percent arithmetic unchanged
```

New target gross-margin semantics must be explicit and cost-backed.

## E11-B — floor / override safety

Packet:

`E11_SLICE_B_EXECUTION_PACKET.md`

Branch:

`impl/e11-floor-safety`

Migration:

```text
6 = pricing.floor_override permission definition
```

Migration 6 grants the permission to **no role by default**.

Server re-resolves current floor at commit time. Client floor evidence is never authoritative.

# E02 first runtime slices

## E02-A — Stock Identity / UOM

Packet:

`E02_SLICE_A_EXECUTION_PACKET.md`

Branch:

`impl/e02-stock-identity`

Migration:

`NONE`

Outputs:

```text
canonical stock-position identity
Decimal/UOM contract
read-only legacy identity mapping report
explicit review/block flags
```

No production stock mutation changes.

## E02-B — Immutable Movement Ledger

Packet:

`E02_SLICE_B_EXECUTION_PACKET.md`

Branch:

`impl/e02-movement-ledger`

Migration:

```text
7 = stock_movement_operations + stock_movement_lines
```

Still no production stock-authority cutover.

Movement evidence must be immutable, replay-safe, explicit-direction and reversable through compensating operations.

## E02-C — Balance Projection

Implementation sequence:

`E02_IMPLEMENTATION_SEQUENCE.md`

Expected next migration:

```text
8 = stock_balances projection
```

This is the first slice that may honestly prove:

```text
concurrent spend cannot overspend current balance
negative physical balance is rejected by the new kernel
```

UI/business reads still remain legacy-authoritative until later shadow/parity gates.

# Canonical migration sequence through prepared E02-B

```text
1  baseline_current_schema_20260810       E00
2  business_operations                    E01-B
3  jobs + job_attempts                    E01-D
4  outbox_events                          E01-E
5  operation_logs.correlation_id          E01-E
6  pricing.floor_override permission      E11-B
7  stock movement operation/line ledger   E02-B
8  expected stock_balances projection     E02-C
9+ reservation / later approved E02 migrations
```

Never reuse/edit an already-recorded migration.

# Universal PR discipline

Every runtime slice:

```text
current merged main
 -> small dedicated branch
 -> focused deterministic tests
 -> existing regressions
 -> tools/verify_release.py
 -> Linux shell gate where applicable
 -> PR review
 -> merge
 -> next branch from new main
```

Do not stack the whole program onto one long-lived feature branch.

# Universal stop conditions

Stop and split/escalate if any PR begins to require:

- guessing unresolved legacy stock/account/location semantics;
- external network I/O inside SQLite business transaction;
- hidden permission expansion;
- silently changing historical pricing arithmetic;
- direct stock balance writes outside the E02 migration plan;
- destructive deletion of evidence/history;
- microservices/Redis/Kafka/Kubernetes merely to implement current scope;
- bypassing fresh production code+DB backup/recovery before server cutover.

# Immediate next action

The project is no longer blocked by lack of design/execution detail.

Immediate action is exactly:

```text
run E00 real-checkout Release Gate
 -> review result
 -> merge E00 only if PASS
 -> start E01-A
```

Everything after that already has a bounded implementation handoff.
