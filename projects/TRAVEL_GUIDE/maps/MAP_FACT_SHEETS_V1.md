# TRAVEL_GUIDE — Scheme Map Fact Sheets V1

Refresh date: 2026-09-02

Purpose: authoritative pre-generation route facts for the five AI route-map renders. The renderer may simplify scale but must not invent roads, gates, bridges, station identity or stop order.

## Shared validated anchors

- Rail origin shown on public maps: Xipu / 犀浦. Do not plot the private home-origin point.
- Preferred central arrival: Lidui Park railway station / 离堆公园站. It is distinct from Dujiangyan railway station / 都江堰站.
- Dujiangyan Scenic Area Gate 1 / 都江堰景区1号门: current Amap place record, Gongyuan Road, treated as the main/south/Lidui-side entrance.
- Dujiangyan Scenic Area Gate 6 / 秦堰楼6号门: confirmed as a current named gate by a 2026-05-13 notice from Qingchengshan–Dujiangyan Scenic Area Administration; the notice only suspended this gate for one day on 2026-05-15 for gate-system work. Recheck before departure for any new notice.
- Core hydraulic nodes: Baopingkou / 宝瓶口, Feishayan / 飞沙堰, Yuzui / 鱼嘴分水堤.
- Cultural/hillside nodes: Anlan Bridge / 安澜索桥, Erwang Temple / 二王庙, Qinyan Tower / 秦堰楼.
- Urban/evening cluster: Nanqiao / 南桥 + Guanxian Ancient City / 灌县古城. These are close to the scenic-area/old-city transition and must not be drawn as remote attractions.

## Shared rendering constraints

1. Show a schematic route, not a fake GIS map.
2. Use numbered nodes and clean route arrows in the AI base render; exact Chinese labels may be added as a verified vector/text overlay later.
3. Distinguish rail, walking and optional local-car segments.
4. No exact private home-origin point.
5. No restaurant pin until the restaurant is separately verified as currently operating.
6. No unverified internal scenic-path geometry.
7. Do not merge Lidui Park station with Dujiangyan station.
8. Do not show a nonexistent subway line into the scenic area.
9. The final receipt must compare the rendered node order with the fact sheet and mark VERIFIED or REJECTED.

---

## Scheme A — Classic Balanced / 经典均衡型

Preferred arrival/departure: Lidui Park station.

Ordered operational sequence:
1. Xipu rail departure.
2. Lidui Park station arrival.
3. Short central-city access to Dujiangyan Scenic Area Gate 1.
4. Gate 1 / Lidui-side entry.
5. Baopingkou.
6. Feishayan.
7. Yuzui.
8. Anlan Bridge — optional if crowd/energy are acceptable.
9. Return/continue to scenic-area south/old-city side.
10. Guanxian Ancient City.
11. Formal-meal area in the verified old-city/central cluster — restaurant pin added later.
12. Nanqiao / riverfront evening stop.
13. Lidui Park station.
14. Rail return to Xipu.

Map emphasis: first-time orientation, hydraulic core first, old city + Nanqiao later.

## Scheme B — Hydraulic History Depth / 水利历史深度型

Preferred arrival/departure: Lidui Park station, with local-car transfer to Gate 6 for the start.

Ordered operational sequence:
1. Xipu rail departure.
2. Lidui Park station arrival.
3. Verified local-car/taxi segment to Qinyan Tower Gate 6.
4. Gate 6 / Qinyan Tower entry — departure-day notice check mandatory.
5. Qinyan Tower viewpoint.
6. Erwang Temple.
7. Anlan Bridge.
8. Yuzui.
9. Feishayan.
10. Baopingkou.
11. Exit on the Lidui/main-gate side.
12. Compact old-city edge / formal-meal area.
13. Nanqiao.
14. Lidui Park station.
15. Rail return to Xipu.

Fallback if Gate 6 is closed: use Gate 4 or Gate 5 only after same-day/current official verification; do not let the AI invent the fallback path.

Map emphasis: elevation/high-to-low narrative and engineering-history interpretation.

## Scheme C — Food + Guanxian Old City / 美食古城型

Preferred arrival/departure: Lidui Park station.

Ordered operational sequence:
1. Xipu.
2. Lidui Park station.
3. Gate 1.
4. Baopingkou.
5. Feishayan.
6. Yuzui.
7. Optional Anlan Bridge only if queue is modest.
8. Exit/return toward old-city side.
9. Small local-snack area in Guanxian Ancient City — no merchant pin yet.
10. Guanxian Ancient City slow-walk cluster.
11. Dessert/tea rest area — no merchant pin yet.
12. Formal meal in verified central/old-city cluster.
13. Nanqiao evening riverfront.
14. Lidui Park station.
15. Xipu.

Map emphasis: shorter heritage loop, more urban-food dwell time.

## Scheme D — Relaxed Connection / 舒适低赶路型

Preferred arrival/departure: Lidui Park station.

Ordered operational sequence:
1. Xipu.
2. Lidui Park station.
3. Gate 1.
4. Baopingkou.
5. Feishayan.
6. Yuzui.
7. Optional Anlan Bridge only if both energy and crowd conditions are good.
8. Exit toward central old-city side.
9. Long formal seated meal in verified central cluster.
10. Short Guanxian Ancient City walk.
11. Quiet dessert/tea rest in verified central cluster.
12. Nanqiao / riverfront.
13. Lidui Park station.
14. Xipu.

Map emphasis: fewer mandatory nodes, strong rest/meal nodes, easy cut points.

## Scheme E — Weather / Crowd Resilient / 天气人流容错型

Preferred arrival/departure: Lidui Park station.

Base ordered sequence:
1. Xipu.
2. Lidui Park station.
3. Gate 1.
4. Baopingkou.
5. Feishayan.
6. Yuzui if rain/crowd conditions permit.
7. Skip Anlan Bridge when slippery or heavily queued.
8. Exit to central old-city side earlier when needed.
9. Covered/indoor-leaning meal/rest node in central cluster.
10. Guanxian Ancient City short segment if weather allows.
11. Nanqiao only if rain/wind/crowd conditions are comfortable.
12. Lidui Park station.
13. Xipu.

Map emphasis: show solid-line core route plus clearly marked optional/cut branches; do not invent indoor attractions as weather substitutes.

## Source anchors

- Chengdu Municipal Government Dujiangyan destination page, 2026-04-29: current major scenic nodes.
- Qingchengshan–Dujiangyan Scenic Area Administration notice published 2026-05-13: Gate 6/Qinyan Tower gate identity and temporary one-day closure notice.
- Current Amap place record checked 2026-09-02: Dujiangyan Scenic Area Gate 1.
- Current map/business entities checked 2026-09-02: Dujiangyan Scenic Area, Nanqiao, Guanxian Ancient City, Dujiangyan station cluster.
- Current rail-search pages checked 2026-09-02: Xipu–Lidui Park direct suburban services and distinct Xipu–Dujiangyan services.

## Freshness gate

Before final map receipt becomes VERIFIED, refresh: exact departure-day rail availability, Gate 6 operation if Scheme B is selected, any temporary scenic closure, and the final restaurant/rest pins.