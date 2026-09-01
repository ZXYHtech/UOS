# Current Phase — Single-Repository Validation

## Operator decision

UOS remains in **single-repository validation mode**.

For this phase:

- UOS may create and manage projects whose project definitions, task state and work outputs live inside `ZXYHtech/UOS`.
- UOS must **not** dispatch, claim, mutate, synchronize or manage AI_book project work.
- Cross-repository task routing is not active.
- Multi-repository orchestration requires a new explicit operator decision.

## Phase goal

Prove this lifecycle entirely inside one repository, including independent clones of that same repository:

```text
Create Project
→ Publish Tasks
→ Discover READY work
→ Agent Claim
→ Work
→ Renew / Fencing
→ Complete
→ Visible Result / Preview Gate
→ Operator Review when required
→ Reconcile
→ Continue until project completion
```

## Ordinary workload milestone

`QUICKBOARD` is **COMPLETED**.

All five project tasks have `.done` records and the project completed its final REVIEW. Evidence is in `docs/PILOT_RESULT_QUICKBOARD.md`.

## Quality Visibility RuleEpoch 1 — ACTIVE

The operator has added a new anti-drift requirement: Agents must not complete large batches while the user has not directly seen representative results.

Policy anchor:

```text
.uos/QUALITY_VISIBILITY_POLICY.yaml
```

Detailed rules:

```text
docs/QUALITY_VISIBILITY_GATE.md
```

Current RuleEpoch behavior:

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

While a quality event is `PENDING`, new Claims are paused. The Agent must present the result summary and previews directly in the conversation; routine review must not require the user to browse GitHub.

If the operator rejects a result, the task `.done` is revoked, feedback is retained, unrelated work remains blocked, and the same task can be explicitly reclaimed for correction. The corrected result is reviewed again.

Whenever these review/preview rules materially change, `RuleEpoch` must increment and the next three completions return to mandatory confirmation.

## Preview contract

Task publication now treats inspectability as part of the original deliverable.

Examples:

```text
SVG       → SVG + PNG
HTML      → HTML + preview PNG
PDF       → PDF + preview PNG
PPT/DOC/XLS → source + preview PDF
CAD/EDA   → source + preview PNG
```

Known preview companions are automatically added during canonical Task Publish. Completion is refused when a required preview is missing.

This prevents a common failure mode where a technically completed source artifact cannot be conveniently inspected until a later cleanup task is added.

## Current standalone kernel

### Deterministic state machine — `tools/uos.py`

Commands:

- `boot`
- `status`
- `reconcile`
- `project init`
- `task publish`
- `claim`
- `renew`
- `complete`

State semantics include:

- dependency-driven READY/BLOCKED;
- Claim ownership;
- LeaseGeneration / LeaseToken / Fencing;
- stale reclaim;
- repository-local input/output path guards;
- completion output existence checks;
- deterministic runtime views (no timestamp-only churn).

### Transport selection

`tools/uos.py` supports:

```text
auto | local | git-cas
```

`auto` behavior:

- no configured Git remote → local same-working-tree mode;
- configured canonical remote → latest-canonical Git-CAS mode;
- configured remote becomes unreachable → fail closed; never silently fall back to local ownership.

`local` remains primarily a test/single-worktree transport. The canonical review/preview gate is integrated into the normal Git-CAS runner path.

### Canonical lifecycle runner — `tools/canonical_runner.py`

For Git-CAS mode, each logical UOS command:

1. fetches latest canonical branch;
2. creates an isolated detached worktree at that exact commit;
3. applies the current preview/review policy;
4. expands task outputs with required preview companions when publishing;
5. blocks Claim when a visible-result review is pending;
6. copies caller-owned completion outputs/previews when needed;
7. runs `tools/uos.py --transport local ...` against that snapshot;
8. validates completion output/preview existence;
9. creates a quality event and presentation packet;
10. creates one candidate tree/commit containing the resulting source-of-truth and derived state;
11. pushes normally, never force;
12. on main-ref race, discards the candidate and reruns the **whole command** from the new canonical snapshot.

This keeps completion sequence, sampling decisions and review state derived from the latest canonical history.

### Quality gate — `tools/quality_gate.py`

Provides:

- preview output expansion;
- preview existence validation;
- RuleEpoch completion sequence;
- first-three mandatory review;
- deterministic periodic sampling;
- HIGH-risk mandatory review;
- pending-review Claim pause;
- Accept / Reject commands;
- rejected-task reopen and re-review;
- conversation presentation packet.

Review commands:

```bash
python tools/quality_gate.py status
python tools/quality_gate.py review accept --task TASK_X --by OPERATOR
python tools/quality_gate.py review reject --task TASK_X --by OPERATOR --feedback "problem description"
```

In normal Agent use, the Agent executes these after the user has seen the result; the user should not need to operate GitHub or the CLI personally.

### Lower-level CAS primitive — `tools/canonical_publish.py`

Still available for focused transport tests and specialized integration:

- create-if-absent;
- expected-blob replace;
- expected-blob-protected delete;
- multi-path atomic tree publish;
- no-clobber;
- non-force ref race retry;
- Repository Identity target/branch verification.

Normal Agents should use `tools/uos.py`, not construct lifecycle state directly with this primitive.

## Regression coverage

`tests/test_single_repo_pilot.py`:

- local lifecycle and dependency release;
- publish creates no ownership;
- concurrent local task publication;
- path escape rejection;
- 10 contenders / one owner;
- stale-owner fencing.

`tests/test_canonical_publish.py`:

- independent-clone disjoint writes;
- unique create-if-absent Claim;
- atomic output + `.done` + Claim release;
- expected-blob stale fencing;
- same-path no-clobber;
- unchecked delete rejection;
- wrong canonical target rejection.

The hardened low-level CAS suite previously passed **7/7** against temporary bare Git remotes and independent clones.

`tests/test_git_cas_lifecycle.py`:

- auto transport + independent-clone unique Claim;
- concurrent task publication replay from latest catalog;
- reconcile ref-race full recomputation;
- repeated unchanged status canonical no-op.

`tests/test_quality_visibility.py` adds:

- SVG → PNG / HTML → PNG / Office → PDF preview expansion;
- first-three mandatory review + deterministic fifth-task sample;
- missing SVG PNG preview rejection;
- rejected task self-reclaim vs unrelated-work block;
- Git-CAS end-to-end preview-gate completion;
- pending-review Claim pause;
- operator Accept unblocks the next Claim.

One-command entrypoint:

```bash
python tools/selftest.py
```

## Exit gate

Do not begin AI_book integration or generic multi-repository orchestration until all of these are demonstrated in `ZXYHtech/UOS`:

| Gate | Current result | Notes |
|---|---|---|
| Standalone control plane runnable | PARTIAL PASS | CLI and selftest entrypoint exist; normal GitHub fresh-clone execution cannot be performed from the current isolated runtime because `github.com` DNS is unavailable. |
| Project creation | CODE INTEGRATED | Local and canonical transport paths are implemented. |
| Task publication without ownership | CODE INTEGRATED | Canonical retry reruns publication from latest catalog. |
| Ordinary project lifecycle | PASS | QUICKBOARD completed SPEC → UI/LOGIC → DOCS → REVIEW. |
| Claim / Lease / Fencing / Recovery | LOW-LEVEL CAS PASS + LIFECYCLE INTEGRATED | Bottom-layer CAS was executed previously; full exact-committed integrated selftest still needs normal runtime evidence. |
| Reconcile latest-canonical semantics | CODE INTEGRATED | Full-command rerun on ref race is implemented. |
| Inspectable deterministic status | CODE INTEGRATED | `TASK_STATUS.csv` / `STATUS.json`; unchanged status should not advance canonical main. |
| Visible-result / preview anti-drift gate | RULEEPOCH 1 ACTIVE / TEST ADDED | Next three completion events must be directly shown and operator-confirmed; preview companions are mechanically required for known visual/source formats. |

## Current blocker to phase closure

Two acceptance items remain important:

1. execute `python tools/selftest.py` against the **exact committed integrated version** from a normal fresh clone/runtime;
2. exercise RuleEpoch 1 through its first three real reviewed task completions, showing the results in conversation and confirming that the anti-drift gate behaves correctly in ordinary Agent work.

Current environment limitation:

```text
git ls-remote https://github.com/ZXYHtech/UOS.git
→ Could not resolve host: github.com
```

This is recorded as an environment limitation rather than marked PASS.

Until these acceptance items close, the phase gate remains open. Even after they pass, AI_book and multi-repository orchestration still require a separate operator decision before activation.
