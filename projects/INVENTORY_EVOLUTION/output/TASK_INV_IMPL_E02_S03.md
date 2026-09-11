# TASK_INV_IMPL_E02_S03 — Balance Projection, Shadow Posting & Reconciliation

## Status

`DESIGN_READY_BLOCKED_BY_E02_S02`

## Objective

Build a fast current-balance projection from the new movement ledger and prove it matches legacy stock before any authoritative read/write cutover.

## Principle

```text
movement ledger = immutable truth
balance projection = fast derived state
reconciliation = proof that projection and source evidence agree
```

A projection may be repaired/rebuilt from authoritative movement evidence; the ledger may not be silently rewritten to match a projection.

## Proposed stock balance projection

Conceptual fields:

```text
position_key PRIMARY/UNIQUE
material_id
warehouse_id
normalized location scope
normalized owner/account scope
stock_status
quantity_on_hand
uom_code
last_movement_operation_id
updated_at
```

Do not retain anonymous `quantity_locked` as reservation truth; S04 introduces first-class reservations.

## Projection update rule

Synchronous stock operations update ledger + projection in one SQLite transaction.

For every affected position:

```text
old projection
+ net movement effect
= new projection
```

`last_movement_operation_id` or equivalent provenance should make the projection's freshness inspectable.

## Rebuild command

Provide a repository-local deterministic command/service that can rebuild or recompute projection into an isolated/temp table from ledger lines.

Example operational shape:

```bash
python3 tools/reconcile_stock_kernel.py --check
python3 tools/reconcile_stock_kernel.py --rebuild-temp
```

A rebuild should not overwrite live projection by default. Publishing a repaired projection must be an explicit controlled action after diff review.

## Shadow migration phase

Before the new projection drives production decisions:

```text
legacy inventory remains authoritative
+ every selected legacy stock action emits a shadow movement in same transaction
+ new projection updates from shadow movement
+ reconciliation continuously compares totals/dimensions
```

Never use an asynchronous best-effort shadow writer because crashes could create false parity gaps unrelated to business semantics.

## Comparison levels

Reconciliation must support at least:

### L1 — global material totals

```text
SUM legacy quantity by material
vs
SUM new projection quantity by material
```

### L2 — warehouse totals

```text
material + warehouse
```

### L3 — normalized stock identity

```text
material + warehouse + location scope + owner scope + status
```

Where legacy lacks a trustworthy dimension, compare against the explicitly mapped `legacy_unassigned` scope rather than inventing detail.

## Opening-balance migration

Before shadow actions begin, create an opening-balance import from current legacy `inventory` rows.

Requirements:

- exact source row ID recorded;
- exact source quantity captured;
- mapping to normalized position identity recorded;
- source database/release/schema identity recorded;
- total input equals total opening balance by deterministic report;
- ambiguous/colliding mappings halt publication.

Opening balance is one migration baseline, not fabricated historical movement.

## Divergence record

Do not only print mismatches to console.

Persist/report a structured reconciliation record with:

```text
run_id
scope/key
legacy_quantity
projected_quantity
delta
last legacy reference if known
last new operation id
classification
created_at
```

This can initially be a generated JSON/CSV artifact rather than a permanent table if that reduces schema churn, but operators must be able to inspect and retain the evidence.

## Divergence classes

At minimum distinguish:

```text
MAPPING_AMBIGUITY
LEGACY_ONLY_WRITE
SHADOW_ONLY_WRITE
QUANTITY_MISMATCH
UNKNOWN_DIMENSION
BROKEN_REFERENCE
EXPECTED_AFTER_CUTOVER (only in controlled transition)
```

Never auto-fix a mismatch by simply copying whichever side has the larger/latest number.

## Parity window

Define an explicit parity criterion before changing authority, e.g.:

```text
N business days or X stock-changing operations
with zero unexplained divergence
```

The exact duration/count is an operator decision. The software should record evidence, not guess the business threshold.

## Cutover readiness output

A machine-readable pre-cutover report should state:

```text
legacy rows mapped
opening total
shadow operations observed
reconciliation runs
unresolved divergence count
last successful reconciliation time
eligible_for_cutover true/false
```

`eligible_for_cutover=false` blocks S07 authority switch.

## Compatibility queries

During shadow mode, UI continues reading legacy stock unless a dedicated comparison/admin view is explicitly enabled.

After an approved read cutover, legacy and new values may be shown side-by-side to privileged operators for a bounded observation period.

Do not expose two conflicting numbers to ordinary operators without labeling authority.

## Tests

- opening import preserves exact total quantity;
- duplicate/colliding legacy mapping is rejected;
- shadow write and legacy write occur in one transaction;
- forced failure rolls both sides back;
- projection equals recomputed ledger result;
- deliberate tamper in projection is detected;
- deliberate legacy-only write is detected;
- cross-warehouse/location mapping error is detected;
- rebuild-temp reproduces expected projection;
- reconciliation output is deterministic;
- unresolved mismatch blocks cutover eligibility;
- full Release Gate passes.

## Rollback

Shadow mode can be stopped by disabling shadow ownership while leaving evidence tables intact.

Do not delete reconciliation artifacts when rolling back; they are migration evidence.

## Acceptance

S03 is complete when opening balances reconcile exactly, shadow posting survives deterministic failure tests, and the system can prove—not assume—that new projection matches legacy authoritative stock through the defined observation window.

## Dependencies

E02-S01 and E02-S02.

## Non-goals

- no reservations yet;
- no order promise logic;
- no bin workflow;
- no lot/serial;
- no automated divergence correction.