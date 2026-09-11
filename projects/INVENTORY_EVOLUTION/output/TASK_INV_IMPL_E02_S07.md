# TASK_INV_IMPL_E02_S07 — Authoritative Cutover, Parity Window & Legacy-write Retirement

## Status

`DESIGN_READY_BLOCKED_BY_E02_S01_TO_S06`

## Objective

Make the new stock kernel authoritative only after measured parity is proven, migrate remaining open commitments, and permanently fence direct legacy balance writes from production use.

## Cutover is a controlled release event

E02 is not complete merely because new tables exist or pilot routes work.

Authority changes only after explicit evidence:

```text
opening balance reconciled
+ shadow ledger/projection parity proven
+ open demand reservations reconciled
+ migrated stock-changing routes proven
+ unresolved divergence = 0 or explicitly approved/blocking exceptions resolved
+ rollback compatibility reviewed
+ full Release Gate PASS
```

## Required pre-cutover report

Produce a retained machine-readable report with at least:

```text
source release SHA
source DB schema version
new target release SHA
legacy inventory row count
legacy total quantity by material/warehouse
opening-balance operation count/quantity
shadow operation count
reconciliation run count
last successful reconciliation timestamp
unresolved divergence count/details
active migrated reservation count
open-demand shortage/review count
legacy direct-write call sites detected
new stock-kernel route coverage
eligible_for_cutover true/false
```

If `eligible_for_cutover=false`, the release script/operator runbook must not switch authority.

## Parity window

Define an operator-approved parity window before cutover.

The software records evidence; it does not invent the threshold.

Possible criteria:

```text
minimum business days
minimum stock-changing operations
zero unexplained divergence
all high-risk flows exercised at least once
```

Any unexplained divergence resets or blocks the parity decision.

## Open business-state migration

Immediately before authority switch, reconcile current live/open state:

```text
open confirmed orders
open shipment tasks
active transfers / in-transit quantity
approved/part-received purchase orders where relevant
nonzero legacy locks/on-transfer counters
pending count corrections
```

Create only evidence that can be justified from current authoritative business objects.

Ambiguous quantities become an exception/review list. Do not fabricate reservation, transfer or movement history to make numbers fit.

## Cutover sequence

Recommended maintenance transaction:

```text
E00-style production prechange backup + restore verification
 -> stop business writers
 -> final legacy/new reconciliation
 -> final open-state migration
 -> final reconciliation = PASS
 -> enable new stock-kernel write authority
 -> enable new ATP/reservation read authority
 -> fence direct legacy mutation path
 -> run post-cutover smoke/integrity
 -> start writers
 -> health + stock sanity check
```

If final reconciliation fails while writers are stopped, remain fail-closed and restore/fix explicitly.

## Legacy write fencing

After cutover, direct legacy writes must be technically prevented, not merely discouraged in documentation.

At minimum:

- `InventoryService.adjust_inventory` becomes a compatibility façade that delegates to stock-domain command, or is removed from production callers;
- direct `UPDATE inventory SET quantity_available=...` outside approved projection/recovery code fails static regression checks;
- legacy fields become read-only compatibility projection where still needed;
- test/tooling paths that intentionally mutate fixtures are clearly scoped to temporary test DBs.

Recommended repository-local static test:

```text
scan production Python for forbidden direct balance UPDATE patterns
allow only explicitly whitelisted stock projection/migration modules
```

## Legacy inventory_logs transition

If `inventory_logs` remains for existing UI/report compatibility:

- populate it from the new authoritative operation transaction/projection;
- mark/document it as compatibility evidence rather than the primary ledger;
- no caller may write only `inventory_logs` and assume stock changed.

Long-term retirement can occur after dependent reports/UI are migrated.

## Read authority

After cutover:

```text
stock balance UI/query -> stock_balances projection
ATP views -> stock balance + reservation policy
movement history -> stock_movement_operations/lines
```

Legacy `inventory.quantity_available` may remain mirrored for a bounded compatibility period but cannot be the deciding source for new business actions.

## Post-cutover monitoring

For a defined stabilization period, run frequent local/server reconciliation:

```text
ledger -> projection
new projection -> compatibility legacy projection
reservation totals -> ATP checks
open shipment/transfer/purchase references -> stock operation existence
```

Use systemd/cron/local worker if scheduled. Do not depend on GitHub Actions.

Any divergence becomes an operational exception with correlation/reference evidence.

## Recovery / rollback

### Before authority switch

Normal code rollback can return to legacy writes because legacy remains authoritative.

### After authority switch

Do not deploy a pre-E02 version that ignores new movement/reservation truth.

Safe rollback choices are:

1. roll back to a specifically prepared compatibility version that still reads/writes new stock kernel; or
2. restore the complete pre-cutover code + DB backup as one recovery event, accepting loss of post-cutover transactions according to approved RPO; or
3. forward-fix the new release.

Never copy only the old `inventory` table back over a live post-cutover database.

## Decommission criteria

Only after stabilization may old direct paths be removed.

Required evidence:

- zero production callers of direct legacy adjustment;
- zero unexplained parity mismatch over stabilization window;
- all supported stock flows represented by movement operations;
- all order promises use first-class reservation/ATP;
- operational runbooks updated;
- backup/restore drill includes new stock tables;
- full Release Gate includes E02 contract tests.

## Tests

- cutover eligibility false when any divergence exists;
- cutover eligibility false when open-demand migration has unresolved shortage/ambiguity;
- final reconciliation can run while writers are quiesced;
- direct legacy mutation static check catches forbidden write;
- compatibility façade delegates to new stock kernel exactly once;
- post-cutover business flow reads new ATP, not legacy raw available quantity;
- pre-E02 incompatible code is rejected by schema/version/startup compatibility check where feasible;
- backup/restore verification covers new ledger/balance/reservation tables;
- complete pre-cutover restore drill is documented/tested on staging copy;
- full Release Gate passes.

## Acceptance

E02 is complete only when:

```text
new movement ledger is authoritative
AND balance projection reconciles
AND active demand uses reservations/ATP
AND all supported stock-changing flows use one kernel
AND direct legacy stock mutation is fenced
AND rollback/recovery procedure is explicit
```

## Dependencies

E02-S01 through S06, E00 recovery foundation.

## Non-goals

- no deletion of historical legacy evidence solely for cleanup;
- no PostgreSQL migration;
- no advanced WMS/lot/serial/manufacturing expansion in the cutover itself.