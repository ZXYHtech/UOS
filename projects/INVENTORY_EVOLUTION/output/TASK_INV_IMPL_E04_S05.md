# TASK_INV_IMPL_E04_S05 — Typed Parametric Attributes and Units

## Status

`DESIGN_READY_BLOCKED_BY_E04_IDENTITY`

## Objective

Upgrade flexible material specifications into a typed, searchable engineering attribute system without creating one database column per RF/electronics parameter.

## Existing capability to preserve

Current `material_specifications` is useful for arbitrary grouped key/value data. It should remain readable during migration and can continue serving legacy/display use while typed attributes are introduced.

## Suggested objects

```text
part_attribute_definitions
  id
  attribute_code
  attribute_name
  data_type
  canonical_unit
  category_id / applicability rule
  searchable
  filterable
  enum_values_json
  status

part_attribute_values
  id
  definition_id
  owner_type
  owner_id
  raw_value
  normalized_text
  normalized_numeric
  min_numeric
  max_numeric
  tolerance_numeric
  source_evidence_id
  verification_status
  created_at
  updated_at
```

`owner_type` must be constrained to supported engineering identities, initially:

```text
internal_material
manufacturer_part
```

## Requirement vs source values

This distinction is mandatory:

```text
internal_material attribute
 = engineering requirement / nominal design intent

manufacturer_part attribute
 = actual supplier/manufacturer datasheet characteristic
```

Do not overwrite the requirement with a source-part datasheet value or vice versa.

## Data types

Minimum P0:

```text
numeric
range
string
enum
boolean
```

Optional later types only when needed.

## Unit model

Each numeric definition has one canonical unit.

Input may accept compatible units, but storage/filter normalization must be deterministic.

Examples:

```text
frequency: Hz canonical, accept kHz/MHz/GHz
voltage: V canonical, accept mV
current: A canonical, accept mA/uA
power: W or dBm depending definition semantics; never auto-convert unrelated power concepts
```

Do not use generic unit conversion where the engineering quantity meaning differs.

## RF attribute examples

- frequency_min / frequency_max;
- gain_db;
- noise_figure_db;
- p1db_dbm;
- oip3_dbm;
- insertion_loss_db;
- isolation_db;
- supply_voltage;
- supply_current;
- input/output impedance.

Definitions, category applicability and test conditions matter. A value such as `gain=20 dB` without conditions/evidence may be useful display metadata but not enough for substitution approval.

## Passive examples

- resistance/capacitance/inductance;
- tolerance;
- voltage rating;
- power rating;
- dielectric;
- temperature coefficient;
- package.

## Evidence

Canonical values should support source/provenance linkage from E04-S07.

A value can be:

```text
unverified
provider_imported
verified
superseded
```

Unknown is preferable to guessed data.

## Legacy migration

Legacy `material_specifications` rows are classified:

```text
exact known definition + parseable unit/value
 -> migration candidate

ambiguous/unparseable
 -> retain legacy value + review queue
```

No lossy conversion.

## Search/filter behavior

Filters operate on typed normalized values and return the canonical object plus match explanation.

Example:

```text
frequency_min <= 1.6 GHz
AND frequency_max >= 1.6 GHz
AND noise_figure <= 1.0 dB
```

This is candidate retrieval only. It is not AVL/substitution approval.

## Tests

- numeric unit normalization exact/deterministic;
- incompatible units rejected;
- range values maintain min/max meaning;
- enum values validated against definition;
- internal requirement and manufacturer source values coexist;
- raw source value preserved after normalization;
- ambiguous legacy specification is not silently converted;
- parametric search returns explainable candidates;
- matching candidate is not automatically approved as substitute.

## Acceptance

Engineering parameters become typed, unit-aware and searchable while preserving raw evidence and the critical separation between internal requirements, manufacturer-part facts and engineering approval.
