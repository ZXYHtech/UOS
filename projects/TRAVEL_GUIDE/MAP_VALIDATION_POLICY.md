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

## AI image-generation workflow for complex route maps

The route maps use an AI_book-style **prompt → image → receipt → verify → revise** loop. Image generation is a rendering stage only; it must never invent operational geography.

For each of the five schemes:

1. Build a `MAP_FACT_SHEET` from validated research: exact current POI names, verified stop order, station/entrance/exit names, relative orientation, transport mode, estimated segment duration, meal/rest nodes and prohibited/obsolete names.
2. Produce a dedicated image-generation prompt from that fact sheet. The prompt must require a clean phone-readable travel route diagram rather than a decorative fantasy map.
3. Generate one independent map image for that scheme.
4. Return a structured generation receipt recording FigureID, prompt version, source fact-sheet version, generation time and intended stop sequence.
5. Inspect the generated image against the fact sheet. Check every label, stop, ordering arrow, station, entrance/exit and transport/walking segment.
6. If any critical geography, label or ordering is wrong, mark the receipt `REJECTED`, revise the prompt and regenerate. Do not patch an incorrect map by merely explaining the error in prose.
7. Only a map with a `VERIFIED` receipt may be embedded into the final guide PDF.

The AI image may simplify scale and geometry for readability, but it may not relocate a critical POI to the wrong side of the route, fabricate a station/entrance, substitute a stale name, or imply a connection that has not been validated.

## Map output standard

Each scheme map must:

- show stop order and direction;
- distinguish rail, local vehicle and walking segments;
- show realistic transfer/walking durations as planning estimates;
- identify meal/rest nodes separately from attractions;
- avoid plotting the private home-origin point;
- include a `Validated` note with source date or refresh date;
- be legible on a phone;
- have a paired prompt file and generation receipt;
- keep the final accepted image plus an archival source representation when practical.

Preferred canonical map bundle per scheme:

- `SCHEME_X_MAP_PROMPT.md`
- `SCHEME_X_MAP.png`
- `SCHEME_X_MAP_RECEIPT.md`
- optional `SCHEME_X_MAP.svg` only when a reliable vector derivative is available; SVG is no longer mandatory if it would reduce geographic fidelity.

## Acceptance failure conditions

A map fails review if any critical POI is misplaced, obsolete, ambiguously named, inaccessible by the shown connection, based only on stale/unverified location evidence, or if its generation receipt has not passed visual/geographic verification.