# TASK_INV_IMPL_E02_S02 — Stock Movement Operation/Line Ledger & Reversal

## Status

`DESIGN_READY_BLOCKED_BY_E02_S01`

## Objective

Introduce the immutable stock-movement truth layer used by all later balance, reservation, transfer, receipt and shipment integrations.

## Principle

A stock movement is a business operation with one or more lines. Balance mutation is a projection effect of a posted operation, not the primary evidence.

```text
business command
 -> stock_movement_operation
 -> stock_movement_lines
 -> balance projection update
 -> audit/result receipt
```

## Proposed additive schema

### stock_movement_operations

```text
id INTEGER PK
operation_key TEXT NOT NULL UNIQUE
action_code TEXT NOT NULL
reference_type TEXT
reference_id INTEGER
reversal_of_operation_id INTEGER NULL
business_operation_id INTEGER NULL
correlation_id TEXT
status TEXT NOT NULL
reason TEXT
created_by INTEGER
occurred_at TEXT NOT NULL
created_at TEXT NOT NULL
```

Suggested posted-state vocabulary:

```text
posted
reversed_partially
reversed_fully
```

Do not use a generic editable workflow engine.

### stock_movement_lines

```text
id INTEGER PK
operation_id INTEGER NOT NULL
line_no INTEGER NOT NULL
material_id INTEGER NOT NULL
quantity TEXT/DECIMAL-SEMANTIC NOT NULL
uom_code TEXT NOT NULL
from_position_key TEXT NULL
into_position_key TEXT NULL
movement_type TEXT NOT NULL
line_reference_type TEXT NULL
line_reference_id INTEGER NULL
created_at TEXT NOT NULL
UNIQUE(operation_id, line_no)
```

A line must express direction through source/destination position semantics. Do not infer direction from a signed delta plus free-text reason alone.

## External source/sink semantics

Receipts/issues may involve one side outside controlled stock.

Use explicit source/sink types such as:

```text
EXTERNAL_SUPPLIER
CUSTOMER_SHIPMENT
ADJUSTMENT_SOURCE
ADJUSTMENT_SINK
```

Do not create fake warehouse locations for external parties.

## Operation-key rule

Every consequential movement requires a deterministic business operation key compatible with E01-S04.

Examples:

```text
shipment:<task_id>:complete:<generation>
transfer:<id>:issue:<generation>
transfer:<id>:receipt:<receipt_event_id>
purchase_receipt:<receipt_id>:post
manual_adjustment:<business_operation_id>
```

Same key + same fingerprint returns original result. Same key + different effect is a conflict.

## Atomic transaction

Posting uses one SQLite transaction:

```text
BEGIN IMMEDIATE
 -> E01 business-operation admission
 -> validate reference/state/scope
 -> validate stock dimensions/UOM
 -> insert movement operation
 -> insert movement lines
 -> update balance projection
 -> append audit evidence
 -> mark operation/business receipt succeeded
COMMIT
```

No external network call inside this transaction.

## Negative stock

Default rule: posting that would make an eligible physical position negative is rejected unless a narrowly defined adjustment/migration policy explicitly permits otherwise.

Do not preserve the current “Python reads quantity then later updates it” pattern as the concurrency contract.

## Reversal

History is never deleted or edited to pretend the original event never happened.

Reversal command creates a new operation with:

```text
reversal_of_operation_id = original.id
```

and opposite lines for the quantity still eligible to reverse.

### Reversal invariants

- cannot reverse more than the remaining unreversed effect;
- replay of the same reversal key returns original receipt;
- second independent reversal cannot exceed remaining quantity;
- original operation remains queryable unchanged;
- reversal reason/actor/time are mandatory for manual reversal.

## Migration opening balance

Legacy balances enter the new truth model through an explicit migration operation category, e.g.:

```text
migration.opening_balance
```

Each line references the exact legacy source row/provenance.

This is not presented as a historical physical movement. It is an opening state transfer into the new ledger.

## Movement types

Keep vocabulary controlled and domain-meaningful, e.g.:

```text
opening_balance
manual_adjustment
purchase_receipt
shipment_issue
transfer_issue
transfer_receipt
reservation_consumption_link (if represented separately, not quantity movement)
count_adjustment
reversal
```

Later E06/E07 can extend with production issue/output/scrap/quality disposition.

## Compatibility with inventory_logs

During coexistence, existing `inventory_logs` may remain for current UI/report compatibility.

Do not make two independent business truths.

Preferred transition:

```text
new stock operation posts once
 -> compatibility writer/projection emits legacy inventory/inventory_logs representation in same transaction
```

or during earlier shadow mode:

```text
legacy action posts
 + deterministic shadow stock operation
same transaction
```

The chosen direction must be explicit per migration phase.

## Tests

- one operation with multiple lines posts atomically;
- duplicate operation key does not post twice;
- same key/different fingerprint conflicts;
- failure on line N rolls back all lines/projection changes;
- concurrent deductions cannot both spend the same remaining balance;
- source/destination quantities reconcile;
- negative stock attempt is rejected;
- reversal creates compensating evidence without editing original;
- partial reversal updates remaining reversible quantity correctly;
- over-reversal is rejected;
- migration opening balance is clearly tagged and source-linked;
- full Release Gate passes.

## Rollback

Before authoritative cutover, stop shadow posting/use while retaining tables/evidence.

After the ledger is authoritative, rollback cannot mean “return to direct legacy balance writes”. It requires a compatible code version that continues to honor posted ledger truth.

## Acceptance

S02 is complete when deterministic fixtures prove stock effects are idempotent, atomic and reversible through immutable operations/lines, with no direct dependence on external services.

## Dependencies

E02-S01, E01-S04 idempotency/correlation/action policy.

## Non-goals

- no reservations/ATP yet;
- no advanced location workflow;
- no lot/serial genealogy;
- no production movements.