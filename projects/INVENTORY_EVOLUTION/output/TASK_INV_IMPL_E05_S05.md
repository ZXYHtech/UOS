# TASK_INV_IMPL_E05_S05 — Release Effectivity and Current Configuration Resolution

## Status

`DESIGN_READY_BLOCKED_BY_E05_S01_S02_S03`

## Objective

Define which released part/BOM revision is effective for new work at a given time without making historical records float to the latest release.

## P0 effectivity

Support deterministic:

```text
effective_from
optional effective_to
explicit work-order revision selection (E06)
```

Future lot/serial-range effectivity waits for E07.

## Rules

- release status and effectivity are separate concepts;
- a released future revision may exist before it becomes default-effective;
- historical WO/build/test references store exact revision IDs and never re-resolve to latest;
- overlapping default-effective ranges for same product/configuration are rejected or explicitly resolved by policy;
- obsolete/withdrawn revision remains historical but cannot be selected for new default use unless an explicit authorized exception/deviation applies;
- `latest created` and `latest released` are not synonyms for `currently effective`.

## Resolution contract

Suggested service:

```text
resolve_effective_configuration(
  material_id,
  as_of,
  configuration_context
)
```

returns explicit identities:

```text
part_revision_id
engineering_bom_revision_id
manufacturing_bom_revision_id
release_package_id if available
resolution_reason
```

No caller should independently guess by sorting revision codes.

## Work-order override

E06 work order may intentionally select a released non-default revision through an approved deviation/change context.

The reason/authority must be explicit and stored on the WO snapshot.

## “Use until exhausted”

Do not implement stock-depletion effectivity as hidden automatic logic in P0.

If an ECO says “use old stock until exhausted”, record the disposition and require an explicit controlled transition/review. Later automation may assist once stock genealogy/planning are trustworthy.

## Tests

- future released revision not selected before effective date;
- current effective revision deterministic;
- overlapping ranges rejected or flagged;
- historical reference stays old after new effectivity begins;
- withdrawn/obsolete excluded from new default resolution;
- explicit authorized WO selection can reference valid released revision;
- draft/review revision never resolves as production effective.

## Acceptance

The system can answer “which released configuration should a new build use now?” while historical builds remain permanently linked to what they actually used.
