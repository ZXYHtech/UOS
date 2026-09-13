# E04 Slice E Execution Packet — Typed Parametric Attributes

## Status

`READY_AFTER_E04_A_B`

## Entry gate

Requires stable internal-part and Manufacturer Part identities merged.

Branch:

```text
impl/e04-parametrics
```

Migration:

```text
NEXT_CONTIGUOUS
= part_attribute_definitions + part_attribute_values + indexes
```

## Purpose

Turn flexible specifications into typed, unit-aware, searchable engineering data without adding one DB column per RF/electronics parameter.

Keep current `material_specifications` readable during migration.

## Schema

### part_attribute_definitions

```text
id
attribute_code UNIQUE
attribute_name
data_type
canonical_unit NULL
category_id/applicability_json
searchable
filterable
enum_values_json NULL
status
created_at
updated_at
```

P0 data types:

```text
NUMERIC
RANGE
STRING
ENUM
BOOLEAN
```

### part_attribute_values

```text
id
definition_id
owner_type
owner_id
raw_value
normalized_text NULL
normalized_numeric NULL
min_numeric NULL
max_numeric NULL
tolerance_numeric NULL
source_evidence_id NULL
verification_status
created_at
updated_at
```

Initial owner types:

```text
INTERNAL_MATERIAL
MANUFACTURER_PART
```

## Critical semantic separation

```text
Internal Material attribute = design requirement / nominal intent
Manufacturer Part attribute = source-part datasheet fact
```

Never overwrite one with the other.

Example:

```text
internal requirement: NF <= 1.0 dB @ 1.6 GHz
manufacturer part claim: NF typ 0.65 dB under datasheet condition X
```

These are related evidence, not one mutable value.

## Units

Each numeric definition has one canonical engineering unit.

Examples:

```text
frequency -> Hz
voltage -> V
current -> A
resistance -> ohm
capacitance -> F
gain/NF/IL/isolation -> dB family with distinct attribute meaning
power -> explicit W or dBm definition, never generic unsafe conversion
```

Input may accept compatible units and normalize deterministically.

Do not perform conversion between quantities that merely share words such as power but have different semantics.

Use Decimal/rational-safe conversion where precision matters; do not make binary floating-point parsing the authoritative stored meaning.

## RF condition/evidence boundary

An RF number without conditions can be searchable metadata but may not be sufficient for substitution approval.

Where meaningful, source evidence should preserve test conditions such as frequency, supply, temperature or reference plane through evidence/document relations rather than stuffing all context into one numeric field.

## Legacy migration

Classify each existing `material_specifications` row:

```text
exact definition + parseable value/unit
 -> migration candidate
ambiguous/unparseable
 -> preserve legacy row + review flag
```

No lossy conversion and no source-text deletion.

## Search

Typed filters return candidates plus explanation:

```text
frequency_min <= query_low
frequency_max >= query_high
noise_figure <= threshold
package = exact identity
```

Candidate retrieval never grants AML/AVL/substitute authority.

## Verification states

```text
UNVERIFIED
PROVIDER_IMPORTED
VERIFIED
SUPERSEDED
```

Unknown/missing data remains missing, not zero.

## Tests

1. compatible unit normalization deterministic;
2. incompatible units rejected;
3. range min/max semantics preserved;
4. enum validation enforced;
5. raw source value preserved after normalization;
6. internal requirement and Manufacturer Part source value coexist;
7. ambiguous legacy spec is not auto-converted;
8. missing value does not become zero;
9. parametric query returns explanation/candidate IDs;
10. candidate match does not create substitute/AVL approval;
11. provider-imported value cannot overwrite VERIFIED value silently;
12. full Release Gate passes.

## Rollback

Keep additive typed tables/evidence; UI may fall back to legacy specifications. Do not delete migrated source rows solely because normalized values exist.

## Stop conditions

Stop if unit conversion loses source meaning, internal requirements and datasheet facts collapse into one field, or search similarity is treated as engineering approval.

## Exit / unlock

Engineering parameters are typed, unit-aware and searchable while raw evidence and approval boundaries remain intact. Unlocks E04-F/G/H.