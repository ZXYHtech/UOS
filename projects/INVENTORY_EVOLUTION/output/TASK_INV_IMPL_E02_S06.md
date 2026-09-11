# TASK_INV_IMPL_E02_S06 — Transfer / Procurement / Manual-adjust Migration

## Status

`DESIGN_READY_BLOCKED_BY_E02_S05`

## Objective

Migrate the remaining high-value stock-changing paths onto the new movement ledger and reservation-aware stock kernel after shipment integration is proven.

Target paths:

```text
transfer issue
transfer receipt / partial receipt / reversal
purchase receipt
manual stock adjustment / count correction bridge
```

Do not broaden this story into advanced WMS receiving/putaway; E03 owns staging/bin workflow.

## 1. Transfer semantics

A transfer is one business flow with two physical events:

```text
source issue
 -> in transit
 -> destination receipt
```

Do not model transfer as an immediate atomic move from source balance to destination balance if the real process has transport time.

### Transfer issue

Expected stock effect:

```text
source available position - quantity
 -> explicit in-transit scope/state + quantity
```

The in-transit quantity must be represented through ledger/balance semantics, not an anonymous `quantity_on_transfer` counter with no traceable transfer-line identity.

Suggested operation key:

```text
transfer:<transfer_id>:issue:<generation>
```

### Transfer receipt

Expected stock effect:

```text
in-transit quantity - received
 -> destination available/unassigned position + received
```

Partial receipt remains supported. Each receipt event requires a deterministic identity linked to the existing transfer receipt event or a new canonical receipt identity.

Suggested operation key:

```text
transfer:<transfer_id>:receipt:<receipt_event_id>
```

### Transfer discrepancy

Short/damaged/missing quantities must not silently disappear.

Until E07 quality states exist, unresolved transfer discrepancy remains linked to the transfer exception/reconciliation flow with explicit quantity/evidence.

Do not manufacture a destination “available” receipt for unconfirmed missing quantity.

### Transfer reversal

Use compensating movement against the exact original transfer operation. Respect how much has already been received; do not reverse source issue blindly if destination receipt already consumed part of the in-transit amount.

## 2. Procurement receipt semantics

Current `ProcurementService.receive` is a good pilot because it already has explicit purchase order/item/receipt concepts.

New flow:

```text
load approved PO + line
 -> validate remaining receivable quantity
 -> create/confirm purchase receipt identity
 -> post purchase_receipt movement into warehouse/unassigned receiving position
 -> update PO receipt state/history
 -> audit/result receipt
COMMIT
```

Do not require IQC/lot/date-code/COC in E02; those arrive later through E07. E03 may later route receipt into staging/putaway rather than final stock position.

### Duplicate receipt protection

A retry of one receipt cannot create a second stock movement.

Use receipt/event identity + E01 business-operation key, not only current PO status.

### Over-receipt

Policy must be explicit:

```text
reject by default
or allow within configured business policy with reason/permission
```

Do not silently increase ordered quantity to make receipt fit.

## 3. Manual adjustment

Manual stock adjustment remains necessary but becomes an explicit movement operation, not a direct balance editor.

Required evidence:

```text
material/position
before projection
adjustment quantity or target quantity
calculated delta
reason code
free-text explanation where required
actor
correlation/business operation
```

For “set quantity to X”, server computes the delta from authoritative projection inside the transaction and posts a movement.

Client does not submit a trusted `quantity_after`.

## 4. Inventory count bridge

E03 will own full count observation/reconciliation design, but current count corrections should transition through the same movement primitive.

Keep count observation separate from balance correction:

```text
observed count != stock movement
approved reconciliation delta -> count_adjustment movement
```

Never rewrite historical movement lines to force the ledger to equal a count.

## 5. Legacy field compatibility

During migration, current fields such as:

```text
inventory.quantity_available
inventory.quantity_on_transfer
```

may be populated through a compatibility projection for existing UI/report paths.

They stop being independently editable truth.

`quantity_locked` transitions to reservation projection only when S04/S05 authority is active.

## 6. Scope/permission

Reuse existing route/service permissions and warehouse access semantics through E01 Action Policy.

Examples:

```text
transfer.process
purchase.manage / purchase receive authority
inventory.adjust
```

If the current purchase receipt permission is too broad, split it in a separately reviewed permission change rather than hiding policy change inside the stock migration.

## 7. Migration sequence

Migrate one path at a time:

```text
A. transfer issue/receipt shadow + parity
B. transfer authoritative posting
C. purchase receipt shadow + parity
D. purchase authoritative posting
E. manual adjustment
F. current count adjustment bridge
```

Run full Release Gate and reconciliation after every path.

If a path reveals unresolved semantic ambiguity, stop there rather than keeping two partial implementations live.

## Tests

- transfer issue reduces source and increases explicit in-transit exactly once;
- partial receipt decreases in-transit and increases destination by exact receipt quantity;
- repeated receipt event cannot double-receive;
- receipt beyond remaining in-transit is rejected;
- transfer reversal cannot over-reverse already received quantity;
- purchase receipt posts stock exactly once under retry;
- purchase over-receipt follows explicit policy;
- failed receipt rolls back PO/receipt/stock effects together;
- manual set-to quantity calculates server-side delta correctly;
- duplicate manual operation key cannot post twice;
- count observation alone does not alter stock;
- approved count reconciliation posts a separate movement;
- compatibility projection equals new authoritative balances;
- full Release Gate passes.

## Rollback

Before a path becomes authoritative, revert that pilot to legacy ownership and retain shadow evidence.

After a path is authoritative, rollback requires code that continues to write movement truth; do not restore direct legacy balance mutation.

## Acceptance

S06 is complete when shipment, transfer, procurement receipt and manual/count stock corrections all use the same idempotent movement kernel and old mutable balance fields are compatibility projections rather than independent truths.

## Dependencies

E02-S05; E01 common primitives.

## Non-goals

- no advanced receiving staging/putaway;
- no IQC/quarantine;
- no supplier lot/serial;
- no work-order material issue;
- no MRP.