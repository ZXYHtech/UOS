# TRAVEL_GUIDE Agent Claim Guide

## Status

Multi-Agent claim recovery is now active.

The logical TRAVEL_GUIDE project family contains:

- 24 legacy canonical tasks under `TRAVEL_GUIDE`;
- 26 book-depth canonical tasks under child project `TRAVEL_GUIDE_DEPTH`;
- total canonical task budget used: **50 / 50**.

The child project exists only to recover clean parallel claimability without fabricating `.done` records or rewriting the old dependency graph.

## Project-level warmup repair

`tools/canonical_runner.py` and `tools/quality_gate.py` now honor an explicit project-level operator policy when all of the following are true:

- `OperatorReviewPolicy: ONE_CONFIRMATION_THEN_CONTINUE`
- `OperatorWarmupRequired: 1`
- `OperatorWarmupStatus: SATISFIED`
- `PostWarmupMode` begins with `PARALLEL_ALLOWED`

For those projects only the RuleEpoch warmup is bypassed. Deterministic sampling and HIGH-risk review still apply.

Both `TRAVEL_GUIDE` and `TRAVEL_GUIDE_DEPTH` declare the satisfied one-confirmation policy.

## Fastest claim method

For each new public research Agent run:

```bash
python projects/TRAVEL_GUIDE/tools/claim_depth.py --agent-id <UNIQUE_AGENT_ID>
```

The helper automatically supplies:

- current ExecutionEpoch acknowledgement;
- project `TRAVEL_GUIDE_DEPTH`;
- capability tier 4;
- tools `web;python`;
- context `XL`;
- normal canonical Claim/Lease/Fencing path through `agent_matching.py` and `uos.py`.

To claim a specific task:

```bash
python projects/TRAVEL_GUIDE/tools/claim_depth.py \
  --agent-id AG_TRAVEL_TRANSIT_MAP \
  --task TASK_TRAVEL_SPOT_DUJIANGYAN_STATION_01
```

## Suggested five-Agent launch

Use five separate Agent sessions and unique IDs:

```text
AG_TRAVEL_TRANSIT_MAP
AG_TRAVEL_CULTURE_REVIEWS
AG_TRAVEL_FOOD_DATA
AG_TRAVEL_FIELD_BOOK
AG_TRAVEL_EVIDENCE_REVIEW
```

Each session runs the helper once; canonical Claim races decide ownership safely. If two Agents race for the same best task the loser refreshes the Work Market and selects another compatible READY task.

## Current public READY pool

The first 23 `TRAVEL_GUIDE_DEPTH` tasks have no canonical dependencies and are intended to be independently READY:

- 12 location dossiers;
- 3 food dossiers;
- 4 field-operation tasks;
- 4 review/evidence tasks.

The last 3 tasks are intentionally dependent:

- book search index;
- V6 book editor;
- final source/mobile QA.

## Execution epoch

Current required acknowledgement is still:

```text
UOS_EXEC_20260902_01
```

The helper reads the current epoch automatically so Agents normally do not need to type it.

## Manual claim envelope

If an Agent does not use the helper:

```bash
python tools/agent_matching.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  claim \
  --agent-id <AGENT_ID> \
  --capability-tier 4 \
  --tools 'web;python' \
  --context XL \
  --project TRAVEL_GUIDE_DEPTH
```

## Private Agent rule

`TRAVEL_GUIDE_DEPTH` is public-only. It must never receive exact private origin/date text; relationship context; gift staging; or private chat scripts.

Private artifacts remain under the legacy `TRAVEL_GUIDE` privacy workflow and require encrypted canonical storage.

## Completion rule

Creating a Markdown/PDF/web artifact is not task completion by itself. Every Agent must finish through canonical `complete` with its LeaseToken so `.done` and quality evidence are created correctly.

Do not manually manufacture claim locks or `.done` files.
