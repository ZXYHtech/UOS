# TASK_INV_IMPL_E14_S05 — Draft / Recommendation / Action Preview & Approval Bridge

## Status
`DESIGN_READY_BLOCKED_BY_E01_E13_ACTION_POLICY`

## Objective
Allow AI to prepare useful business actions without hiding execution inside conversational prose.

## Flow

```text
AI recommendation/draft
 -> structured action preview/diff
 -> deterministic current-state validation
 -> permission/risk/approval decision
 -> explicit user or E13 approval
 -> normal domain command
 -> E01 business-operation receipt
 -> AI provenance links accepted action
```

## Typical bounded actions
Examples:

- create PO draft from accepted MRP recommendations;
- draft quotation using PricingService outputs;
- create follow-up draft/todo;
- add case note draft;
- propose material alias candidate;
- propose NCR/ECO text or supplier communication.

AI never directly releases BOM/quality, deducts stock, approves refund or changes public price as a default autonomous mode.

## Preview contract
Before any write show:

- action type;
- exact target objects;
- before/current state where relevant;
- proposed fields/lines;
- deterministic warnings/errors;
- evidence/source records;
- risk class and required approval;
- irreversible/external side-effect warning where applicable.

## Revalidation
The server re-reads authoritative state at commit. An old AI preview is not authority if inventory, price, approval, order status or target revision changed.

## Idempotency
Accepted action uses E01 idempotency; retry returns the original receipt and never duplicates PO/quote/order/note mutations.

## Tests
- AI text alone cannot cause a write;
- stale preview is rejected/recomputed;
- duplicate approve/retry creates one domain result;
- action beyond user's permission remains blocked even when AI recommends it;
- accepted write links preview/evidence/model task to domain receipt.

## Done
AI can save operator time preparing actions while the final business mutation remains visible, deterministic, permissioned and auditable.