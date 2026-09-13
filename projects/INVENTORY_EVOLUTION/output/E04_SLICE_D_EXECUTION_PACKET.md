# E04 Slice D Execution Packet — Package / Footprint Identity

## Status

`READY_AFTER_E04_B`

## Entry gate

Requires Manufacturer+MPN identity merged and current-main Release Gate PASS.

Branch:

```text
impl/e04-package-footprint
```

Migration:

```text
NEXT_CONTIGUOUS
= packages + footprints + package_footprint_relations + indexes
```

## Purpose

Separate physical package identity from PCB/CAD footprint identity.

```text
Package = physical body/leads/mechanical family
Footprint = CAD/library land pattern identity
```

They are related, not interchangeable.

## Schema

### packages

```text
id
package_code UNIQUE
package_name
package_family
body_dimensions_json NULL
pin_count NULL
pitch NULL
status
source_evidence_id NULL
created_at
updated_at
```

### footprints

```text
id
footprint_code
cad_system
library_name
footprint_name
revision
status
source_evidence_id NULL
created_at
updated_at
UNIQUE(cad_system, library_name, footprint_name, revision)
```

### package_footprint_relations

```text
id
package_id
footprint_id
approval_status
qualification_reference
created_by
created_at
updated_at
UNIQUE(package_id, footprint_id)
```

Suggested relation states:

```text
CANDIDATE
APPROVED
CONDITIONAL
REJECTED
RETIRED
```

## Manufacturer Part relationship

Manufacturer Part may reference one physical package identity.

Do not force one footprint directly onto every Manufacturer Part. Multiple approved footprints may exist depending on CAD/library/revision.

E05 BOM/EDA workflows later decide the exact footprint/revision used for released design configuration.

## Legacy migration

Package-like values in `model/spec/material_specifications` or EDA imports are migration candidates only.

Rules:

- preserve raw source text;
- exact known match may be staged/linked after review;
- similar punctuation/dimensions do not justify automatic merge;
- footprint string and package string are never treated as synonyms by default.

## Search / alias behavior

Canonical package/footprint identities may have aliases/search normalization, but alias never grants approved package-footprint compatibility.

## Tests

1. package_code uniqueness deterministic;
2. footprint identity includes CAD/library/revision namespace;
3. one package may link multiple approved footprints;
4. one footprint may link multiple packages only with explicit relation evidence;
5. Manufacturer Part package link does not force a footprint;
6. candidate relation cannot be used as approved footprint;
7. free-text legacy package remains reviewable without source rewrite;
8. package and footprint are never silently conflated;
9. full Release Gate passes.

## Rollback

Additive identity tables remain inert if feature disabled. Preserve relations/evidence once referenced.

## Stop conditions

Stop if implementation collapses Package and Footprint into one text field, or if unreviewed candidate relation becomes usable in released engineering flow.

## Exit / unlock

Package and CAD footprint become reusable, separately governed identities ready for EDA/BOM integration and component search.