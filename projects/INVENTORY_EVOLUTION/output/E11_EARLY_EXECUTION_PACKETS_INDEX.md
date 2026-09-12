# E11 Early Execution Packets Index

## Status

`EARLY_E11_PACKETS_READY_BLOCKED_BY_E01_PRICING_EXTRACTION`

This index covers only the early commercial-safety bridge that must land before E02.

## Entry sequence

```text
E00 merged
 -> E01 A-E cross-cutting primitives complete
 -> E01 pricing extraction complete with parity
 -> E11 Slice A pricing semantics
 -> E11 Slice B floor/override safety
 -> E02 Stock Ledger / Reservation / ATP
```

Do not jump from E01 directly to E02.

## Slice A — Pricing Semantics

Packet:

`E11_SLICE_A_EXECUTION_PACKET.md`

Recommended branch:

`impl/e11-pricing-semantics`

Migration:

```text
NONE
```

Key invariants:

- existing `margin_percent` arithmetic remains unchanged;
- no historical pricing rule is bulk-rewritten;
- new ambiguous `margin_percent` creation is blocked;
- target gross-margin math is explicit and cost-backed;
- current reference cost is labeled estimate/reference, never actual COGS;
- API/UI expose semantic evidence additively;
- rollback cannot silently mis-evaluate new semantic types.

## Slice B — Floor / Override Safety

Packet:

`E11_SLICE_B_EXECUTION_PACKET.md`

Recommended branch:

`impl/e11-floor-safety`

Migration:

```text
6 = pricing.floor_override permission definition
```

Migration 6 must not grant the permission to any role automatically.

Key invariants:

- server resolves current floor from authoritative DB rows;
- floor is not inferred from cost;
- ordinary `pricing.manage` cannot override floor;
- commit re-resolves current floor rather than trusting quote/client evidence;
- below-floor override requires dedicated permission + reason;
- price revision/audit/idempotency receipt commit atomically;
- old historical revisions remain untouched.

## Canonical migration chain before E02

```text
1  baseline_current_schema_20260810      E00
2  business_operations                   E01-B
3  jobs + job_attempts                   E01-D
4  outbox_events                         E01-E
5  operation_logs.correlation_id         E01-E
6  pricing.floor_override permission     E11-B
```

Therefore the first E02 schema migration must begin at **version 7** unless the then-current main contains another explicitly approved migration that changes this sequence.

Never reuse a migration number.

## Merge discipline

```text
pricing extraction parity PR
 -> full Gate
 -> E11-A
 -> full Gate
 -> E11-B Migration 6 + enforcement
 -> full Gate
 -> E02 starts from new main
```

## Stop conditions

Stop/split if early E11 work starts requiring:

- realized order-profit accounting;
- work-order actual cost;
- channel settlement;
- generalized approval/workflow engine;
- AI pricing;
- E02 inventory redesign;
- accounting/GL semantics.

Those belong to later E11/domain waves.

## Completion

The early E11 bridge is complete only when:

```text
historical pricing arithmetic remains stable
AND new margin/markup semantics are explicit
AND below-floor selling is server-controlled
AND authorized exceptions are auditable/idempotent
AND full Release Gate passes after each slice
```

Only then may E02 runtime implementation begin.
