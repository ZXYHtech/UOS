> Execution target: **ZXYHtech/inventory-Pro** only. Read [repository isolation](../REPOSITORY_ISOLATION.md) before acting; old production/PR instructions below are superseded.

# E02 Slice G Execution Packet — Transfer Issue / In-transit / Receipt

## Status

`READY_AFTER_E02_SLICE_F`

This packet migrates warehouse transfer stock effects onto the authoritative E02 movement/balance kernel while preserving current transfer workflow, partial receipt and exception semantics.

## Entry gate

All must be true:

```text
E02-F selected shipment cohort proves reservation + issue authority
Movement/Balance/Reservation recovery verification PASS
stock reconciliation has zero unexplained divergence for migrated paths
full current-main Release Gate PASS
```

Suggested branch family:

```text
impl/e02-transfer-issue
impl/e02-transfer-receipt
impl/e02-transfer-reversal
```

Migration:

```text
NONE expected
```

Use Migration 7/8 stock truth. If a durable transfer-line transition reference is genuinely missing, allocate a separately reviewed next contiguous migration rather than altering prior migrations.

## 1. Core transfer model

A transfer is not an instantaneous warehouse-to-warehouse balance change.

Authoritative timeline:

```text
SOURCE AVAILABLE
 -> transfer_issue
 -> IN_TRANSIT owned by this transfer/line
 -> transfer_receipt(s)
 -> DESTINATION AVAILABLE / receiving scope
```

At any time:

```text
issued quantity
= received quantity
+ remaining in-transit
+ explicitly resolved loss/variance when later policy allows
```

Do not use anonymous `quantity_on_transfer` as independent truth.

## 2. Important legacy behavior to retire

Current `TransferService.receive()` contains compatibility logic that can detect missing legacy `transfer_out` evidence and post a source deduction during receipt before crediting destination stock.

That behavior must **not** survive once E02 transfer movement becomes authoritative.

In authoritative mode:

```text
receipt requires an existing posted transfer_issue for the relevant transfer line/generation
```

If missing:

```text
BLOCK receipt
 -> create reconciliation/migration exception
```

Do not silently manufacture a historical source issue at receipt time.

A one-time migration/repair command may reconstruct an opening/in-transit state from proven legacy evidence before authority switch, but it must be explicitly labeled migration/reconciliation evidence rather than a normal receipt side effect.

## 3. Transfer issue operation

Current transfer `ship()` / dispatch path becomes the only normal creator of source issue.

Target transaction:

```text
BEGIN IMMEDIATE
 -> E01 business-operation admission
 -> load transfer + items
 -> existing permission/from-warehouse scope/state checks
 -> validate source stock from E02 balances
 -> for each item post transfer_issue movement:
      source available position -> transfer-specific IN_TRANSIT position/scope
 -> update stock_balances atomically
 -> update transfer shipped/in_transit state/logistics timestamps using current workflow
 -> append existing transfer/audit evidence
 -> result receipt
COMMIT
```

No external carrier/platform call inside transaction.

## 4. In-transit identity

In-transit stock must be attributable to a specific transfer and item/requirement.

Do not create one anonymous warehouse-level in-transit bucket that loses ownership.

Recommended canonical semantics:

```text
stock status/scope = IN_TRANSIT
reference_type = transfer_order
reference_id = transfer_id
line_reference_id = transfer_item_id
```

The physical owner remains the company unless a later ownership domain says otherwise.

The exact position-key encoding must reuse E02 identity helpers and not overload a fake warehouse/bin.

## 5. Transfer issue operation key

Stable semantic identity, e.g.:

```text
transfer:<transfer_id>:issue:generation:<n>
```

Generation changes only after a legitimate reversal/reissue cycle.

Replay same key/same effect returns original receipt.

Same key/different quantities/logistics effect conflicts.

## 6. Receipt operation

Receipt consumes only quantity actually present in transfer-specific in-transit state.

Target transaction:

```text
BEGIN IMMEDIATE
 -> E01 business-operation admission
 -> load transfer + current lines + authoritative issue/in-transit evidence
 -> destination warehouse permission/scope/state checks
 -> normalize actual received quantities
 -> require 0 <= received <= remaining_in_transit per line
 -> post transfer_receipt movement:
      transfer-specific IN_TRANSIT -> destination receiving/available scope
 -> update balances
 -> update transfer_items.received_quantity compatibility state
 -> append transfer_receipt_events using current workflow semantics
 -> update transfer status/exception/completion
 -> audit/result receipt
COMMIT
```

Do not alter source warehouse again during normal receipt.

## 7. Partial receipt

Current workflow supports partial receipt and shortage/exception reason.

Preserve it.

Example:

```text
issue 10
receipt #1 = 7
```

Result:

```text
source available already -10
in-transit remaining = 3
destination +7
transfer remains exception/pending according to existing workflow
```

A later receipt of 3 consumes the remainder.

No receipt may exceed remaining in-transit.

## 8. Receipt identity

Every receipt event needs deterministic business identity.

Preferred:

```text
existing transfer_receipt_events.id
```

if the event is created in the same authoritative transaction and can safely back the operation key.

Conceptual operation key:

```text
transfer:<transfer_id>:receipt:<receipt_event_id>
```

If the receipt event ID is only known after insert, use E01 operation identity as the outer replay key and bind the resulting receipt event/movement IDs in the result receipt.

Do not use `transfer_id` alone because partial receipt legitimately occurs multiple times.

## 9. Missing / damaged / discrepancy quantities

Until E07 quality states exist, unresolved transfer discrepancy remains explicit business exception evidence.

Do not:

- credit missing quantity to destination;
- delete in-transit quantity;
- silently shrink original issued quantity;
- auto-scrap it without authority.

Keep unresolved quantity in attributable in-transit/exception state until a controlled resolution posts the correct compensating/disposition movement.

## 10. Transfer receive exception / resume

Existing `receive-exception` and `resume-receive` workflow remains state/evidence control.

Reporting an exception alone must not alter physical balances unless the business action includes an actual receipt/disposition.

`resume_receive` may make the transfer receivable again but must not reset/recreate in-transit quantity.

E02 balance truth comes from posted movements.

## 11. Shipment/issue reversal before any receipt

Existing `revoke_shipment` concept can be migrated safely when:

```text
received quantity = 0
remaining in-transit = full issued quantity
```

Target:

```text
original transfer_issue remains immutable
 -> post compensating transfer_issue_reversal:
      IN_TRANSIT -> source available
 -> update balances
 -> transition transfer workflow state
 -> audit/result receipt
```

Never delete original issue movement.

## 12. Reversal after partial receipt

Do not blindly reverse the original full issue once destination receipt exists.

Example:

```text
issued = 10
received = 7
remaining in-transit = 3
```

Maximum normal source-return reversal from transit is 3.

The 7 already received at destination requires its own destination-side return/transfer-back business action if it must be undone.

Tests must enforce this boundary.

## 13. Legacy reconciliation before transfer authority

Before enabling E02 transfer authority for open transfers, build a read-only preview:

```text
transfer/order line
legacy status
planned quantity
legacy transfer_out net evidence
legacy received_quantity
legacy transfer_in evidence
expected source issue
expected remaining in-transit
expected destination received
classification
```

Classifications at minimum:

```text
CLEAN_NOT_SHIPPED
CLEAN_IN_TRANSIT
CLEAN_PARTIAL_RECEIPT
CLEAN_COMPLETED
MISSING_SOURCE_ISSUE
SOURCE_ISSUE_MISMATCH
RECEIPT_MISMATCH
AMBIGUOUS
```

No authoritative transfer cutover with unresolved `MISSING_SOURCE_ISSUE` or quantity mismatch.

A migration repair operation must preserve source legacy references and never pretend it happened at the historical business timestamp unless that timestamp is actually evidenced.

## 14. Compatibility fields

During migration, existing:

```text
transfer_items.received_quantity
transfer_orders.status
inventory.quantity_on_transfer (if still used by UI/report)
```

may remain compatibility projections/fields.

They must no longer be independent stock truth once a transfer cohort is E02-authoritative.

If `quantity_on_transfer` is retained for old UI, derive it from authoritative transfer/in-transit state rather than mutating it independently.

## 15. Permission/scope preservation

Reuse current Action Policy semantics:

```text
transfer.process
ship/revoke-ship -> from_warehouse scope
receive/receive-exception/resume -> to_warehouse scope
```

Do not broaden transfer authority while migrating stock semantics.

Existing admin approval rules for transfer requests remain separate workflow rules.

## 16. Failure/replay tests

### Issue

- same issue operation retry posts one movement only;
- failure after movement insert but before transfer state update rolls back all;
- insufficient source balance rejects without any in-transit residue;
- same key/different quantity conflicts.

### Receipt

- partial receipt posts exact in-transit -> destination quantity;
- lost response retry does not double receive;
- over-receipt rejected;
- missing authoritative issue blocks receipt;
- forced failure rolls movement/balance/received_quantity/event/status back together.

### Reversal

- pre-receipt revoke restores source once through compensation;
- replay safe;
- partial receipt prevents full issue reversal;
- max reversible amount equals remaining in-transit.

## 17. End-to-end conservation test

For each material/transfer line:

Before transfer:

```text
source 20
destination 5
```

Issue 10:

```text
source 10
in_transit 10
destination 5
company physical total = 25
```

Receive 7:

```text
source 10
in_transit 3
destination 12
company physical total = 25
```

Receive 3:

```text
source 10
in_transit 0
destination 15
company physical total = 25
```

No quantity appears/disappears through normal transfer execution.

## 18. Backup/integrity/reconciliation

Extend stock reconciliation to check:

```text
transfer issue quantity
= received + remaining in transit + approved resolved variance
```

Integrity checks should surface:

- receipt without issue;
- negative in-transit;
- receipt exceeding issued;
- completed transfer with unresolved in-transit;
- compatibility received_quantity differing from movement evidence.

Recovery verifier already covers Movement/Balance tables; no new table is expected in this slice unless an explicitly approved migration is added.

## 19. Expected files

Likely touchpoints:

```text
inventory_app/domains/stock/movement.py
inventory_app/domains/stock/balances.py
inventory_app/domains/stock/reconciliation.py
inventory_app/services.py or extracted transfer facade
inventory_app/platform/action_policy.py
inventory_app/db_integrity.py
tools/test_transfer_stock_kernel.py
tools/test_transfer_stock_reversal.py
tools/preview_open_transfer_migration.py
tools/reconcile_stock_kernel.py
tools/verify_release.py
```

Do not add E03 putaway or E07 quality/lot semantics.

## 20. Gate commands

```bash
python3 tools/test_transfer_stock_kernel.py
python3 tools/test_transfer_stock_reversal.py
python3 tools/preview_open_transfer_migration.py --check
python3 tools/reconcile_stock_kernel.py --check
python3 tools/verify_release.py
```

Linux release host:

```bash
python3 tools/verify_release.py --require-bash
```

## 21. PR review checklist

```text
[ ] transfer is source issue -> in-transit -> destination receipt
[ ] normal receipt never backfills missing source issue
[ ] in-transit is transfer/line attributable
[ ] partial receipt supported
[ ] over-receipt impossible
[ ] missing/damaged quantity remains explicit unresolved evidence
[ ] original movements immutable; reversal compensates
[ ] partial receipt limits issue reversal
[ ] current permissions/scope preserved
[ ] compatibility counters are not independent truth
[ ] open-transfer migration preview has no unresolved blocker for authority cohort
[ ] full Release Gate PASS
```

Any `no` blocks merge.

## 22. Rollback

Once selected transfers become E02-authoritative, rollback must use a code version that still honors posted transfer movements/in-transit balances.

Do not return those transfers to legacy receipt logic that may backfill source deductions or mutate anonymous counters independently.

New transfer creation/processing may be paused if a defect is found while existing E02 transfer evidence remains preserved.

## 23. Exit / unlock

Slice G completes when controlled real transfers prove:

```text
source issue exactly once
in-transit quantity attributable and conserved
partial/multiple receipts exactly once
destination receipts cannot exceed transit
legacy receipt backfill behavior retired for authoritative cohort
reversal bounded by remaining transit
reconciliation zero unexplained divergence
```

Then unlock:

```text
E02 Slice H — Procurement Receipt Integration
```
