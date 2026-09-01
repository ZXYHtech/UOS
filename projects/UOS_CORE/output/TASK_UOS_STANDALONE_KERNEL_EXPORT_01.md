# TASK_UOS_STANDALONE_KERNEL_EXPORT_01 — progress record

Status: **IN PROGRESS — implementation integrated, final execution evidence pending**  
Project: `UOS_CORE`  
Phase: `SINGLE_REPOSITORY_VALIDATION`

## Goal

Extract the reusable UOS kernel from the historical AI_book host into `ZXYHtech/UOS` without copying AI_book project/runtime state and without activating cross-repository scheduling.

## Standalone capability now present

### Repository identity / phase boundary

- `.uos/REPOSITORY_IDENTITY.yaml` anchors canonical upstream at `https://github.com/ZXYHtech/UOS`, branch `main`.
- `docs/CURRENT_PHASE.md` keeps the operator hold explicit: no AI_book dispatch and no multi-repository orchestration.

### Deterministic lifecycle state machine

`tools/uos.py` provides:

- Boot / Status / Reconcile
- Project Init
- Task Publish
- dependency-driven READY/BLOCKED
- Claim
- Lease / Renew
- LeaseGeneration / LeaseToken / Fencing
- stale reclaim
- Complete
- repository-local path validation
- deterministic derived runtime files

This state machine completed QUICKBOARD through SPEC → UI/LOGIC → DOCS → REVIEW.

### Same-working-tree transport

`local` mode retains the repository-local mutex used by the first pilot and by isolated unit tests.

### Latest-canonical Git transport

`tools/uos.py` now exposes:

```text
--transport auto | local | git-cas
```

`auto` selects Git-CAS when a remote is configured. A configured remote that becomes unreachable fails closed rather than creating a local fallback Claim.

`tools/canonical_runner.py` integrates the whole lifecycle with canonical Git:

```text
fetch latest main
→ isolated detached worktree
→ rerun full UOS command
→ candidate tree/commit
→ non-force push
→ ref race?
   yes: discard candidate + worktree and rerun from new main
```

This integrates Project Init, Task Publish, Claim, Renew, Complete, Status and Reconcile without teaching each command a second distributed state machine.

### Reconcile correctness

A main-ref race never re-parents stale runtime. The entire local reconcile command is re-executed from the newer canonical snapshot.

Derived `STATUS.json` is now deterministic and does not include a changing generated-at timestamp, so unchanged status can be a canonical no-op.

### Completion correctness

Git-CAS completion:

- reads declared output paths from latest canonical Task Catalog;
- copies caller-owned outputs into the isolated snapshot;
- refuses a different pre-existing canonical artifact at the same output path;
- rechecks Claim owner/token/fencing on latest canonical state;
- creates `.done`, releases Claim and recomputes derived state in the same candidate tree;
- force-stages declared artifacts inside the clean isolated worktree so `.gitignore` cannot produce a `.done` without its output.

### Lower-level CAS primitive

`tools/canonical_publish.py` remains a focused transport primitive with:

- latest-canonical fetch/build/push;
- non-force update;
- create-if-absent;
- expected-blob replacement;
- expected-blob-protected delete;
- multi-path tree transaction;
- no-clobber;
- Repository Identity remote/branch verification.

The hardened low-level bare-Git / multi-clone suite previously passed **7/7**.

## Regression suites now in repository

- `tests/test_single_repo_pilot.py`
- `tests/test_canonical_publish.py`
- `tests/test_git_cas_lifecycle.py`
- `tools/selftest.py`

The new integrated lifecycle suite covers:

- auto transport unique Claim across independent clones;
- Complete + Claim release through `uos.py`;
- declared output canonicalization even when `.gitignore` matches it;
- concurrent Task Publish replay from latest catalog;
- Reconcile ref-race full recomputation;
- unchanged Status canonical no-op;
- remote disappearance fail-closed behavior.

## AI_book used only as read-only design evidence

Referenced generic design behavior included:

- `coordination/MAIN_REF_WRITE_GATE.md`
- `orchestration/CONTROL_PLANE_WRITER.md`
- `tools/main_ref_publish.py`
- `tools/main_ref_publish_legacy.py`

No AI_book Claim, Grant, Done, project content, book/game assets, credentials or runtime history were copied into UOS.

## What remains before DONE

The major implementation gap — lifecycle-to-CAS integration — is now closed in code.

The remaining acceptance item is execution evidence for the **exact committed integrated version** from a normal checkout/fresh clone:

```text
git clone https://github.com/ZXYHtech/UOS.git
cd UOS
python tools/selftest.py
```

The current chat execution container cannot resolve `github.com`, so this exact fresh-clone run cannot be performed here. This is an environment limitation and must not be rewritten as a PASS.

## Current decision

Keep `TASK_UOS_STANDALONE_KERNEL_EXPORT_01` open until the committed integrated selftest is executed successfully in a normal Git environment.

Even after that acceptance closes, do **not** begin AI_book integration or multi-repository orchestration without a new explicit operator decision.
