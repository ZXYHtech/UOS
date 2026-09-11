# TASK_INV_IMPL_E04_S07 — Lifecycle, Compliance and Engineering Provenance

## Status

`DESIGN_READY_BLOCKED_BY_E04_IDENTITY`

## Objective

Make engineering facts evidence-bound so lifecycle/compliance/parametric values can be distinguished as verified, stale, imported or unknown instead of being treated as timeless free text.

## Evidence model

Suggested reusable object:

```text
engineering_evidence
  id
  entity_type
  entity_id
  evidence_type
  source_type
  source_provider
  source_url
  attachment_id
  source_document_revision
  source_document_date
  retrieved_at
  last_verified_at
  verified_by
  verification_status
  confidence_class
  raw_payload_json
  remark
```

Initial supported entity types may include:

```text
manufacturer
manufacturer_part
internal_material
supplier_part
package
footprint
attribute_value
approval
```

Keep the type list explicit; do not turn this into an unrestricted polymorphic dumping ground.

## Verification status

Suggested vocabulary:

```text
unverified
provider_imported
verified
stale
superseded
rejected
```

Unknown/stale is a valid state and preferable to silently carrying an old claim as current truth.

## Lifecycle model

Manufacturer-part lifecycle may use:

```text
active
NRND
EOL
obsolete
unknown
```

Each non-unknown lifecycle assertion should link to evidence where practical.

A lifecycle state change:

- does not auto-replace the part;
- does not rewrite BOMs;
- may raise sourcing/engineering review;
- preserves previous evidence/history.

## Compliance

Initial compliance records can cover business-relevant declarations such as:

- RoHS;
- REACH;
- halogen-free if needed;
- conflict-minerals/document evidence if commercially needed.

Do not infer compliance from manufacturer/category or reuse one declaration across unrelated MPNs without explicit scope.

## Datasheets/resources

Reuse existing `material_resources` / attachments where appropriate.

E04 should add relation/provenance around those resources instead of creating a second unmanaged file store.

A datasheet resource should retain:

```text
which entity it supports
source/revision/date
retrieved/verified timestamps
current/superseded state
```

## Parametric evidence

A typed attribute value may point to evidence and verification status.

Example:

```text
manufacturer_part X
noise_figure = 0.8 dB
source = datasheet rev Y
condition = captured text/metadata
verification = verified
```

If conditions are missing, the value may still be searchable but must not be presented as universally valid for substitution approval.

## External provider freshness

Provider refresh never silently replaces a verified value.

Preferred behavior:

```text
new provider value differs
 -> create candidate/evidence record
 -> flag diff
 -> review/accept/reject
```

## Retention

Evidence used for an approval/BOM/procurement decision must not be hard-deleted merely because a newer document arrives.

Supersede rather than erase.

## Tests

- verified value retains source evidence;
- stale/unknown states distinguishable;
- provider refresh cannot silently overwrite verified canonical value;
- lifecycle change preserves prior evidence;
- compliance scope tied to correct MPN/entity;
- superseded datasheet remains historically queryable;
- approval can point to qualification/evidence;
- missing evidence does not get auto-labeled verified.

## Acceptance

Engineering master data can answer not only “what value/status do we currently show?” but also “where did it come from, when was it checked, who verified it, and what did it replace?”.
