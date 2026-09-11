# TASK_INV_IMPL_E07_S07 — RF/Electrical Test Run, Measurements and Raw Artifacts

## Status

`DESIGN_READY_BLOCKED_BY_E07_S01_S06`

## Objective

Treat RF/electrical test data as structured manufacturing evidence around a DUT serial/lot, preserving raw machine-readable artifacts and deterministic evaluated measurements rather than screenshot-only proof.

## Test run identity

Suggested:

```text
test_runs
  id
  test_run_no
  serial_id
  lot_id
  work_order_id
  product_material_id
  product_revision_id
  test_spec_revision_id
  limit_set_revision_id
  station_id
  operator_user_id
  started_at
  completed_at
  result
  retest_of_test_run_id
  firmware_release_id
  station_software_version
  station_script_revision
  notes
```

Result vocabulary:

```text
pass
fail
aborted
invalid
```

Aborted/invalid/failed runs remain historical.

## Measurements

Suggested:

```text
test_measurements
  id
  test_run_id
  item_code
  sequence_no
  condition_json
  measured_value
  measured_text
  unit
  lower_limit_snapshot
  upper_limit_snapshot
  evaluation_rule_snapshot
  result
  source_artifact_id
```

Examples:

- DC current/voltage;
- gain at frequency;
- NF;
- P1dB/output power;
- insertion loss;
- S11/S22/VSWR;
- isolation;
- attenuation-state error;
- harmonic/spur values.

## Raw artifacts

Suggested:

```text
test_artifacts
  id
  test_run_id
  artifact_type
  attachment_id / storage_key
  original_filename
  mime_type
  sha256
  file_size
  original_or_derived
  derived_from_artifact_id
  exporter_name/version
  created_at
```

Artifact types include:

```text
touchstone
spectrum_data
screenshot
power_sweep
nf_export
station_log
calibration_log
report
other
```

## Raw-before-rendered principle

When instrument/script can export raw data:

```text
raw machine-readable artifact
 -> structured summary/measurements
 -> rendered plot/report derivative
```

A PNG/PDF does not replace `.s2p`, CSV or original measurement export when retention policy requires raw evidence.

## Touchstone

For `.s1p/.s2p/...` retain:

- original bytes/hash;
- port count/format metadata if parsed;
- frequency range/point count summary;
- derived plots linked back to raw artifact;
- no destructive rewrite during visualization/report generation.

## Deterministic evaluation

Server/test service evaluates released E07-S06 limits from structured/raw data where supported.

AI may later summarize or flag anomalies but cannot decide production PASS/FAIL in place of deterministic released rules.

## Retest

```text
TR-001 FAIL
 -> NCR/rework
 -> TR-002 PASS, retest_of=TR-001
```

Both remain visible. Final release references accepted valid run(s), not just “latest row”.

## Automatic ingestion

Future local station uploader/API may:

```text
create run
upload raw artifact
post measurements
complete run
```

Use E01 idempotency/jobs where needed. Required production path is server/local-agent owned, never GitHub Actions.

## Manual entry

Permitted with:

- predefined item/unit;
- validation;
- operator identity;
- required evidence policy;
- override reason/permission when deterministic result is overridden.

Do not allow free-text `PASS` when mandatory numeric evidence is required.

## Tests

- run binds exact DUT/config/spec/limit revisions;
- failed/aborted/invalid retained;
- measurement condition/unit/limits preserved;
- raw artifact hash detects replacement;
- derived plot points back to raw artifact;
- same ingestion operation does not duplicate run/artifact;
- current limit changes do not mutate historical result;
- retest chain preserves original failure;
- missing mandatory raw/structured evidence blocks valid completion according to policy.

## Acceptance

For a finished RF serial, the system can retrieve exact structured results and original raw traces that produced its historical test decision, not merely a screenshot or operator-entered PASS.
