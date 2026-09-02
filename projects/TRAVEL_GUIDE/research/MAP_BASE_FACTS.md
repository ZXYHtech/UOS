# Dujiangyan Map Base Facts — pre-image-generation fact sheet V1

## Purpose

This is the factual map baseline used before any AI route-map image is generated. It is intentionally conservative. If a relationship below is not validated strongly enough, the image prompt must not invent it.

## Validated central places / nodes

### Rail / arrival nodes

- **Lidui Park railway station / 离堆公园站** — current rail station serving the central scenic-area / old-city side of Dujiangyan; current rail searches show direct suburban services from Xipu.
- **Dujiangyan railway station / 都江堰站** — separate station farther from the scenic-area / old-city walking cluster; useful for timetable/return flexibility but must not be confused with Lidui Park station.

### Core heritage / urban nodes

- **Dujiangyan Scenic Area / 都江堰景区** — ticketed heritage scenic area along the Min River; Park Road / Lidui-side visitor access is a principal first-time visitor anchor.
- **Yuzui / 鱼嘴分水堤** — core hydraulic-work node inside the scenic area.
- **Feishayan / 飞沙堰** — core hydraulic-work node inside the scenic area, downstream in the system relationship from Fish Mouth.
- **Baopingkou / 宝瓶口** — core intake-control node inside the scenic area.
- **Anlan Bridge / 安澜索桥** — bridge node linking the hydraulic landscape and east-bank temple / hillside side.
- **Erwang Temple / 二王庙** — hillside cultural/commemorative node associated with Li Bing and the water-management tradition.
- **Nanqiao / 南桥** — covered bridge on the urban riverfront, close to the scenic-area / old-city transition.
- **Guanxian Ancient City / 灌县古城** — old-city pedestrian/commercial/cultural area adjacent to the central riverfront cluster.

## Functional spatial relationships allowed in image prompts

The AI image may depict the following broad planning relationships:

1. Xipu rail -> Lidui Park station as a direct arrival concept.
2. Lidui Park station -> central Dujiangyan scenic-area / old-city cluster as a short local access relationship.
3. Scenic-area core: Fish Mouth, Feishayan and Baopingkou belong to one hydraulic-system visit, not three remote attractions.
4. Nanqiao and Guanxian Ancient City form an evening/food/urban-atmosphere cluster close to the scenic-area edge.
5. Dujiangyan station is a **different rail node** and should be shown as an alternate arrival/departure option rather than merged with Lidui Park station.

## Relationships NOT yet safe to draw as exact geometry

- Exact entrance numbers / gate positions unless separately refreshed from current official scenic-area material.
- Exact walking lines through internal scenic paths.
- Exact one-way direction of all visitor circulation paths.
- Exact taxi pickup/drop-off points.
- Exact restaurant pins before restaurant research verifies current operation.
- Exact walking minutes between internal scenic nodes before route-specific validation.

## Prompt prohibition list

The image generator must not:

- merge Lidui Park station and Dujiangyan station;
- place Nanqiao inside the wrong part of the hydraulic system;
- treat Guanxian Ancient City as a remote standalone town far from central Dujiangyan;
- invent subway service directly into the Dujiangyan scenic area;
- fabricate a 'Dujiangyan scenic-area railway station' name;
- invent bridges, roads, gates or cableways to make the diagram look prettier;
- use obsolete / unverified restaurant names;
- plot the private exact home-origin location.

## Image design rule

The final route images should be **schematic operational travel maps**, not cartographic substitutes for Amap/Gaode or official GIS. Accurate stop identity, order, connection type and relative travel logic are mandatory; exact visual scale can be simplified for phone readability.

## Current source anchors

- Current local-business/map entities for Dujiangyan Scenic Area, Nanqiao, Guanxian Ancient City, Lidui Park area and Dujiangyan station checked 2026-09-02.
- Chengdu Municipal Government Dujiangyan destination page (2026-04-29).
- Current rail search pages for Xipu -> Lidui Park and Xipu -> Dujiangyan.
- Current Dujiangyan scenic-area travel-platform operations pages.

## Next required map-validation step

Before creating the five final image prompts, each scheme must receive a scheme-specific `MAP_FACT_SHEET` with:

- exact ordered stops;
- chosen arrival and departure station;
- verified entrance/exit;
- transport mode for each segment;
- validated meal/rest area anchors;
- estimated time for each segment;
- date of last refresh.

Only then may the prompt-image-receipt workflow begin.