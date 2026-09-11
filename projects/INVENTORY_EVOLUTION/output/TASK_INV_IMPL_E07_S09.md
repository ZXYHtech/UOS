# TASK_INV_IMPL_E07_S09 — Final Quality Release, Shipment Trace and Recall Impact

## Status

`DESIGN_READY_BLOCKED_BY_E07_QUALITY_TEST_CORE`

## Objective

Make saleable release a controlled quality decision backed by required inspection/test evidence, then preserve exact lot/serial identities through shipment so future recall/RMA analysis is deterministic.

## Final release contract

For a product/trace policy requiring final quality/test:

```text
E06 physical output
 -> pending/non-saleable quality state
 -> required inspections/test runs
 -> resolve NCR/rework where applicable
 -> quality release decision
 -> E02 quality-state movement to ACCEPTED/saleable
```

Physical completion alone does not grant saleability.

## Suggested release evidence

```text
quality_release_records
  id
  material_id
  lot_id
  serial_id
  work_order_id
  product_revision_id
  release_status
  released_by/at
  inspection_evidence_json / relations
  accepted_test_run relations
  override_authority_id
  reason
  movement_operation_id
```

Prefer normalized join relations for primary evidence; bounded snapshot may assist support/audit.

## Release preconditions

Policy evaluates:

- required test/inspection plan for product/revision;
- required valid test run(s) exist;
- latest relevant accepted evidence passes;
- no unresolved blocking NCR;
- calibration/setup validity acceptable;
- firmware/configuration matches allowed release contract;
- actor has quality-release authority.

## Override

Critical override/concession requires explicit separate permission, reason and E05/E07 authority.

Original failed/missing evidence remains visible.

## Shipment serial/lot assignment

When trace policy requires:

```text
shipment line
 -> exact serial(s)/lot quantity
```

Assignment validates:

- material/product matches order line;
- quality state eligible;
- serial not already shipped/unavailable;
- quantity/cardinality correct;
- warehouse/location allocation valid;
- shipment completion exact-once.

## Shipment genealogy

Suggested evidence relation:

```text
shipment_trace_items
  shipment_task_id
  order_item_id
  serial_id
  lot_id
  quantity
  assigned_by/at
```

E02 stock movement remains physical truth; trace relation records identity delivered.

## Core queries

### Serial view

```text
serial
 -> product revision / WO
 -> component genealogy
 -> firmware
 -> inspections/tests/rework
 -> quality release
 -> shipment/order/customer
```

### Supplier lot impact

```text
supplier lot
 -> receipt
 -> WO issues
 -> finished serial/output lots
 -> shipped customers/orders
```

### Equipment calibration impact

```text
equipment + invalid time range
 -> affected test runs
 -> serials
 -> quality releases
 -> shipments/customers
```

## Recall assessment

E07 provides impact set/evidence; it does not automatically contact customers or declare a regulatory recall.

A later support/quality process can create controlled recall/campaign actions.

## Shipped serial state

Shipped serial remains the same historical entity; do not delete/move it into a disconnected “archive” table that breaks genealogy.

E10 RMA returns the same serial into service history.

## Tests

- required failed/missing test blocks normal release;
- unresolved blocking NCR blocks release;
- valid evidence release transitions quality state exactly once;
- unauthorized override blocked;
- shipped serial must be ACCEPTED/eligible;
- same serial cannot ship twice concurrently;
- shipment retry exact-once;
- serial -> customer query deterministic;
- supplier lot -> affected shipped serials query deterministic;
- calibration-impact query identifies released/shipped affected units;
- historical release retains exact evidence after newer tests/specs exist.

## Acceptance

No controlled finished RF unit becomes normal saleable/shippable stock without an auditable quality decision, and every shipped trace-controlled unit can later be connected back to its manufacturing/test/source evidence and customer destination.
