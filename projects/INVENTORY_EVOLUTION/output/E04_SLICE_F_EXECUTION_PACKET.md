# E04 Slice F Execution Packet — Engineering Evidence / Lifecycle / Compliance

## Status

`READY_AFTER_E04_CORE_IDENTITY`

## Entry gate

Requires E04 internal/manufacturer/supplier/package identities and current-main Release Gate PASS.

Branch:

```text
impl/e04-engineering-evidence
```

Migration:

```text
NEXT_CONTIGUOUS
= engineering_evidence + lifecycle/compliance relation objects/indexes as required
```

## Purpose

Bind engineering facts to evidence so the system can answer:

```text
what do we believe now?
where did it come from?
when was it retrieved/verified?
who verified it?
what did it supersede?
```

Unknown/stale is valid and preferable to invented certainty.

## Evidence schema

```text
engineering_evidence
  id
  entity_type
  entity_id
  evidence_type
  source_type
  source_provider
  source_url
  attachment_id NULL
  source_document_revision NULL
  source_document_date NULL
  retrieved_at
  last_verified_at NULL
  verified_by NULL
  verification_status
  confidence_class NULL
  raw_payload_json NULL
  supersedes_evidence_id NULL
  remark
```

Explicit supported entity types only; do not create an unrestricted polymorphic dumping ground.

Initial examples:

```text
MANUFACTURER
MANUFACTURER_PART
INTERNAL_MATERIAL
SUPPLIER_PART
PACKAGE
FOOTPRINT
ATTRIBUTE_VALUE
APPROVAL
```

## Verification states

```text
UNVERIFIED
PROVIDER_IMPORTED
VERIFIED
STALE
SUPERSEDED
REJECTED
```

Provider confidence is not verification authority.

## Lifecycle

Manufacturer Part lifecycle assertions:

```text
UNKNOWN
ACTIVE
NRND
EOL
OBSOLETE
```

Non-UNKNOWN assertions should link to evidence where practical.

Lifecycle update:

- appends/supersedes evidence;
- does not rewrite released BOMs;
- does not auto-approve substitutes;
- may generate later review/automation events only after E13 policies exist.

## Compliance

P0 support only business-relevant declarations:

```text
RoHS
REACH
halogen-free (if used)
other controlled declarations as configured
```

Scope must identify the exact entity/MPN/document. Never copy one declaration across unrelated MPNs by category inference.

## Datasheets/resources

Reuse existing `material_resources` / attachment storage where applicable.

Evidence relation adds source/revision/date/current/superseded semantics rather than building a second file store.

A new datasheet never deletes the old one when the old one supported historical approval/BOM/procurement decisions.

## Provider refresh

Safe flow:

```text
provider observes new value/document/status
 -> stage new evidence/candidate
 -> compare with current verified record
 -> explicit accept/reject/review
 -> supersede only through controlled command
```

Verified canonical values are never silently overwritten by refresh.

## Parametric linkage

Typed attribute values may point to evidence.

Missing test conditions reduce evidence quality; they do not become universal engineering truth.

## Tests

1. VERIFIED fact has traceable evidence;
2. UNKNOWN/STALE distinguishable;
3. provider refresh cannot overwrite VERIFIED value silently;
4. lifecycle change preserves previous evidence;
5. compliance declaration remains scoped to correct MPN/entity;
6. superseded datasheet remains queryable;
7. approval may reference qualification evidence;
8. missing evidence cannot be labeled VERIFIED automatically;
9. retained attachments/evidence are covered by E00 backup/recovery scope when production-critical;
10. full Release Gate passes.

## Rollback

Keep evidence records. Disable new consumption/UI if needed. Do not erase historical evidence to emulate old behavior.

## Stop conditions

Stop if provider refresh destructively replaces verified truth or evidence retention is not covered by backup/recovery for release-critical files.

## Exit / unlock

Identity/parametric/lifecycle/compliance facts are evidence-bound and history-preserving. Unlocks robust AVL approval and component workspace.