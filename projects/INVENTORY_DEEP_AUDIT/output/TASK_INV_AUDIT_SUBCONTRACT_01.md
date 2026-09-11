# TASK_INV_AUDIT_SUBCONTRACT_01 — Outsourced Processing and Consigned-material Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed supplier/purchase, transfer, inventory/BOM/cost foundations and searched the inspected core service layer for first-class subcontract semantics. No dedicated subcontract workflow was found in the inspected service surface.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The current system can purchase from suppliers and transfer stock between internal warehouses, but outsourced manufacturing is a different business process:

```text
company-owned material
 -> physically sent to subcontractor
 -> processed as external WIP
 -> returned as processed component/subassembly/product
 -> quantity/yield/scrap reconciled
 -> processing service cost captured
```

A normal purchase order cannot by itself represent ownership of supplied material, and an internal warehouse transfer should not pretend a subcontractor is simply another company warehouse unless ownership/accountability semantics are explicit.

Preliminary subcontract maturity: **0.5/5**.

## 2. Common RF/electronics subcontract scenarios

The target design should support at least these patterns:

- PCB fabrication from released Gerber package;
- SMT/PCBA assembly using company-supplied components;
- mixed consignment: some parts supplied by company, others purchased by assembler;
- CNC/enclosure machining;
- plating/coating/laser marking;
- cable harness assembly;
- shielding cover fabrication/assembly;
- outsourced calibration/test step;
- repair/rework by external vendor.

Not all need dedicated UI variants; they can share a common outside-processing order model.

## 3. Three ownership models to distinguish

### 3.1 Buy finished/processed item

Supplier owns inputs; company buys resulting item. Normal procurement may be sufficient.

### 3.2 Company-consigned material

Company owns material sent to subcontractor. It should leave internal physical stock but remain a company asset and remain traceable.

### 3.3 Mixed material responsibility

Some components are company-supplied; subcontractor supplies others and charges them in processing price.

The data model must not collapse these into one `PO received` quantity.

## 4. Outside-processing order

Recommended first-class header:

```text
subcontract_orders
  id
  subcontract_no
  supplier_id
  source_work_order_id
  product/subassembly_material_id
  product_revision_id
  mbom_revision_id
  planned_qty
  status
  sent_at
  expected_return_at
  completed_at
  currency
  processing_price
  created_by/approved_by
```

Possible lifecycle:

```text
draft
 -> approved
 -> material_prepared
 -> sent
 -> partially_returned
 -> returned
 -> quality_closed
 -> financially_closed
```

Keep physical return/quality completion separate from financial settlement when useful.

## 5. Consigned material lines

```text
subcontract_material_lines
  subcontract_order_id
  material_id
  required_qty
  sent_qty
  returned_unused_qty
  consumed_qty
  scrapped_qty
  supplier_lot/reference
  company_lot_id
  ownership: company | supplier
```

The important reconciliation is:

```text
sent company-owned qty
= consumed + returned_unused + accepted_process_loss + scrap + unresolved variance
```

Unresolved variance must become an exception, not silently disappear.

## 6. Stock state at subcontractor

A company-owned part sent externally should become something like:

```text
INTERNAL_AVAILABLE
 -> RESERVED_FOR_SUBCONTRACT
 -> AT_SUBCONTRACTOR / EXTERNAL_WIP
 -> CONSUMED_IN_SUBCONTRACT
      or RETURNED_UNUSED
      or SCRAPPED
```

The company should be able to report the quantity/value physically held by each subcontractor.

Do not count `AT_SUBCONTRACTOR` as local ATP, but do count it as company-owned inventory/WIP for accountability where appropriate.

## 7. Relationship to internal transfers

Existing transfer logic is a useful implementation pattern for:

- dispatch confirmation;
- in-transit quantity;
- receive confirmation;
- partial receipt;
- discrepancy handling.

But subcontract has additional semantics:

- external counterparty rather than internal warehouse;
- material transformation;
- ownership retained while offsite;
- consumed inputs vs returned output;
- processing service charge;
- yield/scrap;
- quality acceptance;
- released manufacturing documents.

Reuse transaction/ledger patterns, not the business object unchanged.

## 8. Output receipt

Returned processed goods may be:

- same material after process;
- different subassembly material;
- finished product;
- partially completed quantity;
- rejected/rework quantity.

Output receipt should reference:

- subcontract order;
- source WO where used;
- output material/revision;
- quantity;
- lot/serial;
- supplier lot/reference;
- quality state;
- received by/time.

Receipt normally enters `PENDING_INSPECTION` if IQC/FQC policy requires it, not directly saleable stock.

## 9. Lot/serial genealogy

For traceable modules/subassemblies, preserve:

```text
company-supplied component lots
 -> subcontract order
 -> returned PCBA/output lot/serial
 -> later internal work order / finished serial
```

If the subcontractor provides its own components, record supplier-provided lot data where the quality plan requires it.

Do not claim exact genealogy beyond the level actually captured by the subcontractor.

## 10. Released package control

Each outside-processing order should reference the exact controlled manufacturing package:

- drawing/PCB/Gerber revision;
- MBOM revision;
- assembly instruction;
- approved AVL;
- firmware/programming package;
- inspection/test specification.

Sending a supplier an unversioned file link is not sufficient release control.

This depends on `TASK_INV_AUDIT_DOC_CONTROL_01` and revision/ECN governance.

## 11. Shortage and kitting

Before dispatch, the system should compute:

- required company-supplied material;
- reserved quantity;
- picked quantity;
- shortage;
- allowed substitute;
- lot/serial allocation.

This is essentially an external kit and should reuse work-order material reservation semantics.

MRP should consider subcontract demand and scheduled return supply.

## 12. Processing cost

Processing cost should be distinct from material purchase cost.

Possible components:

- per-unit processing fee;
- setup/NRE fee;
- stencil/tooling fee;
- testing fee;
- freight;
- supplier-provided material charge;
- expedite charge;
- scrap/rework charge.

The returned assembly actual cost can then include:

```text
company-owned material consumed
+ subcontract processing/service cost
+ supplier-provided material cost
+ inbound/outbound freight allocation
+ accepted scrap/yield cost
```

Do not double-count company-supplied material in a subcontractor invoice and internal material issue.

## 13. Purchase-order relationship

It is reasonable to use the existing procurement subsystem for commercial approval/payment, but link a PO/service line to the subcontract order.

Recommended separation:

- subcontract order = operational/material transformation authority;
- purchase order = commercial commitment/payment authority.

One subcontract order may map to one PO initially. Keep IDs separate so operational reconciliation is not trapped inside accounting fields.

## 14. Quality and NCR

Returned goods should support:

- incoming/final inspection;
- accepted quantity;
- rejected quantity;
- supplier rework;
- return for rework;
- NCR;
- supplier corrective action;
- chargeback/credit where applicable.

An external processor's `returned qty` is not the same as `accepted qty`.

## 15. Supplier accountability

Useful supplier metrics:

- on-time return rate;
- yield/accepted quantity;
- unexplained material variance;
- scrap rate;
- rework rate;
- quality rejects;
- average processing lead time;
- cost variance;
- company-owned inventory currently at supplier;
- overdue consigned inventory.

These should derive from actual orders/transactions, not subjective scoring alone.

## 16. Exceptions

High-value exception types:

- overdue return;
- material sent but order not acknowledged;
- returned quantity mismatch;
- unexplained consigned-material loss;
- unapproved substitute used;
- output revision/package mismatch;
- failed inspection;
- processing cost exceeds tolerance;
- supplier stock confirmation mismatch;
- order closed while company-owned material remains unresolved.

Closing must be blocked when reconciliation invariants fail unless an authorized variance disposition exists.

## 17. Permissions

Suggested control split:

- production/planner: create subcontract requirement;
- procurement: supplier/price/PO approval;
- warehouse: dispatch and receive physical material;
- engineering: approve package and substitutions;
- quality: release/reject returned output;
- finance/admin: invoice/cost reconciliation;
- manager: approve significant scrap/loss variance.

## 18. Minimal target schema

```text
subcontract_orders
subcontract_material_lines
subcontract_shipments
subcontract_receipts
subcontract_output_lines
subcontract_cost_lines
subcontract_variances
```

Use the shared inventory ledger and lot/serial tables; do not maintain a separate quantity universe.

## 19. Priority roadmap

### P0

1. subcontract order lifecycle;
2. company-owned consigned stock state;
3. material dispatch/return reconciliation;
4. partial output receipt;
5. quality gate;
6. processing cost line;
7. released document/BOM reference.

### P1

1. lot/serial genealogy;
2. supplier-provided vs company-provided material split;
3. PO/invoice linkage;
4. scrap/rework/variance approval;
5. supplier performance metrics;
6. MRP scheduled return integration.

### P2

1. supplier portal/acknowledgement;
2. electronic stock confirmation;
3. automated ASN/status exchange;
4. advanced subcontract capacity planning.

## 20. Acceptance signals

- company-owned material sent to a subcontractor disappears from local ATP but remains visible as company-owned external WIP;
- partial returns do not close unresolved quantities;
- sent quantity reconciles to consumed/returned/scrapped/variance;
- returned output enters the correct quality state;
- a returned lot/serial resolves the exact released manufacturing package and source WO/subcontract order;
- processing fees are not double-counted with company material;
- overdue/unreconciled consigned stock is actionable;
- a subcontract order cannot close with unexplained company-owned material unless an approved variance disposition exists;
- no required operational/validation path depends on GitHub Actions.

## 21. Core recommendation

Model subcontracting as **external WIP with retained ownership and explicit material transformation**, linked to but separate from normal purchasing. Reuse existing transfer/procurement/ledger primitives where they fit, while adding reconciliation, quality, released-package and processing-cost semantics.