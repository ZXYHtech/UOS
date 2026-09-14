> Execution target: **ZXYHtech/inventory-Pro** only. Read [repository isolation](../REPOSITORY_ISOLATION.md) before acting; old production/PR instructions below are superseded.

# E02 Slice D Execution Packet — Same-transaction Shadow Posting

## Status

`READY_AFTER_E02_SLICE_C`

This packet introduces the first production-like shadow use of the new stock ledger/projection while the legacy `inventory` table remains the sole business authority.

It is deliberately **not** a stock cutover.

## Entry gate

All must be true:

```text
E00 PASS / merged
E01 complete / merged
E11-S01/S02 complete / merged
E02-A identity/UOM contract complete
E02-B Migration 7 movement ledger complete
E02-C Migration 8 balance projection/opening reconciliation complete
legacy opening mapping unresolved blockers = 0
full current-main Release Gate = PASS
```

Suggested branch:

```text
impl/e02-shadow-stock
```

Migration:

```text
NONE
```

Slice D reuses Migration 7/8 objects. If the implementation discovers a genuinely missing schema field, stop and create a separately reviewed contiguous migration rather than silently editing Migration 7/8.

## 1. Purpose

Prove that an existing real stock-changing operation can write:

```text
legacy inventory + inventory_logs
AND
new stock_movement_operations/lines + stock_balances
```

inside one SQLite transaction, with the legacy result still authoritative to operators/business flows.

The first pilot is intentionally low-risk:

```text
POST /api/inventory/adjust
```

Existing characteristics to preserve:

- requires `inventory.adjust`;
- validates material usage/current route policy;
- calls `InventoryService.adjust_inventory(...)`;
- produces legacy `inventory_logs` / operation audit evidence;
- does not involve an external network side effect.

Do not begin with shipment, purchase receipt or transfer receipt. Those paths have additional state and economic semantics and are migrated later.

## 2. Authority mode

During Slice D:

```text
LEGACY = authoritative
NEW KERNEL = shadow evidence only
```

Therefore:

- normal UI reads legacy inventory;
- shipment availability logic reads legacy inventory;
- no reservation/ATP authority exists yet;
- no ordinary API exposes new balance as the number users should act on;
- privileged reconciliation tooling may show old/new side-by-side with an explicit `SHADOW` label.

No code path may select the new quantity merely because the table exists.

## 3. Feature-mode contract

Introduce a code-owned/configured stock-kernel mode with deliberately small vocabulary, e.g.:

```text
legacy_only
shadow
```

Do not add `authoritative` in Slice D unless it is an unreachable enum reserved for later E02-J cutover.

Recommended configuration behavior:

- default after deploy remains `legacy_only`;
- test/staging can enable `shadow`;
- production shadow enablement is explicit/operator-controlled after opening reconciliation is clean;
- changing the mode requires restart or a controlled admin configuration path with audit, not an arbitrary request parameter.

Client payload must never choose shadow mode.

## 4. Target implementation seam

Preferred target boundary:

```text
InventoryService.adjust_inventory(...)
```

Do not duplicate legacy inventory mutation logic in the route.

Introduce a bounded compatibility/shadow adapter around the existing mutation, conceptually:

```text
post_legacy_adjustment_with_optional_shadow(conn, ...)
```

or an equivalent helper in:

```text
inventory_app/domains/stock/compatibility.py
```

The helper receives the caller-owned `sqlite3.Connection`.

It must not open another connection or call `commit()` independently.

## 5. Exact transaction invariant

The current request transaction remains one atomic unit.

Conceptually:

```text
BEGIN IMMEDIATE / caller-owned write transaction
 -> E01 business-operation/idempotency admission where route is wrapped
 -> execute existing legacy InventoryService.adjust_inventory
      -> update inventory
      -> insert inventory_logs
      -> existing operation audit
 -> normalize the exact same material/warehouse/location/owner/status identity
 -> post shadow stock_movement_operation/line
 -> update shadow stock_balances
 -> compare the affected identity old vs new
 -> mark business-operation receipt succeeded
COMMIT
```

If **any** shadow insert/projection/reconciliation assertion fails:

```text
ROLLBACK everything
```

Do not allow the legacy write to succeed while shadow evidence is missing for a path declared shadow-enabled.

This is why asynchronous/best-effort shadow posting is forbidden.

## 6. Operation identity

Shadow movement must have deterministic identity derived from the same E01 business operation, not a timestamp-only random key.

For the manual adjustment pilot, prefer:

```text
business_operation_id / operation key
 -> stock movement operation key
```

Example semantic form:

```text
manual_adjustment:<business_operation_id>
```

Do not use free-text `reason` as identity.

Replay of the E01 operation must return the original result and must not create a second legacy log or second shadow movement.

## 7. Movement semantics

Legacy `quantity_delta` is translated into explicit source/destination direction.

For a positive adjustment:

```text
ADJUSTMENT_SOURCE -> stock position
quantity = abs(delta)
```

For a negative adjustment:

```text
stock position -> ADJUSTMENT_SINK
quantity = abs(delta)
```

Movement metadata records:

```text
action_code = inventory.adjust
reference_type / reference_id where current route provides them
reason
actor
correlation_id
business_operation_id
```

The new movement must never infer a historical lot/bin/account that legacy evidence does not contain.

## 8. Position identity mapping

Use the exact E02-A identity helper.

Do not hand-build a second key in the shadow adapter.

If the current legacy row has no trustworthy location:

```text
location scope = LEGACY_UNASSIGNED
```

If a non-null `platform_account_id` cannot yet be safely classified as physical owner scope:

```text
block/flag according to E02-A mapping report
```

Do not silently map it to company-owned stock.

The initial production shadow pilot may be limited to identities already classified as safe if that is necessary to avoid guessing.

## 9. Affected-row parity check

After each shadow-enabled adjustment and before commit, calculate a narrow deterministic parity check for the affected canonical identity.

At minimum compare:

```text
legacy mapped quantity
new stock_balances quantity_on_hand
```

If they differ unexpectedly:

```text
raise / rollback
```

This transaction-local assertion complements the repository-wide reconciliation command from Slice C.

Do not auto-copy one side to the other to make the check pass.

## 10. Repository-wide reconciliation

Continue to run:

```text
L1 material totals
L2 material + warehouse
L3 canonical position identity
```

A shadow run result should capture:

```text
run id
authority = legacy
shadow enabled paths
opening baseline id
number of observed stock changes
unresolved divergence count
last divergence source/action
eligible_for_next_slice true/false
```

Slice D completion requires zero unexplained divergence in deterministic fixtures and the agreed observation window for the pilot path.

The business duration/operation-count threshold remains an operator decision, not a hard-coded guess.

## 11. Failure-injection tests

Required deterministic tests:

### Legacy succeeds, shadow insert forced to fail

Inject failure after legacy inventory DML and before shadow completion.

Require:

- legacy balance rolls back;
- legacy `inventory_logs` rolls back;
- new movement/projection absent;
- E01 operation not marked succeeded;
- retry can execute exactly once.

### Shadow movement inserts, projection fails

Require whole transaction rollback.

### Projection updates, parity assertion fails

Require whole transaction rollback and explicit test-visible error.

### Lost response after commit

Retry same operation key:

- no second legacy delta;
- no second legacy inventory log;
- no second movement;
- no second projection effect;
- same E01 receipt returned.

### Same key / different delta

Require idempotency conflict with no mutation.

## 12. Concurrency tests

Two different adjustment operations may serialize under SQLite `BEGIN IMMEDIATE`.

For the same stock identity, test:

```text
starting legacy qty = 10
A delta = -6
B delta = -6
```

Since Slice C projection and the legacy mutation both run in the same serialized transactions, require:

- at most one operation can produce a result that would leave physical quantity negative;
- successful legacy and shadow results remain equal;
- failed operation leaves no ledger/projection residue.

Important: this test proves the **shadow adapter remains coherent** under contention. It does not make the new projection production authority yet.

## 13. Existing API compatibility

`POST /api/inventory/adjust` response contract should remain compatible.

Do not require clients to know about shadow movement IDs.

A privileged debug/test response may expose correlation/operation evidence only behind explicit non-default diagnostics if needed.

Normal users should not see two competing balances.

## 14. Observability

Add bounded diagnostic counters/logging for:

```text
shadow adjustment attempts
shadow adjustment commits
shadow rollback/failures
parity assertion failures
reconciliation divergence count
```

Do not emit customer secrets or full payloads in logs.

A parity failure is high-severity migration evidence, not a warning to ignore.

## 15. Explicit non-goals

Do not include:

- reservation/ATP;
- shipment/purchase/transfer route migration;
- lot/serial/quality state;
- E03 bin allocation;
- UI authority switch;
- automatic legacy/new divergence correction;
- channel inventory publication;
- removal of current `inventory`/`inventory_logs`.

If any of these become necessary, stop and split work.

## 16. Required test/gate commands

Focused examples:

```bash
python3 tools/test_stock_identity.py
python3 tools/test_stock_movement.py
python3 tools/test_stock_projection.py
python3 tools/test_stock_shadow_adjustment.py
python3 tools/reconcile_stock_kernel.py --check
python3 tools/verify_release.py
```

On Linux release workstation:

```bash
python3 tools/verify_release.py --require-bash
```

## 17. PR review checklist

```text
[ ] branch based on post-E02-C main
[ ] no schema migration
[ ] legacy remains explicit authority
[ ] only selected adjustment path shadow-enabled
[ ] one connection / one transaction
[ ] no async best-effort shadow writer
[ ] E02-A identity helper reused
[ ] same E01 business operation keys both effects
[ ] forced shadow failure rolls legacy back
[ ] normal API response remains compatible
[ ] ordinary reads still legacy
[ ] reconciliation shows zero unexplained divergence
[ ] full Release Gate PASS
```

Any `no` blocks merge.

## 18. Rollback

Before new stock kernel authority:

```text
disable shadow mode / revert Slice D code
```

Keep Migration 7/8 evidence and reconciliation artifacts.

Do not delete shadow movement history merely because shadow mode is disabled.

Rollback must leave the legacy authoritative path intact.

## 19. Exit / unlock

Slice D is complete when:

```text
one real low-risk stock-changing path
writes legacy + new kernel atomically
with deterministic replay/failure/concurrency proof
and zero unexplained divergence
while legacy remains business authority
```

Then unlock:

```text
E02 Slice E — Reservation / ATP
```
