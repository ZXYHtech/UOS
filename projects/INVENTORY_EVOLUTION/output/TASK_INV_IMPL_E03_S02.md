# TASK_INV_IMPL_E03_S02 — Receiving Staging and Putaway

## Status

`DESIGN_READY_BLOCKED_BY_E02_MOVEMENT_KERNEL`

## Objective

Separate the fact that stock has physically arrived from the later fact that it has been stored in a permanent bin.

## Target flow

```text
PO / transfer inbound
 -> receive into warehouse receiving/staging location
 -> create putaway task
 -> suggest/select final storage bin(s)
 -> scan/confirm execution
 -> E02 location-to-location movement
```

## Data objects

Suggested additive objects:

```text
putaway_tasks
putaway_task_lines
```

Header should include:

- warehouse;
- source receiving location;
- source document type/id;
- status;
- assignee;
- create/start/complete timestamps.

Line should include:

- material;
- source stock position;
- expected quantity;
- destination location;
- confirmed quantity;
- status / exception reason.

## State model

```text
pending
 -> in_progress
 -> partially_completed
 -> completed

or
 -> cancelled / exception
```

Cancellation never deletes already executed E02 movements.

## Semantics

- receipt posts stock first into staging;
- putaway task is execution evidence, not stock truth;
- partial putaway leaves remainder visible in staging;
- one quantity may split into multiple destination bins;
- retry uses E01 idempotency and cannot move stock twice;
- completion calls E02 movement kernel;
- E07 may later insert IQC/quality gates before stock becomes pickable, without changing the basic receipt -> staging -> putaway shape.

## Existing workflow coexistence

Do not immediately force every legacy purchase/transfer receipt through staging.

Rollout:

1. create staging location model;
2. prove putaway fixture;
3. pilot one inbound path;
4. reconcile source/destination balances;
5. expand only after full Release Gate passes.

## Tests

- received stock exists at staging before putaway;
- destination quantity increases only through E02 movement;
- source staging decreases by same amount;
- partial putaway preserves remainder;
- split destinations sum exactly to confirmed quantity;
- wrong warehouse/destination rejected;
- double submit is exact-once;
- failure rolls task/movement transaction back together where required;
- completed task cannot be silently edited to a different destination.

## Acceptance

Operators can receive stock without knowing its final bin, and later move it from a traceable staging position to exact storage bins through controlled, idempotent putaway tasks.
