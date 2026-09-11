# TASK_INV_IMPL_E06_S02 — Material Requirement Snapshot, Reservation and Shortage

## Status

`DESIGN_READY_BLOCKED_BY_E06_S01_E02`

## Objective

Freeze material demand from the selected released MBOM at WO release, then reserve stock through E02 so production commitments are visible without consuming physical inventory prematurely.

## Suggested object

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
  status
```

Substitution fields are added/used with E06-S07 when actual substitute execution occurs.

## Snapshot contract

At production WO release:

```text
selected released MBOM
 -> deterministic explosion for planned quantity
 -> requirement rows
 -> snapshot source line/revision/quantity/UOM metadata
```

The requirement row never recomputes from future MBOM revisions.

If planned quantity is amended under policy, preserve the amendment history and before/after requirement basis rather than silently rewriting the original release evidence.

## Reservation

Each requirement requests E02 reservation(s) with:

```text
reservation_type = work_order
reference_type = work_order_requirement
reference_id = requirement id
material
warehouse/scope
quantity
```

Reservation is a commitment, not issue/consumption.

## Shortage

Requirement status must distinguish:

```text
unreserved
partially_reserved
reserved
shortage
```

Shortage remains visible to E08 planning and production users.

Do not manufacture fake reserved quantity to make readiness look green.

## Material readiness

WO-level readiness is derived from requirement states, not manually edited.

Example:

```text
0% reserved
partial
fully reserved
```

A production policy may allow starting with partial kit; that is an explicit rule, not hidden status inference.

## Reservation release

Unused reservations are released when:

- WO cancels before issue;
- requirement is reduced through controlled amendment;
- approved substitution moves demand to another material;
- explicit replanning/reassignment occurs.

Release is idempotent and retains historical evidence.

## E03 interaction

After reservation, E03 may allocate exact bins/pick stock. E06 does not duplicate source-location allocation logic.

## Tests

- requirement quantity equals exact released MBOM explosion × planned quantity;
- later MBOM edit/revision does not change requirement;
- reservation lowers ATP, not physical on-hand;
- competing sales/WO reservations cannot oversubscribe;
- partial availability creates explicit shortage;
- replayed release/reserve cannot duplicate reservation;
- cancellation releases only unused reservation;
- issued quantity is not accidentally unreserved as if unused;
- readiness derived deterministically.

## Acceptance

Every released WO has a frozen material-demand snapshot and truthful reservation/shortage state that E03/E08 can consume without changing physical stock until issue occurs.
