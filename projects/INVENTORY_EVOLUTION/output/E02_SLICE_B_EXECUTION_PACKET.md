# E02 Slice B Execution Packet — Immutable Stock Movement Ledger

## Status

`READY_TO_IMPLEMENT_AFTER_E02_SLICE_A`

This packet turns `TASK_INV_IMPL_E02_S02.md` into a code-level implementation handoff.

## Entry gate

Do not implement until:

```text
E02 Slice A merged
AND legacy stock identity mapping has no unexplained BLOCKED condition for fixture data
AND current main passes tools/verify_release.py
```

Recommended branch:

```text
impl/e02-movement-ledger
```

## Migration ownership

### Migration 7

Create only the immutable movement evidence layer:

```text
stock_movement_operations
stock_movement_lines
```

Do **not** create authoritative balance/reservation tables in this migration.

Canonical migration chain at entry:

```text
1 E00 baseline
2 E01 business_operations
3 E01 jobs/job_attempts
4 E01 outbox_events
5 E01 operation_logs.correlation_id
6 E11 pricing.floor_override permission
7 E02 stock movement ledger
```

## Critical boundary correction

Slice B does **not** yet own authoritative `stock_balances`.

Therefore Slice B may prove:

- idempotent immutable movement evidence;
- multi-line atomicity;
- deterministic stock effect representation;
- reversal bounds against original/reversal evidence;

but it must **not** claim production negative-stock/oversell prevention yet.

Authoritative balance concurrency/negative-stock protection belongs to Slice C when `stock_balances` projection is introduced.

## Target files

Recommended:

```text
inventory_app/domains/stock/
  movement.py
  movement_queries.py

inventory_app/schema_migrations.py
inventory_app/db_integrity.py
inventory_app/recovery_verifier.py

tools/test_stock_movement_ledger.py
```

Reuse Slice A:

```text
identity.py
quantity.py
```

No production `server.py` route is migrated in Slice B.

## Migration 7 schema

### stock_movement_operations

Recommended columns:

```text
id INTEGER PRIMARY KEY AUTOINCREMENT
operation_key TEXT NOT NULL UNIQUE
effect_fingerprint TEXT NOT NULL
action_code TEXT NOT NULL
reference_type TEXT
reference_id INTEGER
reversal_of_operation_id INTEGER
business_operation_id INTEGER
correlation_id TEXT
reason TEXT
created_by INTEGER
occurred_at TEXT NOT NULL
created_at TEXT NOT NULL
```

Indexes:

```text
(reference_type, reference_id, id)
(reversal_of_operation_id, id)
(business_operation_id)
(correlation_id)
(action_code, occurred_at, id)
```

### Immutable-state rule

A posted operation row is evidence and should not be rewritten to mimic reversal.

Prefer:

```text
original operation remains immutable
reversal = a new stock_movement_operation
reversal effective state = derived from linked reversal operations
```

Expose derived query state such as:

```text
POSTED
PARTIALLY_REVERSED
FULLY_REVERSED
```

without mutating original movement lines.

### stock_movement_lines

Recommended columns:

```text
id INTEGER PRIMARY KEY AUTOINCREMENT
operation_id INTEGER NOT NULL
line_no INTEGER NOT NULL
material_id INTEGER NOT NULL
quantity_text TEXT NOT NULL
uom_code TEXT NOT NULL
from_endpoint_type TEXT NOT NULL
from_position_key TEXT
to_endpoint_type TEXT NOT NULL
to_position_key TEXT
movement_type TEXT NOT NULL
line_reference_type TEXT
line_reference_id INTEGER
created_at TEXT NOT NULL
UNIQUE(operation_id, line_no)
```

Use declared FK to operation/material when compatible with the then-current schema; E00 logical integrity checks remain mandatory regardless.

## Quantity direction contract

`quantity_text` is a canonical **positive magnitude**.

Do not encode direction using negative numbers.

Direction comes from explicit endpoints:

```text
FROM -> TO
```

Examples:

```text
purchase receipt:
  EXTERNAL_SUPPLIER -> POSITION

shipment:
  POSITION -> CUSTOMER_SHIPMENT

transfer:
  POSITION -> POSITION

manual increase:
  ADJUSTMENT_SOURCE -> POSITION

manual decrease:
  POSITION -> ADJUSTMENT_SINK

opening balance later:
  MIGRATION_OPENING -> POSITION
```

This avoids ambiguous signed deltas with free-text reasons.

## Endpoint vocabulary

Initial controlled endpoint types:

```text
POSITION
EXTERNAL_SUPPLIER
CUSTOMER_SHIPMENT
ADJUSTMENT_SOURCE
ADJUSTMENT_SINK
MIGRATION_OPENING
```

Rules:

- `POSITION` requires a valid Slice-A canonical position key;
- external endpoints must not pretend to be warehouses/locations;
- both endpoints cannot represent the exact same physical position for a non-zero movement unless a future explicit semantic requires it;
- every line must have one source and one destination endpoint type.

## Operation effect fingerprint

The stock domain must self-protect even when called from a future non-HTTP/internal path.

Compute SHA-256 over canonical normalized stock effect:

```text
action_code
reference identity
ordered normalized lines:
  material_id
  quantity_text
  uom_code
  from endpoint
  to endpoint
  movement_type
  line reference
reversal_of_operation_id
```

Same `operation_key` + same effect fingerprint:

```text
return original operation receipt
```

Same `operation_key` + different fingerprint:

```text
conflict
```

This complements, not replaces, E01 `business_operations`.

## Posting transaction

Initial isolated ledger posting:

```text
BEGIN IMMEDIATE
 -> validate canonical operation key/effect fingerprint
 -> if existing same fingerprint: return existing receipt
 -> if existing different fingerprint: conflict
 -> validate all lines before publishing
 -> insert operation
 -> insert all movement lines
 -> append audit evidence where caller supplies business context
COMMIT
```

Any failure on line N rolls back operation and all prior lines.

No external network call is allowed.

## Relationship to E01 business_operations

For later real business commands:

```text
E01 business operation
 -> one or more stock movement operations
```

`business_operation_id` should be populated when available.

Do not make stock movement operation the new authorization/idempotency framework for the whole application.

## Reversal command

Recommended API:

```python
reverse_movement(
    conn,
    *,
    original_operation_id,
    operation_key,
    line_quantities=None,
    reason,
    actor_id,
    business_operation_id=None,
    correlation_id=None,
)
```

### Reversal rules

1. reversal is a new operation;
2. `reversal_of_operation_id` points to original;
3. reversal endpoints are inverse of original effect;
4. original rows never change;
5. full or partial reversal allowed only up to unreversed quantity;
6. over-reversal rejected;
7. same reversal key replays safely;
8. manual reversal requires non-empty reason;
9. reversing a reversal is not implicitly allowed; if future policy needs it, use a separate explicit command.

## Partial reversal accounting

For each original line derive:

```text
original quantity
- sum(valid linked reversal quantities)
= remaining reversible quantity
```

No mutable `reversed_quantity` cache is required in Slice B.

If later performance requires a projection/cache, it must reconcile back to immutable movement evidence.

## Movement query/read model

Expose domain queries, not raw table assumptions:

```text
get_operation(id/key)
list_reference_movements(reference_type, reference_id)
get_reversal_state(operation_id)
get_remaining_reversible_quantities(operation_id)
```

These become the compatibility surface for later E02 slices.

## Integrity checks

Extend E00 logical integrity with at least:

```text
movement line -> operation exists
movement line -> material exists
reversal -> original operation exists
reversal cannot self-reference
business_operation_id -> business_operations exists when non-null
```

Where position keys are used, validate parseability/identity contract at application posting time. Do not silently accept malformed position keys.

## Recovery verifier

Recovery smoke should verify:

- movement tables readable;
- operation/line joins execute;
- migration 7 registry row present after adoption;
- integrity checker detects an injected orphan line/reversal in tests.

Do not claim balance recovery yet; Slice C owns projection.

## No production authority in Slice B

Forbidden:

- changing `InventoryService.adjust_inventory()`;
- changing shipment/transfer/procurement stock writes;
- using ledger totals as UI inventory balance;
- creating production opening balances from live legacy data;
- creating reservations;
- deleting legacy `inventory_logs`;
- calling Slice B authoritative stock truth for production.

## Tests

Create:

```text
tools/test_stock_movement_ledger.py
```

Must prove:

1. one operation/one line posts;
2. multi-line operation posts atomically;
3. failure on line N rolls back operation + all lines;
4. same key/same fingerprint returns original operation;
5. same key/different fingerprint conflicts;
6. line numbers unique per operation;
7. quantity canonical Decimal string round-trips;
8. zero/negative magnitude is rejected;
9. POSITION endpoint requires valid canonical position key;
10. external endpoints do not require fake warehouse position;
11. transfer POSITION->POSITION stores both exact identities;
12. full reversal produces inverse evidence and leaves original unchanged;
13. partial reversal reduces remaining reversible quantity;
14. over-reversal is rejected;
15. duplicate reversal key does not post twice;
16. orphan line/reversal is detected by integrity tests;
17. full `tools/verify_release.py` passes.

## Explicitly deferred test

Do **not** mark this slice failed merely because it does not yet prove concurrent negative-stock prevention.

That test is mandatory in Slice C after an authoritative balance projection exists:

```text
two concurrent spend attempts
 -> at most one may consume remaining balance
```

The implementation sequence must reflect this dependency.

## Rollback

Before any production route uses ledger authority:

```text
rollback application code
 -> leave Migration 7 evidence tables in place
 -> old production inventory path remains unchanged
```

Do not drop ledger tables merely because a code rollback occurs.

## Review checklist

- [ ] Migration number is exactly next contiguous version 7;
- [ ] operation and line evidence are immutable;
- [ ] quantities are positive canonical magnitudes;
- [ ] direction comes from explicit endpoints;
- [ ] operation key + effect fingerprint protect replay;
- [ ] partial/full reversal is bounded;
- [ ] no production stock route changed;
- [ ] no false oversell-prevention claim before Slice C;
- [ ] integrity/recovery checks include Migration 7 tables;
- [ ] full Release Gate passes.

## Exit gate

Slice B completes when the repository has a deterministic, immutable, idempotent and reversible movement evidence layer that is still isolated from production stock authority.

Then unlock:

```text
E02 Slice C — stock_balances projection + opening-balance reconciliation
```
