# Canonical Git CAS — standalone single-repository transport

Status: `PILOT_VALIDATED_PRIMITIVE`  
Scope: one UOS repository, potentially many independent clones/worktrees  
Entrypoint: `python tools/canonical_publish.py`

## Purpose

The first QUICKBOARD pilot proved UOS lifecycle correctness inside one shared working tree. A repository-local mutex is sufficient for that topology, but it cannot arbitrate independent clones.

`tools/canonical_publish.py` adds the next transport layer without enabling multi-repository project orchestration. It lets several Agents work from separate clones of the **same UOS repository** while Git remains the canonical arbiter.

The design is extracted from the already-proven AI_book Main Ref Gate / latest-canonical transaction model, but intentionally omits AI_book-specific Project Namespace, Grant compatibility, PathAuthority and provider workflow assumptions.

## Invariant

Every successful transaction is built from the latest fetched canonical branch and advances it by a normal non-force update.

```text
fetch latest origin/main
        ↓
verify canonical repository identity / branch
        ↓
validate transaction preconditions against latest main
        ↓
build a new tree from that exact base
        ↓
commit-tree -p <latest-main>
        ↓
normal push to refs/heads/main
        ↓
ref race?
  yes → discard candidate, fetch latest, rebuild
  no  → canonical fact
```

Never force-push and never rebase a stale candidate's derived decisions onto a newer canonical state.

If `.uos/REPOSITORY_IDENTITY.yaml` exists, the publisher verifies the requested target branch and the selected remote against its `Canonical.DefaultBranch` and `Canonical.Repository` before writing.

## Supported transaction semantics

### 1. Create-if-absent

Use for a new canonical Claim or other append-only object:

```bash
python tools/canonical_publish.py \
  --path coordination/claims/TASK_X.lock \
  --require-absent coordination/claims/TASK_X.lock \
  --message "claim TASK_X"
```

If two clones race, only one can advance canonical history with the absent path. The loser refetches and then fails the `require-absent` precondition.

### 2. Expected-blob replacement

Use for fenced replacement such as Renew/Reclaim:

```bash
python tools/canonical_publish.py \
  --path coordination/claims/TASK_X.lock \
  --expect-blob coordination/claims/TASK_X.lock=<EXPECTED_BLOB_SHA> \
  --allow-replace \
  --message "renew TASK_X"
```

A stale Agent cannot replace a lock after another generation has changed its canonical blob. Replacement of different canonical content requires both an explicit expected blob and `--allow-replace`.

### 3. Atomic completion + lock release

A completion can publish all task-owned outputs and `.done` while deleting the Claim in the same Git tree transaction:

```bash
python tools/canonical_publish.py \
  --path projects/DEMO/result.md \
  --path coordination/completed/TASK_X.done \
  --delete-path coordination/claims/TASK_X.lock \
  --expect-blob coordination/claims/TASK_X.lock=<CURRENT_LOCK_BLOB_SHA> \
  --message "complete TASK_X"
```

The output, completion fact and ownership release become visible together or not at all.

**Every deletion requires an expected canonical blob.** An unchecked `--delete-path` is refused, so a stale completion cannot delete a newer Agent's Lock.

### 4. Disjoint concurrent writes

When two clones publish different paths from the same base, one push may win first. The loser fetches the new canonical head, rebuilds its candidate from that head and retries. Both paths are preserved.

## Default no-clobber rule

For a published path:

- canonical path absent → create;
- canonical blob equals local blob → idempotent no-op;
- canonical blob differs → `TARGET_PATH_CONFLICT`, unless the caller supplied the current expected canonical blob and explicitly enabled replacement.

For a deleted path:

- deletion is refused unless the caller supplies the exact expected canonical blob;
- if that blob changed before publication, the transaction is fenced by `EXPECTED_BLOB_MISMATCH`.

This prevents retries from silently overwriting or deleting another Agent's result.

## Regression evidence

`tests/test_canonical_publish.py` creates a temporary bare Git repository and independent clones. It verifies:

1. two clones concurrently publishing disjoint paths preserve both results;
2. two clones racing for one create-if-absent Claim produce exactly one winner;
3. output + `.done` + Claim deletion are one completion transaction;
4. expected-blob fencing rejects a stale replacement;
5. conflicting writes to the same path do not clobber canonical content;
6. deletion without an expected blob is rejected;
7. a repository identity anchor pointing at a different canonical remote is rejected.

The hardened suite was executed in the current isolated environment against local Git/bare repositories and passed **7/7**.

## One-command regression

From a checkout containing Git and Python 3:

```bash
python tools/selftest.py
```

This runs both the same-working-tree lifecycle suite and the multi-clone CAS suite.

## What this does not mean

This primitive does **not** activate:

- AI_book dispatch;
- external repository adapters;
- one UOS controlling several project repositories;
- cross-repository ownership;
- provider-specific automation requirements.

It is still a single-repository capability: several clones may contend for the same repository's canonical main.

## Remaining integration work

`tools/uos.py` still uses the same-working-tree local mutex for its default `project/task/claim/renew/complete/reconcile` commands. The CAS primitive must next be integrated as the canonical transport for those lifecycle operations, with full-recompute-on-race for derived `reconcile` state.

Until that integration is tested, the single-repository Exit Gate remains open and multi-repository work remains operator-blocked.
