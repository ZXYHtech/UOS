# TRAVEL_GUIDE Route Map Return QA — Round 2

Reviewed: 2026-09-02
Source prompt packet: ROUTE_MAP_PROMPT_PACKET_V3.md
Mapping rule: user return order A -> B -> C -> D -> E; no opportunistic remap.

## Shared checks

PASS:
- five independent images;
- 1024x1536 portrait output;
- no readable text / FigureID / TaskID / logo;
- one central rail-station anchor per image;
- much simpler topological background than Round 1;
- no dense pseudo-GIS road network.

Shared failure pattern:
- image generation is still deciding route direction, operational sequencing and semantic node identity;
- arrows are reversed or ambiguous in multiple renders;
- several required route-specific nodes/branches are missing or merged;
- therefore rendered route semantics are not reliable enough for final guide use.

## FIG-TG-DJY-MAP-A
Status: REJECTED_STRUCTURE_DIRECTION

Good:
- one station;
- hydraulic core + optional bridge + city cluster are visually separated;
- visual quality and phone readability are good.

Failure:
- route arrows do not create an unambiguous Station -> Gate 1 -> Baopingkou -> Feishayan -> Yuzui -> optional Anlan -> south return -> old city -> meal -> Nanqiao -> station loop;
- the station-to-scenic outbound segment is not clearly represented as the first operational leg;
- arrows on the scenic spine conflict in direction.

## FIG-TG-DJY-MAP-B
Status: REJECTED_WRONG_OPERATIONAL_STRUCTURE

Good:
- one station;
- high/low visual separation exists;
- optional bridge is distinct.

Failure:
- missing a clearly distinct station -> local-car/taxi -> Qinyan Gate 6 high-entry segment;
- direct station-to-scenic walking line substitutes for the required vehicle transfer;
- Qinyan Tower / Erwang Temple / Anlan / Yuzui / Feishayan / Baopingkou high-to-low interpretation cannot be reliably mapped from the generic icons;
- long return arc is invented rather than fact-sheet-driven.

## FIG-TG-DJY-MAP-C
Status: REJECTED_MISSING_REQUIRED_NODES

Good:
- one station;
- simple hydraulic spine;
- city cluster is enlarged relative to scenic core.

Failure:
- three distinct food/rest roles are not present: snack, dessert/tea rest, formal seated meal;
- only one clear food icon appears, with generic walking/bridge nodes replacing required semantic stops;
- city route order is therefore incomplete.

## FIG-TG-DJY-MAP-D
Status: REJECTED_DIRECTION_AND_REST_NODE

Good:
- visually the cleanest/minimal render of the set;
- one station;
- optional bridge is weak/dashed;
- city and scenic blocks are easy to read.

Failure:
- scenic spine arrows largely read north-to-south toward the station rather than outbound station -> scenic core followed by return to city;
- formal meal exists but the separate quiet dessert/tea rest node is missing;
- route semantics are still being inferred by the image generator rather than controlled by a route overlay.

## FIG-TG-DJY-MAP-E
Status: REJECTED_MISSING_EARLY_EXIT_BRANCH

Good:
- one station;
- optional bridge is dashed;
- background is comparatively simple.

Failure:
- no explicit Feishayan-area Early Exit / Cut Branch to the sheltered meal/rest city node;
- core/conditional/cut routes are not separated into three unmistakable layers;
- arrows mainly describe one long descending route, so weather/crowd decision logic is lost.

## Round 2 decision

AcceptedFinalMaps: 0/5
BackgroundStyleAcceptedAsReference: YES
OperationalRouteLayerAccepted: NO

## Protocol change for Round 3

Do not ask the image model to generate any operational route line, arrow, station/attraction icon, route branch, node number, POI symbol or semantic stop marker.

AI generation is reduced to a `GEOGRAPHIC BACKGROUND BASE RENDER` only:
- simplified north-up Min River / Dujiangyan hydraulic landscape scaffold;
- simplified mountain mass;
- clearly separated scenic-core land/water zone;
- clearly separated south/southeast old-city + Nanqiao urban-riverfront zone;
- a neutral southwest station-zone landing area without station icon or rail line;
- generous blank corridors for later overlays.

All operational semantics will be added in a deterministic vector overlay after the background is accepted:
- route line;
- direction arrows;
- station icon;
- entrance/attraction icons;
- node numbers;
- labels;
- taxi segment;
- optional branches;
- food/rest icons;
- source refresh note.

Reason: the image model is useful for aesthetic geographic context but not trustworthy enough for itinerary topology/direction. Vector overlay becomes canonical for route semantics.