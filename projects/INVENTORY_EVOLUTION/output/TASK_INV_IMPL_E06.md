# TASK_INV_IMPL_E06 — Work Order and Manufacturing Execution Spine

## Status

`DESIGN_READY_BLOCKED_BY_E05_GATE`

E06 is design-only while earlier runtime gates remain open.

## 1. Objective

Introduce a deliberately small manufacturing work-order domain for low-volume RF/electronics production.

E06 must answer:

```text
what exact product/revision is being built?
which released MBOM/release package authorized it?
how much is planned?
what material was required/reserved/picked/issued/returned/scrapped?
what output was actually completed?
what WIP remains?
which approved substitutions/deviations were used?
```

It must not become a generic MES framework.

## 2. Domain boundaries

```text
E02 = stock movement / balance / reservation truth
E03 = bin allocation, scan, warehouse execution evidence
E04 = part/MPN/AML/substitute engineering authority
E05 = released part revision / MBOM / effectivity / ECO / release package
E06 = work-order manufacturing demand, WIP custody and actual execution document
E07 = lot/serial genealogy, quality, RF test, final release
E08 = planning/MRP recommendations and pegging
E11 = standard/actual cost economics built from E06 evidence
```

E06 never creates a second inventory ledger.

## 3. Work-order header

Suggested object:

```text
work_orders
  id
  work_order_no
  product_material_id
  product_revision_id
  mbom_revision_id
  release_package_id
  planned_quantity
  completed_quantity
  scrapped_output_quantity
  warehouse_id
  planned_start_at
  due_at
  priority
  status
  source_demand_type
  source_demand_id
  created_by/at
  released_by/at
  hold_by/at
  cancelled_by/at
  closed_by/at
```

## 4. Minimal lifecycle

```text
draft
 -> released
 -> material_reserved
 -> in_progress
 -> partially_completed
 -> completed
```

Controlled side paths:

```text
released/material_reserved/in_progress/partially_completed
 -> on_hold
 -> previous valid active state

released/... -> cancel_pending_disposition -> cancelled
```

Do not add dozens of operation statuses initially.

Work-order status, material-requirement state and quality state remain separate.

## 5. Release freezes manufacturing configuration

At release, one WO stores exact IDs for:

```text
product_material_id
product_revision_id
mbom_revision_id
release_package_id where required
approved deviation/ECO context where applicable
```

Hard invariant:

> Opening a historical WO never recalculates its configuration from the currently effective MBOM.

Engineering may release a newer configuration later; the existing WO remains on its frozen one unless an explicit authorized change/disposition creates a controlled amendment.

## 6. Requirement snapshot

At WO release, explode the selected released MBOM and create immutable requirement identity/snapshot rows.

Suggested:

```text
work_order_material_requirements
  id
  work_order_id
  mbom_line_id
  required_material_id
  required_quantity
  uom
  requirement_snapshot_json
  reservation_status
  reserved_quantity
  picked_quantity
  issued_quantity
  returned_quantity
  scrapped_quantity
  consumed_quantity
  actual_substitute_material_id
  substitution_authority_type
  substitution_authority_id
  status
```

The snapshot preserves planned manufacturing demand even if future MBOM revisions exist.

## 7. Reservation / shortage

WO release creates manufacturing demand.

Preferred flow:

```text
WO released
 -> requirement snapshot
 -> request E02 reservations
 -> fully/partially reserved
 -> shortage remains explicit
 -> E03 bin allocation/pick
 -> E02 issue into WO custody/WIP
```

Reservation reduces ATP/nettable supply but does not reduce physical on-hand.

Do not use legacy `quantity_locked` as the manufacturing contract after E02 is authoritative.

## 8. Kitting

Kitting is an operational grouping/view, not inventory truth.

A kit view may show:

```text
required
reserved
shortage
allocated bin
picked
issued
returned
scrapped
approved substitute
```

For P0, one WO can have one logical kit context; advanced kit waves/carts are unnecessary.

## 9. WIP custody

Do not solve manufacturing by inventing one fake `WIP` warehouse and losing WO ownership.

When material is issued, E02 movement must preserve:

```text
reference_type = work_order
reference_id   = WO
business operation identity
from stock position
WO-owned WIP/custody scope
quantity
```

Minimal P0 WIP accounting:

```text
issued
returned
scrapped
remaining/unresolved WIP
```

Detailed operation-by-operation consumption can be deferred.

## 10. Material issue

Normal issue:

```text
reserved/picked stock
 -> exact-once E02 movement
 -> WO-owned WIP
 -> requirement issued quantity updates atomically
```

Issue must be idempotent through E01.

No generic negative adjustment is accepted as a substitute for manufacturing issue.

## 11. Overissue

Overissue may be legitimate for:

- reel/feeder setup;
- process loss;
- hand assembly loss;
- destructive tuning/testing;
- consumable rounding.

Policy:

- explicit threshold/policy;
- reason mandatory;
- actor/time recorded;
- does not silently rewrite planned MBOM requirement;
- actual excess is separately visible for variance/cost.

## 12. Return

Unused issued material returns through a referenced movement tied to the original WO/issue context.

Support partial return.

Return cannot exceed unresolved issued/WIP quantity.

E07 later preserves lot/serial genealogy through the same path.

## 13. Scrap

Scrap is not equivalent to normal consumption.

Record separately:

```text
material scrap
output scrap
reason / disposition
actor/time
reference to WO/requirement
```

Quality/NCR detail can extend this in E07.

## 14. Partial completion

One WO may complete output in multiple receipts:

```text
planned 20
 -> output receipt 8
 -> output receipt 7
 -> output receipt 5
 -> completed 20
```

Each completion is an idempotent E02 stock movement into finished-output position/state.

Do not close a WO just because planned quantity equals a user-entered number; accepted posted output drives completed quantity.

## 15. Output before E07

E06 must leave a clean seam for E07 quality/test release without fabricating quality history.

P0 design:

- output receipt identifies WO/product/revision/quantity;
- product families that later require quality release can route through an explicit pending-release stock status once E07 exists;
- before E07 authority exists, do not invent pass/fail/test evidence.

## 16. Cancellation and hold

### Hold

Hold stops new issue/completion commands but preserves all existing reservations/WIP/evidence according to policy.

### Cancel

Cancellation after any reservation/issue cannot simply set `status=cancelled`.

Required flow:

```text
cancel requested
 -> release unused reservations
 -> return/scrap/disposition issued WIP
 -> account for any completed output
 -> unresolved quantity must reach zero or approved exception
 -> cancelled/closed
```

No unexplained WIP may be stranded.

## 17. Substitution at WO execution

Picker/operator may not edit the MBOM.

Actual substitute use records:

```text
original requirement material
actual issued material
quantity
E04 approved substitute / AML authority
or E05 deviation authority
actor/time
```

If authority is missing/expired/out of scope, issue is blocked.

## 18. Prototype / engineering build mode

Prototype work may need draft design context before full production release.

Do not contaminate standard production WO semantics.

Preferred approach:

```text
prototype_build / engineering_order mode
```

with explicit rules:

- non-production designation;
- draft/review BOM snapshot allowed only under engineering permission;
- output excluded from normal saleable production release by default;
- all material still reserved/issued through E02;
- actual material use retained for project cost/learning;
- transition to production requires released E05 configuration, not renaming prototype WO.

## 19. Actual material evidence

E06 records physical/operational actuals:

- issued quantities;
- returns;
- scrap;
- substitutions;
- accepted output.

E11 later converts this evidence into actual WO cost and variance.

E06 does not overwrite standard cost.

## 20. Operation/labor scope

P0 intentionally does **not** require full routing/MES execution.

Optional later extension:

```text
work_order_operations
  operation identity
  planned sequence
  started/completed
  optional labor/time actual
```

Only add once there is operational value. Do not block core material-control WO on routing sophistication.

## 21. Permissions

Suggested action split:

```text
wo.view
wo.create
wo.release
wo.hold
wo.cancel
wo.material.reserve
wo.material.issue
wo.material.return
wo.material.scrap
wo.output.complete
wo.substitution.approve/use
```

Engineering approval authority remains E04/E05; E06 only consumes the approved reference.

## 22. Audit / correlation

All consequential WO actions use E01:

- Action Policy;
- Business Operation / idempotency;
- correlation ID;
- operation log;
- durable/outbox infrastructure for external side effects where needed.

## 23. Migration policy

There is no existing first-class WO history to manufacture artificially.

Do not convert generic inventory adjustments into fake historical WOs.

If legacy project/prototype notes suggest manufacturing activity, keep them as legacy references unless an explicit migration with evidence exists.

Exact migration numbers are assigned only from then-current merged main.

## 24. Required tests

### Release / snapshot

- release only accepts released/effective E05 manufacturing configuration for production WO;
- requirement snapshot matches selected MBOM revision;
- later BOM revision does not change open/historical WO requirements.

### Reservation / issue

- reservation reduces ATP but not on-hand;
- partial shortage explicit;
- issue exact-once;
- issue cannot exceed authorized reservation/policy;
- two workers cannot overissue same requirement.

### Return / scrap

- partial return allowed;
- return cannot exceed unresolved issued quantity;
- scrap separate from return/normal consumption;
- overissue requires reason/policy.

### Completion

- multiple partial receipts aggregate correctly;
- replay does not duplicate finished stock;
- output revision remains WO frozen revision;
- completion cannot exceed policy/planned quantity without authorized exception.

### Cancel / hold

- hold blocks new execution but preserves evidence;
- cancellation cannot close with unexplained reservations/WIP;
- disposition events are immutable/reversible via compensating actions.

### Substitute

- unapproved similar part blocked;
- expired AML/deviation blocked;
- actual substitute use remains linked to original requirement.

## 25. Definition of done

E06 is complete only when:

- a WO freezes one exact released manufacturing configuration;
- material requirements are snapshotted;
- E02 reservation/ledger drives manufacturing material truth;
- E03 can kit/pick/scan exact stock;
- issue/return/scrap/overissue are distinct auditable events;
- WIP belongs to a WO;
- partial finished output is supported;
- cancellation cannot strand unexplained WIP;
- substitutions require E04/E05 authority;
- prototype mode is explicitly non-production;
- E11 can later derive actual material cost from E06 evidence;
- no required runtime depends on GitHub Actions.
