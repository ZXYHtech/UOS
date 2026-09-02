# TASK_UOS_STANDALONE_KERNEL_EXPORT_01 — progress record

Status: **IN PROGRESS — generic extraction expanded; final execution + visible-result evidence pending**  
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

### P0 synchronized now

#### ExecutionEpoch

Anchor:

```text
.uos/EXECUTION_CONTRACT.yaml
ExecutionEpoch: UOS_EXEC_20260902_01
```

Critical `project / task / claim / renew / complete / reconcile` operations require the current acknowledgement. `boot` and `status` remain discovery/read entrypoints.

This prevents stale chat/Agent execution semantics from creating new canonical control-plane mutations.

`tools/canonical_runner.py` extracts the global Epoch Ack before quality routing and reinserts it only when invoking the local state machine. Therefore adding a global safety parameter cannot make Preview/Claim/Complete logic mis-detect the business command.

#### Project WorkRoot authority

Task Publish and Complete now enforce each project's `WorkRoot` as its output boundary.

Current catalogs were checked and are compatible:

```text
UOS_CORE   → projects/UOS_CORE/...
QUICKBOARD → projects/QUICKBOARD/...
```

#### READY Work Market

Every Reconcile derives:

```text
coordination/runtime/WORK_MARKET.csv
```

The market exposes only READY tasks plus compact Project/Role/Priority/Capability/Context/Tool metadata. Market listing is discovery, never ownership.

#### Artifact Durability Receipt

A key generic AI_book lesson was that “visible/accepted” and “durably persisted” are separate facts.

Standalone UOS now writes:

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

and the standalone design does not need AI_book's larger project-specific persistence bridge.

## P1 candidates intentionally not enabled yet

Useful next standalone capabilities:

- bounded Work Session;
- capability/tool/context-aware Claim matching;
- Partial Handoff;
- Resource Admission / Backpressure when a real scarce resource or concurrency cap exists.

These should be implemented as small standalone mechanisms rather than copied wholesale from AI_book.

## P2 deferred

Not justified during current single-repository validation:

- Role Broker / role leases;
- OUTBOX_INGEST;
- complex Kernel self-orchestration / problem planner;
- external repository adapters / multi-repository routing.

## Regression surface

Current selftest discovery includes:

- `tests/test_single_repo_pilot.py`
- `tests/test_canonical_publish.py`
- `tests/test_git_cas_lifecycle.py`
- `tests/test_quality_visibility.py`
- `tests/test_quality_warmup_serial.py`
- `tests/test_ai_book_delta_sync.py`

The AI_book delta regression covers:

- stale ExecutionEpoch rejection;
- Epoch Ack does not contaminate business argv;
- Project WorkRoot isolation;
- all current catalog outputs obey WorkRoot;
- READY-only Work Market;
- durability path/SHA-256 binding.

The Git-CAS fixture now includes `control_extensions.py`, and completion regression expects a canonical durability receipt.

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

The next three real UOS task completion results must be shown directly to the operator and accepted one by one.

## Current decision

Keep `TASK_UOS_STANDALONE_KERNEL_EXPORT_01` open until exact-current selftest evidence and RuleEpoch-1 real visible-result evidence are both satisfactory.

Do **not** begin AI_book integration or multi-repository orchestration without a new explicit operator decision.
