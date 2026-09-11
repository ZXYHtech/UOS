# TASK_INV_IMPL_E07_S02 — Lot-aware Receiving and Quality Stock State

## Status

`DESIGN_READY_BLOCKED_BY_E07_S01_E02_E03`

## Objective

Make trace-controlled purchase receipts create honest lot identities and place received quantity into the correct quality stock state before it becomes usable supply.

## Receiving flow

For materials requiring incoming inspection:

```text
PO receipt
 -> capture supplier/manufacturer lot/date-code evidence
 -> create one or more stock lot identities
 -> E02 receipt movement into PENDING_INSPECTION position
 -> create IQC work (E07-S03)
```

For materials whose policy permits direct acceptance, receipt may enter ACCEPTED according to explicit configured policy. Never infer direct acceptance just because no inspector is available.

## Multi-lot receipt

One PO receipt line may contain:

```text
100 pcs total
 -> supplier lot A: 60
 -> supplier lot B: 40
```

Validation:

```text
sum lot quantities == receipt quantity represented by that transaction
```

Partial receipt and later receipt continue to use their own lot evidence.

## Quality-state dimension

E02 stock identity/projection is extended with controlled quality state when E07 becomes authoritative.

Initial states:

```text
PENDING_INSPECTION
ACCEPTED
QUARANTINE
REJECTED
REWORK
SCRAP
```

Only configured eligible states count toward:

- sales ATP;
- WO reservation;
- MRP nettable supply later.

## Movement semantics

Quality transition is a referenced E02 movement/disposition, e.g.:

```text
+100 PENDING_INSPECTION on receipt
-95 PENDING / +95 ACCEPTED on IQC accept
-5 PENDING / +5 QUARANTINE on failed/uncertain disposition
```

Do not edit `quality_status` in place with no ledger evidence.

## Receipt evidence

Capture, when policy requires:

- supplier lot;
- manufacturer lot;
- date code;
- expiry;
- supplier/manufacturer-part identity;
- COC/test certificate attachment/evidence;
- packaging/condition note;
- actor/time.

Missing required evidence blocks controlled receipt completion or leaves the quantity in a visible pending/exception state; do not silently fabricate values.

## E03 interaction

Physical receipt may still use E03 receiving/staging location. Location and quality are separate dimensions:

```text
where is it?        = location
can it be used?     = quality state
which batch is it?  = lot identity
```

A bin named `QC` is not quality authority.

## Tests

- trace policy requires lot fields appropriately;
- one receipt line splits into multiple lots exactly;
- received quantity and lot totals reconcile;
- pending-inspection stock excluded from normal ATP/reservation;
- location and quality state remain independent;
- required certificate/date-code missing produces explicit block/exception;
- receipt retry does not duplicate lot or stock movement;
- direct-accept path only works under configured policy;
- quality-state transition cannot be performed by editing lot row directly.

## Acceptance

Incoming trace-controlled electronics stock enters the system with truthful source-lot evidence and correct usability state, so physical receipt can occur without falsely making uninspected material available for sale or production.
