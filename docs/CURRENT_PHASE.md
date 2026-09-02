# Current Phase — Single-Repository Validation

## Operator decision

UOS remains in **single-repository validation mode**.

For this phase:

- UOS may create and manage projects whose definitions, task state and outputs live inside `ZXYHtech/UOS`.
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
→ Reconcile READY Work Market
→ Capability-aware discovery when used
→ canonical Agent Claim
→ Work
→ Renew / Fencing
→ Complete outputs + preview + durability receipt + .done
→ Visible Result / Preview Gate
→ Operator Review when required
→ bounded continuation decision when a Work Session is active
→ Next compatible Claim or safe stop
```

## Ordinary workload milestone

`QUICKBOARD` is **COMPLETED**.

It proved the first ordinary same-repository lifecycle through SPEC → UI/LOGIC → DOCS → REVIEW.

# ExecutionEpoch — ACTIVE

Anchor:

```text
.uos/EXECUTION_CONTRACT.yaml
```

Current value:

```text
UOS_EXEC_20260902_01
```

Critical `uos.py` control-plane commands require the current acknowledgement:

```text
project
task
claim
renew
complete
reconcile
```

The new `task_requirements.py` and `work_session.py` canonical mutations independently enforce the same current Epoch.

`boot` and `status` remain discovery/read entrypoints.

Purpose: old Agent instructions or old chat context cannot silently create new canonical mutations after execution semantics change.

# Quality Visibility RuleEpoch 1 — ACTIVE

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

If the operator rejects a result, the standalone pilot revokes that task's current `.done`, retains feedback and allows the same task to be corrected/re-reviewed before unrelated work resumes.

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

# AI_book generic delta synchronized on 2026-09-02

Primary inventory:

```text
docs/AI_BOOK_UPSTREAM_DELTA_20260902.md
```

## P0 integrated

```text
ExecutionEpoch stale-Agent gate
Project WorkRoot output authority
READY-only WORK_MARKET.csv
UOS_ARTIFACT_DURABILITY_V1 receipt
```

## P1A integrated

```text
Capability / Tool / Context Matching
Bounded Work Session
Task Agent requirement sidecar
```

Details:

```text
docs/WORK_SESSION_AND_AGENT_MATCHING.md
docs/AI_BOOK_P1_SYNC_20260902.md
```

## P1B still pending

```text
Partial Handoff                    NEXT CANDIDATE
Resource Admission / Backpressure NEED-DRIVEN
```

P2 remains deferred:

```text
Role Broker / role leases
OUTBOX_INGEST
complex Kernel self-orchestration
multi-repository adapters/routing
```

# Artifact durability invariant

A visible/accepted result must not be confused with durable repository persistence.

Standalone Complete creates:

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

# Project WorkRoot authority

Current projects are compatible with the rule:

```text
UOS_CORE   → projects/UOS_CORE/...
QUICKBOARD → projects/QUICKBOARD/...
```

Task Publish and Complete refuse cross-project output paths.

# Work Market + Agent Matching

Every reconcile derives:

```text
coordination/runtime/WORK_MARKET.csv
```

It contains READY work and compact capability/context/tool metadata.

The optional matching path is:

```text
latest canonical WORK_MARKET
→ tools/agent_matching.py
→ capability/tool/context/role filter
→ selected compatible Task
→ tools/uos.py claim
```

Matching is not ownership.

Optional project-local overrides:

```text
orchestration/projects/<PROJECT>/TASK_AGENT_REQUIREMENTS.csv
```

They may only refine matching hints; they do not alter task authority.

# Bounded Work Session

Tool:

```text
tools/work_session.py
```

State:

```text
coordination/work_sessions/<AGENT>/<SESSION>.json
```

A Work Session records a deadline, maximum task count, project scope and Agent capability envelope.

It is a continuation guard, not a scheduler.

No unrelated next Claim is allowed until the current task has:

```text
canonical .done
+ durability receipt = DURABLE_READY
+ Quality Event gate released
```

Important stop behavior:

```text
review PENDING  → STOP_REVIEW_PENDING
review REJECTED → REWORK_REQUIRED on same task
missing receipt → STOP_DURABILITY_PENDING
missing quality event while policy enabled → fail closed
deadline with no current Claim → stop before new Claim
deadline with current Claim → WORK_CURRENT_TASK + stop_after_current=true
```

If Claim succeeds before Session bookkeeping is durably updated, the next session check may adopt the single live canonical Claim for that Agent. More than one live Claim yields `RECOVERY_REQUIRED` rather than guessing.

# Current standalone kernel

## `tools/uos.py`

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

## Transport selection

```text
auto | local | git-cas
```

`auto` behavior:

- no configured Git remote → local;
- configured canonical remote → latest-canonical Git-CAS;
- configured remote becomes unreachable → fail closed, never local fallback ownership.

## `tools/canonical_runner.py`

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

## `tools/quality_gate.py`

Provides preview expansion/validation, RuleEpoch sequence, first-three mandatory review, deterministic sampling, pending-review Claim pause, Accept/Reject correction and conversation presentation packets.

## `tools/control_extensions.py`

Provides ExecutionEpoch, Project WorkRoot output guard, Work Market builder and Artifact Durability Receipt.

## `tools/agent_matching.py`

Provides capability/tool/context/optional-role filtering over latest canonical READY work and delegates final ownership to `uos.py claim`.

## `tools/task_requirements.py`

Maintains optional project-local matching hint sidecars using canonical CAS.

## `tools/work_session.py`

Maintains bounded continuation state and only requests another canonical Claim after durability/review/deadline guards pass.

## `tools/canonical_publish.py`

Lower-level latest-canonical CAS primitive: create-if-absent, expected-blob replace/delete, no-clobber, non-force ref-race retry and Repository Identity target verification.

Normal Agents should not construct task lifecycle state directly with this primitive.

# Regression coverage

Existing suites cover local lifecycle, low-level CAS, independent-clone `uos.py` lifecycle, Preview/Review Gate, RuleEpoch warmup, ExecutionEpoch, WorkRoot, Work Market and durability.

P1 additions:

```text
tests/test_agent_matching.py
tests/test_task_requirements.py
tests/test_work_session_guard.py
tests/test_work_session_git_cas.py
```

These cover:

- incompatible higher-priority task skipped;
- missing tool is a hard mismatch;
- context capacity ordering;
- sidecar override;
- stale Epoch rejected before matching-policy write;
- PENDING review stops continuation;
- REJECTED review forces same-task rework;
- durability missing fails closed;
- max-task stop;
- deadline does not abandon current Claim;
- bare-Git / independent-Clone Session + capability matching integration.

One-command entrypoint:

```bash
python tools/selftest.py
```

# Exit gate

| Gate | Current result | Notes |
|---|---|---|
| Standalone control plane runnable | PARTIAL PASS | CLI/selftest exist; exact current committed fresh-clone execution still needs normal network runtime evidence. |
| ExecutionEpoch stale-Agent safety | CODE / TEST PRESENT | Current Epoch `UOS_EXEC_20260902_01`. |
| Project creation | CODE INTEGRATED | Canonical/local paths implemented. |
| Task publication without ownership | CODE INTEGRATED | Output scope constrained to Project WorkRoot. |
| Work discovery | CODE / TEST PRESENT | Reconcile derives READY-only Work Market. |
| Capability-aware discovery | CODE / TEST PRESENT | Matching adapter delegates final ownership to canonical Claim. |
| Bounded Work Session | CODE / TEST PRESENT | Durability/review/deadline/max-task guard implemented. |
| Ordinary project lifecycle | PASS | QUICKBOARD completed SPEC → UI/LOGIC → DOCS → REVIEW. |
| Claim / Lease / Fencing / Recovery | LOW-LEVEL CAS PASS + LIFECYCLE INTEGRATED | exact-current full suite still needs execution evidence. |
| Artifact durability | CODE / TEST PRESENT | Complete binds output digest receipt + `.done` in same candidate tree. |
| Reconcile latest-canonical semantics | CODE INTEGRATED | full-command rerun after ref race. |
| Visible-result / preview anti-drift | RULEEPOCH 1 ACTIVE / TEST PRESENT | next three real reviewed completions must be directly shown and accepted. |
| Partial Handoff | NOT YET | Recommended next P1B capability. |
| Resource Admission / Backpressure | NOT YET | Add only with real capacity need. |

# Current blocker to phase closure

Two acceptance items remain primary:

1. run `python tools/selftest.py` against the **exact current committed version** from a normal fresh clone/runtime;
2. exercise Quality RuleEpoch 1 through its first three real reviewed task completions in ordinary Agent work.

Current chat execution environment has previously failed direct GitHub DNS access, so exact fresh-clone execution is not falsely marked PASS.

Even after these close, AI_book dispatch and multi-repository orchestration require a separate operator decision.
