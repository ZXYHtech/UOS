# E08 Implementation Sequence — MRP + Subcontract

## Status
`DESIGN_READY_BLOCKED_BY_E07_GATE`

E08 is intentionally split into small independently gated slices. Exact migration numbers are assigned only from the then-current contiguous migration history.

## Preconditions

Before runtime E08 begins:

- E00–E07 relevant gates are green;
- E02 stock/reservation/quality-aware balance contracts are authoritative;
- E04 approved sourcing identity exists;
- E05 released/effective MBOM resolution is authoritative;
- E06 WO demand/supply is authoritative;
- E07 quality/lot/serial states are authoritative;
- production pre-change backup/recovery policy still applies to every release.

## Slice A — Planning policy schema/service
Implement E08-S01 only. No MRP output yet.

STOP if policy data cannot be audited/effectivity-controlled.

## Slice B — Typed demand/supply projection
Implement E08-S02 read models/adapters only.

STOP if any quantity can be double-counted or if quarantine/other-demand reservations leak into usable supply.

## Slice C — Released MBOM explosion
Implement E08-S03 with deterministic local tests.

STOP if draft/sales BOM can enter manufacturing demand or cycle detection is incomplete.

## Slice D — MRP run identity/input snapshot
Introduce durable run identity before netting publishes recommendations.

STOP if a historical run cannot identify its source assumptions.

## Slice E — Daily PAB/netting + pegging/exceptions
Implement E08-S04.

Start in shadow/report-only mode. Compare hand-worked fixtures against computed results.

STOP on unexplained quantity/date differences.

## Slice F — Planner recommendation review
Expose proposed BUY/MAKE/TRANSFER/reschedule/cancel/review-substitute actions. No conversion initially.

STOP if explanations/pegging are incomplete.

## Slice G — Idempotent conversion pilot
Implement E08-S05 one document type at a time:

1. BUY -> purchase order/request;
2. MAKE -> work order;
3. TRANSFER -> transfer request.

Each uses E01 business-operation idempotency and revalidates authority/source at conversion time.

STOP on any duplicate-document or stale-advice bypass.

## Slice H — Subcontract order / dispatch / external WIP
Implement E08-S06 after internal inventory flows are proven.

STOP if company-owned sent material disappears from ownership reporting or remains local ATP.

## Slice I — Subcontract return/reconciliation/quality
Implement E08-S07.

STOP if partial returns can close unresolved material or returned output bypasses E07 quality.

## Slice J — MRP sees subcontract scheduled supply
Add confirmed external-WIP return dates as typed scheduled supply and overdue-return exceptions.

STOP if unconfirmed/draft subcontract output is counted as firm supply.

## Slice K — Durable scheduler + exception workbench
Implement E08-S08 through E01 durable jobs/systemd-owned execution.

No GitHub Actions dependency.

## Release gates for every slice

At minimum:

```text
schema migration test where applicable
+ deterministic domain-unit tests
+ historical fixture migration/integrity
+ E00 Release Gate
+ no existing procurement/WO/inventory regression
```

For planning math changes, keep explicit golden fixtures covering quantity/date/MOQ/lead-time/quality/reservation cases.

## Authority rule

MRP remains advisory even after E08 completion:

```text
MRP computes/explains
 -> planner reviews
 -> authorized E01 action converts
 -> PO/WO/transfer/subcontract domain owns execution
```

Never make automatic purchase/order execution the default definition of E08 success.