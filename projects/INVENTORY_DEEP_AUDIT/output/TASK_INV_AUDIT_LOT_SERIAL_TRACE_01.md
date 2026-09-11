# TASK_INV_AUDIT_LOT_SERIAL_TRACE_01 — Lot, Serial Number and End-to-End Traceability Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed inventory and inventory-log schema, purchase receipt structures, order/shipment references, attachment/resource capabilities, BOM structures and the absence of first-class lot/serial genealogy fields in the inspected core schema/service layer.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The current system records **quantity movement**, but not product genealogy. In the inspected schema, inventory and inventory logs are keyed around material/warehouse/platform/location and movement references; they do not carry first-class supplier lot, date code, internal lot, serial number or parent-child genealogy.

That is acceptable for simple commerce inventory, but insufficient for electronics/RF manufacturing where failures often need to be traced to:

- finished-module serial number;
- product/BOM revision;
- PCB revision or lot;
- IC manufacturer lot/date code where risk justifies it;
- supplier/source;
- assembly work order;
- firmware version;
- RF/electrical test record;
- rework history;
- customer shipment/RMA.

Preliminary traceability maturity: **0.5/5**.

## 2. Traceability should be risk-based

Do not serial-track every passive component individually. Introduce a configurable traceability class by material/product category:

```text
NONE
LOT
SERIAL
LOT_AND_SERIAL
```

Optionally add capture policies:

- supplier lot required;
- manufacturer date code required;
- expiry required;
- test certificate required;
- serial auto-generated vs supplier-provided.

Typical examples:

- 0402 resistor: none or supplier lot for critical builds;
- SAW filter / MMIC: lot/date code for higher-risk products;
- bare PCB: lot + revision;
- finished RF module: serial mandatory;
- calibrated instrument/module: serial + test/calibration history mandatory.

## 3. Required identity layers

Do not overload `material_code` or barcode with lot/serial meaning.

### Material identity

Answers: **what part is it?**

### Lot identity

Answers: **which homogeneous receipt/build batch did it come from?**

### Serial identity

Answers: **which individual unit is it?**

### Stock balance

Answers: **how many qualifying units exist in a particular stock state/location?**

These must relate but remain distinct.

## 4. Receiving traceability

Purchase receipt lines need optional/required lot capture according to material policy.

Recommended receipt sequence:

```text
PO line
 -> physical receipt
 -> capture supplier lot/date code/expiry where required
 -> IQC/quarantine state
 -> accepted lot quantity released to stock
```

Fields may include:

```text
inventory_lots
  id
  material_id
  internal_lot_no
  supplier_id
  supplier_lot_no
  manufacturer_lot_no
  date_code
  manufactured_at
  expiry_at
  receipt_id / receipt_line_id
  quality_status
  created_at
```

One receipt line may contain multiple supplier lots; do not force one lot per receipt line.

## 5. Serial-number model

Finished-product serial numbers and selected serialized components need a unique identity.

```text
serial_units
  id
  material_id
  serial_no
  lot_id
  revision_id
  status
  warehouse_id/location_id
  work_order_id
  quality_status
  current_owner/reference
  created_at
```

Use a unique constraint with the intended scope. For internally assigned product serials, global uniqueness is usually simplest.

Never recycle a retired/shipped/scrapped serial number.

## 6. Quantity-to-lot balance

A future inventory model should be able to answer both aggregate and lot-level quantities.

Recommended invariant:

```text
aggregate stock for material/location/state
  = sum(lot/serial-qualified stock positions)
```

Do not maintain unrelated aggregate and lot tables that can drift without reconciliation.

A practical implementation can derive aggregate balances from a ledger/position table or maintain cached aggregates with strict transactional updates and reconciliation checks.

## 7. Manufacturing genealogy

For a work order, preserve component-to-output relationship:

```text
component lot(s)/serial(s)
  -> WO material issue
  -> work order / product revision / MBOM revision
  -> finished serial(s) or output lot
```

Minimal genealogy table:

```text
genealogy_links
  parent_serial_id or parent_lot_id
  child_lot_id / component_serial_id
  work_order_id
  material_id
  quantity
  relation_type
  created_at
```

Naming parent/child can be confusing; document direction explicitly, for example `output_serial_id` and `consumed_lot_id`.

## 8. Consumption granularity

Two valid operating modes should be supported:

### Lot-level backflush

For low-volume batches where exact per-unit component mapping is unnecessary, link consumed lot quantities to the WO/output lot.

### Serial-level genealogy

For critical modules, map component serial/lot to each finished serial if actual process captures it.

Do not claim per-unit genealogy unless the shop-floor workflow actually records it.

## 9. Shipment traceability

Shipment must preserve which serials/lots were delivered to which order/customer.

Required query:

```text
serial -> shipment -> order -> customer/channel/date
```

and inverse:

```text
customer shipment -> all serials/lots delivered
```

This enables targeted recall/RMA analysis without broad manual searching.

## 10. RMA/service loop

Traceability becomes much more valuable once returned units can re-enter history.

Future chain:

```text
customer shipment
 -> RMA received
 -> serial identified
 -> failure/test record
 -> repair/rework parts
 -> firmware/revision changes
 -> retest
 -> reship / scrap / replace
```

The original genealogy must remain intact; repair creates additional history rather than replacing it.

## 11. Quality-state interaction

Lot/serial must carry or resolve current quality disposition:

- pending inspection;
- accepted;
- quarantine;
- rejected;
- MRB review;
- rework;
- scrapped;
- released.

MRP and order allocation must count only policy-approved states as usable supply.

Quality status should not be editable as an isolated free-form text without a disposition transaction.

## 12. Test-record interaction

For finished RF modules, a serial should link directly to:

- test specification/limit-set revision;
- raw measurement file where retained;
- summarized metrics;
- pass/fail;
- instrument and calibration state;
- operator;
- firmware;
- timestamp.

This is covered in `TASK_INV_AUDIT_TEST_RECORD_01`, but serial identity is the key join contract.

## 13. Barcode/QR policy

Barcode/QR should encode or resolve stable identifiers, not be the sole source of truth.

Recommended labels:

- material code / MPN label;
- lot label;
- finished serial label.

A scan workflow should resolve the database entity and then post a controlled transaction.

Avoid putting mutable state such as `quality=accepted` directly into a static QR code.

## 14. Data integrity rules

P0 invariants:

1. serial number uniqueness;
2. lot/serial material identity cannot silently change after movement;
3. shipped serial cannot simultaneously be available stock;
4. scrapped quantity/serial cannot be reissued without a formal reversal;
5. lot quantity movements cannot drive below zero unless an explicit migration exception exists;
6. genealogy links reference released WO/BOM context;
7. quality state controls nettable/ATP eligibility;
8. all corrections are reversals or disposition events, not destructive history edits.

## 15. Minimum queries the system must answer

- Where is serial `X` now?
- Which customer received serial `X`?
- Which WO/BOM revision created serial `X`?
- Which component lots were used in serial/output lot `X`?
- Which finished units used supplier lot `Y`?
- Which supplier/PO/receipt introduced lot `Y`?
- Which tests/reworks occurred on serial `X`?
- How much accepted/quarantined/rejected quantity remains in lot `Y`?

If these cannot be answered deterministically, genealogy is incomplete.

## 16. Migration strategy

Do not fabricate historical lot/serial data.

Suggested migration:

1. add traceability policy to material/product master;
2. enable lots on new qualifying receipts only;
3. mark legacy stock as `LEGACY_UNTRACED` where necessary;
4. start finished-product serial generation at a controlled cutover date;
5. require WO output serials after work-order rollout;
6. attach shipments/RMA from cutover forward;
7. retain explicit evidence boundaries for old stock.

## 17. Priority roadmap

### P0

1. lot and serial master identities;
2. lot-aware receipt and stock ledger;
3. finished-product serial generation;
4. WO output linkage;
5. shipment serial capture;
6. quality-state integration.

### P1

1. component-lot genealogy;
2. RMA/rework genealogy;
3. manufacturer date code/expiry policy;
4. recall impact query;
5. label/scan UX.

### P2

1. richer station-level genealogy;
2. automated instrument/test attachment;
3. supplier certificate matching;
4. advanced traceability analytics.

## 18. Acceptance signals

- a new finished RF module cannot be received as serialized stock without a unique serial when policy requires it;
- a lot-controlled receipt can split one PO line across multiple supplier lots;
- quarantine lot quantity is excluded from normal allocation/MRP;
- a shipped serial resolves its customer/order/shipment;
- a finished serial resolves the work order and released BOM/product revision used to build it;
- a suspect component lot can identify affected finished units;
- legacy untraced stock is labeled honestly rather than assigned invented genealogy;
- no acceptance test requires GitHub Actions.

## 19. Core recommendation

Introduce **risk-based lot/serial identity and genealogy as a first-class ledger dimension**, starting at receiving and finished-product serialization. This will unlock meaningful quality, test, RMA, recall and manufacturing-cost workflows without forcing excessive tracking onto every low-value component.