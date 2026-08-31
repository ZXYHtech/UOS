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

## Exit gate

Do not begin AI_book integration or generic multi-repository orchestration until all of these are demonstrated in `ZXYHtech/UOS`:

1. standalone UOS control plane is runnable;
2. project creation works without hand-editing hidden runtime state;
3. task publication creates READY/BLOCKED work but no ownership;
4. at least one ordinary project is completed through UOS task lifecycle;
5. claim uniqueness, lease/fencing, recovery and completion remain correct;
6. operator can inspect project status without reading the whole repository.

Only after this gate should a new, separately approved phase introduce external repositories.
