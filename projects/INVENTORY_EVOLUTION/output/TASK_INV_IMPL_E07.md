# TASK_INV_IMPL_E07 — Lot/Serial Genealogy, Quality and RF Test Evidence

## Status

`DESIGN_READY_BLOCKED_BY_E06_GATE`

E07 is design-only while earlier runtime gates remain open.

## 1. Objective

Create risk-based traceability and quality/test evidence suitable for RF/electronics manufacturing without forcing excessive serialization onto every low-value component.

Target evidence chain:

```text
supplier / PO / receipt
 -> lot / date code where required
 -> quality disposition
 -> E02 stock position
 -> E06 WO issue
 -> component genealogy
 -> finished output serial / lot
 -> firmware/configuration
 -> RF/electrical test runs
 -> raw artifacts + structured measurements
 -> instrument/calibration evidence
 -> NCR/rework/retest when needed
 -> final quality release
 -> shipment/customer
```

## 2. Domain boundaries

```text
E02 = stock movement/balance + stock-state dimensions
E03 = location/scan warehouse execution
E04 = part/MPN/source identity + engineering approval
E05 = product/BOM/document/firmware/test-spec release identity
E06 = WO material/output execution
E07 = trace policy + lot/serial genealogy + quality disposition + test evidence + release
E10 = customer support/RMA workflow later
```

E07 adds trace/quality dimensions to E02; it does not create a disconnected inventory system.

## 3. Risk-based traceability policy

Suggested policy values:

```text
NONE
LOT
SERIAL
LOT_AND_SERIAL
```

Optional capture requirements:

```text
supplier_lot_required
manufacturer_lot_required
date_code_required
expiry_required
certificate_required
finished_serial_required
quality_inspection_required
final_test_required
```

Examples:

- 0402 passive: NONE or LOT for critical product families;
- MMIC / SAW / RF switch: LOT/date-code where risk justifies;
- bare PCB: LOT + board revision;
- finished RF module: SERIAL;
- calibrated/programmable module: SERIAL + test/firmware history.

Do not serial-track every passive by default.

## 4. Lot identity

Suggested object:

```text
stock_lots
  id
  material_id
  internal_lot_no
  supplier_id
  supplier_part_id
  manufacturer_part_id
  supplier_lot_no
  manufacturer_lot_no
  date_code
  manufactured_at
  expiry_at
  source_receipt_id
  status
  created_at
```

One PO receipt line may create multiple lots.

Material identity of a lot cannot silently change after stock movements exist.

## 5. Serial identity

Suggested:

```text
serial_units
  id
  material_id
  serial_no
  lot_id
  product_revision_id
  work_order_id
  status
  created_at
  retired_at
```

Current physical position/quality state should resolve through E02 position/ledger relations rather than being manually duplicated as an independent balance truth where avoidable.

For internally generated finished-product serials, global uniqueness is preferred unless a documented namespace policy says otherwise.

Never recycle a historical serial number.

## 6. Quality state is stock semantics

Minimum quality-state vocabulary:

```text
PENDING_INSPECTION
ACCEPTED
QUARANTINE
REJECTED
REWORK
SCRAP
```

Optional later states only with clear business meaning, e.g.:

```text
CONCESSION_ACCEPTED
RETURN_TO_VENDOR
HOLD
```

Quality status changes happen through E02 movement/disposition operations, not a free-text edit on a lot/serial row.

Only policy-approved states count toward normal ATP/MRP/WO allocation.

## 7. Receiving + IQC

For controlled incoming material:

```text
PO receipt
 -> capture lot/date-code/certificate evidence
 -> stock enters PENDING_INSPECTION
 -> IQC inspection
 -> accepted qty -> ACCEPTED
 -> failed/uncertain qty -> QUARANTINE / NCR
```

Partial acceptance/rejection is required.

Do not use one boolean `receipt.passed`.

## 8. Inspection model

Suggested:

```text
inspection_orders
  id
  inspection_no
  inspection_type        IQC|IPQC|FQC|OQC
  source_type/id
  material_id
  lot_id
  serial_id
  work_order_id
  quantity_presented
  inspection_plan_revision_id
  status
  inspector_id
  started_at/completed_at

inspection_results
  id
  inspection_id
  characteristic_code/snapshot
  method_snapshot
  limit_snapshot
  sampled_quantity
  defect_quantity
  measured_value / result_json
  result
  evidence_attachment_id
```

Sampling policy is configurable and versioned. Do not hard-code one universal AQL/standard.

## 9. NCR / MRB-lite

Failed/uncertain material or product needs first-class NCR:

```text
ncr_records
  id
  ncr_no
  source_type/id
  material_id
  lot_id
  serial_id
  work_order_id
  defect_category
  defect_description
  quantity_affected
  severity
  status
  owner_user_id
  opened_at/closed_at

ncr_dispositions
  ncr_id
  disposition
  quantity
  approved_by
  engineering_authority_id
  quality_authority_id
  reason
```

Possible dispositions:

```text
use_as_is
rework
return_to_vendor
scrap
sort
engineering_deviation
```

One NCR can split quantity among dispositions.

## 10. Rework

Rework is history, not an edit that removes the failure.

Track:

```text
NCR source
rework instruction revision
serial/lot/WO
assigned operator
materials consumed
firmware/revision change if any
retest requirement
outcome
```

For serialized units, rework remains permanently visible on serial history.

## 11. Genealogy

Manufacturing trace must answer:

```text
component lot/serial
 -> WO issue
 -> exact WO + MBOM/product revision
 -> output lot/finished serial
```

Suggested explicit relations:

```text
output_genealogy_links
  id
  work_order_id
  output_serial_id / output_lot_id
  consumed_material_id
  consumed_lot_id / consumed_serial_id
  quantity
  issue_movement_line_id
  relation_type
  created_at
```

Name direction explicitly; avoid ambiguous `parent/child` terminology.

## 12. Genealogy granularity

Support honest modes:

### WO/output-lot level

Consumed component lots are linked to an output lot/WO batch.

### Per-finished-serial level

Consumed critical component lot/serial is linked to each output serial when shop-floor capture actually supports it.

Never claim per-serial component genealogy when process only captured WO-level consumption.

## 13. Finished serial generation

When product trace policy requires SERIAL:

- E06 output cannot be finalized into serialized stock without required unique serial identity;
- serial generation/allocation is deterministic and collision-safe;
- printed barcode/QR resolves the serial entity;
- static label does not encode mutable quality state as truth.

## 14. Test specification boundary

E05 controls released test procedure/document/limit-set identity.

E07 consumes exact released revisions during execution and snapshots evaluated limits/conditions where needed for historical explanation.

Do not store acceptance limits only in frontend code, operator memory or test scripts with no released identity.

## 15. Test run

Suggested:

```text
test_runs
  id
  test_run_no
  serial_id / lot_id
  work_order_id
  product_material_id
  product_revision_id
  test_spec_revision_id
  limit_set_revision_id
  station_id
  operator_user_id
  started_at/completed_at
  result              pass|fail|aborted|invalid
  retest_of_test_run_id
  firmware_release_id
  station_software_version
  notes
```

Failed/aborted/invalid runs remain historical after a later passing retest.

## 16. Structured measurements

Suggested:

```text
test_measurements
  id
  test_run_id
  item_code
  condition_json
  measured_value
  measured_text/json
  unit
  lower_limit_snapshot
  upper_limit_snapshot
  evaluation_rule_snapshot
  result
  source_artifact_id
```

Support scalar and richer structured results.

## 17. RF raw artifacts

Examples:

- Touchstone `.s1p/.s2p/...`;
- spectrum CSV/binary export;
- VNA state/screenshot;
- gain/power sweep;
- NF result export;
- calibration/tuning log;
- generated PDF report.

Suggested metadata:

```text
test_artifacts
  test_run_id
  artifact_type
  attachment_id / storage_key
  original_filename
  mime/file type
  sha256
  file_size
  original_or_derived
  derived_from_artifact_id
  exporter/software metadata
```

Raw machine-readable data is preferred over screenshot-only evidence when available.

## 18. Equipment / calibration

Suggested:

```text
test_equipment
  id
  asset_code
  equipment_type
  manufacturer
  model
  serial_no
  location
  status
  calibration_required

equipment_calibrations
  id
  equipment_id
  certificate_no
  calibrated_at
  valid_until
  provider
  result/status
  certificate_attachment_id

test_run_equipment
  test_run_id
  equipment_id
  role
  calibration_record_id
  setup_state_reference
```

A historical test asks whether calibration was valid **at execution time**, not whether the instrument is calibrated today.

## 19. RF setup provenance

Where relevant capture:

- local VNA calibration state/id;
- calibration performed timestamp;
- cables/ports/fixture identity;
- de-embedding file/revision;
- reference plane note;
- attenuation/gain correction configuration.

Do not turn Inventory Lite into an instrument-control application; preserve evidence and configuration contract.

## 20. Firmware/software provenance

Test run should reference E05 controlled firmware release when applicable plus station software/script revision/hash.

Historical test validity must not depend on an unversioned filename such as `final.py` or `v2.bin`.

## 21. Quality release

Test engine supplies evidence; quality controls release.

Example finished RF flow:

```text
E06 physical output
 -> pending final quality/test state
 -> required test runs
 -> PASS evidence
 -> quality release disposition
 -> E02 stock becomes eligible/saleable
```

Rules:

- mandatory test missing => no release;
- required latest valid test FAIL => no normal release;
- invalid calibration can mark test invalid/require review;
- override requires separate authority/reason;
- release references accepted inspection/test evidence.

## 22. Shipment trace

When serial tracking required, shipment preserves exact serial(s)/lot(s) delivered.

Queries:

```text
serial -> shipment -> order/customer/date
customer shipment -> serials/lots
```

E10 RMA later reuses this identity/history.

## 23. Recall / impact queries

Minimum deterministic questions:

- where is serial X?
- which customer received serial X?
- which WO/product/MBOM revision created serial X?
- which component lots were used?
- which finished outputs used supplier lot Y?
- which PO/receipt/supplier introduced lot Y?
- which tests/reworks occurred on serial X?
- which units were tested on equipment during a calibration-invalid interval?

## 24. Legacy migration

Do not fabricate traceability.

Migration:

```text
add trace policy
 -> new controlled receipts start lot capture
 -> legacy existing stock marked explicit LEGACY_UNTRACED where needed
 -> finished serial generation begins at controlled cutover
 -> shipment/test genealogy from cutover forward
```

Old stock can be used according to policy, but evidence boundaries remain visible.

## 25. Backup / retention

E00 recovery must cover:

- DB metadata;
- raw test artifacts;
- controlled certificates/documents;
- hashes/storage keys.

A DB restore with missing released RF test raw data is incomplete where retention policy requires that evidence.

Cleanup/retention never deletes an artifact still referenced by retained/released test evidence.

## 26. Required tests

### Trace identity

- trace policy enforced by material/product;
- unique serial; never recycled;
- receipt can split multiple lots;
- legacy stock stays explicitly untraced rather than invented.

### Quality

- pending/quarantine excluded from normal ATP/MRP;
- partial accept/reject balances exactly;
- quality state transitions post E02 movements/dispositions;
- warehouse cannot simply edit rejected stock back to accepted.

### Genealogy

- consumed lot links to correct WO/output;
- query supplier lot -> affected outputs deterministic;
- per-serial claim allowed only when capture evidence exists.

### Test

- run binds exact DUT/config/limit revision;
- raw artifact checksum immutable;
- measurements retain unit/condition/evaluated limits;
- changing current limits does not rewrite historical result;
- failed run remains after passing retest;
- equipment calibration validity evaluated at run time.

### Release

- missing/failed mandatory test blocks normal release;
- override requires explicit quality authority/reason;
- released serial can be linked to shipment/customer.

## 27. Definition of done

E07 is complete only when:

- traceability policy is risk-based;
- lot/serial identity is first-class;
- quality state is part of authoritative stock semantics;
- IQC/NCR/rework/scrap are controlled;
- WO consumption can generate honest genealogy;
- finished RF serial links to exact released configuration/firmware;
- structured test + raw RF artifacts are retained;
- equipment/calibration-at-test-time is provable;
- quality release gates saleable stock;
- shipment/customer trace is deterministic;
- legacy untraced evidence is labeled honestly;
- no required ingestion/worker/release path depends on GitHub Actions.
