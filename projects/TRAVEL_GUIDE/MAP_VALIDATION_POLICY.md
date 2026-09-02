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

The canonical operator handoff packet is:

`projects/TRAVEL_GUIDE/maps/ROUTE_MAP_PROMPT_PACKET_V2.md`

The five per-scheme prompt files remain standalone complete subprompts so separate Agents can work independently.

## Prompt → operator render → receipt → QA workflow

The default route-map workflow is now **prompt handoff first**, not direct Agent generation:

1. Build/refresh a `MAP_FACT_SHEET` from validated research.
2. Prepare one complete independent prompt per FigureID and one combined prompt packet for operator copy/paste.
3. Set map generation state to `AWAITING_RENDER_RETURN`; prompt delivery alone is not `Produced`, not `VERIFIED`, and not task completion.
4. The operator may generate the five images in an independent image-generation environment and return one or more images.
5. Map every returned image to its FigureID; an uncertain mapping remains `RETURNED_UNMAPPED`.
6. Run Subject QA first, then route/order/spatial logic QA, fact/evidence boundary QA, text-clean QA, mobile visual QA.
7. Return a structured receipt recording FigureID, prompt version, source fact-sheet version, returned-image identity and intended stop sequence.
8. If any critical route, node class, station logic, entrance logic or spatial relationship is wrong, mark `REJECTED`, revise the specific Figure prompt and request a new independent render. Wrong-subject images must not be remapped to another Figure opportunistically.
9. Only a returned image with a `VERIFIED` receipt may enter a final guide PDF.

Direct Agent image generation is allowed only when the operator explicitly requests it; otherwise the prompt-handoff workflow is authoritative.

## Base-render text rule

The AI-generated route image is a no-readable-text `Base Render｜基础渲染`. Exact station names, scenic names, gate names, node numbers, durations, legends and validation notes are added later as a verified vector/text overlay.

The base render may contain:

- unlabeled route arrows;
- visually distinct rail/walk/local-car/optional branch line styles;
- generic unlabeled station, attraction, bridge, meal and rest icons;
- blank callout space for later text.

The base render must not contain readable titles, FigureID, Chinese/English labels, numbers, percentages, place names, gate names, road names, SourceID, TaskID, AgentID, brand marks or readable signage.

## Map output standard

Each accepted scheme map must ultimately:

- show stop order and direction after verified overlay;
- distinguish rail, local vehicle and walking segments;
- identify meal/rest nodes separately from attractions;
- avoid plotting the private home-origin point;
- add a verified source/refresh note in the vector/text layer, not in the AI base render;
- remain legible on a phone;
- have a paired prompt file and generation receipt;
- preserve the accepted raster base render plus the annotated/assembled derivative when practical.

Preferred bundle per scheme:

- `SCHEME_X_MAP_PROMPT.md`
- returned base render image
- verified annotated derivative used in the PDF
- `SCHEME_X_MAP_RECEIPT.md`
- optional vector source/overlay

## Acceptance failure conditions

A map fails review if any critical POI class is misplaced, the stop order contradicts the fact sheet, Lidui Park station and Dujiangyan station are conflated, an unverified gate/connection is invented, an obsolete or unsupported place is introduced, readable AI-generated map labels are relied upon as authoritative, or the generation receipt has not passed visual/geographic verification.