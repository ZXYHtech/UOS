# TASK_INV_AUDIT_WORK_ORDER_01 — Production Work Orders, Kitting and Completion Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed BOM/cost structures, inventory movement service, warehouse/transfer behavior, purchase flows and database/service search for first-class manufacturing work-order semantics.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The application currently has **no first-class production work-order domain** in the inspected core database/service surfaces. Existing BOM operations are cost-estimation inputs; they are not executable manufacturing operations. Existing stock adjustment and transfer mechanisms are useful infrastructure but do not provide reservation, kitting, issue/return, WIP, partial completion, scrap or finished-goods receipt against a production order.

Preliminary work-order maturity: **0.5/5**.

The correct next step is not to imitate an enterprise MES. For the company's likely low-volume RF/electronics manufacturing, introduce a deliberately small production-order state machine that connects a released MBOM to controlled inventory transactions and actual output.

## 2. Why a work order must be first-class

A manufacturing work order answers questions that a BOM and stock adjustment cannot:

- what product/revision is being built;
- how many units are planned;
- which MBOM revision was authorized;
- when materials are needed;
- what was reserved, picked, issued and returned;
- which substitutions were actually used;
- how much was scrapped;
- what quantity completed/passed/failed;
- which serial/lot genealogy resulted;
- who executed/approved the transaction;
- what actual cost was incurred.

Without this document, manufacturing consumption becomes indistinguishable from generic inventory shrinkage.

## 3. Recommended minimal lifecycle

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
released/in_progress -> on_hold -> in_progress
released/in_progress -> cancelled
in_progress -> partially_completed
```

Cancellation after material issue must require explicit return/scrap/WIP disposition before closing.

Avoid dozens of statuses initially. Separate order status from material-line state and quality state.

## 4. Work-order header contract

Minimum header fields:

```text
work_orders
  id
  work_order_no
  product_material_id
  product_revision_id
  mbom_revision_id
  planned_qty
  completed_qty
  scrapped_output_qty
  warehouse/site_id
  planned_start
  due_date
  status
  priority
  source_demand_type
  source_demand_id
  created_by
  released_by/released_at
  closed_by/closed_at
```

Hard rule: after release, the work order must retain the exact BOM/revision/effectivity contract it used even if engineering later releases a new revision.

## 5. Material requirements snapshot

At release, generate controlled material requirements from the effective MBOM.

```text
work_order_materials
  work_order_id
  bom_line_id
  material_id
  required_qty
  reserved_qty
  issued_qty
  returned_qty
  scrapped_qty
  substitute_for_material_id
  substitution_approval_id
  source_location/lot
```

Do not recompute a historical order from the latest BOM every time it opens.

A released snapshot also makes later ECN impact analysis possible: open WOs can be classified as before/after effectivity or requiring disposition.

## 6. Reservation before issue

Production reservation must be a stock commitment, not immediate consumption.

Required sequence:

```text
WO released
 -> calculate required material
 -> reserve available qualified supply
 -> shortage remains visible to MRP/planner
 -> warehouse picks/allocates concrete stock
 -> issue posts ownership/state change to WIP
```

Reservation should reduce ATP and MRP nettable availability without reducing physical on-hand.

This exposes the current weakness of non-authoritative `quantity_locked`: a dedicated reservation ledger or equivalent invariant is needed.

## 7. Kitting

Kitting should be optional operational grouping, not a second inventory model.

Useful states per material requirement:

- not reserved;
- partially reserved;
- reserved;
- picked;
- issued;
- shortage;
- substituted;
- returned/closed.

For low-volume electronics, a simple kit list with barcode scan and shortage highlighting is enough initially.

The kit must show:

- required vs reserved vs issued;
- exact location;
- lot/date code when traceability applies;
- approved alternate availability;
- shortage cause;
- whether engineering approval is required.

## 8. Material issue, overissue and return

### Normal issue

Post a referenced ledger movement from qualified warehouse stock into WIP/work-order custody.

### Overissue

Allow only with a reason and policy. Common legitimate causes:

- feeder/reel setup quantity;
- process loss;
- hand-assembly loss;
- destructive tuning/testing;
- packaging/process consumable rounding.

Overissue must not silently change the planned BOM requirement.

### Return

Unused material returns should reference the original WO/issue, preserve lot/serial where applicable and restore the correct stock state.

### Scrap

Scrap must be separate from consumption because it drives yield and cost variance.

## 9. WIP representation

Do not create a fake warehouse named `WIP` and stop there.

A useful minimal WIP model tracks ownership by work order:

```text
issued_to_wo quantity
consumed/installed quantity (optional initially)
returned quantity
scrapped quantity
remaining_wip quantity
```

For the first release, it is acceptable to treat issued material as WO-owned WIP until order closure if detailed operation-level backflush is unnecessary.

## 10. Completion and finished-goods receipt

Completing output is a controlled inventory transaction:

```text
WO WIP/material consumption
 -> finished product receipt
```

Support partial completion. A work order for 20 units may receive 8, then 7, then 5.

Each completion should capture:

- quantity;
- output revision;
- receiving warehouse/location;
- serial numbers or lot/batch identifier where configured;
- test/quality disposition;
- operator/time;
- related actual material/cost snapshot.

Do not mark an order completed merely because planned quantity was entered. Actual accepted output must drive the completed quantity.

## 11. Quality gate interaction

For RF modules, finished output commonly requires electrical/RF test before saleable release.

Recommended flow:

```text
physical completion
 -> pending final test / quarantine
 -> quality release
 -> saleable finished-goods stock
```

If the company chooses a simpler model, at least ensure failed units cannot enter normal available stock before disposition.

This creates a dependency on `TASK_INV_AUDIT_QC_NCR_01` and `TASK_INV_AUDIT_TEST_RECORD_01`.

## 12. Lot/serial genealogy interaction

When traceability is enabled, each WO completion should connect:

```text
component lots/serials
 -> work order
 -> finished serial/lot
```

Not every 0402 resistor requires individual serial tracking. Configure traceability class by material category/part risk:

- none;
- lot/date-code;
- serial;
- mandatory supplier-lot capture.

## 13. Substitutions

A picker should not replace a component by editing the BOM or choosing any similar SKU.

WO substitution requires:

- original BOM material;
- selected approved alternate;
- scope/product revision applicability;
- engineering approval when conditional;
- quantity actually issued;
- resulting genealogy.

This reuses the AVL/substitution model established in W3.

## 14. Cost interaction

The current cost engine can estimate component/labor/overhead cost from BOM and operation profiles. Work orders should add actual execution evidence:

- actual material issued/returned/scrapped;
- actual substitute cost;
- optionally actual labor/time;
- subcontract charge;
- rework cost;
- accepted output quantity.

Do not overwrite standard cost with actual WO cost. Preserve both for variance analysis.

## 15. Minimal transaction types

Recommended manufacturing ledger events:

```text
WO_RESERVE
WO_UNRESERVE
WO_PICK
WO_ISSUE
WO_RETURN
WO_SCRAP
WO_OUTPUT_RECEIPT
WO_OUTPUT_REVERSAL
WO_CANCEL_DISPOSITION
```

`PICK` may be non-financial/non-quantity-changing if it only assigns a bin/lot; `ISSUE` is the important ownership/state transition.

Use reversals rather than editing closed stock logs.

## 16. Permissions

Suggested split:

- planner/production manager: create/release/hold/cancel WO;
- warehouse: reserve/pick/issue/return materials;
- operator: record progress/output where appropriate;
- quality: release/reject finished output;
- engineering: approve conditional substitution/ECN disposition;
- admin: policy/configuration only.

Every released/cancelled/completed transition should be logged with actor and before/after state.

## 17. UX priority

A small-company WO UI should emphasize exceptions rather than ERP density.

High-value views:

1. WO list: due date, status, material readiness, completion progress.
2. WO detail: product/revision/MBOM snapshot.
3. Material kit: required/reserved/issued/shortage/substitute.
4. Scan issue/return.
5. Completion receipt with serial/test linkage.
6. Exception panel: shortage, unapproved substitute, overdue, failed quality.

## 18. Priority roadmap

### P0

1. work-order header and lifecycle;
2. released MBOM snapshot;
3. material requirement snapshot;
4. reservation ledger integration;
5. issue/return/scrap transactions;
6. partial finished-goods receipt;
7. cancellation disposition.

### P1

1. barcode-assisted kitting;
2. lot/serial genealogy;
3. test/quality release gate;
4. approved substitution workflow;
5. actual material variance.

### P2

1. routing/operation execution;
2. labor time capture;
3. capacity scheduling;
4. backflush policies;
5. MES-style station integrations if volume eventually justifies them.

## 19. Acceptance signals

- releasing a WO freezes the selected product/MBOM revision contract;
- reserved material cannot also be promised as free sales stock;
- issued material has a WO reference and can be partially returned;
- overissue and scrap require explicit reason/disposition;
- partial completion creates real finished-goods receipts without closing the remainder;
- cancellation cannot strand unexplained WIP;
- a finished serial/lot can later resolve the WO that created it;
- an ECN can identify affected open WOs;
- actual material use can be compared with standard BOM requirement;
- no acceptance test requires GitHub Actions.

## 20. Core recommendation

Implement a **small, auditable WO state machine around released MBOM + reservation + inventory ledger + finished receipt**. This delivers most of the manufacturing-control value needed by a low-volume electronics/RF business without prematurely building a full MES.