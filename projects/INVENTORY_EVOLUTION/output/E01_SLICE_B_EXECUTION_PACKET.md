# E01 Slice B Execution Packet — Business Operation Idempotency

## Status

`READY_TO_START_ONLY_AFTER_E01_SLICE_A_MERGE`

This is the second actual E01 implementation handoff. It introduces **Migration 2** and the reusable idempotency primitive, but it does **not** yet migrate production stock-affecting routes.

## 1. Entry gate

All must be true:

```text
E00 real-checkout Release Gate = PASS
Inventory PR #3 merged
E01 Slice A merged to main
new branch created from current main
```

Suggested branch:

```text
impl/e01-idempotency
```

## 2. Purpose

Provide a durable business-operation identity so later consequential commands can safely handle:

```text
double click
client retry
proxy retry
response loss
concurrent same-key requests
```

without Redis, distributed transactions or a second database.

## 3. Existing transaction seam

Current application behavior already supports the desired design:

```text
get_conn()
 -> one sqlite3 connection
 -> caller-owned request transaction
 -> services accept the same conn
 -> operation_logs are written with the same conn
```

Therefore Slice B must keep local business idempotency in SQLite and preserve a single commit boundary.

## 4. Proposed files

Add:

```text
inventory_app/platform/idempotency.py
tools/test_business_operations.py
```

Modify:

```text
inventory_app/schema_migrations.py
inventory_app/db_integrity.py            # only additive integrity checks for the new table if useful
tools/verify_release.py                  # include required new deterministic tests
```

Optional bounded compatibility edit:

```text
inventory_app/platform/action_policy.py  # connect metadata to idempotency mode, but no real write route yet
```

Do **not** edit stock/reservation tables or production transfer/purchase/shipment service semantics in this slice.

## 5. Migration 2

Migration sequence must remain contiguous:

```text
1  baseline_current_schema_20260810       [E00]
2  business_operations                    [this slice]
```

Suggested table contract:

```sql
CREATE TABLE business_operations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  operation_key TEXT NOT NULL,
  action_code TEXT NOT NULL,
  actor_id INTEGER,
  target_type TEXT,
  target_id INTEGER,
  request_fingerprint TEXT NOT NULL,
  correlation_id TEXT,
  status TEXT NOT NULL,
  result_type TEXT,
  result_id INTEGER,
  result_json TEXT,
  error_code TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  UNIQUE(action_code, operation_key),
  CHECK(status IN ('running','succeeded','failed','manual_review'))
);
```

Indexes:

```text
(status, started_at)
(actor_id, started_at DESC)
(target_type, target_id, started_at DESC)
(correlation_id)
```

Migration must use the E00 immutable checksum/version mechanism. Do not extend legacy `database.migrate(conn)` with this table as the authoritative new migration path.

## 6. Module contract

Suggested public surface:

```text
canonical_request_fingerprint(action_code, target_identity, effect_payload)
validate_operation_key(value)
lookup_operation(conn, action_code, operation_key)
admit_atomic_local_operation(...)
mark_operation_succeeded(...)
read_operation_receipt(...)
```

Do not expose raw SQL handling to HTTP routes.

The module must not open its own business connection when used inside a consequential request. It receives the caller-owned `conn`.

## 7. Atomic-local transaction rule

The later production caller will use:

```text
BEGIN IMMEDIATE
 -> find/insert business_operation
 -> execute domain mutation on SAME conn
 -> write authoritative audit/event on SAME conn
 -> write bounded deterministic result receipt
 -> mark operation succeeded
COMMIT
```

Critical invariant:

```text
operation success
business mutation
authoritative audit/result receipt
```

must all commit together or all disappear together.

Never support this pattern:

```text
transaction 1 = idempotency admission
transaction 2 = inventory mutation
transaction 3 = success receipt
```

## 8. Request fingerprint

Use SHA-256 over canonical effect-bearing JSON only.

Include:

```text
action_code
authoritative target identity
normalized quantities/item lines
business options changing the side effect
```

Exclude:

```text
correlation ID
request timestamp
retry count
UI-only labels
presentation-only metadata
```

Rules:

- stable key ordering;
- deterministic number representation;
- only sort arrays where ordering is semantically irrelevant;
- no normalization may erase a field that changes stock/state/price.

## 9. Operation-key safety

Require a bounded opaque string.

Reject:

- empty value;
- excessive length;
- control characters;
- attempts to treat the key as user/warehouse authority.

The key is command identity only.

Preferred sources later:

1. stable provider/business event ID;
2. explicit client idempotency key;
3. server-generated key retained by controlled UI flow.

## 10. Slice-B execution target

Do not start with transfer/purchase/shipment production routes.

Create a deterministic synthetic/isolated command fixture that proves the primitive with a simple test-owned side-effect table or bounded fixture callback.

This separates:

```text
Does the idempotency primitive work?
```

from:

```text
Did we migrate a complex stock workflow correctly?
```

Production pilots belong to Slice C.

## 11. Required concurrency tests

### Same key / same fingerprint

Two SQLite connections/threads contend for one operation.

Require:

- mutation callback executes once;
- final receipt exists once;
- second request cannot create a second operation;
- after first commit, replay returns the same receipt.

### Same key / different fingerprint

Require:

- deterministic `idempotency_conflict`;
- original row/receipt unchanged;
- no second mutation.

### Failure before commit

Inject exception after test mutation DML but before success marking.

Require:

- explicit rollback;
- mutation disappears;
- operation row disappears for pure atomic-local path;
- retry can execute once normally.

### Lost response after commit

Commit successful operation, suppress first response, replay same request.

Require:

- no second callback;
- stored result returned;
- result/audit counts unchanged.

### Pre-existing transaction guard

The atomic-local executor should either own `BEGIN IMMEDIATE` from a clean connection state or reject an unsafe nested write transaction deterministically.

Do not silently emulate nested transactions.

## 12. Result receipt

Store small deterministic evidence only, e.g.:

```json
{
  "target_type": "fixture",
  "target_id": 42,
  "status": "completed",
  "result_id": 99
}
```

Rules:

- bounded JSON size;
- no API keys/tokens/secrets;
- no raw image/document blobs;
- no huge response cache;
- prefer stable IDs + status + quantity/result summary.

## 13. Status semantics

For the first `atomic_local` implementation:

```text
running     transaction currently owns execution
succeeded   committed effect + receipt
failed      reserved for explicit durable semantics; do not persist casually after rolled-back local transaction
manual_review reserved for later ambiguous/external workflows
```

A pure local crash before commit normally removes the uncommitted `running` row.

Do not implement lease/retry semantics here; that is Slice D (`jobs`).

## 14. Interaction with Action Policy

Slice A policy metadata may declare:

```text
idempotency = none | optional | required
```

Slice B can provide the executor primitive but still must not route the three production pilots yet.

An action marked `required` must not be callable through the consequential wrapper unless an operation key/fingerprint path exists.

## 15. Integrity / recovery additions

E00 backup/recovery must automatically carry the new table because it is in the same SQLite DB.

Add only bounded checks such as:

- table/required columns present after Migration 2;
- duplicate `(action_code, operation_key)` impossible;
- status value constrained;
- malformed migration rollback tested through existing migration framework.

Do not create a parallel backup mechanism.

## 16. Required Release Gate additions

`tools/verify_release.py` must fail closed if the new test file is absent and run:

```bash
python3 tools/test_business_operations.py
```

Full gate remains mandatory:

```bash
python3 tools/verify_release.py
```

Linux profile:

```bash
python3 tools/verify_release.py --require-bash
```

## 17. PR review checklist

```text
[ ] based on post-Slice-A main
[ ] Migration 2 is contiguous/immutable/checksummed
[ ] no edit to legacy migration path as authoritative source
[ ] no production stock route migrated
[ ] module uses caller-owned SQLite connection
[ ] one atomic commit boundary proven
[ ] same-key/same-request executes once
[ ] same-key/different-request conflicts
[ ] rollback leaves no false success
[ ] lost response replay returns stored receipt
[ ] result JSON bounded / secret-free
[ ] no Redis/external coordinator
[ ] full Release Gate PASS
```

Any `no` blocks merge.

## 18. Rollback

Application rollback:

- stop using the module;
- keep `business_operations` table as inert evidence;
- do not drop operation history in production rollback.

Because no real business route is migrated in Slice B, rollback should not require stock correction.

## 19. Exit / unlock

Slice B completes only when the primitive is proven under deterministic concurrency/replay/failure tests and full Release Gate.

Then unlock:

```text
E01 Slice C — consequential pilot migration
  1. transfer.receive
  2. purchase.receive
  3. shipment.complete
```

Each pilot gets its own parity/replay gate; do not migrate all three in one unreviewable commit.
