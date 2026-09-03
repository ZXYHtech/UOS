# AI_book → UOS Claim Concurrency Delta Sync Report

Date: 2026-09-03
Status: PHASE-1 BACKPORT COMPLETE

## Executive conclusion

The standalone UOS repository already had latest-canonical Git CAS replay/recompute semantics in `tools/canonical_runner.py`. The production gap exposed by `TRAVEL_GUIDE_DEPTH` was narrower but important: AI_book's exact-task high-contention ingress had not been fully carried over.

The missing behavior was:

1. bounded random startup jitter for explicit Task claims;
2. read-only fetch of latest canonical state before constructing a claim transaction;
3. latest canonical lock preflight;
4. active owner => local `NO_MATCH` with zero canonical write;
5. only a compatible READY task proceeds into the normal CAS transaction;
6. a higher retry budget for burst contention.

This behavior is now available generically in `tools/high_contention_claim.py`. `projects/TRAVEL_GUIDE/tools/claim_depth.py` is only a thin project envelope around that Kernel ingress.

## What was already synchronized before this incident

- latest-canonical detached-worktree Git CAS transactions;
- ref race => discard stale candidate and rerun command from the new canonical snapshot;
- canonical Claim lock;
- LeaseToken / LeaseGeneration / fencing checks;
- stale lock reclaim primitive;
- deterministic Work Market / Task Status reconcile;
- ExecutionEpoch critical-command gate;
- project-scoped quality visibility / warmup override;
- canonical Complete + `.done` + durability receipt.

Therefore it was incorrect to describe standalone UOS as lacking Git CAS entirely. The issue was high-contention ingress and write amplification during simultaneous explicit claims.

## Phase-1 backport completed

### Generic Kernel ingress

`tools/high_contention_claim.py`

Properties:

- exact Task only;
- default jitter: 0–3000 ms, matching the production idea used by AI_book;
- capability/context/tool compatibility checked from latest canonical Work Market without first publishing a `status` transaction;
- latest canonical lock checked read-only;
- active lock returns `NO_MATCH` / `canonical_write=NONE`;
- stale lock is allowed to reach normal UOS reclaim logic;
- normal ownership remains exclusively in `tools/uos.py`;
- default inner CAS retries raised to 20 for this high-contention ingress;
- bounded outer retry for transient canonical ref races.

### TRAVEL_GUIDE adapter

`projects/TRAVEL_GUIDE/tools/claim_depth.py`

The former project-local retry implementation was removed. It now only supplies:

- Agent ID;
- explicit Task ID;
- project `TRAVEL_GUIDE_DEPTH`;
- capability tier 4;
- tools `web;python`;
- context XL;
- lease duration.

It delegates contention behavior and canonical ownership to generic Kernel tools.

## Production-style contention acceptance

Workflow: `.github/workflows/uos-high-contention-claim.yml`

Test: `tests/test_high_contention_claim.py`

Acceptance scenario intentionally matches the incident that affected `AG_TRAVEL_FOOD_DATA`:

- independent Git clones;
- Agents claim different explicit tasks at the same time;
- all tasks are READY;
- all Agents must obtain distinct canonical locks;
- every lock must contain owner, LeaseGeneration and LeaseToken;
- no task may be lost due only to canonical branch contention.

Matrix results on 2026-09-03:

- 5 Agents / 5 distinct tasks: PASS
- 10 Agents / 10 distinct tasks: PASS
- 30 Agents / 30 distinct tasks: PASS

GitHub Actions run: `33709893514`, conclusion `success`.

## Still not fully backported from AI_book

Phase 1 fixes the immediate multi-Agent startup problem, but the following AI_book production mechanisms are not yet declared synchronized:

1. persistent Claim Request + Claim Grant as a second immutable ownership anchor;
2. Remote Claim Broker V2 CREATE/RECLAIM ingress;
3. exact-SHA broker reclaim tickets and Claim Integrity scan;
4. Work Session integration around repeated automatic next-task acquisition;
5. provider-neutral observation metrics for claim request→grant latency and broker throughput;
6. publish/integration queue concepts for very high write volume.

These must be backported only as generic `KERNEL_SYNC` artifacts. AI_BOOK task history, project-specific quality rules, runtime locks, grants and `.done` files must never be copied into UOS.

## Operational rule until Phase 2

For explicit high-contention project tasks, use the project helper when one exists, or generic:

```bash
python tools/high_contention_claim.py \
  --agent-id <AGENT_ID> \
  --task <TASK_ID> \
  --project <PROJECT_ID> \
  --capability-tier <N> \
  --tools '<tool1;tool2>' \
  --context <S|M|L|XL>
```

Ownership still means only: command returns GRANTED and matching canonical lock exists.

## Next Kernel sync phase

P2 claim integrity backport should add Grant anchoring without introducing a second scheduler:

`exact preflight → canonical transaction → Request/Grant + Lock → fencing checkpoint → Complete`

Acceptance before declaring that phase complete:

- same-task 30-contender uniqueness;
- distinct-task 30-Agent all-success;
- stale reclaim generation increment;
- old-token fencing rejection after reclaim;
- no Request/Grant write from preflight losers;
- restart from current ExecutionEpoch.
