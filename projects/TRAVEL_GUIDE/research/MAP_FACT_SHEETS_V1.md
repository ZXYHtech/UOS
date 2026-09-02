# TRAVEL_GUIDE — Five Scheme Map Fact Sheets V1

Refresh baseline: 2026-09-02

This file converts the shared Dujiangyan map baseline into scheme-specific operational facts before AI route-map generation. It deliberately separates `VERIFIED`, `PLANNING_ESTIMATE`, and `CONDITIONAL` items so the image model does not invent geography.

## Shared verified anchors

- Xipu / 犀浦: Chengdu-side suburban-rail transfer origin for the public route skeleton.
- Lidui Park railway station / 离堆公园站: preferred central arrival candidate for scenic-area + Guanxian Ancient City day trips; separate from Dujiangyan railway station.
- Dujiangyan railway station / 都江堰站: alternate rail node, not interchangeable with Lidui Park station.
- Dujiangyan Scenic Area / 都江堰景区: ticketed heritage area.
- Main / Lidui Park side entrance: current mainstream visitor entrance on Gongyuan Road / Lidui Park side; use as the default entrance when an upper entrance is not independently validated.
- Baopingkou / 宝瓶口, Feishayan / 飞沙堰, Yuzui / 鱼嘴: three core hydraulic-system nodes.
- Anlan Suspension Bridge / 安澜索桥: scenic-area bridge node connecting toward the east-bank / temple side.
- Erwang Temple / 二王庙: hillside cultural node with additional climbing.
- Nanqiao / 南桥 and Guanxian Ancient City / 灌县古城: central evening / food / urban-atmosphere cluster outside the main hydraulic-core visit.

## Global map drawing constraints

1. Never merge Lidui Park station with Dujiangyan station.
2. Do not draw a subway line directly to the scenic area.
3. Do not place Nanqiao inside the Fish Mouth / Feishayan / Baopingkou hydraulic core.
4. Do not draw exact internal footpaths unless separately verified; use schematic connection arrows instead.
5. Do not invent a numbered entrance. The frequently shared `Qinyanlou / upper entrance / 6号门` advice is useful as a planning hypothesis but is not yet strong enough in the current source set to be treated as an authoritative operational map fact.
6. Restaurant names must not appear on the map until current operation and location are separately verified. Use `formal meal zone`, `snack zone`, or `tea/dessert rest zone` as area anchors in V1.
7. Exact home origin is private and must never appear on route images.

---

# Scheme A — Classic Balanced

## Intended stop order

Xipu -> Lidui Park station -> Dujiangyan Scenic Area main/Lidui-side entrance -> Fulong/Baopingkou area -> Feishayan -> Yuzui -> Anlan Bridge if queue and energy allow -> return toward main/central exit side -> Guanxian Ancient City -> formal meal zone -> Nanqiao -> Lidui Park station -> Xipu

## Status by segment

- Xipu -> Lidui Park station: VERIFIED transport relationship; exact train/time remains dynamic.
- Lidui Park station -> scenic-area main side: VERIFIED short central access relationship; exact walking minutes are PLANNING_ESTIMATE.
- Main side -> Baopingkou -> Feishayan -> Yuzui: VERIFIED attraction sequence logic at schematic level; exact internal trail geometry must not be drawn.
- Yuzui -> Anlan Bridge: VERIFIED attraction relationship; optional in this scheme.
- Scenic area -> Guanxian Ancient City / Nanqiao: VERIFIED central-cluster relationship.
- Nanqiao -> Lidui Park station: VERIFIED same central zone relationship; exact route/time is PLANNING_ESTIMATE.

## Map emphasis

First-time clarity: rail, hydraulic core, old city, evening riverfront. Medium walking; no hillside detour required.

---

# Scheme B — Hydraulic History Depth

## Preferred concept

Xipu -> Lidui Park station -> local vehicle transfer toward a validated upper/east-side entrance -> Erwang Temple / upper heritage viewpoint -> Anlan Bridge -> Yuzui -> Feishayan -> Baopingkou/Fulong -> old-city edge -> compact formal meal -> Nanqiao -> Lidui Park station -> Xipu

## Critical conditional gate

The upper/east-side entrance must be revalidated from a current operational source before the map is generated. Current traveler guides frequently recommend a Qinyanlou-side downhill route, but this V1 fact sheet does **not** authorize an exact numbered gate or taxi drop pin.

If upper entrance validation is not obtained, Scheme B automatically falls back to:

Lidui Park station -> main/Lidui-side entrance -> Baopingkou -> Feishayan -> Yuzui -> Anlan Bridge -> Erwang Temple -> return/exit toward old city -> Nanqiao -> station.

## Map emphasis

History/engineering depth, temple/hillside context, more elevation. Clearly mark `conditional upper-entry transfer` rather than fabricating a gate.

---

# Scheme C — Food + Guanxian Ancient City

## Intended stop order

Xipu -> Lidui Park station -> scenic-area main/Lidui-side entrance -> Baopingkou -> Feishayan -> Yuzui -> optional Anlan Bridge only when low queue -> exit central side -> local savory snack area -> Guanxian Ancient City slow walk -> dessert/tea rest area -> formal Sichuan meal zone -> Nanqiao -> Lidui Park station -> Xipu

## Status by segment

- Rail and scenic-area access: same VERIFIED logic as Scheme A.
- Core hydraulic stop order: VERIFIED schematic logic.
- Old city + Nanqiao: VERIFIED central urban cluster.
- Food anchors: area-level only in V1; no named restaurant pins until merchant verification.

## Map emphasis

Show a shorter scenic-core block and a larger old-city/food block. The image must not imply that food venues are inside the ticketed hydraulic core.

---

# Scheme D — Relaxed Comfort / Low Rush

## Intended stop order

Xipu -> Lidui Park station -> scenic-area main/Lidui-side entrance -> Baopingkou -> Feishayan -> Yuzui -> optional Anlan Bridge only if both travelers still feel comfortable -> exit -> long formal meal zone -> short Guanxian Ancient City walk -> quiet tea/dessert rest zone -> Nanqiao riverfront -> Lidui Park station -> Xipu

## Status by segment

- Same verified core geography as A/C.
- Anlan Bridge is explicitly optional, not a mandatory loop.
- No Erwang Temple / upper-hill node in the base map; avoid adding climbing merely for completeness.
- Meal/rest zones are area anchors, not merchant pins.

## Map emphasis

Fewest compulsory nodes, widest rest buffers, easiest visual reading on phone. This should look deliberately simple rather than incomplete.

---

# Scheme E — Weather / Crowd Resilient

## Base dry-weather order

Xipu -> Lidui Park station -> scenic-area main/Lidui-side entrance -> Baopingkou -> Feishayan -> Yuzui -> skip Anlan / hillside whenever crowd, rain, slippery surfaces, or fatigue make it unattractive -> central exit -> Guanxian Ancient City covered/urban segments -> seated meal/rest -> Nanqiao only when weather and crowd conditions are acceptable -> Lidui Park station -> Xipu

## Fallback logic shown on map

- `Core route`: main entrance -> Baopingkou -> Feishayan -> Yuzui.
- `Optional branch`: Anlan Bridge / hillside only in favorable conditions.
- `Early-exit branch`: return toward central old-city / meal area when rain or crowd is high.
- `Evening branch`: Nanqiao only if conditions remain comfortable; otherwise station return.

## Map emphasis

Use clearly separated solid and dashed arrows: solid = baseline route; dashed = optional/fallback branches. Do not create a fake indoor attraction route to make the rainy-day plan look fuller.

---

# AI image prompt requirements derived from these fact sheets

Every scheme prompt must state:

- schematic travel-planning map, not a literal GIS map;
- Chinese labels must exactly match the fact sheet;
- station names must be visually distinct;
- route sequence must be readable with arrows;
- rail / local vehicle / walking must use different visual semantics;
- conditional nodes must be marked `可选` or `条件成立时` rather than presented as mandatory;
- no private origin point;
- no unverified restaurant names;
- no invented numbered gate;
- no invented bridges, roads, cableways or subway connection;
- phone portrait layout preferred for later PDF embedding.

# Receipt verification checklist

A generated map receives `VERIFIED` only when all are true:

1. All labels are legible and correctly spelled.
2. Lidui Park station and Dujiangyan station are not merged or confused.
3. Stop order matches the corresponding fact sheet.
4. Nanqiao / Guanxian Ancient City are presented as the central urban/evening cluster, not as hydraulic-core structures.
5. Yuzui, Feishayan and Baopingkou are presented as one connected scenic-area system.
6. Conditional branches remain conditional.
7. No unverified restaurant or numbered gate appears.
8. No private home-origin information appears.
9. Visual simplification does not reverse the route logic.
10. Any factual discrepancy triggers `REJECTED` and regeneration rather than manual rationalization.
