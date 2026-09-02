# TRAVEL_GUIDE Five-Scheme Architecture V1

## Shared constraints

- Two adults, one-day Chengdu-area suburban-rail trip.
- Paid Dujiangyan Scenic Area is included in all base schemes.
- Moderate walking; avoid turning 15,000 steps into a quota.
- One formal seated meal plus limited local snack/dessert sampling.
- Base cash-spend target remains <= CNY 500 for two.
- No Qingcheng Mountain / Panda Valley / remote-attraction stacking.
- Exact private travel date, exact departure schedule, relationship-specific timing and scripts remain outside this plaintext file.
- All maps follow `MAP_VALIDATION_POLICY.md` and the AI prompt -> image -> receipt -> verify loop.

## Scheme A — Classic Balanced / 经典均衡型

### Core idea
The safest first-time recommendation: understand the hydraulic system, see the signature river/bridge landscape, then transition into Guanxian old city for food and evening atmosphere.

### Public route skeleton
**Xipu -> Lidui Park station -> Dujiangyan Scenic Area main/Park-Road side -> Fulong/Baopingkou -> Feishayan -> Yuzui -> Anlan Bridge (if crowd/energy good) -> exit toward central old-city side -> Guanxian Ancient City -> formal Sichuan meal -> Nanqiao -> verified late rail return**

### Time allocation logic
- heritage core: ~3-4 h including explanation/rest;
- old city + meal + evening: ~3-4 h;
- substantial buffer for station transfer / navigation / fatigue.

### Walking
Medium, roughly 13k-16k steps depending on internal detours.

### Tradeoff
Broadest experience, but not the deepest on any single theme.

## Scheme B — Hydraulic History Depth / 水利历史深度型

### Core idea
Make the engineering/history itself the main experience rather than treating the scenic area as a photo park.

### Preferred route skeleton — conditional gate validation
**Xipu -> Lidui Park station -> verified local transfer to an upper/east-side entrance if current access is confirmed -> Qinyanlou/upper heritage viewpoint -> Erwang Temple -> Anlan Bridge -> Yuzui -> Feishayan -> Baopingkou/Fulong -> old-city edge -> compact formal meal -> Nanqiao -> rail return**

The upper/east-side start is **conditional**. Before map generation, current entrance name, opening/access and actual local transfer must be verified. If that validation fails, Scheme B switches to a main-gate route while preserving the deeper interpretation and extra temple/hillside time.

### Time allocation logic
- heritage / interpretation: ~4-5 h;
- food / evening: shorter but still includes one seated meal.

### Walking
Medium-high, with more elevation than other schemes.

### Tradeoff
Best cultural depth; highest fatigue risk and least food-wandering time.

## Scheme C — Food + Guanxian Old City / 美食古城型

### Core idea
See the hydraulic must-sees efficiently, then spend more of the day in the living urban fabric around Guanxian Ancient City / Nanqiao.

### Public route skeleton
**Xipu -> Lidui Park station -> Dujiangyan Scenic Area main side -> Baopingkou -> Feishayan -> Yuzui -> choose Anlan Bridge only if low queue -> return/exit toward old city -> small savory local snack -> Guanxian Ancient City slow walk -> dessert/rest -> formal local Sichuan meal -> Nanqiao/riverfront -> rail return**

### Food structure
- one representative savory tasting;
- one sweet/cooling rest item;
- one proper seated meal;
- do not chase every famous shop.

### Walking
Medium; later part is flatter/urban and easier to shorten.

### Tradeoff
Strongest everyday atmosphere and food variety; gives up some hillside heritage nodes.

## Scheme D — Relaxed Connection / 舒适低赶路型

### Core idea
Protect energy, seated time and unstructured shared experience. Fewer attractions are treated as a feature, not a failure.

### Public route skeleton
**Xipu -> Lidui Park station -> scenic-area main side -> Baopingkou -> Feishayan -> Yuzui -> optional Anlan Bridge only if energy/crowd good -> exit -> long formal meal -> short old-city walk -> quiet dessert/tea rest -> Nanqiao/riverfront -> rail return**

### Cut rules
- no mandatory Erwang Temple climb;
- skip a photo queue immediately if it exceeds the planned pause;
- use local vehicle/shorter link if heat/rain/fatigue makes walking quality poor;
- old-city section can be shortened without damaging the core experience.

### Walking
Medium-low to medium, roughly 11k-14k steps before optional additions.

### Tradeoff
Lowest sightseeing count but strongest comfort margin.

## Scheme E — Weather / Crowd Resilient / 天气人流弹性型

### Core idea
A decision-tree plan rather than one brittle sequence.

### Branch 1 — good weather + manageable crowd
Use a shortened Scheme A core, then preserve flexible meal/rest time.

### Branch 2 — rain or heat spike in the morning
Use the central old-city / seated meal / covered-rest block first only if current ticket/entry windows leave sufficient safe time; enter the scenic core after conditions improve and keep only Baopingkou -> Feishayan -> Yuzui essential sequence.

### Branch 3 — scenic entry/crowd-control problem
Wait in the central old-city cluster rather than adding remote attractions; recheck official access; if entry becomes impractical, do not invent an unauthorized alternative gate.

### Return resilience
Keep both Lidui Park and Dujiangyan railway station as candidates until the final exact-date schedule/availability check. Choose the station that gives the best evening margin after the actual final stop.

### Walking
Variable with explicit cut points.

### Tradeoff
Least visually elegant fixed route, but highest robustness.

## Preliminary ranking before exact-date refresh

1. **Scheme D** — best fit for comfort and sustained interaction while still delivering the first-time essentials.
2. **Scheme A** — strongest generic first-time recommendation and easiest to explain/execute.
3. **Scheme C** — best if food/old-city interest becomes clearly stronger.
4. **Scheme B** — best for a traveler who actively enjoys history/engineering and accepts more walking/elevation.
5. **Scheme E** — fallback architecture; may become #1 if weather/crowd conditions deteriorate.

This ranking is public planning logic only. The final private recommendation can incorporate encrypted interpersonal context and exact-date conditions.

## Required scheme-specific map facts before image generation

For each A-E:

1. chosen arrival station;
2. exact verified entrance/exit name;
3. ordered scenic nodes;
4. whether Erwang Temple / Anlan Bridge is mandatory or optional;
5. old-city and Nanqiao connection;
6. exact formal-meal anchor after live business verification;
7. walking vs local-vehicle segments;
8. expected segment durations;
9. prohibited obsolete/ambiguous names;
10. map-fact refresh date.
