# TASK_INV_IMPL_E07_S08 — Test Equipment, Calibration and Setup Provenance

## Status

`DESIGN_READY_BLOCKED_BY_E07_S07`

## Objective

Prove which equipment and calibration/setup state were valid when an RF/electrical test ran, rather than relying on free-text instrument names or today’s calibration status.

## Equipment master

Suggested:

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
  calibration_policy_reference
  created_at
```

Examples:

- VNA;
- spectrum analyzer;
- signal generator;
- power meter/sensor;
- noise source/analyzer;
- oscilloscope;
- DMM;
- PSU;
- controlled attenuator/coupler/calibration kit.

## Calibration records

```text
equipment_calibrations
  id
  equipment_id
  certificate_no
  calibrated_at
  valid_from
  valid_until
  provider
  result_status
  certificate_attachment_id
  uncertainty_reference
  created_at
```

Never overwrite prior calibration record when a new calibration occurs.

## Test-run equipment join

```text
test_run_equipment
  test_run_id
  equipment_id
  role
  calibration_record_id
  calibration_valid_at_run
  setup_state_reference
  notes
```

The join freezes the calibration evidence selected at execution.

## Calibration-at-test-time rule

For controlled equipment, test validity evaluates:

```text
run timestamp within selected calibration validity
AND calibration result acceptable
AND equipment status permitted
```

Whether equipment is calibrated **today** is irrelevant to a historical run.

## Local RF calibration / de-embedding

Where significant, capture optional setup artifacts/metadata:

- VNA SOLT/TRL/ECal state identifier;
- local calibration timestamp;
- calibration kit identity;
- cable/fixture identity;
- reference plane;
- de-embedding file revision/hash;
- correction/attenuation configuration.

These may link to E05 controlled documents/artifacts or E07 test artifacts.

Do not require this for every simple DMM check.

## Station identity

Suggested:

```text
test_stations
  id
  station_code
  name
  location
  status
  station_software_identity
```

Station is an execution grouping, not substitute for individual equipment identities.

## Calibration expiry behavior

Before run:

- warn/block based on policy.

After run discovery of invalid calibration:

- do not delete affected runs;
- mark evidence review/invalidity status through quality process;
- support impact query by equipment + time interval;
- affected released serials can be identified for review/recall decision.

## Tests

- equipment asset identity unique;
- calibration history immutable;
- run captures exact calibration record;
- valid-at-run calculation deterministic;
- current new calibration does not alter old run evidence;
- expired required calibration blocks/invalidates per policy;
- impact query finds all runs in selected invalid interval;
- setup/de-embedding artifact checksum retained where required.

## Acceptance

For every controlled RF test the company can prove which physical instruments/setup were used and whether their calibration evidence was valid at the moment of execution.
