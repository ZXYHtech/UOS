# TASK_INV_IMPL_E14_S04 — Extraction / Matching Review & Human Correction Evidence

## Status
`DESIGN_READY_BLOCKED_BY_E14_S01_S02`

## Objective
Generalize the existing OCR human-in-loop pattern for supplier quotes, datasheets, BOMs, inquiries, receipts and case classification.

## Flow

```text
source artifact / text
 -> AI structured candidate
 -> deterministic identity/schema validation
 -> confidence + evidence display
 -> human accept / correct / reject
 -> normal domain service write if approved
 -> correction/provenance record
```

## Candidate classes
Initial high-value tasks:

- supplier quotation extraction;
- datasheet metadata/parametric extraction;
- BOM/EDA normalization and internal-part candidate ranking;
- receipt/packing-list extraction;
- inquiry/technical requirement extraction;
- support-case classification.

## Safety rules
- extraction never overwrites approved E04/E05 engineering truth automatically;
- BOM ambiguity never silently chooses base model or substitute;
- datasheet claim remains tied to source document/revision/page/evidence;
- human accepted/corrected/rejected state is retained;
- corrections identify changed fields and optionally correction reason;
- source documents remain untrusted input and cannot grant tools/permissions.

## Learning signal
Aggregate correction patterns may improve prompts/rules/evaluation datasets. Do not automatically train external providers on customer/business data without explicit governance/consent policy.

## Tests
- ambiguous MPN is routed to review;
- corrected field survives as canonical approved value while original AI candidate remains auditable;
- rejected candidate causes no business write;
- source/evidence pointer is retained per extracted claim where required;
- same source/task replay is idempotent or creates an explicit new model-attempt revision, never duplicate canonical data.

## Done
Machine extraction accelerates data entry while a human-reviewed evidence boundary protects canonical business and engineering records.