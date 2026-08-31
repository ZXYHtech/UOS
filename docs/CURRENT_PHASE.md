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

Regression coverage in `tests/test_single_repo_pilot.py` includes:

- task lifecycle and dependency release;
- project/task publication creates no ownership;
- concurrent task publication preserves both catalog rows;
- repository path escape is rejected;
- ten contenders create one owner;
- expired owner is fenced after reclaim.

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
| 1. Standalone control plane runnable | PARTIAL PASS | CLI exists and synthetic lifecycle tests passed; exact committed fresh-clone suite still needs an unrestricted execution environment. |
| 2. Project creation | CODE/TEST PASS | `project init` exists; publishing mutations are serialized in the same-working-tree pilot. |
| 3. Task publication without ownership | CODE/TEST PASS | Regression verifies publish creates catalog work but no Claim/Done. |
| 4. Ordinary project lifecycle | PASS | QUICKBOARD completed SPEC → UI/LOGIC → DOCS → REVIEW. |
| 5. Claim/Lease/Fencing/Recovery | CODE/TEST PASS | Unique-owner and stale-reclaim tests exist; distributed multi-clone CAS is not yet claimed. |
| 6. Inspectable status | CODE/TEST PASS | `status` / derived `TASK_STATUS.csv` and `STATUS.json` are implemented. |

The phase gate is **not closed yet** because the standalone repository still lacks fresh-clone validation of the committed suite and the stronger latest-canonical Git CAS transaction path required before independent clones or repositories are introduced.

Only after this gate is closed — and only after a new explicit operator decision — should a new phase introduce external repositories.
