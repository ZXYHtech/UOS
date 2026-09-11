# TASK_INV_IMPL_E06_S01 — Work Order Lifecycle and Frozen Configuration

## Status

`DESIGN_READY_BLOCKED_BY_E05_GATE`

## Objective

Create the first-class manufacturing work-order header and state machine, freezing the exact released E05 configuration when the WO is released.

## Suggested object

```text
work_orders
  id
  work_order_no
  order_type
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
  hold_reason
  cancelled_by/at
  cancel_reason
  closed_by/at
```

Initial `order_type`:

```text
production
engineering_prototype
```

Production and prototype release rules differ; do not infer type from a remark.

## State machine

```text
draft
 -> released
 -> material_reserved
 -> in_progress
 -> partially_completed
 -> completed
```

Side states:

```text
released/material_reserved/in_progress/partially_completed
 -> on_hold
 -> resume to recorded prior valid active state

released/... -> cancel_pending_disposition -> cancelled
```

Do not use free-form status values.

## Production release preconditions

- product material exists/enabled;
- product revision is released;
- MBOM revision is released and belongs to correct product/revision context;
- MBOM is effective or explicitly authorized by E05 deviation/effectivity policy;
- required release package/document policy satisfied where configured;
- warehouse/site permitted;
- actor has `wo.release` and scope.

## Freeze rule

On release persist exact IDs and release snapshot metadata.

After release:

- product revision cannot be silently swapped;
- MBOM cannot be re-resolved to latest;
- release package cannot float to current;
- planned quantity changes require controlled amendment policy rather than casual edit.

## Source demand

Optional structured source:

```text
sales_order
forecast/planned_order later
project/prototype
manual
```

Source demand links planning intent but does not own manufacturing execution state.

## Tests

- unique WO number;
- draft editable according to policy;
- invalid/review/draft MBOM rejected for production release;
- released config IDs immutable;
- newer MBOM release does not change existing WO;
- hold/resume preserves prior state;
- invalid transition rejected;
- cancel enters disposition path when obligations exist;
- warehouse permission/scope enforced;
- operation/correlation evidence recorded.

## Acceptance

A production WO has one auditable lifecycle and permanently knows which released product/MBOM/package it was authorized to build.
