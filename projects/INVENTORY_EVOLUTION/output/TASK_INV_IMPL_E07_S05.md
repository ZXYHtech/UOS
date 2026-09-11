# TASK_INV_IMPL_E07_S05 — Work-order Genealogy and Finished Serial/Output Lot

## Status

`DESIGN_READY_BLOCKED_BY_E06_E07_S01`

## Objective

Connect actual component-lot/serial consumption to the finished output identity created by a work order, at a granularity the shop-floor process can honestly support.

## Suggested object

```text
output_genealogy_links
  id
  work_order_id
  output_serial_id
  output_lot_id
  consumed_material_id
  consumed_lot_id
  consumed_serial_id
  quantity
  issue_movement_line_id
  relation_type
  capture_scope
  created_by/at
```

Use explicit field names instead of ambiguous parent/child direction.

## Capture scopes

```text
work_order
output_lot
finished_serial
```

The stored scope says how precise the evidence really is.

Do not present WO-level lot consumption as if it were per-serial mapping.

## Finished serial creation

When trace policy requires serial:

```text
E06 output receipt
 -> allocate/provide unique serial(s)
 -> bind product material/revision/WO
 -> attach to output stock position
```

Quantity/serial cardinality must match policy.

## Component link

Genealogy source should come from actual E06 issue/consumption movements, not from theoretical MBOM lines alone.

It must preserve:

- required material;
- actual substitute material where used;
- consumed lot/serial;
- quantity;
- WO/revision/MBOM context.

## Backflush mode

For low-volume batch builds where per-unit scan is unnecessary:

- link consumed component lots to output lot / WO batch;
- label capture scope accordingly;
- do not synthesize per-serial assignment.

## Per-serial mode

For critical components/products, operator/station flow may explicitly assign component lot/serial to each output serial.

Use E03 scan resolver for capture and server validation.

## Trace queries

Must support:

```text
finished serial -> WO -> MBOM/product revision -> consumed lots/serials
supplier/component lot -> WOs -> affected outputs/serials
```

## Corrections

Genealogy correction cannot simply delete old relation after release/shipment.

Use controlled correction/reversal evidence with reason/authority.

## Tests

- finished serial unique and linked to correct WO/revision;
- genealogy references actual issue movement;
- substitute actual material preserved;
- WO-level capture not displayed as serial-level;
- per-serial mapping quantity/cardinality validated;
- suspect input lot returns deterministic affected outputs;
- future WO/BOM edits do not change genealogy;
- correction retains original history.

## Acceptance

The system can honestly trace manufactured output back to the actual controlled component lots/serials captured during execution, with explicit evidence granularity.
