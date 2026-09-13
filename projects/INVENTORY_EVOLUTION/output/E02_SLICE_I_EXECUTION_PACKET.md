# E02 Slice I Execution Packet — Manual Adjustment / Inventory Count Bridge

## Status

`READY_AFTER_E02_SLICE_H`

This packet makes manual stock corrections and approved count variances use the authoritative E02 movement/balance kernel.

It also retires the Slice-D shadow-only adapter for manual adjustment after parity is proven.

## Entry gate

All must be true:

```text
E02-H purchase receipt stock integration PASS
reconciliation zero unexplained divergence for shipment/transfer/procurement cohorts
manual adjustment shadow evidence from Slice D remains clean
full current-main Release Gate PASS
```

Suggested branch family:

```text
impl/e02-adjustment-authority
impl/e02-count-adjustment-bridge
```

Migration:

```text
NONE expected
```

Use existing count tables and Migration 7/8 stock truth.

## 1. Manual adjustment authority switch

Current route:

```text
POST /api/inventory/adjust
```

already requires `inventory.adjust` and routes through `InventoryService.adjust_inventory(...)`.

Slice D proved the path in same-transaction shadow mode.

Slice I changes the authority direction for the selected cohort/path:

```text
BEFORE
legacy inventory mutation = authority
new movement/balance = shadow

AFTER
new movement/balance = authority
legacy inventory/inventory_logs = compatibility projection/evidence only
```

Do not leave both as independent writers.

## 2. Manual adjustment command

Canonical E02 command:

```text
post_manual_adjustment
```

Required inputs/evidence:

```text
material_id
warehouse_id
canonical position identity
quantity_delta OR requested target quantity (one explicit mode)
reason_code
free-text reason where required
actor
business_operation_id
correlation_id
```

Client must not submit trusted `quantity_after`.

## 3. Delta mode

For an explicit delta:

```text
+N -> ADJUSTMENT_SOURCE -> stock position
-N -> stock position -> ADJUSTMENT_SINK
```

Quantity is absolute Decimal/UOM amount in movement line; direction comes from endpoints.

Negative result is rejected by authoritative Balance Projection unless a separately approved migration/correction policy permits otherwise.

## 4. Set-to mode

If UI/business requires “set current quantity to X”:

```text
BEGIN IMMEDIATE
 -> load current E02 balance under transaction
 -> requested target quantity validated
 -> delta = target - current
 -> post one manual_adjustment movement for delta
 -> update projection
 -> audit/result receipt
COMMIT
```

Do not:

```text
client reads current = 10
client sends delta based on stale value
```

for a set-to operation.

Server computes the delta from current authoritative state at commit time.

## 5. Adjustment reason taxonomy

Keep a small controlled set plus explanation, for example:

```text
physical_correction
data_migration_correction
damage_not_yet_quality_managed
administrative_correction
count_reconciliation
other_requires_reason
```

Do not use reason taxonomy to bypass future E07 scrap/quality processes.

Once a richer domain exists, high-consequence reasons should route to it instead of generic adjustment.

## 6. Idempotency

Every manual adjustment is E01 exactly-once.

Replay same operation key/same request:

```text
return original movement/result receipt
```

Same key/different delta/target/reason effect:

```text
idempotency conflict
```

Do not use button disable as the safety control.

## 7. Legacy compatibility after authority switch

If current UI/reports still read:

```text
inventory.quantity_available
inventory_logs
```

update/emit them from the authoritative movement transaction as compatibility representation.

Required invariant:

```text
E02 stock_balances = truth
legacy quantity = projection compatibility
```

No code outside compatibility adapter may directly edit the legacy balance for migrated manual adjustment.

Add a static/code scan test for forbidden direct writer patterns where practical.

## 8. Retire Slice-D shadow adapter

For manual adjustment path only:

```text
legacy-authoritative + shadow
```

must be replaced by:

```text
E02-authoritative + legacy compatibility
```

Do not keep a hidden configuration that can flip this path back and forth casually after authority switch.

Rollback requires a code version that still understands Movement/Balance truth.

## 9. Inventory count separation

Existing count domain remains conceptually:

```text
count session
 -> snapshot quantity
 -> physical counted quantity
 -> difference
 -> submit/review
```

Important invariant:

```text
observation != stock mutation
```

Creating/editing/submitting a count observation must not change stock.

Only an approved reconciliation action posts stock movement.

## 10. Count approval transaction

When reviewer approves a submitted count:

```text
BEGIN IMMEDIATE
 -> E01 operation admission
 -> load count session/items + authoritative warehouse scope/state
 -> for each count item load current E02 balance
 -> determine approved target/count policy
 -> calculate authoritative reconciliation delta
 -> post count_adjustment movement line(s)
 -> update balances
 -> update count session reviewed/approved state
 -> append audit/result receipt
COMMIT
```

All count movements for one approval should be one atomic operation or one clearly bounded transaction set according to current session semantics.

A failure on one required item must not leave a partially approved session unless partial approval is an explicit business feature.

## 11. Snapshot drift policy

A count session may record:

```text
snapshot_quantity at count creation
counted_quantity observed later
```

Meanwhile legitimate stock movements may occur before approval.

Do **not** blindly post:

```text
difference = counted - old_snapshot
```

against today's balance without considering current count policy.

Before implementation, characterize existing operational expectation and choose an explicit policy.

Safe options include:

### Policy A — freeze/lock counted scope during count

Then snapshot-to-count delta is valid under controlled freeze.

### Policy B — reconcile to counted target at approval

Server computes:

```text
current_authoritative_balance
 -> target observed count
 -> delta at approval
```

and records intervening movement evidence for reviewer visibility.

### Policy C — invalidate/recount if stock moved during count window

For a small warehouse this may be safest for selected scopes.

The system must not guess. Record the chosen count policy and test it.

Until approved, Slice I should not silently change the current count review arithmetic.

## 12. Count rejection

Rejecting a count session:

```text
updates review state/evidence only
```

No stock movement.

A rejected session remains auditable.

## 13. Count movement identity

Use deterministic identity linked to session/review generation, e.g.:

```text
inventory_count:<session_id>:approve:<review_generation>
```

Movement lines reference count item IDs.

Replay review request cannot post differences twice.

A previously approved session cannot be normally approved again without an explicit reversal/reopen workflow.

## 14. Count reversal/correction

If an approved count adjustment was wrong:

- do not edit/delete original movement;
- post compensating correction/reversal with reason/authority;
- preserve original count observation and review evidence.

Reopening a count should be a distinct controlled action if required.

## 15. Location dimension

Current count items are material/warehouse oriented and may not capture precise bin observation.

Slice I does not fabricate locations.

Use the canonical legacy/unassigned warehouse scope defined by E02-A for current count compatibility.

E03 later adds location-aware count observation and allocations.

## 16. Concurrency tests — manual adjustment

Fixture:

```text
balance = 10
A set-to 8
B set-to 7 concurrently
```

Each set-to computes delta under its own serialized transaction from then-current authoritative balance.

Final result must correspond to a valid ordered execution, with two explicit movements, never lost update caused by both using stale `10`.

Also test competing negative deltas cannot make balance negative.

## 17. Concurrency tests — count approval

At minimum:

- same approval operation cannot post twice;
- stock movement occurring after count snapshot is detected/handled according to chosen count policy;
- two reviewers cannot both approve the same session independently;
- failure mid-session approval rolls all required count movements/state back.

## 18. Legacy writer scan

After Slice I, scan repository for direct writes to:

```text
UPDATE inventory SET quantity_available
INSERT/UPDATE patterns that bypass stock domain
InventoryService.adjust_inventory legacy-authoritative use
```

Classify remaining writers:

```text
migrated / compatibility only
not-yet-migrated (must be named)
forbidden
```

Do not declare E02 ready for cutover while unnamed direct writers exist.

## 19. Integrity/reconciliation

Extend reconciliation:

```text
manual adjustment movements -> compatibility inventory/log rows
count approval movements -> approved count evidence
```

Detect:

- approved count with no required movement;
- count movement linked to unapproved/rejected session;
- legacy quantity diverging from E02 projection;
- duplicate adjustment for one business operation.

## 20. Expected files

Likely touchpoints:

```text
inventory_app/domains/stock/movement.py
inventory_app/domains/stock/balances.py
inventory_app/domains/stock/compatibility.py
inventory_app/services.py or extracted InventoryCount facade
inventory_app/server.py route adapter
inventory_app/platform/action_policy.py
inventory_app/db_integrity.py
tools/test_manual_adjustment_kernel.py
tools/test_inventory_count_bridge.py
tools/scan_direct_stock_writers.py
tools/reconcile_stock_kernel.py
tools/verify_release.py
```

## 21. Gate commands

```bash
python3 tools/test_manual_adjustment_kernel.py
python3 tools/test_inventory_count_bridge.py
python3 tools/scan_direct_stock_writers.py --check
python3 tools/reconcile_stock_kernel.py --check
python3 tools/verify_release.py
```

Linux release host:

```bash
python3 tools/verify_release.py --require-bash
```

## 22. PR review checklist

```text
[ ] manual adjust now posts Movement as authority
[ ] legacy inventory is compatibility projection only for this path
[ ] set-to delta computed server-side under transaction
[ ] reason/actor/idempotency evidence retained
[ ] count observation does not mutate stock
[ ] count approval posts explicit movement
[ ] count snapshot drift policy explicitly chosen/tested
[ ] rejected count posts no movement
[ ] duplicate approval/adjustment cannot double-post
[ ] location history not fabricated
[ ] remaining direct writers are named/classified
[ ] reconciliation zero unexplained divergence
[ ] full Release Gate PASS
```

Any `no` blocks merge.

## 23. Rollback

After manual/count path authority switches to E02, rollback must retain code compatible with Movement/Balance truth.

Do not restore a release that directly edits legacy balances for those paths.

If a defect is found, pause adjustment/count approval actions while preserving posted evidence and repair through a compatible release.

## 24. Exit / unlock

Slice I completes when:

```text
manual adjustment uses only E02 movement authority
approved count differences use the same movement kernel
observations stay separate from corrections
no stale set-to lost updates
remaining direct stock writers are fully inventoried
reconciliation remains clean
```

Then unlock:

```text
E02 Slice J — Final Authority Cutover / Legacy Write Fencing
```
