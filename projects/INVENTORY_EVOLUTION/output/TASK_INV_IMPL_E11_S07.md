# TASK_INV_IMPL_E11_S07 — Settlement Import, Matching & Reconciliation

## Status
`DESIGN_READY_BLOCKED_BY_E09_E11_S06`

## Objective
Import marketplace/payment settlement observations into immutable staging, normalize them to economic events, and surface expected-vs-actual differences without rewriting original order prices.

## Staging
Settlement batch stores platform account, external statement identity, period/currency, immutable source hash/reference, import status and actor/time.

Settlement lines preserve external line/order/refund identity, native type/description, amount/date and match status.

## Flow

```text
statement/API
 -> immutable staging
 -> normalize event type
 -> match order/refund/shipment
 -> create/link economic event
 -> unresolved rows queue
 -> expected-vs-actual reconciliation
 -> reviewed/closed batch
```

## Rules
- duplicate statement ID/hash/line cannot duplicate events;
- unmatched rows remain visible;
- settlement mismatch never edits order sale price merely to force equality;
- manual match/adjustment requires actor/reason/audit;
- secrets are not stored in settlement payload/log evidence;
- tax observations are preserved, not treated as universal filing logic.

## Reconciliation examples
- expected vs actual commission;
- expected net receivable vs settled amount;
- refund/fee reversal mismatch;
- freight observation mismatch where carrier data exists;
- unknown penalty/adjustment.

## Tests
- importing same statement twice is idempotent;
- unmatched row persists as exception;
- manual match is audited;
- actual fee variance is visible without rewriting order;
- re-import after partial failure resumes safely.

## Done
Channel cash/fee observations can be reconciled to operational orders with a clear unresolved-exception queue.