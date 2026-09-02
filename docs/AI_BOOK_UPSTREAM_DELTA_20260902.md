# AI_book → standalone UOS generic delta — 2026-09-02

## Scope

This document records reusable orchestration lessons observed in the historical `ZXYHtech/AI_book` UOS implementation and whether they should be carried into standalone `ZXYHtech/UOS`.

Only domain-neutral kernel behavior is eligible. AI_BOOK project content, task runtime, claims/grants/done history, publication assets, credentials and project-specific policies are not synchronization material.

The current operator phase remains **single-repository validation**. Nothing in this delta activates AI_book dispatch or multi-repository orchestration.

## Already rebuilt in standalone UOS

Standalone UOS already has a smaller independent implementation of several capabilities that existed in AI_book:

- provider-neutral `git + python3` execution;
- latest-canonical, non-force Git CAS;
- independent-clone Claim contention;
- LeaseGeneration / LeaseToken / Fencing;
- full-command recomputation after canonical ref races;
- deterministic Status/Reconcile;
- completion that commits declared outputs and `.done` in one canonical tree transaction;
- Repository Identity gate;
- staged visible-result / preview review gate.

These should not be replaced by the larger AI_book implementations merely for feature parity.

## P0 — synchronized now

### 1. ExecutionEpoch stale-Agent gate

Standalone anchor:

```text
.uos/EXECUTION_CONTRACT.yaml
```

Current Epoch:

```text
UOS_EXEC_20260902_01
```

`project`, `task`, `claim`, `renew`, `complete` and `reconcile` require acknowledgement of the current Epoch. `boot` and `status` remain safe discovery/read paths.

Purpose: old chat context or old Agent instructions must not create new canonical control-plane mutations after execution semantics change.

### 2. Project WorkRoot authority

Each project already declares a `WorkRoot`. Task publication and completion now enforce that every declared output remains inside that root.

Example:

```text
Project DEMO
WorkRoot: projects/DEMO

allowed: projects/DEMO/result.md
refused: projects/OTHER/result.md
```

This is a deliberately smaller standalone equivalent of the broader AI_book Project Namespace / Path Authority system.

### 3. WORK_MARKET_V1-lite

Every reconcile now derives:

```text
coordination/runtime/WORK_MARKET.csv
```

It contains READY tasks only and exposes compact selection metadata:

- task ID;
- project;
- priority;
- role;
- title;
- workstream;
- size;
- minimum capability tier;
- context class;
- tool requirements;
- output.

The market is discovery state, not ownership. A task shown there still requires a successful canonical Claim.

Role opportunities are intentionally not added yet.

### 4. Artifact Durability Receipt

AI_book exposed an important generic failure class: a result can be visible or even approved before its required artifact is durably bound to canonical repository state.

Standalone UOS already avoids much of that gap because `complete` publishes outputs and `.done` together. It now additionally writes:

```text
coordination/quality/durability/<TASK_ID>.json
```

Schema:

```text
UOS_ARTIFACT_DURABILITY_V1
```

The receipt records each declared artifact path, object kind and SHA-256 and states that the receipt/output/`.done` are bound by the same canonical tree transaction.

Therefore these dimensions remain explicitly separate:

```text
Preview visible
≠ Operator accepted
≠ Artifact durably canonical
≠ Task canonical .done
```

Continuation must never infer durability merely from a chat preview or path string.

## P1 — useful next, but not synchronized yet

### Bounded Work Session

Useful for requests such as “continue for 30 minutes” or “keep taking tasks”, but must obey the visible-result gate:

```text
canonical completion
→ durability ready
→ review/preview gate
→ only then continuation decision
```

The first-three RuleEpoch warmup must always override AUTO continuation.

### Capability / Tool / Context matching

Task Catalog already stores `min_capability_tier`, `tool_requirements`, `context_class` and `context_refs`. Standalone Claim selection does not yet mechanically filter on an Agent capability envelope.

A small matcher is preferable to copying the full AI_book Broker.

### Partial Handoff

A durable handoff is useful when ownership cannot safely complete but useful partial work exists. It must not equal `.done` and must not transfer ownership by itself.

### Resource Admission / Backpressure

AI_book proved claim-coupled frozen reservations and broker-only constrained claims. Standalone UOS should add this only when a real project needs scarce shared resources or project-level concurrency caps.

Do not add resource infrastructure merely for theoretical completeness.

## P2 — intentionally deferred

These AI_book capabilities are real but would currently add more complexity than value to the standalone single-repository pilot:

- Role Broker / role leases;
- OUTBOX_INGEST;
- full Kernel self-orchestration registry / problem planner;
- complex project graph interrupts/routing beyond current needs;
- provider-specific automation adapters beyond a thin optional layer.

They may be reconsidered only after the current single-repository gate is stable and when a concrete workload needs them.

## Extraction rule

When evaluating future AI_book changes:

```text
1. Is the behavior domain-neutral?
2. Is it already solved more simply in standalone UOS?
3. Does the current single-repository phase actually need it?
4. Can it be expressed with canonical Git state rather than a second database/daemon?
5. Can it be covered by deterministic regression tests?
```

Only sync when the answer supports a smaller, safer standalone kernel.

## Current result

The 2026-09-02 P0 sync adds four generic protections without activating cross-repository control:

```text
ExecutionEpoch
+ Project WorkRoot authority
+ READY Work Market
+ Artifact Durability Receipt
```

P1/P2 remain explicit backlog, not silently enabled behavior.
