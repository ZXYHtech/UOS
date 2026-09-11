# TASK_INV_IMPL_E03_S04 — Exact Bin Allocation and Scan-first Picking

## Status

`DESIGN_READY_BLOCKED_BY_E02_RESERVATION`

## Objective

Convert E02 material/warehouse reservation into concrete warehouse execution: which exact storage location the operator should pick from, and proof that the correct location/material/quantity was actually handled.

## Boundary

E02 owns reservation and final stock movement.

E03 owns pick task/allocation and scan evidence.

```text
E02 reservation
 -> E03 bin allocation
 -> E03 scan-confirmed pick
 -> E02 reservation consumption + movement at shipment completion
```

## Suggested objects

```text
pick_tasks
  id
  shipment_task_id
  warehouse_id
  status
  assigned_user_id
  created_at
  started_at
  completed_at

pick_task_lines
  id
  pick_task_id
  reservation_id
  material_id
  source_location_id
  expected_quantity
  confirmed_quantity
  status
  exception_reason
  picked_by
  picked_at
```

Do not store an independent stock balance in pick tables.

## Allocation policy P0

Use deterministic explainable rules only:

1. correct warehouse and material;
2. E02 eligible/reserved quantity;
3. `pick_enabled` location;
4. preferred bin if configured;
5. lower `pick_sequence`;
6. minimize unnecessary split picks.

Lot/serial/expiry/quality ranking is not implemented until E07 provides those authoritative dimensions.

## Guided execution

```text
scan/open shipment task
 -> display suggested bin and expected quantity
 -> scan source location
 -> scan material
 -> enter/confirm quantity
 -> server revalidates task/reservation/location
 -> mark line picked
```

Wrong location/material must block or create an explicit exception path.

## Partial picking

Support explicit partial state:

```text
pending
in_progress
partially_picked
picked
exception
cancelled
```

A partial pick must never be represented as full shipment completion.

## Shipment interaction

Shipment completion must not infer pick success from UI state alone.

Before consuming reservation/posting movement it verifies:

- required pick lines;
- confirmed quantity;
- current reservation state;
- Action Policy/state/idempotency.

## Tests

- deterministic allocation from multiple bins;
- preferred bin honored when eligible;
- insufficient single bin can split when policy allows;
- wrong location scan rejected;
- wrong material scan rejected;
- partial pick state preserved;
- replay cannot increment confirmed quantity twice;
- two operators cannot independently over-pick same reservation;
- cancellation releases execution claim without deleting stock history;
- shipment cannot consume more than reserved/picked policy permits.

## Acceptance

The system can tell an operator where to pick, require proof of the exact bin/material, and preserve partial/exception evidence without creating a second inventory truth.
