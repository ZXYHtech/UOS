# Current Phase — Single-Repository Validation

## Operator decision

UOS remains in **single-repository validation mode**.

For this phase:

- UOS may create and manage projects whose definitions, task state and outputs live inside `ZXYHtech/UOS`.
- UOS must **not** dispatch, claim, mutate, synchronize or manage AI_book project work.
- AI_book may be read only as historical evidence for domain-neutral Kernel lessons.
- Cross-repository task routing is not active.
- Multi-repository orchestration requires a new explicit operator decision.

This boundary is unchanged by the Phase 1–6 Kernel synchronization work.

## Current lifecycle target

The standalone lifecycle now includes both the direct fast path and the high-contention completion fallback:

```text
Boot / current ExecutionEpoch
→ Create Project
→ Publish Tasks inside Project WorkRoot
→ Reconcile READY Work Market
→ Capability-aware discovery when used
→ canonical Broker V2 Claim
   Request → Grant → active Lock
→ Work
→ Renew / Lease / Fencing
→ Complete
   ├─ direct latest-main CAS → canonical Done
   └─ pure main-ref race exhaustion only
      → non-canonical Completion Outbox
      → mechanical batch Integration
      → latest-main authority/fencing/read-set revalidation
      → canonical Done
→ durability + preview / quality visibility gate
→ operator review when required
→ bounded Work Session continuation
→ next compatible Claim / exact-current recovery / handoff / safe stop
```

## Ordinary workload milestone

`QUICKBOARD` is completed and remains the first ordinary same-repository lifecycle milestone through SPEC → UI/LOGIC → DOCS → REVIEW.

# ExecutionEpoch — ACTIVE

Anchor:

```text
.uos/EXECUTION_CONTRACT.yaml
```

Current Epoch:

```text
UOS_EXEC_20260902_01
```

Critical lifecycle mutations require the current acknowledgement. Old Agent instructions must not silently mutate ownership or completion state after execution semantics change.

# Quality Visibility RuleEpoch 1 — ACTIVE

Policy anchors:

```text
.uos/QUALITY_VISIBILITY_POLICY.yaml
docs/QUALITY_VISIBILITY_GATE.md
```

Current behavior still requires visible operator review during warmup, deterministic later sampling, and mandatory review for high-risk work. A pending/rejected review prevents unrelated next Claims according to policy.

Inspectability remains part of task acceptance:

```text
SVG          → SVG + PNG
HTML         → HTML + preview PNG
PDF          → PDF + preview PNG
PPT/DOC/XLS  → source + preview PDF
CAD/EDA      → source + preview PNG
```

# AI_book generic delta status

The 2026-09-03 Claim/Concurrency synchronization inventory is now closed through Phase 6:

```text
docs/AI_BOOK_CLAIM_DELTA_SYNC_20260903.md
```

Implemented generic Kernel phases:

```text
Phase 1  high-contention exact-task ingress
Phase 2  immutable Claim Request + Grant + Broker V2 CREATE/RECLAIM
Phase 3  exact-predecessor reclaim provenance + Claim Integrity
Phase 4  contention / fencing lifecycle acceptance
Phase 5  Work Session V2 + Claim CAS telemetry / observability
Phase 6  Completion Outbox + mechanical batch Integration
Closeout WAITING_INTEGRATION + Outbox queue/batch/wait metrics
```

This does not enable AI_book dispatch and does not claim full AI_book Kernel parity.

# Canonical ownership model

Current ownership is not a filename convention or Agent announcement. It is:

```text
immutable Claim Request
+ immutable Claim Grant
+ matching current active Lock
+ current LeaseGeneration / LeaseToken / Fencing
```

Primary authority:

```text
UOS_CLAIM_BROKER_V2
```

RECLAIM increments `LeaseGeneration` and binds exact predecessor provenance. Old tokens and old-generation candidates are fenced.

Claim Request/Grant are immutable ownership anchors; they are not a second scheduler.

# Artifact durability invariant

Canonical direct completion creates the business outputs/previews, durability receipt and `.done`, and removes the active Lock in one candidate canonical tree.

```text
business outputs / previews
+ coordination/quality/durability/<TASK>.json
+ coordination/completed/<TASK>.done
- coordination/claims/<TASK>.lock
```

The receipt binds artifact paths and SHA-256 digests.

Therefore:

```text
Preview visible
≠ Operator accepted
≠ Artifact durably canonical
≠ Task canonical completion
```

A Partial Handoff and a staged Outbox candidate are also not canonical completion.

# Project WorkRoot authority

Tasks remain constrained to their owning project WorkRoot. Task Publish, Complete and recovery paths refuse unauthorized cross-project outputs.

The matching layer may refine task suitability but never changes path authority or ownership.

# Work Market + Agent Matching

Every reconcile derives:

```text
coordination/runtime/WORK_MARKET.csv
```

READY work may be filtered by capability tier, tools, context capacity and optional role constraints through `tools/agent_matching.py`.

Matching is discovery only. Final ownership always goes through canonical Claim/Broker semantics.

# Work Session V2

Tool:

```text
tools/work_session.py
```

Canonical session state:

```text
coordination/work_sessions/<AGENT>/<SESSION>.json
```

A Work Session is a bounded continuation guard, not a scheduler. It records deadline, task limit, project scope, Agent capability envelope, transition events and metrics.

No unrelated next Claim is allowed until the current task has canonical Done, durable artifacts and a released quality/review gate.

Important outcomes now include:

```text
WORK_CURRENT_TASK         current owned work is still incomplete
CURRENT_TASK_RECLAIMED    stale current Lease recovered on the exact same task
OWNERSHIP_LOST            canonical ownership moved elsewhere / recovery failed
RECOVERY_REQUIRED         ambiguous state; fail closed instead of guessing
WAITING_INTEGRATION       exact current Grant already has a staged Completion Outbox ref
STOP_REVIEW_PENDING       visibility/review gate blocks continuation
REWORK_REQUIRED           same rejected task must be corrected
STOP_DURABILITY_PENDING   canonical durability not complete
SESSION_STOPPED           deadline / max tasks / operator stop reached
```

## WAITING_INTEGRATION invariant

If the current completion was already staged after direct-main race exhaustion, Session `next` checks the exact current canonical `GrantID` and exact expected Outbox ref.

When found, it returns `WAITING_INTEGRATION` and instructs the Agent not to modify or re-complete the task. Mechanical ingest must run first.

The exact GrantID check is important because retained prior-generation Outbox refs are audit/recovery evidence. A Generation+1 owner must not be blocked by a Generation-1 candidate.

# Completion Outbox / Integration Lane — ACTIVE

Tool:

```text
tools/completion_outbox.py
python tools/uos.py outbox status
python tools/uos.py outbox ingest
```

The Outbox is targeted write-plane backpressure for validated Completion candidates. It is not a general ownership queue.

Fast path remains direct canonical Complete. Only pure canonical main-ref race exhaustion after successful local completion validation may stage a fallback candidate.

Core invariants:

```text
Outbox != ownership
Outbox != Done
Claim/Renew never use Outbox
non-race Complete errors never become staged success
old-generation candidate cannot integrate after RECLAIM
same-path/read-set conflicts fail closed
latest-main authority is revalidated during ingest
runtime views are reconciled from the final latest-main batch tree
```

The accepted 2 / 5 / 10 / 30 candidate matrix proved independent completions can be mechanically integrated in one canonical batch commit while preserving fencing.

# Claim + Session + Outbox observability

Tool:

```text
tools/claim_observability.py
```

Workflow:

```text
.github/workflows/uos-claim-observability.yml
```

The snapshot covers:

- Request/Grant totals and Broker authority;
- CREATE / RECLAIM counts and max LeaseGeneration;
- active Locks;
- Claim CAS attempt / latency / contention telemetry;
- Work Session metrics;
- Completion Outbox queue depth;
- canonical integration receipt count;
- retained ingested vs invalid/fenced Outbox refs;
- batch size p50/p95/max;
- integration wait p50/p95/max.

Outbox refs are intentionally retained as work-plane evidence, so `remote_refs_total` is not queue depth. `valid_queue_depth` is the current mechanically ingestible queue; canonical receipts are the authoritative integrated count.

The 2026-09-03 closeout production snapshot reported all recorded Grants under `UOS_CLAIM_BROKER_V2`, no active Locks, Outbox queue depth 0 and no invalid/fenced Outbox refs.

The observability workflow runs on relevant canonical main changes and on an hourly schedule so a queue consisting only of non-main Outbox refs can still be observed.

# Partial Handoff

Tools:

```text
tools/partial_handoff.py
tools/handoff_takeover.py
```

Invariants remain:

```text
Handoff != Done
Handoff != ownership transfer
Handoff != Acceptance PASS
```

`HANDOFF_READY` can persist recovery evidence and make the current Lease reclaimable without silently granting ownership to the successor. The successor still uses normal Broker reclaim and receives a new Generation/LeaseToken.

# Current standalone Kernel components

## Ownership / lifecycle

```text
tools/uos.py
tools/claim_broker_v2.py
tools/canonical_runner.py
tools/canonical_publish.py
tools/claim_integrity_scan.py
```

Responsibilities include latest-main replay/recompute CAS, Request/Grant/Lock ownership, Lease/Fencing, exact stale reclaim, Complete and deterministic reconcile.

## Discovery / continuation

```text
tools/agent_matching.py
tools/task_requirements.py
tools/work_session.py
```

Responsibilities include READY-market capability matching and bounded safe continuation/recovery.

## Completion write-contention lane

```text
tools/completion_outbox.py
```

Responsibilities include non-canonical completion persistence, latest-main batch validation/integration and Outbox status metrics.

## Quality / durability / recovery

```text
tools/quality_gate.py
tools/control_extensions.py
tools/partial_handoff.py
tools/handoff_takeover.py
```

## Observability

```text
tools/claim_telemetry.py
tools/claim_observability.py
```

# Regression evidence

Coverage now includes:

- local and independent-clone lifecycle;
- latest-main CAS replay/recompute;
- ExecutionEpoch stale-Agent rejection;
- Project WorkRoot authority;
- Request/Grant/Lock integrity;
- CREATE and stale RECLAIM;
- old-token fencing;
- high-contention 5 / 10 / 30 Agent Claim acceptance with telemetry anchors;
- Work Session V2 exact-current recovery and immediate safe continuation;
- Partial Handoff and successor takeover;
- Completion Outbox fallback after pure ref race;
- no Outbox on ownership/protocol errors;
- prior-generation Outbox fencing after reclaim;
- Completion batch Integration at 2 / 5 / 10 / 30 candidates;
- `WAITING_INTEGRATION` and old-generation non-misclassification;
- Claim / Session / Outbox observability.

The permanent `.github/workflows/uos-selftest.yml` ran from a fresh GitHub Actions checkout of the cleaned final Kernel/runtime tree at commit `c009f7d2d92b02f1e3f6bdcd05cec0a09fe405fa` (Actions run `33724704449`). The checkout resolved `origin/main` to that exact SHA, then `python tools/selftest.py` completed **68 / 68 tests PASS**. This closes the former exact-current fresh-checkout execution-evidence blocker.

The Phase-6 targeted closeout gates and production observability workflow also executed successfully. Documentation-only commits after `c009f7d2...` do not change the tested Kernel/runtime code.

One-command local regression entrypoint remains:

```bash
python tools/selftest.py
```

# Exit / status gate

| Gate | Current result | Notes |
|---|---|---|
| Single-repository control plane | PASS / EXACT-CURRENT SELFTESTED | Final cleaned Kernel/runtime tree `c009f7d2...`; permanent selftest run `33724704449`; 68 / 68 PASS. |
| ExecutionEpoch stale-Agent safety | PASS / TESTED | Current Epoch gate remains active. |
| Project creation / Task publication | INTEGRATED | WorkRoot constrained. |
| READY discovery / capability matching | PASS / TESTED | Discovery delegates ownership to Broker. |
| Broker V2 Request/Grant/Lock | PASS / TESTED | Immutable anchors + active pointer. |
| Lease / Fencing / exact RECLAIM | PASS / TESTED | Old token/generation fails closed. |
| Work Session V2 | PASS / TESTED | Recovery, continuation, rejected-result rework priority and `WAITING_INTEGRATION`. |
| Partial Handoff | PASS / TESTED | Recovery fact without implicit completion/ownership transfer. |
| Artifact durability | PASS / TESTED | Digest receipt + canonical Done semantics. |
| Quality visibility | ACTIVE / TESTED | Real work still follows operator-review policy when triggered. |
| High-contention Claim | PASS | 5 / 10 / 30 independent-Agent acceptance. |
| Completion Outbox fallback | PASS | Pure ref-race fallback only. |
| Mechanical batch Integration | PASS | 2 / 5 / 10 / 30 candidate acceptance. |
| Outbox-aware observability | PASS | Production snapshot workflow successful. |
| Generic scarce-resource admission | NEED-DRIVEN / NOT REQUIRED FOR PHASE 6 | Add only after a real scarce-resource requirement. |
| Multi-repository routing | NOT ACTIVE | Requires explicit operator decision. |

# Remaining boundaries, not Phase-6 blockers

The Phase-6 Claim/Concurrency closeout is complete. The former exact-current fresh-checkout test-evidence blocker is also closed. The following are deliberately outside this closure:

1. **AI_book dispatch** — standalone UOS still does not manage AI_book tasks or runtime state.
2. **Multi-repository orchestration** — requires a new explicit operator decision.
3. **Generic Resource Admission / Backpressure** — remains need-driven; Completion Outbox solves a demonstrated Git write-plane contention problem but is not a universal resource broker.
4. **Outbox ref archival / GC policy** — retained refs are currently audit/recovery evidence; long-term cleanup may be added when repository measurements justify it.
5. **Adaptive GitHub write/API budget governance** — optional future optimization based on observed scale and throttling, not required for current correctness.

No further AI_book Claim/Concurrency mechanism from the six-item 2026-09-03 delta list remains declared unsynchronized.
