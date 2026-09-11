# TASK_INV_IMPL_E01_S03 — Pilot High-risk Routes on Action Wrapper

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Prove the Action Policy wrapper on a small set of existing write paths before wider migration.

This design is now bound to the audited pre-E00 code at:

`ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`

so implementation can preserve current route/service behavior rather than inventing new endpoints.

## Pilot 1 — transfer receive

Current HTTP family:

```text
POST /api/transfer-orders/{id}/receive
```

Current server behavior already has useful safety primitives:

```text
require_perm(ctx, "transfer.process")
load transfer row
receive/receive-exception/resume-receive
 -> require_warehouse_access(ctx, transfer_row, "to_warehouse_id")
 -> TransferService.receive(conn, tid, uid, data)
```

The current application development index also documents the transfer state family as roughly:

```text
draft
 -> pending_out_confirm
 -> in_transit / pending_receive
 -> completed
```

with exception/cancel paths.

### E01 action declaration target

```text
action_code: transfer.receive
permission: transfer.process
scope: loaded transfer.to_warehouse_id
state/precondition: existing TransferService receive rules
idempotency: REQUIRED in S04
business owner: TransferService.receive
```

### Why this is the first pilot

It is the cleanest proof that scope must come from the **loaded transfer object**, not a client warehouse field. It also has real replay consequences because receiving adds stock to the destination warehouse.

## Pilot 2 — purchase receipt

Current route family:

```text
POST /api/purchase-orders/{id}/{action}
action=receive
```

Current server dispatch:

```text
receive
 -> purchase permission path
 -> ProcurementService.receive(conn, order_id, data, uid)
```

Existing core-workflow tests already exercise a real receipt and assert that received quantity increases inventory at the PO warehouse.

### E01 action declaration target

```text
action_code: purchase.receive
permission: preserve current purchase-manage/approval routing contract
scope: loaded purchase_order.warehouse_id
state/precondition: existing ProcurementService.receive rules
idempotency: REQUIRED in S04
business owner: ProcurementService.receive
```

Implementation must inspect and preserve the current distinction between `purchase.manage` and approval-specific permission handling rather than flattening all purchase actions into one broad permission.

## Pilot 3 — shipment completion / reversal

Current route family:

```text
POST /api/shipment-tasks/{id}/{action}
```

Current server action dispatch includes:

```text
complete -> ShipmentService.complete(conn, tid, uid)
revoke   -> ShipmentService.revoke_completion(conn, tid, uid)
```

Current permission family is `shipment.process`; warehouse scope remains a backend-enforced concept rather than a frontend authority claim.

Existing core workflow tests prove that `ShipmentService.complete` decreases inventory and that reversal/revoke paths have state constraints.

### E01 action declaration targets

```text
action_code: shipment.complete
permission: shipment.process
scope: loaded shipment_task.warehouse_id
state/precondition: existing ShipmentService.complete rules
idempotency: REQUIRED in S04
business owner: ShipmentService.complete

optional second pilot after complete is stable:
action_code: shipment.revoke_completion
permission: shipment.process
scope: loaded shipment_task.warehouse_id
state/precondition: existing revoke rules
idempotency: REQUIRED in S04
business owner: ShipmentService.revoke_completion
```

Do not migrate completion and every shipment transition at once. Completion is the first consequential pilot; reversal follows only after parity is proven.

## Common migration method

For each route:

```text
existing HTTP parser
 -> authenticate
 -> load authoritative business object
 -> build RequestContext
 -> ActionPolicy lookup
 -> permission check
 -> warehouse/object scope check from loaded object
 -> existing state/precondition service logic
 -> existing domain/service method
 -> existing operation/stock evidence
 -> existing API response shape
```

E01 does **not** rewrite the underlying stock semantics. E02 owns Stock Position / Reservation redesign.

## Required invariants

- warehouse scope is derived from the loaded transfer/PO/shipment, never accepted from client authority claims;
- invalid state is rejected before business mutation;
- existing service/business behavior remains authoritative during the pilot;
- current operation/audit evidence is preserved;
- current API route and response compatibility is maintained;
- Action Policy must not become a second competing state machine;
- S03 proves centralized authorization/precondition wiring; S04 supplies the durable idempotency contract.

## Concrete implementation order

```text
1. transfer.receive
2. run full Release Gate
3. purchase.receive
4. run full Release Gate
5. shipment.complete
6. run full Release Gate
7. optional shipment.revoke_completion
```

Each pilot should be independently reviewable and revertible.

## Required tests per pilot

### Authorization / scope

- unauthenticated denied;
- wrong permission denied;
- permission present but warehouse/object outside actor scope denied;
- correct actor/scope allowed.

### State / mutation

- invalid state denied before stock mutation;
- success path matches existing service fixture;
- rejected action produces no inventory delta;
- existing operation/audit evidence is still written exactly once on success.

### Compatibility

- current endpoint remains unchanged;
- current response structure remains compatible;
- existing core workflow regression remains green.

### Idempotency handoff

Before the pilot is considered production-complete under E01-S04:

- same operation key + same request must not post the stock consequence twice;
- same operation key + different request must be rejected as conflict;
- timeout/retry must be able to return/reconstruct the original business result.

## Data migration

None in S03 itself.

The durable operation records required for replay protection belong to the proposed Migration 2 in E01-S04.

## Acceptance

At least these three materially different existing stock-affecting paths execute through the same Action Policy machinery without changing their public routes or existing business semantics:

```text
TransferService.receive
ProcurementService.receive
ShipmentService.complete
```

## Dependencies

E01-S01 and E01-S02 design/implementation first. E01-S04 must follow before these pilots can be considered fully replay-safe.

Runtime implementation remains blocked until:

```text
E00 real-checkout Release Gate = PASS
AND Inventory PR #3 is reviewed/merged
```
