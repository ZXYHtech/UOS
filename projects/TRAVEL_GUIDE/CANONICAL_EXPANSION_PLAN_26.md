# TRAVEL_GUIDE Canonical Expansion Plan — 26 Remaining Slots

The project currently publishes 24 canonical tasks and has a hard ceiling of 50. This plan uses the remaining **26 slots** to turn the book-depth work into genuinely claimable multi-Agent tasks.

## Immediate parallel public research — 23 tasks

These tasks should be publishable without waiting on the legacy intake `.done`, because their public input (`REQUIREMENTS_PUBLIC.md`, current map policy, public research baseline) already exists. They remain subject to normal Claim/Lease/Fencing and evidence requirements.

| # | Proposed ID | Owner type | Output |
|---:|---|---|---|
| 25 | TASK_TRAVEL_SPOT_DUJIANGYAN_STATION_01 | RESEARCHER | research/book/spots/DUJIANGYAN_STATION.md |
| 26 | TASK_TRAVEL_SPOT_GATE1_01 | RESEARCHER | research/book/spots/GATE1.md |
| 27 | TASK_TRAVEL_SPOT_FULONG_01 | RESEARCHER | research/book/spots/FULONG.md |
| 28 | TASK_TRAVEL_SPOT_BAOPINGKOU_01 | RESEARCHER | research/book/spots/BAOPINGKOU.md |
| 29 | TASK_TRAVEL_SPOT_FEISHAYAN_01 | RESEARCHER | research/book/spots/FEISHAYAN.md |
| 30 | TASK_TRAVEL_SPOT_YUZUI_01 | RESEARCHER | research/book/spots/YUZUI.md |
| 31 | TASK_TRAVEL_SPOT_ANLAN_01 | RESEARCHER | research/book/spots/ANLAN.md |
| 32 | TASK_TRAVEL_SPOT_ERWANG_01 | RESEARCHER | research/book/spots/ERWANG.md |
| 33 | TASK_TRAVEL_SPOT_QINYAN_01 | RESEARCHER | research/book/spots/QINYAN.md |
| 34 | TASK_TRAVEL_SPOT_OLDCITY_01 | RESEARCHER | research/book/spots/GUANXIAN_OLD_CITY.md |
| 35 | TASK_TRAVEL_SPOT_NANQIAO_01 | RESEARCHER | research/book/spots/NANQIAO.md |
| 36 | TASK_TRAVEL_SPOT_LIDUI_STATION_01 | RESEARCHER | research/book/spots/LIDUI_PARK_STATION.md |
| 37 | TASK_TRAVEL_FOOD_XIAOZHUO_01 | RESEARCHER | research/book/food/COURTYARD_MEAL.md |
| 38 | TASK_TRAVEL_FOOD_XIJIE_01 | RESEARCHER | research/book/food/QUIET_OLD_CITY_MEAL.md |
| 39 | TASK_TRAVEL_FOOD_ZHAOMAI_01 | RESEARCHER | research/book/food/REPRESENTATIVE_SNACK.md |
| 40 | TASK_TRAVEL_FIELD_FACILITIES_01 | RESEARCHER | research/book/field/FACILITIES.md |
| 41 | TASK_TRAVEL_FIELD_AMAP_MATRIX_01 | ANALYST | research/book/field/AMAP_TIME_MATRIX.md |
| 42 | TASK_TRAVEL_FIELD_RETURN_RAIL_01 | RESEARCHER | research/book/field/RETURN_RAIL_MATRIX.md |
| 43 | TASK_TRAVEL_FIELD_RAIN_CROWD_01 | PLANNER | research/book/field/RAIN_CROWD_DECISION_TREE.md |
| 44 | TASK_TRAVEL_REVIEWS_2026_DEEP_01 | RESEARCHER | research/book/evidence/REVIEWS_2026.md |
| 45 | TASK_TRAVEL_PROFILE_EVIDENCE_AUDIT_01 | REVIEWER | research/book/evidence/VISITOR_PROFILE_AUDIT.md |
| 46 | TASK_TRAVEL_SEASON_EVIDENCE_AUDIT_01 | REVIEWER | research/book/evidence/SEASONALITY_AUDIT.md |
| 47 | TASK_TRAVEL_POI_SOURCE_AUDIT_01 | REVIEWER | research/book/evidence/POI_SOURCE_AUDIT.md |

### Common acceptance standard for location dossiers

Each spot dossier should include:

- current canonical name and AMap link;
- stable vs dynamic facts;
- at least 800-1500 Chinese characters of useful detail;
- historical/cultural significance where relevant;
- suggested dwell time;
- previous/next-node realistic time range;
- best observation/interpretation position;
- recent visitor feedback themes;
- crowd/rain/fatigue fallback;
- toilet/rest/food relationship where relevant;
- source list with dates;
- no fake exact path when only a schematic route is known.

## Dependent integration — 3 tasks

| # | Proposed ID | Dependency idea | Output |
|---:|---|---|---|
| 48 | TASK_TRAVEL_BOOK_SEARCH_INDEX_01 | spot/food/field dossiers | web/BOOK_SEARCH_INDEX.json |
| 49 | TASK_TRAVEL_BOOK_EDITOR_V6_01 | all expansion evidence | book/BOOK_V6_MASTER.md + web V6 |
| 50 | TASK_TRAVEL_BOOK_FINAL_SOURCE_QA_01 | editor/search index | book/BOOK_V6_SOURCE_QA.md |

## Parallel topology after publication

- AG_TRAVEL_TRANSIT_MAP: 25, 26, 36, 41, 42
- AG_TRAVEL_CULTURE_REVIEWS: 27-35, 44
- AG_TRAVEL_FOOD_DATA: 37-39, 45-46
- AG_TRAVEL_FIELD_BOOK: 40, 43, 47, 48
- AG_TRAVEL_SYNTHESIS_VISUAL: 49
- AG_TRAVEL_REVIEW: 50

Steady-state target: **4-5 active Agents**, with one optional reviewer.

## Important

This file is a publication plan, not a second ownership system. These IDs become claimable only after they are actually published into the canonical `TASK_CATALOG.csv` through UOS-compatible publication/recovery work.
