# TASK_UOS_STANDALONE_KERNEL_EXPORT_01 — progress record

Status: **IN PROGRESS — generic extraction expanded through P1B; final execution + real RuleEpoch evidence pending**  
Project: `UOS_CORE`  
Phase: `SINGLE_REPOSITORY_VALIDATION`

## Goal

Extract reusable UOS behavior from the historical AI_book host into standalone `ZXYHtech/UOS` without copying AI_book project/runtime state and without activating cross-repository scheduling.

## Standalone capability now present

### Core lifecycle

`tools/uos.py` provides:

- Boot / Status / Reconcile
- Project Init / Task Publish
- dependency-driven READY/BLOCKED
- Claim
- Lease / Renew
- LeaseGeneration / LeaseToken / Fencing
- stale reclaim
- Complete
- deterministic derived runtime state

QUICKBOARD completed SPEC → UI/LOGIC → DOCS → REVIEW through the standalone lifecycle.

### Latest-canonical Git transport

`tools/canonical_runner.py` runs each mutating lifecycle command from a fresh canonical snapshot in an isolated detached worktree and publishes via normal non-force Git update.

```text
fetch latest main
→ isolated worktree
→ rerun full UOS command
→ candidate tree
→ non-force push
→ ref race?
   yes → discard + rerun from latest main
```

A ref race therefore never re-parents a stale Reconcile decision.

### Visible-result / preview RuleEpoch 1

`.uos/QUALITY_VISIBILITY_POLICY.yaml` and `tools/quality_gate.py` enforce:

- first three real completion results are serial and operator-reviewed;
- at most one active new Claim during warmup;
- pending review blocks unrelated new Claims;
- later completion `5, 10, 15, ...` is deterministically sampled;
- HIGH-risk work may always require review;
- results/previews must be presented directly in conversation;
- source formats such as SVG/HTML/PDF/Office/CAD/EDA require inspectable preview companions;
- missing required preview blocks completion;
- rejected standalone task is reopened for correction and re-review.

## 2026-09-02 AI_book generic delta review

The richer historical AI_book UOS was re-screened for domain-neutral improvements not yet present in standalone UOS.

Inventory:

```text
docs/AI_BOOK_UPSTREAM_DELTA_20260902.md
```

Only capabilities valuable to the current single-repository phase were selected.

# P0 synchronized

## ExecutionEpoch

Anchor:

```text
.uos/EXECUTION_CONTRACT.yaml
ExecutionEpoch: UOS_EXEC_20260902_01
```

Critical `project / task / claim / renew / complete / reconcile` operations require the current acknowledgement. `boot` and `status` remain discovery/read entrypoints.

This prevents stale chat/Agent execution semantics from creating new canonical control-plane mutations.

`tools/canonical_runner.py` extracts the global Epoch Ack before quality routing and reinserts it only when invoking the local state machine. Therefore adding a global safety parameter cannot make Preview/Claim/Complete logic mis-detect the business command.

## Project WorkRoot authority

Task Publish and Complete enforce each project's `WorkRoot` as its output boundary.

Current catalogs are compatible:

```text
UOS_CORE   → projects/UOS_CORE/...
QUICKBOARD → projects/QUICKBOARD/...
```

## READY Work Market

Every Reconcile derives:

```text
coordination/runtime/WORK_MARKET.csv
```

The market exposes only READY tasks plus compact Project/Role/Priority/Capability/Context/Tool metadata. Market listing is discovery, never ownership.

## Artifact Durability Receipt

Standalone UOS writes:

```text
coordination/quality/durability/<TASK>.json
```

using schema `UOS_ARTIFACT_DURABILITY_V1`.

For each declared output it records path, object kind and SHA-256. Complete binds:

```text
output / preview
+ durability receipt
+ .done
- Claim lock
```

in the same canonical candidate tree.

Thus:

```text
Preview visible
≠ Operator accepted
≠ Artifact durably canonical
≠ Task .done
```

# P1A synchronized

Details:

```text
docs/WORK_SESSION_AND_AGENT_MATCHING.md
docs/AI_BOOK_P1_SYNC_20260902.md
```

## Capability / Tool / Context Matching

`tools/agent_matching.py` filters latest canonical READY work by:

```text
CapabilityTier
Tool availability
Context capacity
optional Role compatibility
```

The selected task is still claimed by `tools/uos.py claim`; matching never grants ownership.

`tools/task_requirements.py` maintains optional project-local matching hints in:

```text
orchestration/projects/<PROJECT>/TASK_AGENT_REQUIREMENTS.csv
```

These hints cannot alter WriteScope, output, dependency, Claim, Lease or Acceptance authority.

## Bounded Work Session

`tools/work_session.py` persists continuation intent:

```text
agent
project scope
deadline
max task count
capability envelope
current/claimed/completed task history
```

Continuation is allowed only after:

```text
canonical .done
+ DURABLE_READY receipt
+ Quality Gate release
+ deadline/max-task budget
+ compatible READY work
```

Deadline controls new Claims and does not abandon an existing Claim.

The operator reviewed the P1A design/result in conversation and explicitly replied `通过，继续`. This is useful anti-drift evidence, but it is **not counted as a canonical RuleEpoch completion event**, because these kernel-maintenance edits were written directly through the GitHub maintenance path rather than completed through a UOS-managed task Claim/Complete/Quality Event.

# P1B synchronized — Partial Handoff

Details:

```text
docs/PARTIAL_HANDOFF.md
docs/AI_BOOK_P1B_SYNC_20260902.md
```

Implementation:

```text
tools/partial_handoff.py
tools/handoff_takeover.py
```

Core invariants:

```text
Handoff != Done
Handoff != ownership transfer
successor must Claim
successor must revalidate Acceptance
```

## Claim-fenced handoff write

Every handoff mutation, even a non-releasing `PARTIAL` checkpoint, is conditioned on the exact current canonical Claim blob.

A stale Agent cannot publish late recovery context after ownership changes.

## Immutable checkpoint artifacts

Unfinished artifacts are copied from Project WorkRoot into unique kernel-managed checkpoint paths:

```text
coordination/handoff_artifacts/<TASK>/<HANDOFF_ID>/<SOURCE_PATH>
```

The handoff records both source and checkpoint paths.

This avoids occupying final output paths with unfinished drafts and preserves no-clobber completion for the successor.

## HANDOFF_READY release

At a safe release point the handoff transaction:

```text
writes handoff record
+ writes immutable checkpoint artifacts
+ expires current Lease
+ annotates Lock with HandoffState/HandoffPath
+ stops active bounded Work Session for current task
```

It does not delete the Lock and does not create `.done`.

After publication, the tool requests a normal Reconcile so Work Market reflects the reclaimable task. A Reconcile failure does not roll back the valid source-of-truth handoff.

## Successor takeover

The successor uses normal stale reclaim:

```text
uos.py claim
→ LeaseGeneration + 1
→ new LeaseToken
```

Only after current ownership is verified may it read the handoff.

`tools/handoff_takeover.py` is a convenience wrapper around:

```text
uos.py claim
→ verified partial_handoff read
```

It does not define a second ownership protocol. If Claim succeeds but handoff read fails, the helper returns `CLAIM_GRANTED_HANDOFF_READ_PENDING` and explicitly tells the Agent not to Claim again.

Every successful read marks the inherited context `UNVERIFIED_PARTIAL_WORK`; original Task Acceptance must be rerun before final completion.

# Remaining generic candidate

`Resource Admission / Backpressure` remains **NEED-DRIVEN**.

Do not add it merely for parity. Activate only when a real standalone project demonstrates scarce shared capacity or explicit concurrency limits such as GPU slots, image quota, simulator licenses, hardware benches or max active tasks.

# P2 deferred

Not justified during current single-repository validation:

- Role Broker / role leases;
- OUTBOX_INGEST;
- complex Kernel self-orchestration / problem planner;
- external repository adapters / multi-repository routing.

# Regression surface

Current selftest discovery includes the earlier lifecycle/CAS/quality suites plus:

```text
tests/test_agent_matching.py
tests/test_task_requirements.py
tests/test_work_session_guard.py
tests/test_work_session_git_cas.py
tests/test_partial_handoff.py
tests/test_partial_handoff_git_cas.py
```

P1 regression intent covers:

- incompatible higher-priority task skipped;
- missing tool/context mismatch;
- task matching sidecar;
- Work Session review/durability/deadline/max-task stops;
- Session recovery from canonical live Claim;
- PARTIAL checkpoint keeps ownership;
- HANDOFF_READY expires Lease without Done;
- cross-project handoff artifact rejected;
- wrong owner/token rejected;
- immutable checkpoint stored away from final output path;
- old bounded Session stopped;
- Work Market refresh requested;
- successor takeover through normal Claim Generation+1;
- old owner Renew/Complete fenced;
- successor final completion retains handoff/checkpoint audit evidence.

## AI_book use boundary

AI_book was used only as read-only design evidence. No private AI_book task content, runtime Claim/Grant/Done state, book assets, credentials or project history were copied into public UOS.

No AI_book dispatch or multi-repository orchestration was activated.

## Remaining acceptance evidence before DONE

### A. Exact committed fresh-clone selftest

```text
git clone https://github.com/ZXYHtech/UOS.git
cd UOS
python tools/selftest.py
```

The current chat execution runtime has previously been unable to resolve `github.com`, so exact fresh-clone execution is still not claimed as PASS.

### B. RuleEpoch 1 real visible-result warmup

Real UOS-managed task completion results must still be shown directly to the operator and accepted according to the RuleEpoch policy. Direct GitHub kernel-maintenance edits do not silently advance that canonical completion counter.

## Current decision

Keep `TASK_UOS_STANDALONE_KERNEL_EXPORT_01` open until exact-current selftest evidence and RuleEpoch-1 real visible-result evidence are satisfactory.

Do **not** auto-start Resource Admission merely because Partial Handoff is complete. Do **not** begin AI_book integration or multi-repository orchestration without a new explicit operator decision.
