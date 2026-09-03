# TRAVEL_GUIDE Agent Claim Diagnosis — 2026-09-03

## Executive conclusion

The multi-Agent failure is real and comes from **four independent state/configuration mismatches**. The project has produced substantial travel-guide outputs, but those outputs were not advanced through the canonical UOS Claim -> Complete state machine. As a result, UOS still sees the project almost at its starting line.

### Canonical task accounting

- Project hard limit: **50 canonical tasks**.
- `PROJECT.yaml` currently declares `CurrentPlannedTaskCount: 24`.
- `TASK_CATALOG.csv` contains **24 canonical tasks**, not 50.
- Current canonical completion evidence for `TRAVEL_GUIDE`: **0 `.done` records** under `coordination/completed/`.
- Therefore, from UOS's point of view, **24 / 24 canonical tasks remain**.
- The previously described “50/50” refers to **book/research work units/articles**, not canonical UOS tasks. That was a terminology/state-accounting error and must not be repeated.
- There is room for **26 additional canonical tasks** while staying within the project ceiling of 50.

## Why other Agents cannot claim work

### Blocker 1 — dependency graph has never advanced

`tools/uos.py::effective_states()` derives state from `.done` records and dependencies. It does **not** infer completion from the existence of output files.

Current graph:

- `TASK_TRAVEL_GUIDE_INTAKE_01`: no dependency -> effectively READY.
- Almost every Wave-1 research task depends on `TASK_TRAVEL_GUIDE_INTAKE_01` -> effectively BLOCKED until its canonical `.done` exists.
- Downstream synthesis/delivery tasks are therefore also BLOCKED.

Because no `TRAVEL_GUIDE` `.done` files exist, the Work Market cannot expose the intended parallel research wave.

### Blocker 2 — default Agent matching envelope cannot even match the only READY task

`tools/agent_matching.py` defaults are:

- capability tier = 1
- tools = empty
- context = S

The intake task requires:

- min capability tier = 3
- context class = M
- tool requirement = web

Therefore an Agent launched with the default `agent_matching.py claim` envelope will return `NO_COMPATIBLE_READY_TASK` even though the intake task is technically READY.

A compatible envelope must explicitly declare at least the task's tier/context/tools. Example:

```bash
python tools/agent_matching.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  claim \
  --agent-id AG_TRAVEL_ARCHITECT \
  --capability-tier 4 \
  --tools web \
  --context L \
  --project TRAVEL_GUIDE \
  --task TASK_TRAVEL_GUIDE_INTAKE_01
```

### Blocker 3 — project one-confirmation policy is documentation only; canonical runner still uses global 3-result warmup

The project file says:

- `OperatorWarmupRequired: 1`
- `OperatorWarmupStatus: SATISFIED`
- `PostWarmupMode: PARALLEL_ALLOWED_WITH_SAMPLING_AND_HIGH_RISK_REVIEW`

But code search shows these project-level keys are not consumed by the canonical runner.

`tools/canonical_runner.py::_warmup_serial_block()` loads `.uos/QUALITY_VISIBILITY_POLICY.yaml`, whose current global policy is:

- `WarmupRequired: 3`
- `WarmupMaxConcurrentClaims: 1`
- `BlockNewClaimsWhilePending: true`

It counts accepted quality events for the RuleEpoch and active claim locks repository-wide. Therefore the current executable behavior is still **serialized warmup**, even though the TRAVEL_GUIDE project documentation says the one-confirmation checkpoint is satisfied.

This is a kernel/config integration bug: **the project override is not wired into execution**.

### Blocker 4 — content production and canonical orchestration drifted apart

A large amount of research, maps, PDFs and web-book content was created outside the canonical Claim/Lease/Fencing/Complete path. The artifacts are useful, but canonical UOS state does not automatically infer task completion from those files. This caused two parallel realities:

1. content layer: many outputs already exist;
2. orchestration layer: 24 tasks still appear unfinished.

The fix must not fabricate `.done` records after the fact. Recovery should preserve canonical ownership rules.

## Additional issue — the project is too coarse for the requested 50-task, multi-Agent research style

The original catalog has only 24 broad tasks. Several research tasks are very large (all geography/transport in one task, all history/culture in one task, all reviews in one task, etc.). That shape is incompatible with the operator's request to treat the project like a book and let several Agents independently deepen locations and evidence.

Recommended use of the remaining 26 task slots:

- 12 location dossiers: station, Gate 1, Fulong Temple, Baopingkou, Feishayan, Yuzui, Anlan Bridge, Erwang Temple, Qinyan Tower/Gate 6, Guanxian Old City, Nanqiao, Lidui Park Station;
- 3 food dossiers: formal courtyard meal, quiet old-city meal, representative snack/noodle;
- 4 field-operation tasks: facilities/toilets/rest, AMap travel-time matrix, return-train matrix, rain/crowd fallback;
- 3 evidence tasks: recent reviews, visitor-profile evidence audit, seasonality evidence audit;
- 4 integration tasks: source audit, search index, book editor, web/mobile QA.

That produces exactly **24 + 26 = 50 canonical tasks** while preserving the ceiling.

## Recovery plan

### Phase A — restore canonical claimability

1. Do not create synthetic `.done` records.
2. Wire the project-level warmup override into the canonical runner, scoped only to projects whose project YAML explicitly says the one-confirmation warmup is satisfied.
3. Publish/adjust the 26 book-depth tasks so public evidence tasks are independently claimable and do not all sit behind a single intake bottleneck.
4. Keep private/high-risk tasks behind privacy-audit dependencies.
5. Reconcile Work Market.

### Phase B — standardize Agent launch envelope

Public research Agents should normally use:

```text
capability-tier: 4
context: L
tools: web
project: TRAVEL_GUIDE
ack-execution-epoch: UOS_EXEC_20260902_01
```

Agents needing artifact processing may additionally declare `python`; private/review tasks must use their stronger tool/context requirements.

### Phase C — parallel book expansion

Once the claim gate is fixed, steady state should be 4-5 concurrent Agents:

- GEO/MAP
- HISTORY/CULTURE
- REVIEWS/NEWS
- FOOD/DATA
- FIELD/BOOK
- optional REVIEW

## Expected healthy state after recovery

- Canonical tasks: 50 maximum.
- Immediate READY pool after publication: multiple independent public research/book tasks, not a single intake task.
- Active concurrency: 4-5 public Agents after the already-satisfied project warmup.
- Private tasks remain dependency-gated and encrypted.
- UOS task counts and book work-unit counts use separate names and are never conflated again.
