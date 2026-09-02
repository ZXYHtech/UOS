# AI_book → standalone UOS generic delta — 2026-09-02

## Scope

This document tracks domain-neutral orchestration lessons found in the historical `ZXYHtech/AI_book` UOS and whether they belong in standalone `ZXYHtech/UOS`.

Never synchronize AI_BOOK project content, task runtime, claims/grants/done history, publication assets, credentials or project-specific policy.

Current operator phase remains **single-repository validation**. Nothing here activates AI_book dispatch or multi-repository orchestration.

## Already rebuilt independently

Standalone UOS already has smaller implementations of several historical AI_book capabilities:

- provider-neutral `git + python3` execution;
- latest-canonical non-force Git CAS;
- independent-clone Claim contention;
- LeaseGeneration / LeaseToken / Fencing;
- full-command recomputation after canonical ref races;
- deterministic Status/Reconcile;
- output + `.done` canonical completion;
- Repository Identity gate;
- staged visible-result / preview review gate.

These should not be replaced by larger AI_book compatibility layers merely for feature parity.

# P0 — synchronized

## 1. ExecutionEpoch stale-Agent gate

Anchor:

```text
.uos/EXECUTION_CONTRACT.yaml
```

Current Epoch:

```text
UOS_EXEC_20260902_01
```

Critical control-plane mutations require current Epoch acknowledgement. `boot` and `status` remain discovery/read paths.

Purpose: old chat context or old Agent execution rules must not create new canonical mutations after semantics change.

## 2. Project WorkRoot authority

Every project declares a `WorkRoot`. Task publication and completion enforce that declared outputs stay inside it.

```text
Project DEMO
WorkRoot: projects/DEMO

allowed: projects/DEMO/result.md
refused: projects/OTHER/result.md
```

This is the standalone single-repository equivalent of the broader AI_book Project Namespace / Path Authority system.

## 3. WORK_MARKET_V1-lite

Every reconcile derives:

```text
coordination/runtime/WORK_MARKET.csv
```

It contains READY tasks only and compact selection metadata.

```text
Market listing ≠ ownership
```

A task shown in the market still needs canonical Claim.

## 4. Artifact Durability Receipt

AI_book exposed a generic failure mode where a user-visible/approved artifact could be followed by new work before the artifact was durably bound to canonical storage.

Standalone UOS now writes:

```text
coordination/quality/durability/<TASK_ID>.json
```

Schema:

```text
UOS_ARTIFACT_DURABILITY_V1
```

The receipt binds declared artifact paths and SHA-256 values to the same canonical tree transaction as task `.done`.

Therefore:

```text
Preview visible
≠ Operator accepted
≠ Artifact durably canonical
≠ Task canonical .done
```

# P1A — synchronized

Detailed design:

```text
docs/WORK_SESSION_AND_AGENT_MATCHING.md
docs/AI_BOOK_P1_SYNC_20260902.md
```

## 5. Capability / Tool / Context Matching

Implementation:

```text
tools/agent_matching.py
```

It consumes latest canonical READY work and filters by an explicit Agent envelope:

```text
CapabilityTier
Tools
ContextCapacity
optional Roles
```

Matching is discovery only. The final transition is always delegated to:

```text
tools/uos.py claim
```

so Lease/Fencing, ExecutionEpoch, Git-CAS and Review Gate remain authoritative.

A lower-priority compatible task may be selected ahead of a higher-priority incompatible task.

### Optional task matching sidecar

Implementation:

```text
tools/task_requirements.py
```

Canonical project path:

```text
orchestration/projects/<PROJECT>/TASK_AGENT_REQUIREMENTS.csv
```

It may override only matching hints:

- `min_capability_tier`;
- `context_class`;
- `tool_requirements`;
- `allowed_roles`.

It cannot grant ownership or change Task outputs, dependencies, WriteScope or completion acceptance.

## 6. Bounded Work Session

Implementation:

```text
tools/work_session.py
```

Canonical session state:

```text
coordination/work_sessions/<AGENT>/<SESSION>.json
```

A Session stores continuation intent such as deadline, max task count, project scope and Agent capability envelope.

It is **not a scheduler** and is **not ownership**.

Continuation requires:

```text
previous task canonical .done
+ UOS_ARTIFACT_DURABILITY_V1 = DURABLE_READY
+ Quality Event released
+ deadline/max-task budget still open
+ compatible READY work
→ canonical uos.py Claim
```

Hard stop states include:

```text
STOP_REVIEW_PENDING
REWORK_REQUIRED
STOP_DURABILITY_PENDING
STOP_QUALITY_EVENT_MISSING
STOP_NO_MATCH
SESSION_STOPPED
RECOVERY_REQUIRED
```

Deadline is a new-Claim boundary. If it expires while a Task is already owned, the Session returns `WORK_CURRENT_TASK` with `stop_after_current=true`; it does not abandon the existing Claim.

If a Claim succeeds but Session bookkeeping fails, the next Session check adopts the single live canonical Claim for that Agent. Multiple live Claims fail closed instead of guessing.

# P1B — synchronized

Detailed design:

```text
docs/PARTIAL_HANDOFF.md
docs/AI_BOOK_P1B_SYNC_20260902.md
```

## 7. Partial Handoff

Implementation:

```text
tools/partial_handoff.py
tools/handoff_takeover.py
```

Preserved invariants:

```text
Handoff ≠ .done
Handoff ≠ ownership transfer
successor must acquire canonical Claim
successor must revalidate Acceptance
```

Every handoff write is conditioned on the exact current Claim blob, including a non-releasing `PARTIAL` checkpoint.

`HANDOFF_READY` does not delete the Lock. It atomically:

```text
writes handoff recovery context
+ writes immutable checkpoint artifacts
+ expires the current Lease
+ annotates current Lock with HandoffState/HandoffPath
+ stops an active bounded Work Session for that task
```

The successor then uses the ordinary stale-reclaim path:

```text
uos.py claim
→ LeaseGeneration + 1
→ new LeaseToken
```

### Immutable artifact checkpoints

Unfinished source files are not published over final task output paths. They are copied to:

```text
coordination/handoff_artifacts/<TASK>/<HANDOFF_ID>/<SOURCE_PATH>
```

The handoff stores both `source_path` and `checkpoint_path`.

This prevents partial work from colliding with the successor's later no-clobber final completion.

### Derived-state refresh

After `HANDOFF_READY`, the source-of-truth task is immediately reclaimable. The tool requests a normal Reconcile so `WORK_MARKET.csv` catches up.

If that derived-state refresh fails, source-of-truth handoff remains valid and explicit `uos.py claim --task` can still reclaim from the expired canonical Lock.

### Safe takeover helper

`handoff_takeover.py` performs:

```text
normal uos.py claim
→ verified handoff read
```

It never creates ownership itself. If Claim succeeds but the handoff read fails, it returns `CLAIM_GRANTED_HANDOFF_READ_PENDING` and tells the Agent not to Claim again.

# Remaining P1 — need-driven only

## 8. Resource Admission / Backpressure

AI_book demonstrated claim-coupled frozen resource reservations and broker-only constrained claims.

Standalone should add this only when a real project needs scarce shared capacity or explicit project-level concurrency caps, for example:

```text
GPU slots
image-generation quota
simulation licenses
hardware benches
max active project tasks
```

Do not add resource infrastructure merely for theoretical completeness.

# P2 — intentionally deferred

These capabilities are real but currently add more complexity than value to the standalone single-repository pilot:

- Role Broker / role leases;
- OUTBOX_INGEST;
- full Kernel self-orchestration registry/problem planner;
- complex project graph interrupts/routing beyond current needs;
- provider-specific automation adapters beyond a thin optional layer;
- multi-repository adapters/routing.

They may be reconsidered only after the current single-repository gate is stable and a concrete workload needs them.

# Regression coverage added by this sync

```text
tests/test_agent_matching.py
tests/test_task_requirements.py
tests/test_work_session_guard.py
tests/test_work_session_git_cas.py
tests/test_partial_handoff.py
tests/test_partial_handoff_git_cas.py
```

The handoff integration scenario covers:

```text
owner Work Session + generation-1 Claim
→ partial checkpoint
→ HANDOFF_READY
→ immutable canonical checkpoint
→ old Session STOPPED
→ Work Market refresh
→ old owner Renew fenced
→ successor takeover through ordinary Claim generation 2
→ verified handoff read
→ old owner Complete fenced
→ successor final completion
```

# Extraction rule

When evaluating future AI_book changes:

```text
1. Is the behavior domain-neutral?
2. Is it already solved more simply in standalone UOS?
3. Does the current single-repository phase actually need it?
4. Can it use canonical Git state instead of a second database/daemon?
5. Can it be covered by deterministic regressions?
```

Only sync when the result is a smaller, safer standalone kernel.

# Current result

```text
P0
  ExecutionEpoch                         ✅
  Project WorkRoot authority             ✅
  READY Work Market                      ✅
  Artifact Durability Receipt            ✅

P1
  Capability / Tool / Context Matching   ✅ CODE / TEST PRESENT
  Bounded Work Session                   ✅ CODE / TEST PRESENT
  Partial Handoff                        ✅ CODE / TEST PRESENT
  Resource Admission / Backpressure      ⏳ NEED-DRIVEN

P2
  Role Broker / OUTBOX / complex planner / multi-repo   ⏸ DEFERRED
```
