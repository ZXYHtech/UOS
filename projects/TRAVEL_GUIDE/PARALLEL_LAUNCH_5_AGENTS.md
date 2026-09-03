# TRAVEL_GUIDE — 5-Agent Parallel Launch

Status: READY FOR PARALLEL CLAIMS

The Work Market has been CI-verified to expose 23 READY tasks in `TRAVEL_GUIDE_DEPTH`.

## Common startup rule

Every Agent must:

1. Work in `ZXYHtech/UOS` on latest `main`.
2. Read `projects/TRAVEL_GUIDE/AGENT_CLAIM_GUIDE.md` and the claimed row in `orchestration/projects/TRAVEL_GUIDE_DEPTH/TASK_CATALOG.csv`.
3. Claim through canonical UOS; never edit a task before Claim succeeds.
4. Preserve the returned `LeaseToken`.
5. Produce only the declared output for that task unless the task explicitly requires supporting files.
6. Complete through `tools/uos.py complete` using the same Agent ID and LeaseToken; do not manufacture `.done` files.
7. After successful completion, claim the next task in its assigned sequence.
8. Keep `TRAVEL_GUIDE_DEPTH` public-only: no exact private origin/date, relationship details, gift staging, or private chat scripts.

## Agent 1 — transit and map facts

Agent ID: `AG_TRAVEL_TRANSIT_MAP`

Suggested task sequence:

1. `TASK_TRAVEL_SPOT_DUJIANGYAN_STATION_01`
2. `TASK_TRAVEL_SPOT_GATE1_01`
3. `TASK_TRAVEL_SPOT_LIDUI_STATION_01`
4. `TASK_TRAVEL_FIELD_AMAP_MATRIX_01`
5. `TASK_TRAVEL_FIELD_RETURN_RAIL_01`

Initial claim:

```bash
python projects/TRAVEL_GUIDE/tools/claim_depth.py \
  --agent-id AG_TRAVEL_TRANSIT_MAP \
  --task TASK_TRAVEL_SPOT_DUJIANGYAN_STATION_01
```

## Agent 2 — hydraulic history and core sights

Agent ID: `AG_TRAVEL_CULTURE_REVIEWS`

Suggested task sequence:

1. `TASK_TRAVEL_SPOT_FULONG_01`
2. `TASK_TRAVEL_SPOT_BAOPINGKOU_01`
3. `TASK_TRAVEL_SPOT_FEISHAYAN_01`
4. `TASK_TRAVEL_SPOT_YUZUI_01`
5. `TASK_TRAVEL_SPOT_ANLAN_01`
6. `TASK_TRAVEL_SPOT_ERWANG_01`
7. `TASK_TRAVEL_SPOT_QINYAN_01`
8. `TASK_TRAVEL_SPOT_OLDCITY_01`
9. `TASK_TRAVEL_SPOT_NANQIAO_01`

Initial claim:

```bash
python projects/TRAVEL_GUIDE/tools/claim_depth.py \
  --agent-id AG_TRAVEL_CULTURE_REVIEWS \
  --task TASK_TRAVEL_SPOT_FULONG_01
```

## Agent 3 — food and meal evidence

Agent ID: `AG_TRAVEL_FOOD_DATA`

Suggested task sequence:

1. `TASK_TRAVEL_FOOD_XIAOZHUO_01`
2. `TASK_TRAVEL_FOOD_XIJIE_01`
3. `TASK_TRAVEL_FOOD_ZHAOMAI_01`

Initial claim:

```bash
python projects/TRAVEL_GUIDE/tools/claim_depth.py \
  --agent-id AG_TRAVEL_FOOD_DATA \
  --task TASK_TRAVEL_FOOD_XIAOZHUO_01
```

## Agent 4 — field operation and resilience

Agent ID: `AG_TRAVEL_FIELD_BOOK`

Suggested task sequence:

1. `TASK_TRAVEL_FIELD_FACILITIES_01`
2. `TASK_TRAVEL_FIELD_RAIN_CROWD_01`

Initial claim:

```bash
python projects/TRAVEL_GUIDE/tools/claim_depth.py \
  --agent-id AG_TRAVEL_FIELD_BOOK \
  --task TASK_TRAVEL_FIELD_FACILITIES_01
```

## Agent 5 — evidence audit

Agent ID: `AG_TRAVEL_EVIDENCE_REVIEW`

Suggested task sequence:

1. `TASK_TRAVEL_REVIEWS_2026_DEEP_01`
2. `TASK_TRAVEL_PROFILE_EVIDENCE_AUDIT_01`
3. `TASK_TRAVEL_SEASON_EVIDENCE_AUDIT_01`
4. `TASK_TRAVEL_POI_SOURCE_AUDIT_01`

Initial claim:

```bash
python projects/TRAVEL_GUIDE/tools/claim_depth.py \
  --agent-id AG_TRAVEL_EVIDENCE_REVIEW \
  --task TASK_TRAVEL_REVIEWS_2026_DEEP_01
```

## Completion command pattern

Use the `LeaseToken` returned by Claim:

```bash
python tools/uos.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  complete \
  --agent-id <AGENT_ID> \
  --task <TASK_ID> \
  --lease-token <LEASE_TOKEN> \
  --result PASS
```

If the current execution epoch changes, run `python tools/uos.py boot` and use the current epoch instead of the example above.

## Integration after the 23 public depth tasks

When all 23 public depth tasks are canonically DONE, UOS will expose:

1. `TASK_TRAVEL_BOOK_SEARCH_INDEX_01`
2. then `TASK_TRAVEL_BOOK_EDITOR_V6_01`
3. then `TASK_TRAVEL_BOOK_FINAL_SOURCE_QA_01`

Do not start these early by bypassing dependencies.
