# TRAVEL_GUIDE Deterministic Map Overlay Semantics V1

Purpose: define the canonical route semantics added after an AI geographic background passes QA. The overlay, not the AI background, owns operational truth.

## Shared overlay rules

- North is up.
- Private home origin is never plotted.
- Public rail origin label: 犀浦站.
- Preferred central arrival/departure label: 离堆公园站 unless the final T-minus-1 transport refresh selects another return station for resilience.
- Station icon appears once per map unless the final exact-date return plan explicitly uses a different verified return station; if so, that exception must be clearly labeled and justified.
- Route line classes: rail = dark dashed; local car/taxi = medium dashed secondary line; walk = solid primary line; optional = thin dashed; cut/early-exit = distinct short dashed branch.
- Node labels and order are deterministic; no node is inferred from background decoration.
- Exact Chinese labels are added in vector text, never copied from AI-generated text.
- Source/refresh note added in final vector layer.

## Scheme A — Classic Balanced

Canonical order:
1. 犀浦站
2. 离堆公园站
3. 都江堰景区1号门 / 离堆侧入口
4. 宝瓶口
5. 飞沙堰
6. 鱼嘴
7. 安澜索桥（可选）
8. 返回景区南侧 / 古城过渡
9. 灌县古城
10. 正式正餐
11. 南桥
12. 离堆公园站
13. 犀浦站

Overlay requirement: scenic outbound and old-city return must be visually unambiguous; optional Anlan branch must not interrupt the main return path.

## Scheme B — Hydraulic History Depth

Canonical order:
1. 犀浦站
2. 离堆公园站
3. 出租车 / 本地车辆接驳
4. 秦堰楼6号门（出发前复核开放）
5. 秦堰楼
6. 二王庙
7. 安澜索桥
8. 鱼嘴
9. 飞沙堰
10. 宝瓶口
11. 景区1号门 / 离堆侧出口方向
12. 正式正餐
13. 南桥
14. 离堆公园站
15. 犀浦站

Overlay requirement: station-to-Gate-6 vehicle transfer must be unmistakably different from walking. Do not show Gate 4/5 unless a current official fallback is explicitly activated.

## Scheme C — Food + Guanxian Old City

Canonical order:
1. 犀浦站
2. 离堆公园站
3. 景区1号门
4. 宝瓶口
5. 飞沙堰
6. 鱼嘴
7. 安澜索桥（可选）
8. 返回古城方向
9. 地方小吃体验
10. 灌县古城慢行
11. 甜品 / 茶饮休息
12. 正式正餐
13. 南桥
14. 离堆公园站
15. 犀浦站

Overlay requirement: snack, dessert/tea and formal meal are three separate semantic nodes with distinct icons.

## Scheme D — Relaxed Connection

Canonical order:
1. 犀浦站
2. 离堆公园站
3. 景区1号门
4. 宝瓶口
5. 飞沙堰
6. 鱼嘴
7. 安澜索桥（弱可选）
8. 提前返回城市侧
9. 正式坐席用餐
10. 灌县古城短段
11. 安静甜品 / 茶饮休息
12. 南桥 / 河岸
13. 离堆公园站
14. 犀浦站

Overlay requirement: fewest mandatory nodes; meal and rest are separate and visually prominent; no Erwang Temple/Qinyan Tower branch.

## Scheme E — Weather / Crowd Resilient

Core order:
1. 犀浦站
2. 离堆公园站
3. 景区1号门
4. 宝瓶口
5. 飞沙堰

Decision branches from Feishayan area:
- Continue branch: 鱼嘴 -> 安澜索桥（更弱可选） -> city side.
- Early-exit branch: directly to sheltered/formal meal-rest node in central city cluster.

After either branch merges:
6. 餐饮 / 休息
7. 灌县古城（天气允许时可选）
8. 南桥（天气/人流舒适时可选）
9. 离堆公园站
10. 犀浦站

Overlay requirement: three route classes must be instantly distinguishable: core solid line, conditional continuation, early-exit cut branch. Do not encode actual rain probability or crowd percentage.

## Final overlay QA checklist

- exact node sequence matches this file and the current scheme fact sheet;
- no extra station or unverified gate;
- route arrows all agree with the intended travel sequence;
- label placement does not imply a false precise road location;
- food/rest nodes remain category-level until final merchant verification;
- optional and cut branches cannot be mistaken for mandatory route;
- mobile legibility at 100% width;
- final map includes refresh date and a short '示意路线，导航以实时地图为准' note in the vector layer.