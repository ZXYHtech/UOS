# TASK_INV_AUDIT_DOC_CONTROL_01 — Drawings, Datasheets, Firmware and Controlled-document Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `material_resources`, generic `attachments`, image/resource metadata, MaterialProfileService resource CRUD, document/resource types, operation logging and the W3 revision/ECN, EBOM/MBOM and test-record requirements.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The current application has a useful **material resource library**, but not yet controlled engineering document management.

Current strengths:

- a material can have specifications and resources;
- resource types include documents/certificates/manuals/datasheets and links;
- resources can reference uploaded attachments;
- generic attachments carry image/file metadata and hashes in some paths;
- resource updates/deletes are operation-logged.

However, the inspected `material_resources` workflow allows direct update/delete and does not establish first-class:

- document number and revision;
- draft/review/released/obsolete lifecycle;
- approvers;
- effective date;
- supersession chain;
- immutable released file checksum;
- applicability to product/part/BOM revision;
- firmware build identity;
- controlled test procedure/limit-set binding;
- acknowledgement/distribution.

Preliminary controlled-document maturity: **1.0/5**.

## 2. Separate reference resources from controlled documents

Not every material link needs PLM-style control.

### Reference resource

Examples:

- manufacturer marketing page;
- distributor product page;
- tutorial;
- external video;
- informal image.

These can remain close to the current `material_resources` model.

### Controlled document

Examples:

- schematic release;
- PCB fabrication package;
- assembly drawing;
- released EBOM/MBOM export;
- mechanical drawing;
- firmware binary/configuration;
- production instruction;
- RF test procedure;
- calibration/tuning procedure;
- customer datasheet release;
- certificate template;
- inspection specification.

These need revision, approval, effectivity and immutable release evidence.

Do not force both categories into one mutable table with an `is_primary` flag.

## 3. Required document identity

Use a stable document identity and separate immutable revisions.

```text
controlled_documents
  id
  document_no
  document_type
  title
  owner_user_id
  product/material scope
  lifecycle_status

controlled_document_revisions
  id
  document_id
  revision_code
  status: draft | review | released | obsolete
  file_attachment_id
  checksum_sha256
  effective_from
  effective_to
  supersedes_revision_id
  change_reason
  created_by
  created_at
  released_by
  released_at
```

Once a revision is released, do not replace the file in-place. A correction creates a new revision or an explicitly audited withdrawal/re-release event.

## 4. Applicability

A document must answer **what configuration it applies to**.

Possible controlled links:

```text
document_applicability
  document_revision_id
  entity_type: material | part_revision | product_revision | bom_revision | work_order | test_spec
  entity_id
  applicability_rule
```

For a simple v1, explicit relation rows are safer than a generic free-text scope expression.

Examples:

- schematic SCH-001 Rev C applies to Product Revision C;
- PCB Gerber package Rev B applies to PCB internal part Rev B;
- assembly drawing Rev D applies to MBOM Rev D;
- test procedure TP-RF-AMP Rev 3 applies to product revisions C-D;
- firmware FW-12.4 applies to hardware Rev C and later.

## 5. Engineering source vs manufacturing release package

Avoid using GitHub or a user desktop folder as the only release authority.

Engineering source may live in EDA/version-control systems, but production should consume an explicit released package with controlled identity/checksum.

Example:

```text
EDA source project
 -> engineering review
 -> ECO release
 -> controlled fabrication/assembly package
 -> manufacturing/work order references released package
```

The inventory/production system does not have to store every editable CAD source itself. It must preserve the release contract and link/artifact needed for production traceability.

## 6. PCB/schematic release package

For electronics, one product revision commonly has multiple coordinated files.

Support a release package or document set containing:

- schematic PDF/source reference;
- PCB fabrication outputs;
- pick-and-place file;
- assembly drawing;
- stencil data where controlled;
- EBOM/MBOM export;
- programming/firmware package;
- test procedure;
- mechanical drawing.

A set should itself have a released version so manufacturing does not accidentally mix Gerber Rev B with assembly drawing Rev C.

## 7. Datasheets

Two different datasheet concepts should be distinguished:

### Supplier/manufacturer component datasheet

Reference evidence for a manufacturer part. Store:

- source URL;
- captured attachment if policy permits;
- manufacturer/MPN;
- retrieved/published revision/date when known;
- checksum;
- source/provenance.

### Company product datasheet

A controlled customer-facing release. It should be versioned, approved and linked to product revision/market status.

Do not treat these as equivalent `datasheet` resources.

## 8. Firmware control

Firmware requires artifact identity beyond a filename.

Recommended model:

```text
firmware_releases
  id
  firmware_code
  version
  build_id/git_commit/source_revision
  binary_attachment_id
  checksum
  hardware_revision_scope
  configuration_schema_version
  release_notes
  status
  released_by/released_at
```

For serialized products, test/build records should capture the exact firmware release installed.

A filename such as `final_v2.bin` must never be the authoritative identity.

## 9. Test procedures and limit sets

`TASK_INV_AUDIT_TEST_RECORD_01` depends on controlled documents.

A test run needs:

- released procedure revision;
- released limit-set revision;
- test-station software/script version;
- optional fixture/de-embedding configuration.

Changing the procedure must not retroactively change what historical tests claim to have executed.

## 10. ECN/ECO integration

Controlled document release should integrate with `TASK_INV_AUDIT_REVISION_ECN_01`.

An ECO may release together:

- part revision;
- EBOM revision;
- MBOM revision;
- schematic/PCB package;
- firmware;
- work instruction;
- test limit set.

The change record should capture old/new revision and effectivity. This creates one coherent configuration baseline.

## 11. Checksums and immutable evidence

Every released uploaded file should store a cryptographic checksum, preferably SHA-256.

Use cases:

- prove the file downloaded today is the file approved at release;
- detect accidental overwrite/corruption;
- link generated reports/artifacts deterministically;
- support backup verification.

The existing attachment/image hash concepts are useful precedents, but controlled documents need an explicit released-artifact checksum contract.

## 12. Supersession and obsolescence

Do not delete an old released drawing because a new one exists.

Lifecycle:

```text
DRAFT -> REVIEW -> RELEASED -> OBSOLETE
```

A new release points to the superseded revision. Historical work orders, tests and shipments continue resolving the old revision.

If a released revision is invalidated urgently, record withdrawal/hold explicitly rather than erasing it.

## 13. Approval model

For a small team, keep approvals pragmatic.

Possible rules:

- engineering drawing/PCB/BOM: author + independent reviewer or owner;
- manufacturing instruction: engineering + production approval where material;
- test specification: engineering/quality approval;
- customer datasheet: product/engineering approval;
- firmware: engineering release + test evidence.

Use configurable policy by document type rather than a universal five-step workflow.

## 14. Access control

Different files can have different sensitivity:

- public product datasheet;
- internal manufacturing instruction;
- supplier NDA document;
- firmware binary/source link;
- customer-specific controlled file.

At minimum, document read/write/release permissions should be separable.

Do not rely only on hidden frontend buttons. Server-side authorization must protect controlled-file retrieval and state transitions.

## 15. Deletion and correction

The current material-resource service supports deleting resource rows. That remains acceptable for low-value reference resources subject to normal audit policy, but released controlled revisions should be non-destructive.

Recommended rules:

- draft: editable/deletable by owner policy;
- released: immutable artifact and metadata except controlled administrative correction fields;
- obsolete: retained;
- incorrect release: withdraw/supersede, never hard-delete under ordinary workflow.

## 16. Release package query

The system should be able to answer:

```text
For finished serial X:
  product revision?
  EBOM/MBOM revision?
  schematic/PCB release package?
  firmware version?
  assembly/work instruction revision?
  test procedure and limit revision?
```

That is the practical definition of configuration traceability.

## 17. Storage and backup

Relational DB should store identity/metadata/checksums; file storage should store payloads.

Backup/restore must preserve:

- database rows;
- referenced artifacts;
- checksums;
- directory/object keys;
- access metadata.

A successful DB-only restore with missing released files is not a successful document-control restore.

## 18. UX requirements

High-value screens:

1. product configuration baseline;
2. document list with current released revision;
3. revision history/diff metadata;
4. pending review/release queue;
5. obsolete/superseded warning;
6. work-order/test page showing exactly referenced release package.

Avoid a generic file-manager experience as the primary workflow.

## 19. Priority roadmap

### P0

1. controlled document + immutable revision entities;
2. document number/revision/status/checksum;
3. release approval and supersession;
4. product/part/BOM revision applicability;
5. firmware release identity;
6. test procedure/limit-set controlled linkage.

### P1

1. coordinated release packages;
2. ECO-driven multi-object release;
3. access-control classes;
4. manufacturing acknowledgement/current-revision warning;
5. backup integrity verification.

### P2

1. EDA source-system integrations;
2. automated package generation/signing;
3. richer document comparison;
4. customer-controlled document portals where needed.

## 20. Acceptance signals

- releasing Rev B does not overwrite or destroy Rev A;
- a historical WO/test still opens the exact released document revision it used;
- a released artifact checksum detects any byte-level replacement;
- firmware version/build and binary checksum are traceable to serialized output;
- manufacturing can obtain one coherent released package without mixing revisions;
- obsolete files are retained but clearly excluded from new work;
- a user without release permission cannot release by calling the API directly;
- backup restore verifies both metadata and referenced released files;
- no required release/validation/backup path depends on GitHub Actions.

## 21. Core recommendation

Keep the current material-resource feature for flexible reference links, but add a separate **immutable controlled-document revision layer** tied to ECN/ECO, BOM/product revision, firmware and test evidence. This avoids turning a convenient resource library into an unsafe pseudo-PLM.