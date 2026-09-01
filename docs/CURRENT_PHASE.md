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
→ Reconcile
→ Continue until project completion
```

## Ordinary workload milestone

`QUICKBOARD` is **COMPLETED**.

All five project tasks have `.done` records and the project completed its final REVIEW. Evidence is in `docs/PILOT_RESULT_QUICKBOARD.md`.

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

`tools/uos.py` now supports:

```text
auto | local | git-cas
```

`auto` behavior:

- no configured Git remote → local same-working-tree mode;
- configured canonical remote → latest-canonical Git-CAS mode;
- configured remote becomes unreachable → fail closed; never silently fall back to local ownership.

### Canonical lifecycle runner — `tools/canonical_runner.py`

For Git-CAS mode, each logical UOS command:

1. fetches latest canonical branch;
2. creates an isolated detached worktree at that exact commit;
3. copies caller-owned declared completion outputs when needed;
4. runs `tools/uos.py --transport local ...` against that snapshot;
5. creates one candidate tree/commit containing the resulting source-of-truth and derived state;
6. pushes normally, never force;
7. on main-ref race, discards the candidate and reruns the **whole command** from the new canonical snapshot.

This gives `reconcile` the required full-recompute-on-race behavior instead of re-parenting stale derived files.

Completion also refuses a caller output when canonical main already contains different content at that declared output path. Declared outputs are force-staged inside the fresh isolated worktree so `.gitignore` cannot create a `.done` without its artifact.

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

`tests/test_git_cas_lifecycle.py` now adds end-to-end integration cases for the actual `uos.py` entrypoint:

- auto transport + independent-clone unique Claim;
- completion publishes an output even when `.gitignore` matches it;
- concurrent task publication replays from latest catalog;
- reconcile ref-race discards stale runtime and recomputes after canonical catalog advance;
- repeated unchanged status is a canonical no-op;
- disappearing configured remote fails closed without creating a local Claim.

One-command entrypoint:

```bash
python tools/selftest.py
```

## Exit gate

Do not begin AI_book integration or generic multi-repository orchestration until all of these are demonstrated in `ZXYHtech/UOS`:

| Gate | Current result | Notes |
|---|---|---|
| Standalone control plane runnable | PARTIAL PASS | CLI and selftest entrypoint exist; normal GitHub fresh-clone execution cannot be performed from the current isolated runtime because `github.com` DNS is unavailable. |
| Project creation | CODE INTEGRATED | Local and canonical transport paths are implemented; integration regression added. |
| Task publication without ownership | CODE INTEGRATED | Canonical retry reruns publication from latest catalog; integration regression added. |
| Ordinary project lifecycle | PASS | QUICKBOARD completed SPEC → UI/LOGIC → DOCS → REVIEW. |
| Claim / Lease / Fencing / Recovery | LOW-LEVEL CAS PASS + LIFECYCLE INTEGRATED | Bottom-layer CAS was executed previously; full `uos.py` independent-clone regression is now present but has not been executed from this chat's isolated repository runtime. |
| Reconcile latest-canonical semantics | CODE INTEGRATED | Full-command rerun on ref race is implemented; dedicated regression added. |
| Inspectable deterministic status | CODE INTEGRATED | `TASK_STATUS.csv` / `STATUS.json`; unchanged status should not advance canonical main. |

## Current blocker to phase closure

The architectural integration is now present. The main remaining gate is **execution evidence against the exact committed integrated code from a normal checkout/fresh clone**.

Current environment limitation:

```text
git ls-remote https://github.com/ZXYHtech/UOS.git
→ Could not resolve host: github.com
```

This is recorded as an environment limitation rather than marked PASS.

Until that exact integrated selftest is executed successfully, the phase gate remains open. Even after it passes, AI_book and multi-repository orchestration still require a separate operator decision before activation.
