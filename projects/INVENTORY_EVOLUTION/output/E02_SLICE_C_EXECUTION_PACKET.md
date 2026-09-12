# E02 Slice C Execution Packet — Balance Projection / Opening Reconciliation

## Status

`READY_TO_IMPLEMENT_AFTER_E02_SLICE_B`

This packet turns `TASK_INV_IMPL_E02_S03.md` into a code-level implementation handoff.

## Entry gate

Do not implement until:

```text
E02 Slice B / Migration 7 merged
AND movement-ledger tests pass
AND current main passes tools/verify_release.py
```

Recommended branch:

```text
impl/e02-stock-projection
```

## Objective

Add a rebuildable current-balance projection derived from immutable Movement Ledger evidence, then prove it can reproduce legacy opening stock exactly **without making the new balance authoritative for production UI/business yet**.

This is the first E02 slice allowed to prove the new kernel's isolated negative-stock/concurrent-spend safety.

## Migration ownership

### Migration 8

Add:

```text
stock_balances
```

No reservation table yet.

Canonical chain:

```text
1 E00 baseline
2 business_operations
3 jobs + job_attempts
4 outbox_events
5 operation_logs.correlation_id
6 pricing.floor_override permission
7 stock_movement_operations + stock_movement_lines
8 stock_balances
```

## Target files

Recommended:

```text
inventory_app/domains/stock/
  balances.py
  reconciliation.py
  opening_balance.py

inventory_app/domains/stock/movement.py   # integrate projection update
inventory_app/schema_migrations.py
inventory_app/db_integrity.py
inventory_app/recovery_verifier.py

tools/reconcile_stock_kernel.py
tools/test_stock_balance_projection.py
tools/test_stock_opening_reconciliation.py
```

No ordinary production route migrates to the new balance in Slice C.

## Migration 8 schema

### stock_balances

Recommended columns:

```text
position_key TEXT PRIMARY KEY
material_id INTEGER NOT NULL
warehouse_id INTEGER NOT NULL
location_scope TEXT NOT NULL
owner_scope TEXT NOT NULL
stock_status TEXT NOT NULL
quantity_text TEXT NOT NULL
uom_code TEXT NOT NULL
last_movement_operation_id INTEGER
updated_at TEXT NOT NULL
```

Indexes:

```text
(material_id, warehouse_id, stock_status)
(warehouse_id, location_scope, material_id)
(last_movement_operation_id)
```

### Identity invariant

The decomposed fields must reconstruct exactly the same `position_key` under Slice-A identity logic.

Do not accept arbitrary client-provided keys that disagree with their dimensions.

### Quantity invariant

`quantity_text` is canonical Decimal serialization.

For current EA stock:

```text
non-negative integer quantity
```

Future fractional UOMs remain governed by Slice-A UOM policy.

## Projection posting algorithm

When the **new kernel** posts a movement in isolated/shadow use:

```text
BEGIN IMMEDIATE
 -> E01/Movement replay admission
 -> validate every movement line
 -> load all affected stock_balances rows
 -> compute Decimal net effect per position
 -> reject any resulting physical POSITION balance < 0
 -> insert movement operation + lines
 -> upsert/update affected stock_balances
 -> store last_movement_operation_id
 -> audit/result receipt where applicable
COMMIT
```

Important:

- ledger and projection commit together for synchronous new-kernel posting;
- projection is derived/cache state, not immutable truth;
- if projection is wrong, repair/rebuild projection; never rewrite movement history merely to fit projection.

## Explicit concurrency proof

Because SQLite serializes writers under `BEGIN IMMEDIATE`, test the actual race:

```text
starting balance = 5
connection A attempts -4
connection B attempts -4 concurrently
```

Require:

```text
at most one posts successfully
final balance cannot be negative
movement evidence count matches successful commits only
```

Do not implement this as:

```text
read balance outside transaction
then later update
```

The authoritative validation read must occur after the new-kernel write transaction owns SQLite write access.

## Projection effect rules

For each movement line:

```text
from_endpoint_type = POSITION
 -> subtract quantity from from_position_key

to_endpoint_type = POSITION
 -> add quantity to to_position_key
```

A transfer POSITION -> POSITION therefore updates two positions atomically.

External endpoints do not have balance rows.

## UOM consistency

For each position:

```text
all movement lines must use the canonical UOM for that material/position policy
```

A movement that tries to add `MASS` into an `EA` position is rejected unless a future explicit conversion operation exists.

No implicit conversion in E02 v1.

## Projection rebuild

Provide a deterministic rebuild service that starts from immutable movement evidence.

Recommended command:

```bash
python3 tools/reconcile_stock_kernel.py --rebuild-temp
```

Behavior:

1. create isolated/temp projection structure;
2. iterate/post movement effects in deterministic operation/line order;
3. derive quantity by canonical position key;
4. compare temp projection to live `stock_balances`;
5. output diff;
6. do **not** overwrite live projection by default.

### Controlled repair

If a future explicit `--publish-rebuild` is implemented, it must require:

- clean ledger integrity;
- reviewed diff;
- pre-change DB backup;
- explicit operator confirmation;
- audit record.

It is not required for Slice C completion.

## Opening-balance import

Legacy stock history is not reconstructed.

Create one explicit opening-baseline event from current legacy balances.

### Preconditions

Opening import may run only when Slice-A mapping report has:

```text
BLOCKED count = 0
```

and every `REVIEW_REQUIRED` item intended for migration has an explicit reviewed resolution.

### Source evidence snapshot

Opening import must record:

```text
source DB identity/hash where available
source schema migration version
source application release ref
import run id
legacy inventory row id per line
legacy quantity
legacy material/warehouse/location/account metadata
normalized position key
normalized UOM
```

Do not fake historical movement dates.

### Recommended operation representation

Use explicit movement type:

```text
migration.opening_balance
```

Endpoint:

```text
MIGRATION_OPENING -> POSITION
```

A single deterministic opening import operation may contain one line per reviewed legacy row if transaction size remains acceptable for the actual dataset.

If batching is required, batches must share an immutable opening-run identity and reconcile as one logical baseline.

### Production timing

Slice C may prove opening import against deterministic/staging copies.

Do **not** assume a development-time opening snapshot is valid for later production cutover.

The production shadow/cutover process must create a fresh opening snapshot from the then-current production database under the approved rollout procedure.

## Legacy/new reconciliation

Provide:

```bash
python3 tools/reconcile_stock_kernel.py --check
```

Comparison levels:

```text
L1 material total
L2 material + warehouse
L3 canonical position identity
```

### Reconciliation source

Before production authority switch:

```text
legacy inventory = current authority
new stock_balances = candidate/shadow projection
```

### Deterministic output

At minimum JSON output with:

```text
run_id
checked_at
legacy_source_identity
ledger_max_operation_id
mapped_legacy_rows
opening_total
projection_total
L1 mismatch count
L2 mismatch count
L3 mismatch count
unresolved divergence count
eligible_for_next_phase
items[]
```

Optional CSV human review output may accompany JSON.

## Divergence classification

Use controlled classes:

```text
MAPPING_AMBIGUITY
LEGACY_ONLY_WRITE
SHADOW_ONLY_WRITE
QUANTITY_MISMATCH
UNKNOWN_DIMENSION
BROKEN_REFERENCE
PROJECTION_TAMPER
```

Do not auto-correct by copying one side over the other.

## Tamper detection

Tests must deliberately alter `stock_balances.quantity_text` without ledger evidence.

Expected:

```text
rebuild/reconciliation detects mismatch
```

The system never rewrites ledger to match the tampered balance.

## Shadow authority boundary

Slice C itself does not migrate a live production route.

It prepares:

- kernel posting with projection;
- opening import;
- reconciliation tooling;
- concurrency safety proof.

Slice D is the first slice that attaches shadow posting to one selected legacy production action.

## Integrity checks

Extend E00 integrity to validate:

```text
balance material exists
balance warehouse exists
position key matches decomposed fields
real location scope belongs to warehouse
quantity_text parses under UOM policy
last_movement_operation_id exists when non-null
no impossible negative physical balance
```

Integrity check should not attempt to infer reservations; they do not exist yet.

## Recovery verifier

Add recovery smoke for:

```text
stock_balances readable
movement -> balance relation inspectable
rebuild-to-temp can execute on fixture
reconciliation returns zero diff on clean fixture
```

Do not make full production-sized rebuild mandatory on every lightweight health request; repository release/recovery drill is the appropriate proof path.

## Deterministic tests

### Balance posting

1. opening +5 produces balance 5;
2. issue 2 produces 3;
3. receipt 4 produces 7;
4. transfer subtract/add happens atomically;
5. failure after source decrement but before destination update rolls all back;
6. resulting negative balance is rejected;
7. UOM mismatch rejected.

### Concurrency

8. two connections competing for insufficient balance cannot both succeed;
9. exactly one successful movement set remains;
10. balance never negative.

### Rebuild

11. rebuild-temp equals live clean projection;
12. tampered balance detected;
13. deleting a movement line in a deliberately corrupted fixture is caught by integrity/reconciliation;
14. reversal evidence rebuilds to same result as live projection.

### Opening import

15. exact legacy total preserved;
16. each migrated line retains source row provenance;
17. duplicate/colliding mapping blocks import;
18. unresolved platform-account/UOM review blocks publication;
19. opening import replay is idempotent;
20. no fabricated historical movement timestamps appear.

### Release

21. existing legacy inventory regressions remain unchanged;
22. full `tools/verify_release.py` passes.

## No production UI/read switch

Forbidden in Slice C:

- using `stock_balances` as ordinary inventory API authority;
- changing shipment/transfer/procurement production write path;
- creating reservations;
- deleting/rewriting legacy `inventory` rows;
- declaring E02 authoritative.

## Rollback

Before shadow production integration:

- old `inventory` remains production authority;
- Migration 7/8 tables remain preserved;
- application may stop using new kernel code without destructive data rollback.

Do not drop movement/balance evidence on code rollback.

## Review checklist

- [ ] Migration 8 is next contiguous migration;
- [ ] balance is explicitly a projection, not immutable truth;
- [ ] movement + projection commit atomically;
- [ ] negative-stock validation occurs inside write transaction;
- [ ] actual concurrent race test exists;
- [ ] rebuild is deterministic and non-destructive by default;
- [ ] opening import preserves provenance and does not invent history;
- [ ] unresolved mapping blocks opening publication;
- [ ] ordinary production reads/writes remain legacy-authoritative;
- [ ] recovery/integrity cover Migration 8;
- [ ] full Release Gate passes.

## Exit gate

Slice C completes when isolated/staging evidence proves:

```text
ledger -> projection is deterministic
negative stock is blocked atomically
concurrent overspend is prevented
opening legacy stock reconciles exactly
projection tamper is detectable/rebuildable
```

while production authority remains on the legacy inventory path.

Then unlock:

```text
E02 Slice D — first same-transaction shadow-posting production pilot
```
