# TRAVEL_GUIDE Final Map Assembly QA

Reviewed: 2026-09-03
Background prompt: ROUTE_MAP_PROMPT_PACKET_V4.md
Overlay semantics: MAP_OVERLAY_SEMANTICS_V1.md

## Background QA

All five returned V4 background renders PASS the background-only gate:
- no readable text;
- no route line/arrows;
- no station/rail/taxi/POI/food/rest icons;
- no pseudo-GIS dense operational network;
- portrait 2:3 mobile-friendly composition;
- sufficient clean overlay corridors;
- north-up broad scenic-core vs old-city/riverfront separation is usable.

AcceptedBackgrounds: 5/5

## Deterministic overlay assembly

Operational semantics were added outside the image generator. The overlay is canonical for route order, arrows, station identity, node labels, optional branches and route classes.

### Scheme A — Classic Balanced
Status: VERIFIED_SCHEMATIC
- single central arrival/departure station: 离堆公园站;
- order: 离堆公园站 -> 景区1号门 -> 宝瓶口 -> 飞沙堰 -> 鱼嘴 -> optional 安澜索桥 -> 灌县古城 -> 正式正餐 -> 南桥 -> 离堆公园站;
- optional Anlan branch remains separate from the main return loop;
- no private home-origin point shown.

### Scheme B — Hydraulic History Depth
Status: VERIFIED_SCHEMATIC_WITH_CONDITIONAL_GATE
- single central station: 离堆公园站;
- distinct taxi/local-car segment to 秦堰楼6号门;
- high-to-low order: 秦堰楼6号门 -> 秦堰楼 -> 二王庙 -> 安澜索桥 -> 鱼嘴 -> 飞沙堰 -> 宝瓶口 -> 景区1号门/离堆侧出口 -> 正式正餐 -> 南桥 -> station;
- Gate 6 remains explicitly conditional on departure-day operation refresh;
- no unverified Gate 4/5 fallback rendered.

### Scheme C — Food + Guanxian Old City
Status: VERIFIED_SCHEMATIC
- scenic core retained;
- three separate city food/rest roles are present: local snack, dessert/tea rest, formal seated meal;
- Nanqiao remains a separate evening node;
- merchant identities are not fabricated.

### Scheme D — Relaxed Connection
Status: VERIFIED_SCHEMATIC
- fewest mandatory sightseeing nodes of the five;
- separate formal seated meal and tea/dessert rest nodes;
- no Qinyan/Erwang branch;
- weak optional Anlan branch does not look mandatory.

### Scheme E — Weather / Crowd Resilient
Status: VERIFIED_SCHEMATIC
- core solid route to Feishayan decision point;
- conditional continuation toward Yuzui;
- weak optional Anlan branch;
- distinct early-exit branch from Feishayan area to sheltered/formal meal-rest node;
- old-city and Nanqiao segments remain optional after the branch merge.

## Final acceptance scope

AcceptedFinalSchematicMaps: 5/5

These maps are `Operational Schematic Maps`, not navigation maps. Their node order and decision logic are authoritative only at the itinerary level. Exact walking streets, real-time closures, rail times, merchant operation and departure-day access must still be checked with current map/rail/scenic sources before travel.

Final PDF maps must include a reader-facing note equivalent to: `示意路线，实际导航以实时地图为准；车次、入口及营业状态请以临行前复核为准。`
