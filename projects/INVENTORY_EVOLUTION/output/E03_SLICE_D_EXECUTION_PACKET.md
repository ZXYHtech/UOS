# E03 Slice D Execution Packet — Exact-bin Picking

## Status

`READY_AFTER_E03_A_B_AND_E02_RESERVATION_AUTHORITY`

## Entry gate

Requires:

```text
E03-A stable locations
E03-B typed scan resolver
E02 reservation/ATP authoritative for the shipment pilot
E02 shipment issue integration stable
full current-main Release Gate PASS
```

Branch:

```text
impl/e03-bin-picking
```

Migration:

```text
NEXT_CONTIGUOUS
= pick_tasks + pick_task_lines + indexes
```

## Purpose

Convert a warehouse-level E02 reservation into execution evidence for **which physical bin** an operator should pick from, without creating another stock truth.

```text
E02 reservation
 -> deterministic E03 bin allocation
 -> scan-confirmed pick evidence
 -> E02 shipment issue consumes reservation/position stock
```

Pick tables never own authoritative quantity-on-hand.

## Objects

### pick_tasks

```text
id
pick_no UNIQUE
shipment_task_id
warehouse_id
status
assigned_user_id
created_at
started_at
completed_at
cancelled_at
```

### pick_task_lines

```text
id
pick_task_id
reservation_id
material_id
source_location_id
expected_quantity
confirmed_quantity
status
picked_by
picked_at
exception_reason
```

Statuses:

```text
pending
in_progress
partially_picked
picked
exception
cancelled
```

## P0 allocation algorithm

Deterministic, explainable only:

1. correct warehouse/material;
2. E02 stock status eligible for fulfilment;
3. location `pick_enabled=1`;
4. quantity available for the relevant reservation/allocation semantics;
5. preferred location when configured;
6. lower `pick_sequence`;
7. minimize split bins when possible.

No FIFO/FEFO/lot/serial logic until E07 has authoritative dimensions.

Allocation suggestion is not a stock reservation substitute. E02 remains promise authority.

## Scan-first execution

```text
open/scan pick task
 -> scan expected source location
 -> scan material
 -> confirm quantity
 -> server reloads task/reservation/balance
 -> append pick evidence
```

The server rejects:

- correct material in wrong location;
- correct location but wrong material;
- amount beyond line remaining;
- amount beyond currently valid allocated/reserved quantity;
- disabled/non-pickable location;
- task assigned to another operator when current assignment policy forbids it.

## When stock moves

Preferred v1 rule:

```text
pick confirmation = execution evidence only
shipment issue = physical E02 movement + reservation consume
```

Do not decrement stock at pick confirmation and again at shipment issue.

If later business policy needs a physical `PICKED_STAGING` position, that is a separately reviewed E02/E03 movement design, not an implicit side effect here.

## Concurrency

Two operators may open the same task only according to explicit assignment policy.

Confirmed quantity update uses idempotency and transaction guards so concurrent scans cannot push line confirmed quantity above expected/reserved amount.

Task version/state is reloaded server-side on every consequential confirmation.

## Existing shipment scan coexistence

Current `shipment_scan_logs` and scan-progress UI are useful evidence. Initial rollout may bridge them into the typed resolver/pick evidence instead of deleting them.

Do not keep two independent counters that can disagree indefinitely. Define one authoritative picked quantity and expose legacy scan counts as compatibility evidence during migration.

## Tests

1. allocation deterministic across multiple bins;
2. preferred location honored only when eligible;
3. split pick generated only when needed/allowed;
4. wrong location scan rejected;
5. wrong material scan rejected;
6. duplicate scan/request does not increment twice;
7. partial pick remains partial;
8. two concurrent operators cannot over-confirm same line;
9. pick cancellation removes remaining execution claim but not stock/reservation history;
10. shipment issue cannot exceed picked policy/reservation;
11. pick confirmation alone does not physically deduct stock;
12. current shipment scan compatibility remains explainable;
13. full Release Gate passes.

## Rollback

Disable pick-task requirement and retain evidence if shipment issue still safely honors E02 reservation/stock authority.

Never roll back by re-enabling a client-side scan counter as stock authority.

## Stop conditions

Stop if:

- pick confirmation and shipment issue both mutate physical stock;
- old and new scan counters cannot be deterministically reconciled;
- two operators can over-confirm one reservation;
- a stale client task version can authorize a scan without current server validation.

## Exit / unlock

A shipment can be guided to exact bins with scan proof and partial/exception evidence while E02 remains the sole stock/reservation authority.