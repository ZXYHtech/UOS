# TASK_UOS_STANDALONE_KERNEL_EXPORT_01 — progress record

Status: **IN PROGRESS**  
Project: `UOS_CORE`  
Phase: `SINGLE_REPOSITORY_PILOT`

## Goal

Extract the reusable UOS kernel from the historical AI_book host into `ZXYHtech/UOS` without copying AI_book project content/runtime state and without activating cross-repository scheduling.

## Extracted / rebuilt in standalone UOS

### Repository identity and phase boundary

- `.uos/REPOSITORY_IDENTITY.yaml` defines `ZXYHtech/UOS` as this repository's identity anchor.
- `docs/CURRENT_PHASE.md` mechanically records the operator hold: no AI_book dispatch and no multi-repository orchestration.

### Same-working-tree lifecycle kernel

`tools/uos.py` now provides a standalone standard-library implementation of:

- Boot / Status / Reconcile
- Project Init
- Task Publish
- dependency-driven READY/BLOCKED derivation
- Claim
- Lease / Renew
- LeaseGeneration / LeaseToken / Fencing
- stale reclaim
- Complete
- repository-local path validation
- atomic local catalog/runtime replacement
- same-working-tree control-plane mutex

This lifecycle completed the ordinary `QUICKBOARD` project through SPEC → UI/LOGIC → DOCS → REVIEW.

### Standalone canonical Git transaction primitive

The stronger AI_book latest-canonical / Main Ref Gate concept has now been reimplemented as a smaller domain-neutral standalone primitive:

`tools/canonical_publish.py`

Implemented semantics:

- explicit latest canonical branch fetch;
- branch-independent worktree operation;
- Repository Identity remote/branch verification when an identity anchor is present;
- non-force canonical ref update;
- ref-race rebuild/retry;
- create-if-absent CAS;
- expected-blob fenced replacement;
- atomic multi-path publish;
- expected-blob-protected deletion;
- atomic output + `.done` + Claim release capability;
- target no-clobber behavior.

The implementation intentionally does **not** copy AI_book-specific PathAuthority, Grant compatibility, AI_BOOK namespace rules, workflow dependencies or project runtime state.

### Regression suites

- `tests/test_single_repo_pilot.py`
- `tests/test_canonical_publish.py`
- `tools/selftest.py`

The canonical Git CAS suite has been exercised with temporary bare Git repositories and independent clones. The hardened CAS suite passes 7/7 cases, including unique Claim contention, ref-race preservation, stale fencing, atomic completion/release, no-clobber, delete fencing and wrong-canonical-target rejection.

## AI_book artifacts used only as read-only design evidence

The extraction referenced generic design behavior from AI_book, especially:

- `coordination/MAIN_REF_WRITE_GATE.md`
- `orchestration/CONTROL_PLANE_WRITER.md`
- `tools/main_ref_publish.py`
- `tools/main_ref_publish_legacy.py`

No AI_book Claim, Grant, Done, project content, game/book assets, credentials or runtime history were copied into UOS.

## Open work before this task can be marked DONE

The extraction task is **not complete yet**.

The remaining major item is lifecycle integration:

```text
tools/uos.py
  project init
  task publish
  claim
  renew
  complete
  reconcile
        ↓
standalone latest-canonical Git CAS transport
        ↓
canonical main
```

Important rule for integration:

- Source-of-truth operations may retry against latest canonical preconditions.
- Derived `reconcile` state must be recomputed from a fresh canonical snapshot after a ref race; stale derived files must never merely be re-parented to a new main.

A normal remote fresh-clone selftest also remains to be executed in an unrestricted Git network environment. The current execution environment cannot resolve `github.com`, so this limitation is recorded rather than falsely marked PASS.

## Current decision

Keep `TASK_UOS_STANDALONE_KERNEL_EXPORT_01` open until canonical transport integration is complete and the standalone selftest can be run from a normal fresh clone.

Do not start AI_book integration or multi-repository orchestration as part of closing this task.
