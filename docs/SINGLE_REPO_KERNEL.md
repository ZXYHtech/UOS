# UOS Single-Repository Pilot Kernel

## Scope

This kernel exists only for the current `SAME_REPOSITORY` pilot. It manages projects, tasks, claims and completion whose canonical files and outputs all live inside one working repository.

It MUST NOT be interpreted as activation of AI_book integration, cross-repository task routing, or multi-repository orchestration. Those remain blocked by `docs/CURRENT_PHASE.md`.

## Pilot lifecycle

```text
project init
-> task publish
-> reconcile/status
-> claim
-> work
-> renew (if needed)
-> complete
-> reconcile
-> next task
```

## Durable objects

- project source: `orchestration/projects/<PROJECT_ID>/PROJECT.yaml`
- task source: `orchestration/projects/<PROJECT_ID>/TASK_CATALOG.csv`
- active ownership: `coordination/claims/<TASK_ID>.lock`
- completion: `coordination/completed/<TASK_ID>.done`
- derived view: `coordination/runtime/TASK_STATUS.csv`
- derived summary: `coordination/runtime/STATUS.json`

Creating or publishing a task never creates ownership. Only `claim` creates a lock.

## Ownership / recovery invariants

1. A live task has at most one current lock.
2. The lock carries `AgentID`, `LeaseGeneration`, `LeaseToken`, `LeaseExpiresAt` and `FencingToken`.
3. A non-expired lock cannot be replaced by another Agent.
4. An expired lock may be reclaimed with `LeaseGeneration + 1` and a new token.
5. Renew and Complete require the current AgentID + LeaseToken and reject stale owners/tokens.
6. `.done` wins over any stale claim state.
7. Completion verifies declared output paths unless an explicit diagnostic override is used.

## Concurrency boundary

The first implementation uses an atomic repository-local mutex and is intended for Agents sharing one canonical working tree during the single-repository pilot. It deliberately does not claim distributed multi-clone/main-ref CAS correctness.

Before UOS is allowed to orchestrate independent repositories/clones, this boundary must be replaced or wrapped by the provider-neutral latest-canonical Git CAS transaction model already proven in the earlier UOS baseline.

## Validation already performed before repository integration

An isolated synthetic harness validated:

- `reconcile -> claim -> complete -> dependent task becomes READY -> next claim`;
- 10 concurrent contenders for one READY task produced exactly 1 successful owner and 1 lock;
- after forced lease expiry, reclaim produced generation 2 with a fresh token;
- the previous owner/token was rejected by the fencing check.

These are pre-integration tests. Repository acceptance still requires running the committed kernel from a fresh clone and completing QUICKBOARD through the actual UOS lifecycle.
