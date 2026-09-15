# TASK_INV_AUDIT_TRANSFER_01 — Inter-Warehouse Transfer & In-Transit Control Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `TransferService`, transfer schema/events, inventory ledger interaction and recent iteration evidence. No GitHub Actions run is used as evidence.

## 1. Executive conclusion

Inter-warehouse transfer is one of Inventory Lite's more mature operational workflows. It is significantly stronger than the simple schema fields might suggest.

The effective transfer truth is built from:

- transfer document status;
- transfer items and cumulative received quantity;
- `transfer_out` inventory ledger entries;
- `transfer_out_revoke` reversal entries;
- `transfer_in` entries;
- transfer receipt/exception events;
- explicit state checks.

This is preferable to trusting the dormant-looking `inventory.quantity_on_transfer` counter.

The main remaining risks are concurrency/idempotency, explicit in-transit ownership/location semantics, and integration with future lot/serial/quality tracking.

## 2. Current state model

Current documented/current-source state family includes variants around:

```text
draft
 -> pending_out_confirm
 -> in_transit / pending_receive / shipped compatibility
 -> completed
```

with:

```text
exception
cancelled
```

and recovery/reversal paths.

Recent iteration evidence shows the workflow was deliberately hardened for:

- normal vs abnormal receipt;
- partial/cumulative receipt;
- shortage/damage/wrong-goods-type exceptions;
- undoing an outbound shipment before receipt;
- restoring stock on outbound reversal;
- preventing cancellation after consequential inventory movement without controlled recovery;
- merge behavior for same-direction pending transfers.

## 3. Outbound inventory posting

Before posting an outbound quantity, `TransferService` calculates net transfer movement from existing ledger entries:

```text
SUM(transfer_out + transfer_out_revoke)
```

for the exact transfer and material.

Observed logic:

- net = 0 -> post expected negative `transfer_out`;
- net = expected negative quantity -> do not post again;
- any other net -> fail and require reconciliation.

This is a strong pattern because it checks durable business evidence instead of trusting only the current document status.

## 4. Undo outbound

If no receiving has yet occurred, the current code can reverse the outbound operation.

Observed behavior:

- if net outbound equals expected negative quantity -> post positive `transfer_out_revoke`;
- if net is already zero -> no duplicate restore;
- inconsistent net -> fail closed;
- transfer returns to pending-out state and logistics fields are cleared;
- exception metadata is reset as appropriate.

This is safer than simply editing the old ledger entry.

## 5. Receiving and partial receipt

For each line, receiving logic checks:

- submitted received quantity >= 0;
- quantity cannot exceed remaining expected quantity;
- outbound ledger net is consistent;
- if expected outbound was never posted, receiving can backfill it;
- only the actual received quantity is posted to the destination warehouse;
- cumulative `received_quantity` is incremented.

This supports real-world transfer discrepancies better than an all-or-nothing transfer model.

## 6. Exception handling

`transfer_orders` contains explicit exception metadata and the schema includes `transfer_receipt_events` with:

- event type;
- exception type;
- item JSON;
- reason;
- actor/time.

This should be preserved and expanded rather than replaced with free-text remarks.

Future exception taxonomy can support:

- short quantity;
- over quantity;
- wrong item;
- damaged;
- package problem;
- missing parcel;
- late/incomplete delivery;
- future wrong lot/serial;
- quality quarantine.

## 7. Idempotency and concurrency risk

The transfer service has good **semantic duplicate protection** based on existing ledger net values, but the sequence is still conceptually:

```text
read ledger net
 -> decide whether to post
 -> post stock movement
```

Without a unique operation/event key, two concurrent requests can potentially both pass the same pre-check before either posts.

SQLite write serialization may reduce practical exposure, but this is not sufficient evidence of domain idempotency.

### Required local race tests

- same transfer `ship` called concurrently from two DB connections;
- same partial receive request concurrently;
- response-lost retry after committed receipt;
- undo and receive racing;
- merge and ship racing;
- abnormal receive then retry.

### Recommended event identity

Use stable event keys such as:

```text
transfer:<id>:line:<id>:outbound
transfer:<id>:outbound-reversal:<generation>
transfer:<id>:receipt:<receipt-event-uuid>:line:<id>
```

protected by a database UNIQUE constraint.

## 8. In-transit stock semantics

Current operational truth is reconstructable from transfer documents and ledger, while `inventory.quantity_on_transfer` does not appear to be the controlling service field.

For future reporting/manufacturing traceability, choose one explicit representation:

### Option A — virtual in-transit location

```text
source bin
 -> IN_TRANSIT:<transfer_id>
 -> destination receiving/staging bin
```

Advantages:

- physically intuitive;
- stock never disappears between warehouses;
- lot/serial genealogy remains continuous;
- inventory valuation/ownership can remain visible.

### Option B — transfer document projection

Derive in-transit quantity from posted outbound minus posted inbound, without a mutable counter.

Advantages:

- lower schema complexity;
- compatible with current ledger concept.

For future lot/serial traceability, Option A is generally stronger because individual lots/serials can occupy a virtual transit location.

## 9. Merge behavior

Recent implementation history includes automatic grouping/merging of same-direction unexecuted transfer lists and explicit rollback when one group is invalid.

This is useful operationally but increases audit complexity.

Future model should preserve provenance:

- source transfer IDs;
- merged target ID;
- exact line quantities before/after;
- actor/time;
- reason;
- no merge after stock movements have begun.

Never delete merge provenance solely to make the UI cleaner.

## 10. Electronics-specific extension

Transfers should eventually support lot/serial/stock-status identity.

Examples:

### Production component transfer

```text
Main warehouse / accepted lot A
 -> production supermarket
 -> work-order kit
```

### Quality hold

```text
receiving
 -> quarantine
 -> quality release
 -> available location
```

### Engineering loan/sample

```text
warehouse
 -> engineering location/project custody
 -> consumed / returned / scrapped
```

This argues for a generic location/status movement kernel underneath transfer documents.

## 11. Operational metrics

Once event timestamps are normalized, useful metrics include:

- request-to-outbound time;
- transit time;
- receive-to-complete time;
- exception rate;
- partial-receipt rate;
- reversal rate;
- quantity discrepancy rate;
- source/destination warehouse pair performance;
- aging in transit.

These can feed the future management dashboard without changing transfer transaction logic.

## 12. Automation opportunities

Independent of GitHub Actions:

- server-side aging alerts for transfers stuck in pending/outbound/transit;
- automatic reminder/escalation based on SLA;
- suggested transfer from low-stock warehouse to surplus warehouse;
- route/parcel status query through logistics adapters;
- anomaly detection when ledger state disagrees with document state;
- scheduled reconciliation of transfer net movements.

All jobs should persist their state in the application DB and run through an independent worker/systemd timer/cron.

## 13. Reconciliation command

Add a direct tool such as:

```bash
python3 tools/check_transfer_integrity.py
```

For every transfer/line verify:

```text
expected outbound qty
= - net transfer_out/revoke qty when currently outbound

received_quantity
= sum destination transfer_in qty

received_quantity <= expected quantity

completed -> all required receipt semantics satisfied

cancelled -> no unreversed consequential outbound movement
```

Later add lot/serial/location dimensions.

## 14. Priority recommendations

### P0

1. add unique operation/event identity for outbound/receive/reversal;
2. build local concurrent/retry tests;
3. formally deprecate or define `quantity_on_transfer`;
4. add transfer integrity checker;
5. keep fail-closed behavior when ledger/document state disagrees.

### P1

1. virtual in-transit/staging locations or a formally documented projection model;
2. location-aware outbound/receiving;
3. logistics event integration;
4. transfer aging/SLA alerts;
5. stronger structured exception taxonomy.

### P2

1. lot/serial transfer genealogy;
2. stock-status transfer/quarantine;
3. automatic transfer suggestions driven by forecast/MRP;
4. optimized consolidated transfers.

## 15. Static maturity score

0–5:

- basic transfer lifecycle: **4.5/5**
- partial receiving: **4.5/5**
- reversal/recovery: **4/5**
- exception evidence: **4/5**
- ledger consistency concept: **4/5**
- concurrency/idempotency proof: **2.5/5**
- explicit in-transit stock representation: **2.5/5**
- location-aware WMS integration: **1.5/5**
- lot/serial traceability: **0.5/5**

## 16. Core judgment

Transfer is not where the system needs a rewrite. It is a good candidate to become a reference implementation for future business workflows.

Preserve its principles:

`state validation + durable movement evidence + reversible compensating movement + structured exception + fail closed on inconsistency`

and strengthen them with database-enforced event identity, location/lot semantics and local concurrency tests.