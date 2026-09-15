# TASK_INV_AUDIT_QC_NCR_01 — Incoming, In-process and Final Quality Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed procurement/receipt, inventory, warehouse, shipment and operation-log foundations together with searches for first-class quarantine, inspection, NCR and scrap semantics in the inspected core database/service layer.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The current application can receive inventory and record generic stock movements, but it does not yet provide a first-class quality-management state machine. In the inspected service layer, dedicated `quarantine` and `scrap` workflow semantics were not found. This means a received component can become ordinary inventory without an authoritative model for pending inspection, accepted quantity, rejected quantity, MRB disposition or supplier corrective action.

For electronics/RF manufacturing this is a material operational gap, because inventory quantity alone cannot answer whether the stock is **usable**.

Preliminary maturity:

- receiving quantity control: 3/5
- quality stock state: 0.5/5
- IQC records: 0.5/5
- in-process/final QC: 0/5
- NCR/MRB/rework: 0/5
- supplier quality loop: 0.5/5

## 2. Core principle: quality status is inventory semantics

Quality should not exist only as a report attachment or remark.

At minimum, stock must distinguish:

```text
PENDING_INSPECTION
ACCEPTED
QUARANTINE
REJECTED
REWORK
SCRAP
```

Depending on the business, additional states such as `CONCESSION_ACCEPTED`, `RETURN_TO_VENDOR` or `HOLD` may be useful.

Only policy-approved states should count toward normal sales ATP and MRP nettable supply.

This is a hard dependency for trustworthy MRP and work-order allocation.

## 3. IQC — incoming quality control

Purchase receipt currently provides an excellent trigger point for quality control.

Recommended flow:

```text
PO receipt
 -> received physically
 -> PENDING_INSPECTION / quarantine stock
 -> IQC inspection
 -> accepted quantity released
 -> rejected quantity -> MRB / RTV / scrap / rework
```

Do not use a boolean `passed` on the PO receipt because one line/lot may be partially accepted and partially rejected.

Minimum IQC record:

```text
inspection_orders
  id
  inspection_no
  inspection_type: IQC | IPQC | FQC | OQC
  source_type
  source_id
  material_id
  lot_id
  quantity_presented
  sampling_plan_id
  status
  inspector_id
  started_at/completed_at

inspection_results
  inspection_id
  characteristic_id or characteristic_name_snapshot
  specification_snapshot
  method_snapshot
  sampled_qty
  defect_qty
  measured_value/result
  result: pass | fail | conditional
  evidence_attachment
```

## 4. Sampling and acceptance policy

Do not hard-code one global sampling standard into the application.

The system should support configurable policies by:

- material category;
- supplier risk;
- product/revision;
- inspection type;
- criticality;
- lot size;
- customer/regulatory requirement.

For early implementation, allow simple policies:

- inspect all;
- fixed sample quantity;
- external sampling-plan reference.

If later implementing standards such as ISO 2859/AQL, store the selected plan/version and do not pretend one threshold applies universally.

## 5. Electronics-specific incoming checks

Examples that the data model should be able to represent without special columns for every component:

- manufacturer/MPN verification;
- package/marking check;
- quantity;
- date code/lot;
- physical damage;
- solderability/moisture-sensitive packaging where relevant;
- key electrical parameter spot check;
- certificate/document presence;
- counterfeit-risk evidence;
- PCB dimensions/revision/finish;
- enclosure/mechanical dimensions.

Use configurable inspection characteristics/limit sets rather than expanding the receipt table repeatedly.

## 6. NCR — nonconformance record

A failed inspection needs a business object, not only `reason='failed'`.

Minimum NCR:

```text
ncr_records
  id
  ncr_no
  source_type/id
  material_id/product_id
  lot_id/serial_id
  defect_category
  defect_description
  quantity_affected
  severity
  status
  owner_user_id
  opened_at
  closed_at

ncr_dispositions
  ncr_id
  disposition: use_as_is | rework | return_to_vendor | scrap | sort | deviation
  quantity
  approved_by
  engineering_approval_id
  quality_approval_id
  reason
```

A single NCR may split quantity across dispositions.

## 7. MRB — material review board

The company may not need a formal committee UI, but the decision roles should still be explicit for consequential defects.

Typical participation:

- quality;
- engineering;
- production;
- procurement/supplier owner;
- product owner when customer impact exists.

For a low-volume RF business, implement a lightweight approval chain rather than a heavy workflow engine.

Critical rule: warehouse personnel should not be able to make rejected stock saleable merely by editing quantity/location.

## 8. IPQC — in-process quality

Work-order execution should support inspection/checkpoints such as:

- visual assembly inspection;
- solder/placement check;
- torque/mechanical check;
- intermediate DC current/voltage;
- calibration/tuning checkpoint;
- cleaning/labeling check.

These may be attached to work-order operations later. Initially, a work-order-linked inspection record is enough.

Do not confuse process completion with quality acceptance.

## 9. FQC/OQC — final and outgoing quality

Finished RF modules often require a final electrical/RF acceptance test before being saleable.

Recommended state transition:

```text
WO output physically completed
 -> pending final test
 -> PASS -> released finished stock
 -> FAIL -> NCR / rework / scrap
```

OQC can then verify shipment-level requirements such as:

- right model/revision/serial;
- accessories;
- test report/certificate;
- packaging;
- labeling;
- customer-specific documentation.

## 10. Test integration

Quality disposition should reference test records instead of copying arbitrary numbers into the NCR.

Example:

```text
Serial ZXYH-...
 -> Test Run TR-...
 -> Limit Set RF-AMP-V3
 -> Gain FAIL
 -> NCR NCR-...
 -> Rework
 -> Retest PASS
 -> Quality release
```

The original failure must remain visible after retest.

## 11. Rework

Rework is not a generic stock adjustment.

Track:

- NCR source;
- rework instruction/document revision;
- assigned person;
- material/components consumed;
- resulting revision/firmware if changed;
- retest requirement;
- outcome.

For serialized modules, rework belongs permanently to that serial's history.

## 12. Scrap

Scrap must be an explicit disposition with financial and inventory consequences.

Required information:

- source document (NCR/WO/engineering issue/etc.);
- material/lot/serial;
- quantity;
- reason category;
- approver when required;
- cost impact;
- timestamp;
- evidence where useful.

Never delete a serial or lot row to represent scrap.

## 13. Supplier quality

Procurement already captures supplier relationships and purchase history; quality should close the loop.

Supplier metrics should include:

- incoming lots received;
- acceptance/rejection rate;
- defect PPM or simpler defect ratio;
- NCR count/severity;
- return-to-vendor quantity/value;
- response/closure time;
- recurring defect categories;
- on-time delivery (from procurement audit);
- SCAR/CAPA status where used.

Do not create a single opaque supplier score without the underlying metrics.

## 14. SCAR/CAPA

For recurring or severe supplier defects, support a lightweight Supplier Corrective Action Request:

```text
SCAR opened
 -> supplier response
 -> root cause
 -> containment
 -> corrective action
 -> verification
 -> closed
```

Internal CAPA may be deferred until volume/process maturity requires it, but the data model should not prevent it.

## 15. Quality specifications and limits

Inspection specifications must be revision-controlled.

Store a snapshot/reference to the exact inspection plan/limit set used. If limits later change, historical results must not be reinterpreted as if measured under the new release.

This aligns with document control and test-record requirements.

## 16. Quality stock ledger

Preferred design:

- common physical stock ledger;
- stock position includes quality state/lot/serial dimensions;
- disposition transaction moves quantity between states.

Example:

```text
RECEIPT: +100 PENDING_INSPECTION
IQC_ACCEPT: -95 PENDING / +95 ACCEPTED
IQC_REJECT: -5 PENDING / +5 QUARANTINE
RTV: -5 QUARANTINE
```

This makes reconciliation much easier than maintaining separate disconnected quarantine spreadsheets.

## 17. Permissions and audit

Minimum controls:

- receiver: create physical receipt, not approve own IQC by default;
- quality: inspect and release/reject;
- engineering: approve technical deviation/use-as-is when required;
- warehouse: execute disposition movements;
- procurement: manage RTV/supplier follow-up;
- admin: configure plans/roles, not rewrite closed quality history.

Closed NCR/inspection records should be append-only or revisioned with explicit reopening/correction.

## 18. Dashboard and exception views

High-value quality KPIs:

- pending IQC quantity/value/age;
- overdue inspections;
- quarantine value;
- top defect categories;
- first-pass yield for finished products;
- rework rate;
- scrap cost;
- supplier reject trend;
- repeat NCRs;
- failed test awaiting disposition.

The dashboard should link directly to actionable records.

## 19. Priority roadmap

### P0

1. quality stock states and release gate;
2. IQC inspection order/result;
3. NCR + disposition;
4. partial accept/reject by lot/quantity;
5. quarantine exclusion from MRP/ATP;
6. finished-test release gate.

### P1

1. IPQC/FQC/OQC types;
2. configurable inspection plans/limit sets;
3. MRB approvals;
4. rework/retest chain;
5. supplier quality KPIs and RTV link.

### P2

1. SCAR/CAPA;
2. risk-based dynamic sampling;
3. statistical quality analytics;
4. automated test-station integration.

## 20. Acceptance signals

- a new receipt can remain physically on-hand while unavailable because IQC is pending;
- one received lot can be partially accepted and partially quarantined;
- rejected quantity cannot silently re-enter available stock;
- an NCR captures affected quantity and final disposition;
- a failed finished-unit test blocks saleable release until approved disposition/retest;
- scrap remains traceable to lot/serial/WO/NCR and cost;
- supplier quality history can be calculated from actual records;
- historical inspection uses the exact specification/limit revision that was valid at execution;
- no acceptance test requires GitHub Actions.

## 21. Core recommendation

Make **quality disposition a first-class stock state transition**, then layer IQC/NCR/MRB/rework records around it. This prevents unusable material from contaminating MRP and customer fulfilment while creating the foundation for supplier quality and RF-module test traceability.