# TASK_INV_IMPL_E01_S03 — Pilot High-risk Routes on Action Wrapper

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Prove the Action Policy wrapper on a small set of existing write paths before wider migration.

## Pilot candidates

1. transfer receive / partial receive;
2. purchase receipt;
3. shipment completion or reversal.

These are selected because they combine permission, warehouse scope, business state, stock mutation and replay risk.

## Migration method

For each route:

```text
existing HTTP parser
 -> build RequestContext
 -> action executor
 -> existing domain/service method
 -> existing API response contract
```

Do not rewrite the underlying stock semantics in E01; E02 owns Stock Position/Reservation redesign.

## Required invariants

- warehouse scope is derived from the loaded transfer/PO/shipment, not accepted from client authority claims;
- invalid state is rejected before mutation;
- service mutation remains inside its existing transaction boundary unless explicitly improved by S04;
- existing operation/audit evidence is preserved;
- API compatibility is maintained.

## Data migration

None.

## Tests

Per pilot route:

- authorization matrix;
- cross-warehouse denial;
- invalid-state denial;
- success path parity with existing fixture;
- rejected action posts no stock mutation;
- same existing core workflow tests continue to pass.

## Rollout

Migrate one route, run the full E00 Release Gate, then the next. Do not combine broad server refactoring with all three route migrations.

## Acceptance

Three materially different write paths execute through the same action-policy machinery without observable business regression.

## Dependencies

E01-S01, E01-S02. Idempotency guarantees are completed by E01-S04 rather than simulated here.
