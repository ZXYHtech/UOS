# TASK_INV_AUDIT_TEST_RECORD_01 — Product Test Data, Limits and Equipment Traceability Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed material/resources/attachments, operation logs, order/manufacturing gaps, and searched the inspected service layer for first-class calibration/test-record semantics. Material resources provide useful generic document linkage, but the current model does not yet establish serial/lot-to-test-run-to-instrument/calibration traceability.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

For an RF/electronics company, product test data should be treated as **structured manufacturing evidence**, not only as screenshots or attached reports.

The current application already has generic attachment/resource primitives and can associate documents with materials, but a product-level test system needs additional first-class entities:

- test specification / limit-set revision;
- test run;
- DUT serial/lot;
- measured characteristics;
- raw data artifact;
- instrument identity;
- calibration status at test time;
- operator/station/software version;
- pass/fail and release decision;
- rework/retest relationship.

In the inspected service layer, first-class `calibration` semantics were not found. Preliminary test-record maturity: **0.5/5**.

## 2. Why screenshots are insufficient

A PNG of a network-analyzer trace is useful evidence but cannot reliably answer:

- which serial number was measured;
- which product/BOM revision was under test;
- which limit set was applied;
- what the numeric S21/S11 values were;
- whether the trace was before or after rework;
- which VNA and calibration kit/state were used;
- whether the instrument calibration was valid;
- whether the operator changed settings;
- whether the same raw data can be re-evaluated later.

Therefore preserve the **raw machine-readable file + structured summary + rendered evidence** where practical.

For RF measurements, Touchstone (`.s1p/.s2p/...`) is substantially more reusable than a screenshot alone.

## 3. Test hierarchy

Recommended conceptual layers:

```text
Test Procedure / Specification
  -> Limit Set Revision
  -> Test Run
      -> DUT serial/lot
      -> Test Conditions
      -> Measurements
      -> Raw Artifacts
      -> Instrument Session
  -> Result / disposition
```

Do not store product acceptance limits only in frontend code or operator memory.

## 4. Test specification and limit-set revision

A historical test must resolve the exact rules used at that time.

```text
test_specifications
  id
  spec_code
  name
  product/material scope
  revision_code
  status: draft | released | obsolete
  effective_from/to
  controlled_document_id

limit_sets
  id
  test_spec_revision_id
  product_revision_scope
  test_item_code
  frequency/condition dimensions
  comparison/operator
  lower_limit
  upper_limit
  unit
```

Not every complex RF mask should be forced into simple scalar min/max rows; allow a structured JSON/mask artifact when needed, but version it and keep deterministic evaluation.

## 5. Test-run identity

Each execution should have a stable ID.

```text
test_runs
  id
  test_run_no
  serial_id / lot_id
  work_order_id
  product_material_id
  product_revision_id
  test_spec_revision_id
  station_id
  operator_user_id
  started_at
  completed_at
  result: pass | fail | aborted | invalid
  retest_of_test_run_id
  software_version
  notes
```

An aborted or invalid run should remain historically visible; do not delete it simply because a later run passes.

## 6. RF/electrical measurement model

The system should represent both generic scalar measurements and richer traces.

### Scalar examples

- DC current;
- supply voltage;
- gain at specified frequency;
- noise figure;
- output power;
- insertion loss;
- return loss/VSWR;
- frequency error;
- attenuation state error;
- harmonic/spurious result.

### Trace/artifact examples

- `.s2p` S-parameters;
- spectrum CSV/binary export;
- VNA state or screenshot;
- power sweep;
- frequency sweep;
- calibration/tuning log;
- generated PDF test report.

Recommended result record:

```text
test_measurements
  test_run_id
  item_code
  condition_json
  measured_value
  unit
  lower_limit
  upper_limit
  result
  source_artifact_id
```

Limits may be snapshot values copied from the released limit set so historical evaluation remains explainable.

## 7. Raw data retention

Use current attachment/resource infrastructure as storage building blocks, but add test-specific references and immutable hashes.

For each artifact record:

- original filename;
- MIME/file type;
- SHA-256 or equivalent checksum;
- file size;
- capture/export software version when relevant;
- test-run reference;
- artifact type (`touchstone`, `spectrum_csv`, `screenshot`, `report`, `station_log`, etc.);
- original vs derived status.

Rendered PNG/PDF should be treated as derivatives of raw data when that relationship exists.

## 8. Instrument master

Create an equipment register rather than typing `VNA1` into notes.

```text
test_equipment
  id
  asset_code
  equipment_type
  manufacturer
  model
  serial_no
  owner/location
  status
  calibration_required
  calibration_interval/reference
```

Possible RF assets:

- VNA;
- spectrum analyzer;
- signal generator;
- power meter/sensor;
- noise figure analyzer/source;
- oscilloscope;
- DMM;
- programmable PSU;
- attenuator/coupler/cal kit where controlled.

## 9. Calibration records

For controlled equipment:

```text
equipment_calibrations
  equipment_id
  certificate_no
  calibrated_at
  valid_until
  provider
  result/status
  certificate_attachment_id
  uncertainty/reference (optional)
```

At test execution, capture the instrument/calibration snapshot used.

Important rule:

A test should not simply ask whether the instrument is calibrated **now**. It must answer whether calibration was valid **when the test ran**.

## 10. Test setup/session traceability

A test run may use multiple instruments. Add a join table:

```text
test_run_equipment
  test_run_id
  equipment_id
  role
  calibration_record_id
  setup_state/reference
```

For measurements where local VNA calibration or fixture de-embedding matters, optionally record:

- calibration type/state identifier;
- calibration performed timestamp;
- port/cable/fixture identity;
- fixture/de-embedding file version;
- reference plane note.

Avoid trying to make the inventory system itself a VNA. It should preserve the evidence and configuration contract.

## 11. Firmware/software traceability

For programmable RF modules, test result validity may depend on firmware.

Capture:

- firmware build/version;
- configuration/profile version;
- test-station software version;
- script revision/hash when automation is used.

This should link to controlled document/artifact records rather than free-text only.

## 12. Automatic ingestion

A high-value future workflow is a station-local uploader/API:

```text
instrument/test script
 -> create test run
 -> upload raw artifacts
 -> post structured measurements
 -> server evaluates released limits
 -> operator reviews exceptions
 -> quality disposition
```

Required operational paths must remain independent of GitHub Actions. Use a local agent, service endpoint, queue/worker or other production-owned mechanism.

## 13. Human-entered test results

Manual entry must remain possible for small-volume processes, but control it:

- predefined test item and unit;
- numeric validation;
- limit display;
- operator identity;
- reason for override;
- attachment when required;
- second approval for critical overrides.

Do not allow a user to type `PASS` without measurements when the procedure requires numeric evidence.

## 14. Retest and rework

Never replace a failed test with the final pass.

Use a chain:

```text
TR-001 FAIL
 -> NCR / rework
 -> TR-002 PASS (retest_of=TR-001)
```

Serial history should display both and explain why the unit was ultimately released.

## 15. Quality-release interaction

The test engine supplies evidence; quality workflow controls disposition.

Recommended rules:

- mandatory test missing -> cannot release;
- latest required valid test fails -> cannot release;
- instrument calibration invalid -> test may be invalid/require review;
- override -> explicit authorization and reason;
- final quality release -> references accepted test runs.

Do not encode all quality authority inside the test endpoint itself.

## 16. Test report generation

A customer-facing/internal report can be generated from structured data:

- product/model/revision;
- serial/lot;
- test date;
- key results;
- plots generated from raw data;
- equipment list;
- report template revision;
- pass/fail;
- approval/signature where needed.

Generated report should retain a link to the underlying test run and artifact checksum.

This aligns well with the company's existing RF module report generation workflows and can reduce manual screenshot/report assembly later.

## 17. Data volume and storage strategy

Do not put large binary traces directly in normal relational columns.

Recommended split:

- relational DB: metadata, numeric summaries, relationships, checksums;
- file/object storage: raw/derived artifacts;
- retention rules by artifact type/product/customer requirement;
- backups include both DB and referenced file store, with integrity verification.

A cleanup job must never delete a raw artifact still referenced by a released test record.

## 18. Minimum queries

The system should answer:

- show all tests for serial X;
- show the exact raw S2P for final released test;
- show which limit-set revision evaluated it;
- show which VNA and calibration record were used;
- show all units tested with an instrument during a calibration-invalid period;
- show failure/retest rate by product/revision;
- show a measurement trend across production lots;
- show firmware versions associated with failures.

## 19. Priority roadmap

### P0

1. finished serial/lot identity dependency;
2. released test specification + limit-set revision;
3. test-run entity;
4. structured scalar measurements;
5. raw artifact linkage/checksum;
6. equipment master + calibration record;
7. pass/fail integration with quality release.

### P1

1. Touchstone/spectrum ingestion;
2. automatic plot/report generation;
3. local station uploader/API;
4. rework/retest chain;
5. firmware/test-software traceability;
6. calibration-expiry exceptions.

### P2

1. statistical trend/SPC views;
2. automatic instrument adapters;
3. fixture/de-embedding configuration management;
4. advanced measurement uncertainty tracking where justified.

## 20. Acceptance signals

- every released serialized RF module resolves at least one valid required test run;
- a test run records the exact test/limit revision;
- a numeric result retains unit, condition and evaluated limits;
- a raw S2P/trace artifact has immutable hash and DUT/test-run linkage;
- equipment and its calibration validity at execution time can be proven;
- a failed test remains visible after rework and passing retest;
- changing current limits does not retroactively rewrite historical pass/fail evidence;
- generated reports are reproducible from stored structured/raw data;
- no required ingestion, validation or report path depends on GitHub Actions.

## 21. Core recommendation

Treat test data as an **evidence graph around the DUT serial**: released limits + structured measurements + raw artifacts + equipment/calibration + operator/software + quality disposition. This is the minimum architecture that turns RF test records into reusable manufacturing, support and product-quality data instead of isolated screenshots.