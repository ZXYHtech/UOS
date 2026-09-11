# TASK_INV_IMPL_E07_S06 — Released Test Specification and Limit-set Execution Contract

## Status

`DESIGN_READY_BLOCKED_BY_E05_CONTROLLED_DOCS`

## Objective

Turn E05 controlled test procedures/limit sets into deterministic executable acceptance contracts for E07 test runs, while preserving historical rules exactly as executed.

## Boundary

E05 owns release/revision/effectivity of controlled test documents/artifacts.

E07 owns execution against an exact released revision and the resulting evidence.

## Suggested test-definition objects

Where scalar/structured machine-evaluable limits are needed, use test-specific structured revisions linked to E05 controlled documents:

```text
test_spec_revisions
  id
  spec_code
  revision_code
  product_material_id / product_revision scope
  controlled_document_revision_id
  status
  effective_from/to

limit_set_revisions
  id
  test_spec_revision_id
  revision_code
  status
  structured_mask_artifact_id
  released_by/at

limit_items
  limit_set_revision_id
  item_code
  condition_json
  comparison_rule
  lower_limit
  upper_limit
  unit
  criticality
```

Do not duplicate E05 document release state inconsistently; structured records must point to the exact controlled release identity.

## RF limit forms

Support:

- scalar min/max;
- band/frequency conditioned limits;
- enum/boolean checks;
- structured mask/artifact for complex curves.

Do not force all RF masks into a single scalar pair.

## Execution selection

At test start resolve and freeze:

```text
product material/revision
DUT serial/lot
work order
released test spec revision
released limit-set revision
required firmware/configuration where applicable
```

After run start, later release of a new limit set never changes that run’s execution contract.

## Snapshot requirement

Measurements should retain enough evaluated-limit snapshot to explain historical pass/fail even if the master limit set is later superseded.

## Re-evaluation

Future analytical re-evaluation against newer limits is allowed only as a separately labeled analysis result.

It never rewrites original execution result.

## Manual override

A measurement/test result override requires:

- separate permission;
- reason;
- actor/time;
- original deterministic result retained;
- quality release decision references the override authority if accepted.

## Tests

- only released/effective test spec selectable for normal production test;
- run freezes exact spec/limit revision;
- later limit change leaves historical result unchanged;
- scalar and structured rules evaluate deterministically;
- missing mandatory item blocks valid completion;
- override never erases original evaluated result;
- draft/unreleased limit set rejected for production release evidence.

## Acceptance

Every production test run can prove the exact released acceptance rules it executed, and historical pass/fail cannot drift when current test limits evolve.
