# E02 Slice J Execution Packet — Authoritative Cutover / Legacy-write Fencing

## Status

`READY_ONLY_AFTER_E02_A_TO_I_PROVEN`

This packet is the **only** E02 slice allowed to declare the new stock kernel globally authoritative.

It is a controlled production release/cutover, not an ordinary feature PR.

## 1. Entry gate

All must be true before a production authority switch is even scheduled:

```text
E02-A canonical identity/UOM PASS
E02-B movement ledger PASS
E02-C balance projection/opening reconciliation PASS
E02-D shadow pilot PASS
E02-E reservation/ATP PASS
E02-F shipment reservation/issue pilot PASS
E02-G transfer issue/in-transit/receipt PASS
E02-H procurement receipt PASS
E02-I manual/count authority PASS
```

Additionally:

```text
all migrated cohorts show zero unexplained divergence
legacy direct-writer inventory complete
backup/recovery verification covers migrations 7/8/9
full current-main Release Gate PASS
operator-approved parity/stabilization criteria met
```

Suggested branch:

```text
impl/e02-stock-cutover
```

Migration:

```text
NONE expected
```

If a final structural constraint/index is genuinely necessary, allocate Migration 10 explicitly before cutover and rerun the entire readiness evidence. Do not modify Migration 7/8/9.

## 2. Cutover changes authority, not history

Before Slice J:

```text
new stock kernel is proven in bounded/selected paths
legacy compatibility remains present
```

After Slice J:

```text
stock_movement_operations/lines = physical stock change truth
stock_balances = current physical balance projection
stock_reservations/events = promise truth
ATP query = promise availability truth
legacy inventory/inventory_logs = compatibility/read evidence only where retained
```

No migration fabricates missing historical movement/lot/bin/reservation evidence.

## 3. Required retained pre-cutover report

Generate and retain a machine-readable signed/hashed artifact containing at least:

```text
report id / generated_at
source production release SHA
source DB path/identity
source schema migration versions/checksums
target release SHA
legacy inventory row count
legacy total quantity by material/warehouse
opening-balance operation totals
stock movement operation/line counts
stock_balances counts/totals
reservation counts/remainings
shadow/parity operation count
reconciliation run count
last clean reconciliation timestamp
unresolved divergence count/details
open order/shipment migration preview
active transfer/in-transit migration preview
legacy quantity_locked review count
pending count/reconciliation items
forbidden legacy writer scan result
backup/recovery verification result
eligible_for_cutover true/false
```

If `eligible_for_cutover=false`, cutover is prohibited.

Do not override the flag manually without resolving or explicitly disposing every blocker through an audited operator decision.

## 4. Parity-window policy

The software records evidence; operator policy decides the required window.

Possible criteria:

```text
minimum business days
minimum stock-changing operations
all high-risk flows exercised
zero unexplained divergence
zero unresolved reservation oversubscription
zero unknown direct writers
```

Record the approved criteria/version in cutover evidence.

Any unexplained divergence before cutover resets/blocks readiness.

## 5. Fresh production safety snapshot — mandatory again

Even if earlier E00/E02 backups exist, immediately before this authority switch perform a **fresh** production protection cycle:

```text
exact currently deployed server-code snapshot
+ consistent production DB backup
+ isolated restore verification
+ manifest/SHA-256
+ off-host Recovery Bundle when configured
```

This is mandatory because the cutover changes authoritative semantics.

Do not use an old pre-E02 development backup as rollback proof.

## 6. Maintenance/quiescence

Final authority switch occurs with business writers stopped.

Recommended order follows E00 fail-closed principles:

```text
stop/suspend scheduled stock-affecting jobs
stop connector/worker jobs that can create local stock effects
stop OCR-derived confirmation writers if applicable
stop Web/API business writers
verify no active writer process
```

Read-only verification tools may continue if they cannot mutate production.

If writer quiescence cannot be proven, do not run final migration/reconciliation.

## 7. Final live-state reconciliation

With writers stopped, rerun from the actual production DB:

### Physical stock

```text
legacy compatibility totals
vs
E02 ledger-derived projection
```

at:

```text
material
material + warehouse
canonical position identity
```

### Shipment/order

Verify migrated/shipment-authoritative tasks:

```text
required demand
reservation remaining/consumed
shipment_issue movements
shipment state
```

### Transfer

Verify:

```text
issued = received + remaining in transit + explicitly resolved variance
```

### Procurement

Verify:

```text
receipt item qty = purchase_receipt movements
received_quantity consistency
```

### Manual/count

Verify:

```text
approved correction evidence = explicit movement operations
```

Any unexplained mismatch blocks authority switch.

## 8. Open-demand reservation migration

Now migrate remaining authoritative open demand that predates the reservation pilot cohort.

Process:

```text
identify eligible confirmed/open order/shipment requirements
 -> derive requirement only from authoritative business objects
 -> resolve authoritative warehouse when known
 -> calculate current ATP
 -> create migration reservation with honest created_at/source marker
 -> classify shortage/ambiguity
```

Do not invent a historical reservation timestamp.

Do not reserve an arbitrary warehouse for open-pool/unassigned tasks.

Unassigned demand remains a queue/review object until warehouse commitment.

Shortage/ambiguity must be explicit and resolved according to business policy before global promise authority is enabled for affected scope.

## 9. Legacy `quantity_locked` / anonymous promise cleanup

Run the Migration-9 legacy lock audit.

For every nonzero legacy lock:

```text
traceable to authoritative open demand -> map/reconcile explicitly
ambiguous -> operator review/disposition
invalid/stale -> controlled cleanup with evidence
```

Never translate anonymous lock quantity directly into a reservation without business reference.

Cutover report must show unresolved anonymous lock count = 0 for authority scope.

## 10. Active transfer migration

For each currently active transfer, create/verify current authoritative E02 state based on proven legacy business evidence:

```text
not shipped -> no in-transit stock
shipped/in-transit -> source issue + remaining in-transit
partial receipt -> issue + received + remaining in-transit
completed -> issue + full receipt, transit zero
```

If source issue evidence is missing/mismatched:

```text
block and reconcile
```

Do not let normal receipt logic fabricate historical issue.

Any migration operation must be clearly labeled `migration.*` / opening/current-state reconciliation and reference legacy evidence.

## 11. Pending counts / adjustments

Before cutover, inspect:

- submitted but unreviewed count sessions;
- pending manual outbound/adjustment approvals;
- any workflow that will post stock after restart.

Ensure their eventual execution calls the new stock kernel.

Do not let a queued legacy action wake after restart and directly edit compatibility inventory.

## 12. Authority marker

After final reconciliation/open-state migration succeeds, persist a DB-level application setting such as:

```text
stock_kernel_authority = e02_v1
stock_kernel_cutover_at = <timestamp>
stock_kernel_cutover_release = <target SHA>
```

Use existing `system_settings` if appropriate; no schema migration is required for key/value settings.

New application startup must:

- read the authority marker;
- refuse to run a configuration/path that would treat legacy direct balance writes as authoritative;
- expose the authority mode in health/admin diagnostics.

The marker is evidence/guardrail, not a substitute for static write fencing.

## 13. Technical legacy-write fencing

After authority marker is set, production code must prevent direct legacy balance mutations.

At minimum:

### `InventoryService.adjust_inventory`

Either:

1. becomes a compatibility façade delegating to E02 movement command; or
2. is removed from production callers and fails if called outside explicitly whitelisted migration/test compatibility context.

### Direct SQL

Repository-local static test scans production Python for patterns such as:

```text
UPDATE inventory SET quantity_available
INSERT/UPDATE inventory quantity paths
```

Whitelist only:

```text
stock compatibility projection
migration/recovery tooling explicitly scoped to non-live repair
fixture/test database code
```

Unknown direct writer = release failure.

### Legacy counters

`quantity_locked` / `quantity_on_transfer` cannot remain independent mutation truth.

If retained for compatibility UI, derive/update them from Reservation/Movement state only.

## 14. Read-authority switch

After marker/cutover:

```text
normal stock balance query -> stock_balances
normal movement history -> stock_movement_operations/lines
normal customer promise / ATP -> stock_balances + active reservations + approved buffer policy
```

Legacy `inventory.quantity_available` may remain mirrored for bounded backward compatibility but must never decide:

- whether a shipment can issue;
- whether an order can reserve;
- whether a transfer can issue;
- whether a purchase receipt already posted;
- authoritative management stock quantity.

## 15. Compatibility write direction

Post-cutover direction is one-way:

```text
E02 authoritative transaction
 -> optional legacy compatibility projection/log
```

Forbidden:

```text
legacy mutation
 -> try to infer/repair E02 later
```

This distinction must be tested.

## 16. Deployment sequence

Recommended production cutover runbook:

```text
1. target release already passed repository Release Gate on real checkout
2. run fresh server-code + DB + restore + manifest backup proof
3. quiesce writers / verify stopped
4. final pre-cutover report -> eligible=true
5. run open-demand/transfer/lock reconciliation migration
6. rerun reconciliation -> PASS
7. set stock_kernel_authority=e02_v1 marker
8. run forbidden direct-writer/static/startup guard checks
9. run DB integrity/postflight
10. start Web/API in new authority mode
11. start workers/connectors
12. run health + stock/ATP business smoke
13. resume schedulers only after smoke PASS
14. record exact cutover receipt/evidence
```

If any step after writer quiescence fails, remain fail-closed while operator chooses restore/forward-fix.

## 17. Business smoke tests immediately after startup

Use controlled/read-only or reversible test objects where possible.

Verify:

```text
stock view reads E02 balance
ATP view reads active reservation model
manual adjustment posts one movement
order reservation consumes ATP
shipment issue consumes reservation + physical stock once
transfer issue/receipt conserves quantity
purchase receipt posts once
count approval posts explicit adjustment
```

Do not use arbitrary production customer orders merely to test the release.

## 18. Post-cutover stabilization monitor

For an operator-approved period, run frequent server-local checks:

```text
ledger -> stock_balances rebuild parity
stock_balances -> legacy compatibility projection parity
reservation remaining/ATP invariants
shipment issue/reservation linkage
transfer conservation
purchase receipt linkage
approved count/manual movement linkage
forbidden writer scan
```

Scheduling uses systemd/cron/E01 durable worker, never GitHub Actions.

A divergence becomes a high-priority operational exception with references/correlation IDs.

Do not auto-fix by copying one table to another.

## 19. Cutover rollback classes

### A. Before authority marker / before post-cutover writes

Abort cutover, leave legacy authority, fix and retry later.

### B. Immediately after marker but before meaningful new production writes

If exact state is known and operator policy allows, restore the **complete** pre-cutover code + DB backup as one recovery event.

Do not restore only `inventory` rows.

### C. After new E02 production writes exist

Do **not** deploy a pre-E02 application that ignores them.

Safe choices:

```text
forward-fix current E02 release
or
roll back to a specifically E02-compatible prior release
or
perform complete pre-cutover code+DB restore, explicitly accepting loss of all post-cutover transactions within approved RPO
```

The decision requires operator authority and recovery evidence.

## 20. Release compatibility guard

Deployment tooling/release procedure should refuse target releases whose migration registry/domain contract cannot understand current production schema/stock authority.

E00 immutable migration/future-version checks remain part of this protection.

Do not bypass the Release Gate for emergency rollback.

## 21. Recovery verification expansion

E00 recovery verifier now must treat E02 evidence as required:

```text
business_operations
stock_movement_operations
stock_movement_lines
stock_balances
stock_reservations
stock_reservation_events
```

Restore smoke should verify at least:

- ledger/projection consistency;
- reservation quantity invariants;
- authority marker;
- representative shipment/transfer/purchase references.

A backup that restores SQLite but fails stock-kernel integrity is not valid rollback evidence.

## 22. Required cutover tests

### Eligibility

- any unresolved divergence -> eligible=false;
- unknown direct writer -> false;
- unresolved open-demand shortage/ambiguity -> false for affected authority scope;
- unresolved transfer mismatch -> false;
- missing recovery evidence -> false.

### Fencing

- forbidden direct SQL writer test fails intentionally on injected bad code;
- legacy adjustment façade delegates exactly once or rejects;
- compatibility fields cannot be used as authoritative inputs after marker.

### Read authority

- stock queries use E02 projection;
- ATP uses reservations/buffer;
- normal migrated write paths never read legacy available quantity to make a consequential decision.

### Recovery

- staging copy performs full pre-cutover restore drill;
- restored DB preserves authority marker/evidence according to snapshot time;
- rollback runbook is executable without GitHub Actions.

## 23. Cutover evidence artifact

After success create a retained record containing:

```text
cutover id
old release SHA
new release SHA
production DB backup manifest ID/hash
server-code snapshot hash
pre-cutover report hash
open-state migration report hash
post-migration reconciliation hash
authority marker values
postflight result
business smoke results
started/stopped timestamps
operator/reviewer identities
rollback decision window/status
```

This becomes the authoritative proof of E02 production activation.

## 24. PR / release review checklist

```text
[ ] A-I all passed/merged
[ ] current production backup/restore fresh PASS
[ ] writers can be quiesced deterministically
[ ] final reconciliation zero unexplained divergence
[ ] open demand reservation migration resolved
[ ] legacy locks resolved
[ ] active transfer migration resolved
[ ] pending legacy stock writers/actions inventoried
[ ] authority marker implemented
[ ] direct legacy writes technically fenced
[ ] read authority switched to E02
[ ] compatibility direction only E02 -> legacy
[ ] E02 recovery verification PASS
[ ] rollback runbook tested on staging copy
[ ] full Release Gate PASS
```

Any `no` blocks production cutover.

## 25. E02 completion definition

E02 is complete only after production/staging-as-authorized evidence proves:

```text
Movement Ledger is authoritative
Balance Projection rebuilds/reconciles
Reservation is authoritative for customer promise
ATP prevents oversubscription
Shipment/Transfer/Procurement/Manual/Count use one stock kernel
Legacy direct balance mutation is fenced
Backup/restore includes all E02 truth
```

Then unlock the next runtime foundation:

```text
E03 Warehouse Execution
```

Do not claim E02 complete because Migration 7/8/9 merely exist.
