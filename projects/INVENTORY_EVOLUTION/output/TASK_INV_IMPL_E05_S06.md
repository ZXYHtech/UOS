# TASK_INV_IMPL_E05_S06 — ECN/ECO, Deviation and Change-impact Control

## Status

`DESIGN_READY_BLOCKED_BY_E05_RELEASE_MODEL`

## Objective

Create a small engineering-change aggregate that records why released configuration changes, what objects are affected, what becomes effective and what must happen to existing stock/WIP/documents.

## Suggested objects

```text
engineering_changes
  id
  change_no
  change_type
  title
  reason
  status
  requested_by/at
  reviewed_by/at
  approved_by/at
  effective_rule
  summary
  closed_at

engineering_change_objects
  id
  engineering_change_id
  entity_type
  before_entity_id
  after_entity_id
  action
  disposition
  impact_status
  notes
```

## Change types

```text
ECN
ECO
deviation
waiver
```

Keep vocabulary small and practical.

## State model

```text
draft
 -> review
 -> approved
 -> implemented
 -> closed

or
 -> rejected / cancelled
```

Do not build a configurable BPM engine.

## Affected objects

Initial entity types may include:

- part revision;
- EBOM revision;
- MBOM revision;
- controlled document revision;
- firmware release;
- E04 AVL/substitute relation;
- release package.

E06/E07 later extend work-order/quality/test objects.

## Impact checklist

A change should explicitly evaluate applicable impacts:

```text
BOM demand
AVL/substitution
existing inventory
open PO
WIP / open WO
fixtures/tools
firmware
RF test procedure / limits
labels/manuals/customer docs
```

Impact state:

```text
not_applicable
no_impact
impact_resolved
impact_open
```

Approval is blocked when required impact remains open.

## Existing-stock disposition

Record decision only; E05 does not directly move/hold stock.

Allowed controlled dispositions may include:

```text
not_affected
use_as_is
use_until_exhausted
rework
hold_for_review
return_supplier
scrap
```

Actual stock execution belongs to E02/E07 workflows.

## Deviation / waiver

Temporary exception requires explicit scope, for example:

```text
material / BOM revision
work order (when E06 exists)
quantity limit
valid-from/to
reason
approved substitute/configuration
```

Expiration/consumption closes the authority; it must not become a permanent hidden BOM edit.

## Release integration

An ECO may release a coordinated set of new revisions.

The change record points from before -> after objects and effectivity decision.

Released objects remain immutable; ECO does not edit them in place.

## Tests

- unique change number;
- unresolved required impact blocks approval;
- approved ECO preserves before/after identities;
- stock disposition record does not directly mutate inventory;
- expired deviation cannot authorize new work;
- closed change remains queryable;
- rejected/cancelled change cannot release new configuration;
- user permission enforced server-side.

## Acceptance

Every controlled configuration change can explain why it occurred, what revisions changed, what operational areas were impacted and what temporary/permanent authority was approved.
