# TRAVEL_GUIDE Map Validation Policy

## Objective

Prevent route-map errors caused by obsolete POIs, renamed sites, wrong station assumptions, stale entrances, unrealistic walking links or decorative-but-inaccurate geography.

## Required validation before a map is accepted

For every operational stop or transfer node:

1. Confirm the current canonical place name.
2. Confirm that the place is currently operating/accessible when operation status matters.
3. Confirm its current geographic position using a current map/business source or authoritative destination source.
4. For scenic-area elements, cross-check against current official scenic-area material whenever available.
5. For stations and public transport, use current railway/transit evidence and preserve the exact station name.
6. For entrances/exits and transfer points, do not infer access from visual proximity alone; verify that the proposed walking or vehicle connection is actually usable.
7. Flag any point supported only by old blogs, old screenshots or unverified reposts and exclude it from the operational map until confirmed.

## Station-choice rule

Research must explicitly compare practical arrival/departure choices serving the Dujiangyan scenic/old-city area instead of blindly inheriting an initial station assumption. Compare rail time, onward transfer, walking burden, first-attraction access and evening return resilience.

## Freshness

- Time-sensitive transport, access and operating claims should preferentially use sources current to 2026 and be refreshed close to departure.
- Older historical/cultural sources may be used only for stable facts, not current access or operation status.

## Prompt policy

All route-map prompts follow `projects/TRAVEL_GUIDE/TRAVEL_FIGURE_PROMPT_POLICY_V1.md`, adapted locally from the current AI_BOOK `FIGURE_PROMPT_PACKET_FORMAT_POLICY_V1` and `BOOK_V1_FIGURE_PRODUCTION_POLICY_V2_4` without creating a runtime dependency on the AI_book repository.

The current canonical operator handoff packet is:

`projects/TRAVEL_GUIDE/maps/ROUTE_MAP_PROMPT_PACKET_V4.md`

V1-V3 prompt packets are retained as provenance only and must not be used as the final rendering instruction.

## Prompt -> operator render -> background QA -> deterministic overlay -> final QA

Round 1 and Round 2 demonstrated that image generation is useful for atmospheric geographic context but is not reliable enough to own route direction, semantic node identity or branch logic. Therefore the canonical workflow is now:

1. Build/refresh a `MAP_FACT_SHEET` from validated research.
2. Prepare one complete independent prompt per FigureID and one combined prompt packet for operator copy/paste.
3. Generate only a `Geographic Background Base Render｜地理背景基础渲染`.
4. The AI background must contain no operational route line, arrows, route branches, station icon, rail line, POI icon, food/rest icon, node number or readable text.
5. Set generation state to `AWAITING_RENDER_RETURN`; prompt delivery alone is not `Produced`, not `VERIFIED`, and not task completion.
6. The operator returns one or more independent backgrounds and they are mapped to FigureIDs by return order / explicit filename. Uncertain mapping stays `RETURNED_UNMAPPED`.
7. Run background QA only: correct north-up broad scaffold, usable separation of scenic core vs old-city/riverfront zone, one southwest transport landing area, no pseudo-GIS details, no invented operational objects, enough clean overlay corridors.
8. If the background fails, mark it `REJECTED_BACKGROUND` and request a redraw.
9. After a background passes, add the route semantics in a deterministic vector/text overlay driven by the validated fact sheet.
10. The overlay is canonical for: route line, direction arrows, rail/local-car/walk distinctions, station and entrance icons, attraction nodes, node numbers, POI labels, food/rest nodes, optional/cut branches, time estimates and validation note.
11. Run final map QA on the assembled derivative: FigureID mapping -> route/order -> station/entrance logic -> spatial relationship -> text/facts -> mobile readability.
12. Only an assembled derivative with a `VERIFIED` receipt may enter the final guide PDF.

Direct Agent image generation is allowed only when the operator explicitly requests it; otherwise the prompt-handoff workflow is authoritative.

## Background Base Render rule

The AI-generated background is deliberately non-operational. It may contain only:

- simplified Min River / hydraulic landscape water bodies;
- simplified mountain/green-space masses;
- simplified old-city urban block texture;
- low-detail blank corridors and landing areas reserved for overlays.

It must not contain:

- route lines or arrows;
- station/train/railroad/taxi icons or rail geometry;
- attraction, bridge, food or rest icons;
- node circles or numbers;
- readable titles, FigureID, Chinese/English labels, percentages, place names, gate names, road names, SourceID, TaskID, AgentID, brand marks or readable signage;
- dense realistic street networks, fake GIS detail, satellite-like geometry, invented bridges or random distributary networks.

## Deterministic overlay rule

The vector/text overlay must be generated from the scheme-specific validated fact sheet and is the authoritative operational layer.

For each scheme it must explicitly encode:

- the unique central arrival/departure station identity;
- selected entrance/exit;
- exact ordered scenic nodes;
- walking vs local-car vs rail semantics;
- mandatory vs optional/cut branches;
- old-city and Nanqiao relationship;
- separate snack/rest/formal-meal nodes where the scheme requires them;
- source refresh date and any conditional-access caveat.

No overlay element may be inferred from the AI background merely because a blank area or decorative structure looks plausible.

## Map output standard

Each accepted scheme map must ultimately:

- show stop order and direction in the verified vector overlay;
- distinguish rail, local vehicle and walking segments;
- identify meal/rest nodes separately from attractions;
- avoid plotting the private home-origin point;
- add a verified source/refresh note in the vector/text layer;
- remain legible on a phone;
- preserve the accepted AI background plus the annotated assembled derivative;
- have a paired prompt file and generation receipt.

Preferred bundle per scheme:

- `SCHEME_X_MAP_PROMPT.md`
- accepted background render
- `SCHEME_X_MAP_OVERLAY.svg` or equivalent deterministic vector source
- `SCHEME_X_MAP_FINAL.png`
- `SCHEME_X_MAP_RECEIPT.md`

## Acceptance failure conditions

Background fails if it contains route semantics, operational icons, pseudo-GIS detail, multiple ambiguous station landing areas, or insufficient clean space for the overlay.

Final assembled map fails if any critical POI class is misplaced, stop order contradicts the fact sheet, Lidui Park station and Dujiangyan station are conflated, an unverified gate/connection is invented, an obsolete or unsupported place is introduced, or the receipt has not passed final route/fact/text/mobile QA.