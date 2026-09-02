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

## Map output standard

Each scheme map must:

- show stop order and direction;
- distinguish rail, local vehicle and walking segments;
- show realistic transfer/walking durations as planning estimates;
- identify meal/rest nodes separately from attractions;
- avoid plotting the private home-origin point;
- include a `Validated` note with source date or refresh date;
- ship as SVG + PNG and remain legible on a phone.

## Acceptance failure conditions

A map fails review if any critical POI is misplaced, obsolete, ambiguously named, inaccessible by the shown connection, or based only on stale/unverified location evidence.