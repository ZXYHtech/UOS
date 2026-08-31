# Current Phase — Single-Repository Pilot

## Operator decision

UOS is currently in **single-repository validation mode**.

For this phase:

- UOS may create and manage projects whose project data and work outputs live inside `ZXYHtech/UOS`.
- UOS must **not** dispatch, claim, mutate, synchronize, or manage AI_book project work.
- Cross-repository task routing is not an active capability target for this phase.
- Multi-repository orchestration remains a future phase and requires an explicit operator decision before activation.

## Phase goal

Prove the following lifecycle entirely inside one repository:

```text
Create Project
-> Publish Tasks
-> Discover READY work
-> Agent Claim
-> Work
-> Review / Revision
-> Complete
-> Reconcile
-> Continue until project completion
```

The purpose is to validate UOS as a usable project operating system before introducing repository boundaries, remote project adapters, or multi-repository scheduling.

## Pilot project

The first ordinary workload is `QUICKBOARD`, a small zero-dependency browser task board. It is intentionally unrelated to UOS Kernel development so the test can show whether UOS can manage a normal project rather than only manage itself.

**QUICKBOARD status: COMPLETED.**

All five project tasks have canonical `.done` records and the project completed its final REVIEW. Detailed evidence and lessons are recorded in `docs/PILOT_RESULT_QUICKBOARD.md`.

## Current single-repository kernel status

Implemented in `tools/uos.py`:

- `boot`
- `status`
- `reconcile`
- `project init`
- `task publish`
- `claim`
- `renew`
- `complete`
- repository-local mutex for same-working-tree control-plane mutations
- atomic derived/runtime file replacement
- dependency-driven READY derivation from `.done`
- LeaseGeneration / LeaseToken / Fencing checks
- stale reclaim with generation increment
- repository-local input/output path guard

Implemented in `tools/canonical_publish.py`:

- latest-canonical fetch/build/push transaction;
- branch-independent explicit canonical target;
- Repository Identity remote/branch verification when an identity anchor exists;
- non-force ref update only;
- ref-race rebuild/retry from latest canonical state;
- create-if-absent transaction for unique Claim creation;
- expected-blob CAS for fenced replacement;
- multi-path atomic publish + expected-blob-protected deletion for completion/release;
- default target no-clobber conflict detection.

Regression coverage:

`tests/test_single_repo_pilot.py` verifies:

- task lifecycle and dependency release;
- project/task publication creates no ownership;
- concurrent task publication preserves both catalog rows;
- repository path escape is rejected;
- ten contenders create one owner;
- expired owner is fenced after reclaim.

`tests/test_canonical_publish.py` verifies against a temporary bare Git remote and independent clones:

- disjoint concurrent writes survive a main-ref race;
- two clones racing for one Claim produce exactly one winner;
- completion can publish output + `.done` + Claim deletion atomically;
- stale expected-blob replacement is fenced;
- same-path conflicting content is not clobbered;
- unchecked deletion is refused;
- wrong canonical remote is refused when Repository Identity is present.

The hardened CAS suite passes **7/7** in local bare-remote / multi-clone execution.

`python tools/selftest.py` is the single regression entrypoint.

## Exit gate

Do not begin AI_book integration or generic multi-repository orchestration until all of these are demonstrated in `ZXYHtech/UOS`:

1. standalone UOS control plane is runnable;
2. project creation works without hand-editing hidden runtime state;
3. task publication creates READY/BLOCKED work but no ownership;
4. at least one ordinary project is completed through UOS task lifecycle;
5. claim uniqueness, lease/fencing, recovery and completion remain correct;
6. operator can inspect project status without reading the whole repository.

### Gate progress

| Gate | Current result | Notes |
|---|---|---|
| 1. Standalone control plane runnable | PARTIAL PASS | CLI and one-command selftest exist; direct network `git clone` cannot be executed in the current isolated environment, so exact remote fresh-clone execution is not claimed. |
| 2. Project creation | CODE/TEST PASS | `project init` exists; same-working-tree publication is serialized. |
| 3. Task publication without ownership | CODE/TEST PASS | Regression verifies publish creates catalog work but no Claim/Done. |
| 4. Ordinary project lifecycle | PASS | QUICKBOARD completed SPEC → UI/LOGIC → DOCS → REVIEW. |
| 5. Claim/Lease/Fencing/Recovery | CAS PRIMITIVE PASS / INTEGRATION PARTIAL | Same-working-tree lifecycle is tested and the hardened canonical Git transaction primitive passes 7/7 independent-clone/bare-remote CAS tests. Default `uos.py` lifecycle commands still need to use that transport before this gate is fully closed. |
| 6. Inspectable status | CODE/TEST PASS | `status` / derived `TASK_STATUS.csv` and `STATUS.json` are implemented. |

## Current blocker to phase closure

The major remaining single-repository task is no longer “invent a distributed CAS algorithm.” The primitive now exists and has passed local multi-clone Git tests.

The remaining work is **integration**:

```text
uos project/task/claim/renew/complete/reconcile
                ↓
standalone canonical Git transaction transport
                ↓
latest canonical main
```

For source-of-truth mutations (Project, Task, Claim, Renew, Complete), the transport may retry from current canonical preconditions. For derived `reconcile` state, a ref race must discard the stale computed result and rerun reconciliation from a fresh canonical snapshot rather than merely re-parenting old derived files.

A normal remote fresh-clone selftest should also be run when an unrestricted Git network environment is available. The current execution environment cannot resolve `github.com`; this is recorded as an environment limitation, not a product failure.

The phase gate is therefore **still open**. AI_book dispatch, external repositories and multi-repository orchestration remain blocked until this integration is complete and a new operator decision explicitly opens the next phase.
