# TASK_INV_IMPL_E05_S07 — Controlled Documents, Release Packages, Firmware and Test Specs

## Status

`DESIGN_READY_BLOCKED_BY_E05_REVISION_MODEL`

## Objective

Separate flexible reference resources from immutable controlled engineering/manufacturing artifacts so production and later test genealogy can resolve the exact released files/configuration that applied.

## Preserve current resources

`material_resources` remains appropriate for low-control reference content such as:

- manufacturer marketing page;
- distributor link;
- tutorial/video;
- informal image;
- non-controlled reference attachment.

Do not convert every URL/file into PLM-style controlled content.

## Controlled document identity

Suggested:

```text
controlled_documents
  id
  document_no
  document_type
  title
  owner_user_id
  status

controlled_document_revisions
  id
  document_id
  revision_code
  status
  attachment_id
  checksum_sha256
  effective_from
  effective_to
  supersedes_revision_id
  change_reason
  created_by/at
  released_by/at
```

## Status / immutability

```text
draft -> review -> released -> obsolete
                     \
                      -> withdrawn
```

Released artifact bytes/checksum and core release metadata cannot be replaced in-place.

Correction creates a new revision or explicit withdrawal/supersession event.

## Document types

P0 examples:

- schematic release;
- PCB fabrication package;
- assembly drawing;
- MBOM/EBOM release export;
- work instruction;
- mechanical drawing;
- firmware binary/configuration;
- RF test procedure;
- test limit set;
- calibration/tuning instruction;
- customer product datasheet.

## Applicability

Suggested explicit relation:

```text
document_revision_applicability
  document_revision_id
  entity_type
  entity_id
```

Initial entities:

```text
material
part_revision
bom_revision
release_package
```

E06/E07 extend WO/test-run applicability later.

## Release packages

Suggested:

```text
release_packages
  id
  package_code
  revision_code
  material_id
  part_revision_id
  status
  released_by/at

release_package_items
  release_package_id
  item_type
  document_revision_id / firmware_release_id / bom_revision_id
```

A released package prevents manufacturing from accidentally combining Gerber Rev B with assembly drawing Rev C.

## Firmware release

Suggested:

```text
firmware_releases
  id
  firmware_code
  version
  build_id
  source_revision
  binary_attachment_id
  checksum_sha256
  status
  release_notes
  released_by/at
```

Applicability to hardware/part revision is explicit.

Filename is not identity.

## Test procedure / limit set

Treat procedure and limit set as separately revisioned controlled artifacts where useful.

Historical E07 test run will snapshot/reference exact:

- procedure revision;
- limit-set revision;
- station software/script version;
- fixture/de-embedding configuration if controlled.

Changing current limits never retroactively changes historical pass/fail evidence.

## Storage / backup

Database stores metadata, identity and SHA-256; file storage stores payload bytes.

E00 backup/recovery must be extended before these become production-critical so a valid restore proves:

- DB row exists;
- referenced artifact exists;
- checksum matches;
- release package relationships resolve.

A DB-only restore with missing released files is a failed recovery for this domain.

## Permissions

Separate at least:

```text
document.view
document.edit_draft
document.release
```

Sensitive artifact retrieval is server-authorized; hidden UI controls are not sufficient.

## Tests

- Rev B release does not overwrite Rev A;
- released checksum detects byte replacement;
- obsolete/withdrawn remains historically available;
- user without release permission blocked at API;
- package cannot include draft/unreleased required item;
- firmware identity includes version/build/checksum, not filename only;
- applicability resolves exact product/BOM revision;
- restore fixture detects missing/corrupt controlled artifact.

## Acceptance

Manufacturing and later quality/test workflows can consume one coherent released configuration package and prove the exact bytes/revisions used historically.
