# TASK_INV_IMPL_E06_S06 — Hold, Cancellation and WIP Disposition

## Status

`DESIGN_READY_BLOCKED_BY_E06_EXECUTION_CORE`

## Objective

Make hold/cancel safe for partially executed manufacturing orders so no reservation, issued material, scrap or completed output disappears behind a status change.

## Hold semantics

`on_hold` means:

- preserve configuration snapshot;
- preserve reservations according to explicit policy;
- preserve issued WIP and output evidence;
- block new issue/completion commands except authorized disposition/correction;
- record prior active state and hold reason;
- resume returns to a valid prior execution state after revalidation.

Hold is not cancellation and not stock release by default.

## Cancellation trigger

A WO can cancel immediately only if no consequential execution exists.

If any of these exists:

```text
active reservation
picked allocation
issued WIP
scrap event
completed output
```

then transition to:

```text
cancel_pending_disposition
```

## Cancellation disposition

The system computes unresolved obligations:

```text
unused reservations
picked-but-not-issued allocations
issued WIP
scrapped material
completed output
open substitutions/deviations
```

Operator/manager must resolve according to allowed paths.

### Reservation

Release unused reservations through E02.

### Pick allocation

Cancel/release E03 execution claim without inventing a stock movement when pick itself was non-moving.

### Issued WIP

Choose explicit disposition:

```text
return to stock
consume/close to prototype or production loss under policy
scrap
transfer to another authorized WO only via explicit future transaction
```

No hidden balance reset.

### Completed output

Already-received finished output remains real inventory.

Cancellation does not delete it. If output itself is invalid, use an output reversal or later E07 quality disposition.

## Close invariant

Final `cancelled` requires:

```text
unused reservation = 0
unresolved issued WIP = 0
unexplained picked quantity = 0
all executed output/scrap preserved as referenced evidence
```

An authorized exception may exist only as explicit disposition evidence, not a force-close boolean with no explanation.

## Reopen

Do not support casual reopen of cancelled/completed WO in P0.

If business needs resume after cancellation, prefer a new WO referencing the old one. Reopening historical closed execution makes audit/cost/traceability harder.

## Tests

- empty released WO cancels safely;
- active reservation forces disposition path;
- unused reservation releases exact-once;
- issued WIP prevents final cancel until resolved;
- completed output survives cancellation;
- hold blocks new execution but preserves balances/evidence;
- resume revalidates current permissions/config/policy without changing frozen BOM;
- duplicate cancel/disposition command idempotent;
- final cancellation invariant detects stranded WIP;
- no hard-delete of execution evidence.

## Acceptance

A manufacturing order can be stopped safely at any stage, and the system can account for every reservation, issued material and completed output before declaring it cancelled.
