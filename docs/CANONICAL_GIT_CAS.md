# Canonical Git CAS — standalone single-repository transport

Status: `LIFECYCLE_INTEGRATED_TEST_PENDING`  
Scope: one UOS repository, potentially many independent clones/worktrees  
Primary entrypoint: `python tools/uos.py`  
Low-level primitive: `python tools/canonical_publish.py`

## Purpose

QUICKBOARD first proved UOS lifecycle correctness inside one shared working tree. The next requirement is to let several Agents operate from independent clones of the **same UOS repository** while Git remains the canonical arbiter.

The design is extracted from the proven AI_book latest-canonical/Main Ref Gate idea, but the standalone implementation intentionally omits AI_book-specific project namespaces, historical Grant compatibility, workflow dependencies and runtime history.

This does **not** enable multi-repository orchestration. It only changes how several clones of this one repository agree on canonical state.

## Two layers

### 1. `tools/canonical_publish.py`

Low-level explicit-path CAS primitive:

- latest canonical fetch;
- Repository Identity remote / branch gate;
- non-force push only;
- create-if-absent;
- expected-blob replacement;
- expected-blob-protected deletion;
- multi-path tree transaction;
- default no-clobber;
- ref-race rebuild/retry.

The hardened primitive suite passed **7/7** against temporary bare Git remotes and independent clones.

### 2. `tools/canonical_runner.py`

High-level lifecycle integration used by `tools/uos.py` in `git-cas` mode.

Each attempt does:

```text
fetch latest origin/main
        ↓
verify canonical identity / branch
        ↓
create isolated detached worktree at exact main@X
        ↓
run complete deterministic UOS command locally
        ↓
produce candidate tree
        ↓
normal non-force push to main
        ↓
ref race?
  no  → canonical fact
  yes → throw away candidate/worktree
        fetch new main@Y
        rerun the whole UOS command from Y
```

The key distinction is that a race causes **re-execution**, not stale candidate re-parenting.

## Why lifecycle replay matters

For source-of-truth commands such as Project Init, Task Publish, Claim, Renew and Complete, replay means all preconditions are reevaluated against latest canonical state.

For derived `reconcile` state, replay is mandatory:

```text
main@X → calculate runtime-X
             ↓
          push loses race
             ↓
main@Y → discard runtime-X
             ↓
          recalculate runtime-Y
```

A stale derived view is never rebased onto newer main.

## `tools/uos.py` transport selection

```text
auto | local | git-cas
```

`auto` is the default:

- no configured remote → local same-working-tree mode;
- configured canonical remote → git-cas;
- configured remote becomes unavailable → fail closed, never create local fallback ownership.

Examples:

```bash
python tools/uos.py claim --agent-id AGENT_001 --project DEMO
python tools/uos.py --transport git-cas reconcile
python tools/uos.py --transport local status
```

## Completion transaction

The Agent creates the declared task output in its own workspace, then runs:

```bash
python tools/uos.py complete \
  --agent-id AGENT_001 \
  --task TASK_X \
  --lease-token <TOKEN>
```

The canonical runner:

1. fetches latest canonical state;
2. finds TASK_X's declared outputs from that canonical catalog;
3. refuses to overwrite a different canonical artifact at the same output path;
4. copies caller-owned output into the isolated snapshot;
5. runs current owner/token/fencing checks there;
6. creates `.done` and removes Claim;
7. recomputes derived state;
8. publishes the resulting tree in one canonical commit.

Declared outputs are force-staged in the clean isolated worktree, so a `.gitignore` rule cannot produce a `.done` without its required artifact.

## Repository Identity

The standalone upstream identity anchors:

```text
Canonical.Repository: https://github.com/ZXYHtech/UOS
Canonical.DefaultBranch: main
```

A different remote or branch is rejected before canonical mutation. Forks/independent installations must reinitialize identity rather than inheriting upstream authority.

## Regression coverage

### Primitive suite

`tests/test_canonical_publish.py` verifies:

1. disjoint concurrent writes both survive;
2. create-if-absent Claim has one winner;
3. output + `.done` + Claim deletion are atomic;
4. stale expected-blob replacement is fenced;
5. same-path conflict does not clobber;
6. unchecked deletion is refused;
7. wrong canonical target is refused.

### Integrated lifecycle suite

`tests/test_git_cas_lifecycle.py` verifies the actual `tools/uos.py` entrypoint for:

1. independent-clone unique Claim;
2. complete + Claim release through auto transport;
3. completion output that matches `.gitignore` is still canonical;
4. concurrent task publication replays from latest catalog;
5. reconcile main-ref race recomputes from the newer catalog;
6. unchanged status is a canonical no-op;
7. configured remote loss fails closed without local Claim fallback.

All suites are discovered by:

```bash
python tools/selftest.py
```

## Evidence status

The low-level CAS primitive was executed against local bare Git and passed 7/7 before lifecycle integration.

The integrated lifecycle code and regression suite are now committed, but this chat runtime cannot resolve `github.com`, so a normal fresh-clone execution of the exact committed integrated version is still pending. Do not convert that missing execution evidence into a claimed PASS.

## Still out of scope

- AI_book dispatch;
- external project repository adapters;
- one UOS controlling several repositories;
- cross-repository ownership/failure isolation;
- provider-specific CI as a correctness requirement.

The current target remains: **many Agents / many clones, one UOS repository, one canonical Git truth.**
