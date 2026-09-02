# Current Phase — Single-Repository Validation

## Operator decision

UOS remains in **single-repository validation mode**.

For this phase:

- UOS may create and manage projects whose project definitions, task state and work outputs live inside `ZXYHtech/UOS`.
- UOS must **not** dispatch, claim, mutate, synchronize or manage AI_book project work.
- AI_book may be read only as historical evidence for domain-neutral kernel lessons.
- Cross-repository task routing is not active.
- Multi-repository orchestration requires a new explicit operator decision.

## Phase goal

Prove this lifecycle entirely inside one repository, including independent clones of that same repository:

```text
Boot / current ExecutionEpoch
→ Create Project
→ Publish Tasks inside Project WorkRoot
→ Discover READY work through Work Market
→ Agent Claim
→ Work
→ Renew / Fencing
→ Complete outputs + preview + durability receipt + .done
→ Visible Result / Preview Gate
→ Operator Review when required
→ Reconcile
→ Continue until project completion
```

## Ordinary workload milestone

`QUICKBOARD` is **COMPLETED**.

It proved the first ordinary same-repository lifecycle through SPEC → UI/LOGIC → DOCS → REVIEW.

## ExecutionEpoch — ACTIVE

Anchor:

```text
.uos/EXECUTION_CONTRACT.yaml
```

Current value:

```text
UOS_EXEC_20260902_01
```

Critical control-plane commands require the current acknowledgement:

```text
project
task
claim
renew
complete
reconcile
```

`boot` and `status` remain discovery/read entrypoints.

Purpose: old Agent instructions or old chat context cannot silently create new canonical mutations after execution semantics change.

## Quality Visibility RuleEpoch 1 — ACTIVE

Policy:

```text
.uos/QUALITY_VISIBILITY_POLICY.yaml
docs/QUALITY_VISIBILITY_GATE.md
```

Current behavior:

```text
completion #1 → mandatory visible operator review
completion #2 → mandatory visible operator review
completion #3 → mandatory visible operator review
completion #4 → normal
completion #5 → deterministic sample review
completion #10 → deterministic sample review
...
HIGH risk       → mandatory review
```

During the first three reviews only one new task Claim may be active at a time. A pending review pauses unrelated new Claims.

The Agent must present result summaries and previews directly in conversation; routine review must not require the user to browse GitHub.

If the operator rejects a result, the standalone pilot revokes that task's current `.done`, retains feedback and allows only that task to be corrected/re-reviewed before unrelated work resumes.

## Preview contract

Inspectability is part of original task acceptance:

```text
SVG          → SVG + PNG
HTML         → HTML + preview PNG
PDF          → PDF + preview PNG
PPT/DOC/XLS  → source + preview PDF
CAD/EDA      → source + preview PNG
```

Known preview companions are added at Task Publish. Completion refuses missing required previews.

## AI_book generic delta synchronized on 2026-09-02

The standalone repo was compared against the historically richer AI_book UOS. Only capabilities useful to the current single-repository phase were synchronized.

Detailed inventory:

```text
docs/AI_BOOK_UPSTREAM_DELTA_20260902.md
```

### P0 now integrated

```text
ExecutionEpoch stale-Agent gate
Project WorkRoot output authority
READY-only WORK_MARKET.csv
UOS_ARTIFACT_DURABILITY_V1 receipt
```

This is a smaller standalone implementation, not a copy of AI_book's historical compatibility layers.

### Artifact durability invariant

A visible/accepted result must not be confused with durable repository persistence.

Standalone Complete now creates:

```text
business outputs / previews
+ coordination/quality/durability/<TASK>.json
+ coordination/completed/<TASK>.done
- coordination/claims/<TASK>.lock
```

in one candidate canonical tree.

The durability receipt binds each declared artifact path to a SHA-256 and records `SAME_CANONICAL_TREE_TRANSACTION`.

Therefore:

```text
Preview visible
≠ Operator accepted
≠ Artifact durably canonical
≠ Task canonical completion
```

### Project WorkRoot authority

Current projects are compatible with the new rule:

```text
UOS_CORE   → projects/UOS_CORE/...
QUICKBOARD → projects/QUICKBOARD/...
```

Task Publish and Complete refuse cross-project output paths.

### Work Market

Every reconcile now derives:

```text
coordination/runtime/WORK_MARKET.csv
```

It contains READY tasks and compact capability/context/tool metadata for discovery. Market presence is never ownership.

## Current standalone kernel

### `tools/uos.py`

Commands:

- `boot`
- `status`
- `reconcile`
- `project init`
- `task publish`
- `claim`
- `renew`
- `complete`

Semantics include:

- ExecutionEpoch acknowledgement;
- dependency-driven READY/BLOCKED;
- Work Market derivation;
- Project WorkRoot authority;
- Claim ownership;
- LeaseGeneration / LeaseToken / Fencing;
- stale reclaim;
- completion output existence checks;
- durability receipt;
- deterministic runtime views.

### Transport selection

```text
auto | local | git-cas
```

`auto` behavior:

- no configured Git remote → local;
- configured canonical remote → latest-canonical Git-CAS;
- configured remote becomes unreachable → fail closed, never local fallback ownership.

### `tools/canonical_runner.py`

Git-CAS lifecycle:

1. fetch latest canonical branch;
2. create isolated detached worktree;
3. retain ExecutionEpoch acknowledgement separately from business argv;
4. apply preview/review policy to clean `task / claim / complete` command shape;
5. copy caller completion outputs/previews;
6. invoke local state machine with the same Epoch acknowledgement;
7. create one candidate tree;
8. normal non-force push;
9. on ref race discard candidate and rerun the whole command from latest canonical state.

The Epoch global parameter therefore cannot accidentally bypass Preview/Review routing.

### `tools/quality_gate.py`

Provides:

- preview expansion and validation;
- RuleEpoch sequence;
- first-three mandatory review;
- deterministic periodic sampling;
- HIGH-risk review;
- pending-review Claim pause;
- Accept / Reject correction loop;
- conversation presentation packet.

### `tools/control_extensions.py`

Small domain-neutral controls synchronized from AI_book lessons:

- ExecutionEpoch;
- Project WorkRoot output guard;
- Work Market builder;
- Artifact durability receipt.

### `tools/canonical_publish.py`

Lower-level latest-canonical CAS primitive:

- create-if-absent;
- expected-blob replace;
- expected-blob-protected delete;
- multi-path atomic tree publish;
- no-clobber;
- non-force ref-race retry;
- Repository Identity target verification.

Normal Agents should use `tools/uos.py`.

## Regression coverage

`tests/test_single_repo_pilot.py` covers local lifecycle, dependency release, publication without ownership, local contention, path escape and stale fencing.

`tests/test_canonical_publish.py` covers the previously executed 7/7 low-level bare-Git / independent-clone CAS cases.

`tests/test_git_cas_lifecycle.py` covers actual `uos.py` Git-CAS lifecycle, concurrent Task Publish replay, Reconcile ref-race recomputation, status no-op, durability receipt presence and Work Market recomputation.

`tests/test_quality_visibility.py` / `tests/test_quality_warmup_serial.py` cover Preview Gate, first-three review, deterministic sampling, Reject/rework and serialized warmup Claims.

`tests/test_ai_book_delta_sync.py` covers:

- stale ExecutionEpoch rejection;
- Epoch Ack removal before business/quality routing;
- Project WorkRoot cross-project rejection;
- all current project catalogs obey WorkRoot;
- READY-only Work Market;
- durability receipt path/SHA-256 binding.

One-command entrypoint:

```bash
python tools/selftest.py
```

## AI_book capabilities intentionally not yet synchronized

Useful P1 candidates:

- bounded Work Session;
- capability/tool/context matching;
- Partial Handoff;
- Resource Admission / Backpressure.

Deferred P2 capabilities:

- Role Broker / role leases;
- OUTBOX_INGEST;
- complex Kernel self-orchestration/problem planner;
- multi-repository adapters/routing.

These are not missing by accident; they are held back to keep the standalone kernel small until a real single-repository workload needs them.

## Exit gate

| Gate | Current result | Notes |
|---|---|---|
| Standalone control plane runnable | PARTIAL PASS | CLI/selftest exist; exact current committed fresh-clone execution still needs normal network runtime evidence. |
| ExecutionEpoch stale-Agent safety | CODE / TEST PRESENT | Current Epoch `UOS_EXEC_20260902_01`; critical commands require Ack. |
| Project creation | CODE INTEGRATED | Canonical/local paths implemented. |
| Task publication without ownership | CODE INTEGRATED | Output scope now also constrained to Project WorkRoot. |
| Work discovery | CODE / TEST PRESENT | Reconcile derives READY-only `WORK_MARKET.csv`. |
| Ordinary project lifecycle | PASS | QUICKBOARD completed SPEC → UI/LOGIC → DOCS → REVIEW. |
| Claim / Lease / Fencing / Recovery | LOW-LEVEL CAS PASS + LIFECYCLE INTEGRATED | exact-current full suite still needs execution evidence. |
| Artifact durability | CODE / TEST PRESENT | Complete binds output digest receipt + `.done` in same canonical candidate tree. |
| Reconcile latest-canonical semantics | CODE INTEGRATED | full-command rerun after ref race. |
| Visible-result / preview anti-drift | RULEEPOCH 1 ACTIVE / TEST PRESENT | next three real reviewed completions must be directly shown and accepted. |

## Current blocker to phase closure

Two acceptance items remain:

1. run `python tools/selftest.py` against the **exact current committed version** from a normal fresh clone/runtime;
2. exercise Quality RuleEpoch 1 through its first three real reviewed task completions in ordinary Agent work.

Current chat execution environment has previously failed direct GitHub DNS access, so exact fresh-clone execution is not falsely marked PASS.

Even after these close, AI_book dispatch and multi-repository orchestration require a separate operator decision.
