# TASK_UOS_STANDALONE_KERNEL_EXPORT_01 — progress record

Status: **IN PROGRESS — implementation integrated, final execution + visible-result evidence pending**  
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

`local` mode retains the repository-local mutex used by the first pilot and isolated unit tests.

### Latest-canonical Git transport

`tools/uos.py` exposes:

```text
--transport auto | local | git-cas
```

`auto` selects Git-CAS when a remote is configured. A configured remote that becomes unreachable fails closed rather than creating a local fallback Claim.

`tools/canonical_runner.py` integrates the lifecycle with canonical Git:

```text
fetch latest main
→ isolated detached worktree
→ apply current quality / preview gate
→ rerun full UOS command
→ candidate tree/commit
→ non-force push
→ ref race?
   yes: discard candidate + worktree and rerun from new main
```

This integrates Project Init, Task Publish, Claim, Renew, Complete, Status and Reconcile without teaching each command a second distributed state machine.

### Reconcile correctness

A main-ref race never re-parents stale runtime. The entire local reconcile command is re-executed from the newer canonical snapshot.

Derived `STATUS.json` is deterministic and does not contain timestamp-only churn.

### Completion correctness

Git-CAS completion:

- reads declared output paths from latest canonical Task Catalog;
- copies caller-owned outputs into the isolated snapshot;
- refuses unrelated conflicting canonical artifacts;
- rechecks Claim owner/token/fencing on latest canonical state;
- creates `.done`, releases Claim and recomputes derived state in the same candidate tree;
- force-stages declared artifacts inside the clean isolated worktree so `.gitignore` cannot produce a `.done` without its output.

## Quality Visibility RuleEpoch 1

The operator added a new anti-drift rule during this extraction task.

Policy:

```text
.uos/QUALITY_VISIBILITY_POLICY.yaml
```

Detailed specification:

```text
docs/QUALITY_VISIBILITY_GATE.md
```

Runtime:

```text
tools/quality_gate.py
```

### Rule-change warmup

Current RuleEpoch is `1`.

Before normal parallel execution resumes:

```text
Task result 1
  → Agent shows result + previews in conversation
  → operator confirms
  → only then Task result 2 may start

Task result 2
  → show + confirm
  → only then Task result 3 may start

Task result 3
  → show + confirm
  → warmup closes
```

`WarmupMaxConcurrentClaims = 1` prevents multiple Agents from pre-claiming the first three tasks and drifting in parallel before the new rule is proven.

After warmup, completion sequence `5, 10, 15, ...` is deterministically sampled, and HIGH-risk tasks may always require review.

### Visible result requirement

Routine completion is no longer allowed to end with only:

```text
"done; inspect GitHub path"
```

The completion packet tells the Agent to present:

- result summary;
- output list;
- previews/screenshots when applicable;
- whether the result is mandatory warmup review or sampled review.

Pending review blocks new Claims.

### Preview requirement

Known source formats automatically gain inspectable preview companions during canonical Task Publish.

Examples:

```text
.svg  → .svg + .png
.html → .html + .preview.png
.pdf  → .pdf + .preview.png
.pptx/.docx/.xlsx → source + .preview.pdf
CAD/EDA → source + .preview.png
```

Completion fails with `PREVIEW_OR_OUTPUT_MISSING` when the required preview does not exist.

This moves preview generation into the original task definition instead of discovering the need after a large batch is complete.

### Reject / rework

If the operator rejects one of the visible results:

1. the quality event records `REJECTED` and feedback;
2. the task canonical `.done` is removed;
3. unrelated new work remains blocked;
4. the same task may be explicitly reclaimed;
5. corrected outputs may replace the rejected versions;
6. completion returns to `PENDING` and must be reviewed again.

## Lower-level CAS primitive

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
- `tests/test_quality_visibility.py`
- `tests/test_quality_warmup_serial.py`
- `tools/selftest.py`

Quality regressions cover:

- preview output expansion;
- SVG missing-PNG rejection;
- first-three review + fifth-completion sampling;
- Git-CAS pending-review Claim blocking;
- operator Accept unblocking;
- rejected-task correction boundary;
- RuleEpoch warmup single-active-Claim behavior.

## AI_book used only as read-only design evidence

Referenced generic design behavior included:

- `coordination/MAIN_REF_WRITE_GATE.md`
- `orchestration/CONTROL_PLANE_WRITER.md`
- `tools/main_ref_publish.py`
- `tools/main_ref_publish_legacy.py`

No AI_book Claim, Grant, Done, project content, book/game assets, credentials or runtime history were copied into UOS.

## What remains before DONE

The major lifecycle-to-CAS implementation gap is closed in code. The new anti-drift gate is also integrated in code.

Remaining acceptance evidence:

### A. Exact committed fresh-clone selftest

```text
git clone https://github.com/ZXYHtech/UOS.git
cd UOS
python tools/selftest.py
```

The current chat execution container cannot resolve `github.com`, so this exact run cannot be performed here. This environment limitation must not be rewritten as a PASS.

### B. Three real RuleEpoch-1 reviewed results

The next three real completion results under RuleEpoch 1 must be shown directly to the operator and accepted one by one. This validates that the anti-drift policy works in ordinary Agent execution, not only in test code.

## Current decision

Keep `TASK_UOS_STANDALONE_KERNEL_EXPORT_01` open until the committed integrated selftest and the RuleEpoch-1 visible-result warmup have acceptable evidence.

Do **not** begin AI_book integration or multi-repository orchestration without a new explicit operator decision.
