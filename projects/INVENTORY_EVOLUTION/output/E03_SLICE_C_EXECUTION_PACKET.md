# E03 Slice C Execution Packet — Receiving Staging + Putaway

## Status

`READY_AFTER_E03_A_B_AND_E02_AUTHORITY_FOR_PILOT`

## Entry gate

Requires:

```text
E03-A stable locations merged
E03-B typed scan resolver merged
E02 movement/balance authority active for the chosen pilot warehouse/path
full current-main Release Gate PASS
```

Branch:

```text
impl/e03-putaway
```

Migration:

```text
NEXT_CONTIGUOUS
= putaway_tasks + putaway_task_lines + indexes
```

## Purpose

Separate two facts that must not be conflated:

```text
stock physically arrived at warehouse
!=
stock has been stored in its final bin
```

Target chain:

```text
inbound document
 -> E02 receipt movement into RECEIVING/STAGING location
 -> putaway task
 -> scan source/material/destination
 -> E02 location-to-location movement
 -> partial/full task completion
```

## Receiving staging

Each warehouse participating in this flow requires a stable E03 location of type `RECEIVING` (or an explicit configured receiving location).

Do not create stock in an anonymous warehouse aggregate and later relabel its `location_id`.

Physical receipt movement lands into the receiving position first.

E07 may later add quality state to that stock; E03 does not infer quality from a bin name.

## Putaway objects

### putaway_tasks

```text
id
putaway_no UNIQUE
warehouse_id
source_location_id
source_type
source_id
status
assigned_user_id
created_by
created_at
started_at
completed_at
cancelled_at
remark
```

Statuses:

```text
pending
in_progress
partially_completed
completed
exception
cancelled
```

### putaway_task_lines

```text
id
putaway_task_id
material_id
source_position_key
expected_quantity
confirmed_quantity
destination_location_id NULL
status
exception_reason
last_movement_operation_id NULL
created_at
updated_at
```

One source quantity may be split across several destination confirmations; either use child confirmation records or multiple deterministic line allocations. Never overwrite one completed destination with another.

## Execution transaction

For one confirmation:

```text
BEGIN IMMEDIATE
 -> E01 business-operation admission
 -> reload putaway task/line
 -> permission + warehouse scope
 -> validate source receiving location
 -> validate scanned material
 -> validate destination belongs to warehouse and putaway_enabled
 -> validate remaining source balance through E02
 -> post E02 location-to-location movement
 -> increment confirmed execution evidence
 -> update task status
 -> audit/result receipt
COMMIT
```

No direct update to `stock_balances` outside E02 movement service.

## Pilot order

Do not immediately force every inbound path into putaway.

Recommended:

```text
1. controlled fixture/manual inbound
2. transfer receipt pilot
3. purchase receipt pilot
```

For purchase receipt, E02-H landed-cost safety prerequisite still applies; putaway must not hide/fix procurement cost semantics.

## Partial / split putaway

- partial confirmation leaves remainder in receiving position;
- split destinations are explicit and quantities must sum correctly;
- completed quantity can never exceed expected/source eligible quantity;
- task cancellation only cancels remaining execution; already posted movements remain immutable.

## Scan sequence

Minimum guided proof:

```text
TASK -> SOURCE LOCATION -> MATERIAL -> DESTINATION LOCATION -> QUANTITY -> CONFIRM
```

Typed resolver identifies objects; putaway command revalidates all facts server-side.

## Permissions

Use current warehouse execution/location permissions where possible. Do not silently make every `inventory.adjust` user a putaway operator.

Initial policy can require:

```text
warehouse/location execution permission selected from existing role model
+ warehouse scope
```

If a new permission is needed, add it as a separate explicit migration/policy decision, not hidden in task-table migration.

## Tests

1. receipt stock exists in receiving location before putaway;
2. putaway decreases staging and increases destination by same exact quantity;
3. wrong warehouse destination rejected;
4. disabled/non-putaway location rejected;
5. wrong material scan rejected;
6. partial putaway leaves remainder in staging;
7. split destinations reconcile exactly;
8. same idempotency key cannot move stock twice;
9. forced failure rolls movement + task evidence back together;
10. completed confirmation cannot be edited to a different destination;
11. task cancellation does not delete posted movement;
12. staging + storage sum remains conserved;
13. full Release Gate passes.

## Rollback

Before a pilot becomes required, disable new putaway task creation and retain all movement/task evidence.

After production receipts are required to land in staging, rollback must use code that still understands staging positions. Do not deploy code that treats receiving stock as final-bin stock automatically.

## Stop conditions

Stop expansion if:

- receipt can bypass staging on the pilot path without explicit compatibility policy;
- retry can duplicate a location-to-location movement;
- putaway task stores its own independent stock total;
- destination location lifecycle is still coupled to layout deletion.

## Exit / unlock

One inbound pilot is fully traceable from warehouse receipt into staging and from staging into stable storage locations through E02 movement truth. Unlocks broader putaway rollout and E03-D picking.