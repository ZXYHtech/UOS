# TASK_INV_IMPL_E14_S01 — Authorized Context Builder & Evidence-first Answer Contract

## Status
`DESIGN_READY_BLOCKED_BY_E01_E12_FOUNDATIONS`

## Objective
Build AI context only from records the current user is authorized to read and make every operational factual answer traceable to source evidence.

## Context builder
Context requests declare:

- AI task purpose;
- user/session identity;
- domain/entity scope;
- warehouse/account/customer scope;
- maximum rows/artifacts/time range;
- required freshness;
- allowed source classes.

Preferred evidence order:

```text
canonical transactional records
 -> released controlled documents
 -> structured product/test/spec records
 -> approved knowledge content
 -> historical cases/notes
 -> external vendor/web evidence only when explicitly needed
```

## Evidence-first response
For factual operational answers return structurally:

```text
answer / recommendation
supporting object references
source timestamp / freshness
known limitations / missing evidence
optional proposed action
```

Examples such as “why can’t order X ship?” must cite actual reservation/ATP/shipment/shortage/supply records rather than infer a plausible story.

## Authorization
AI tools receive no broader permission than the user. Server-side tool functions independently enforce role, warehouse/account/customer scope and sensitive-field masking.

Secrets/credentials are categorically excluded from model context.

## Rules
- hidden data is not exposed merely because it is semantically relevant;
- stale or missing facts are explicitly labeled;
- external claims are distinguishable from internally approved engineering truth;
- arbitrary historical notes never override current released/canonical records;
- evidence IDs/hashes used for consequential recommendations are retained with AI provenance.

## Tests
- restricted user cannot retrieve another warehouse/account/customer data through AI;
- secret/credential fields never enter constructed prompt/context;
- answer with missing source explicitly reports insufficiency;
- stale source receives freshness warning;
- supporting records are sufficient to reconstruct the deterministic facts stated.

## Done
AI answers are permission-scoped and evidence-bound instead of being plausible free-form summaries with hidden provenance.