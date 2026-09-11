# TASK_INV_AUDIT_REVISION_ECN_01 — Part/BOM Revision & ECN/ECO Change-Control Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Static search found revision mechanisms for pricing and OCR corrections, but no first-class engineering revision/ECN/ECO domain.

## 1. Executive conclusion

Inventory Lite knows how to preserve revisions in some domains, which is encouraging, but engineering configuration control is currently missing.

For electronics products the critical question is not “what does the BOM look like now?” It is:

```text
What exact released design/BOM/firmware/test specification was effective for this build at that time?
```

Without this, historical manufacturing and RMA traceability will eventually point to today’s BOM instead of the BOM actually built.

## 2. Existing reusable patterns

Current code already demonstrates revision concepts through:

- `material_price_revisions`
- `order_item_price_revisions`
- `recognition_revisions`
- recognition correction before/after state
- operation logs

The project therefore does not need to invent revision history from scratch. The engineering domain should reuse the principle of immutable released versions plus explicit changes.

## 3. Missing engineering entities

Static search did not find canonical:

- part revision
- BOM revision
- drawing revision
- ECN/ECO
- effectivity
- released/frozen BOM state
- deviation/waiver

Generic `updated_at` or operation logs are not substitutes.

## 4. Recommended configuration model

### Product/part revision

```text
part_revision
  material_id
  revision_code
  status: draft | review | released | obsolete
  description
  created_by/at
  released_by/at
  supersedes_revision_id
```

### BOM revision

```text
bom_revision
  parent_material_id
  revision_code
  status
  effective_from/to or effectivity rule
  source_design_revision
  released_by/at
```

BOM lines reference `bom_revision_id`, not merely parent material.

### Engineering change

```text
engineering_change
  change_no
  type: ECN/ECO/deviation
  reason
  impact
  status
  requester/reviewer/approver
  affected objects
  before revision
  after revision
  effective rule
```

## 5. Draft versus released

Do not allow production to consume mutable draft BOMs by default.

Recommended rule:

- R&D may edit draft revision;
- released revision is immutable;
- change to released design creates new revision through ECN/ECO;
- work order snapshots/references one released revision;
- historical work order never follows future BOM edits.

## 6. Effectivity

Revision change may apply by:

- date
- work order
- production lot
- serial number range
- first build after depletion of old stock

Start with date/work-order effectivity; add serial/lot effectivity only where operationally needed.

## 7. Change impact analysis

Before release, change review should identify impacts on:

- BOM/material demand
- approved substitutes/AVL
- existing stock disposition
- WIP
- open purchase orders
- fixtures/tools
- firmware
- test limits/procedures
- labels/manuals
- customer-specific configuration

This is where inventory and engineering systems create real combined value.

## 8. Existing stock disposition

An ECN should not silently make existing components unusable.

Disposition examples:

- use as is
- use until exhausted
- rework
- segregate
- return supplier
- scrap
- engineering approval required

These decisions later connect to inventory status and quality/MRB.

## 9. Document linkage

Released engineering revision should link to controlled resources:

- schematic
- PCB/Gerber
- assembly drawing
- BOM source
- firmware
- test procedure
- calibration/config file

The existing `material_resources` concept can be extended, but controlled documents need revision/effectivity rather than mutable links only.

## 10. Minimal implementation path

Do not implement a giant PLM workflow engine.

Phase 1:

- BOM revision table
- revisioned BOM lines
- draft/released/obsolete state
- change reason/approval
- work-order reference

Phase 2:

- engineering change record
- affected objects
- stock/WIP disposition
- controlled documents

Phase 3:

- richer effectivity and change impact automation.

## 11. Priorities

### P0

1. released BOM revision identity;
2. immutable released BOM;
3. new revision for released changes;
4. work-order/build reference to BOM revision;
5. change reason/release actor/time.

### P1

1. ECN/ECO aggregate;
2. impact analysis checklist;
3. stock/WIP disposition;
4. controlled document revision links;
5. deviation/waiver path.

## 12. Acceptance signals

- editing a released BOM is rejected;
- new revision can supersede old one without deleting it;
- historical work order continues to display old BOM after new release;
- an ECN lists affected parts/BOM/docs;
- BOM revision used by finished serial genealogy is immutable.

All tests are local/server-side; no GitHub Actions dependency.

## 13. Preliminary maturity

- generic revision patterns: 3/5
- engineering part revision: 0.5/5
- BOM revision/release: 0.5/5
- ECN/ECO: 0/5
- effectivity: 0/5
- historical build configuration: 0.5/5

## 14. Core recommendation

Add a small configuration-control layer before expanding manufacturing. Otherwise MRP, work orders, test records and RMA will all inherit an unstable “current BOM” reference and become difficult to trust historically.