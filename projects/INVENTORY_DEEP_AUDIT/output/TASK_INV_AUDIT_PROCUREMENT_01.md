# TASK_INV_AUDIT_PROCUREMENT_01 — Supplier, Purchase Order & Receiving Workflow Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed current schema and `ProcurementService` behavior, plus API/permission evidence. No GitHub Actions result is used as proof.

## 1. Executive conclusion

Procurement is **real and useful**, not a placeholder. The current source supports supplier master data, purchase orders, approval metadata, partial receiving, receipt records, freight/other-cost allocation, purchase-price history and inventory posting.

For a small e-commerce/electronics team this is a meaningful foundation. For electronics production, however, it is still a purchasing execution module rather than a full supply-planning/quality-controlled procurement system.

The most important next gaps are:

1. supplier-part / manufacturer-part identity;
2. MOQ, order multiple and lead-time policy;
3. RFQ/quotation comparison and price-break history;
4. MRP/demand pegging;
5. IQC/quarantine/accepted-rejected receipt states;
6. supplier lot/date-code/COC capture;
7. robust idempotency for receiving;
8. better landed-cost allocation semantics across multiple partial receipts.

## 2. Current supplier master

`suppliers` contains:

- supplier code/name;
- contact/name/phone/email/address;
- payment terms;
- tax number;
- remark/enabled state;
- created/updated metadata.

This is sufficient for basic procurement, but supplier identity is not yet connected to a controlled `SupplierPart` record.

For electronics, the missing relation matters because the real procurement object is often:

```text
Internal Part
 -> Manufacturer + MPN
 -> Approved Supplier
 -> Supplier Part Number
 -> Packaging
 -> MOQ / multiple
 -> lead time
 -> price breaks
 -> lifecycle / authorization
```

A generic supplier plus material ID cannot fully represent this.

## 3. Purchase order lifecycle

`purchase_orders` contains:

- purchase number;
- supplier;
- receiving warehouse;
- status;
- currency/tax;
- freight/other amount;
- expected date;
- creator;
- submitted time;
- approval actor/time/remark;
- completion time.

`purchase_order_items` includes:

- material;
- quantity;
- unit price;
- received quantity;
- tax rate;
- remark.

This supports a credible:

`draft -> submit -> approve -> partial receive -> complete`

operating model.

### Positive controls

Source confirms order creation validates:

- supplier exists and is enabled;
- warehouse exists;
- at least one item is provided.

API evidence also shows procurement actions are gated by `purchase.manage`, with separate `purchase.approve` available in the permission vocabulary.

## 4. Partial receiving

`ProcurementService.receive` accepts only an approved or partially received PO. It:

1. loads PO lines;
2. validates submitted received quantity does not exceed remaining line quantity;
3. rejects an all-zero receipt;
4. creates a unique receipt number;
5. creates `purchase_receipts` and receipt lines;
6. updates cumulative `received_quantity`;
7. posts stock via `InventoryService.adjust_inventory(... movement_type='purchase_receipt')`;
8. stores purchase/landed-cost history;
9. marks PO `part_received` or `completed`.

This is a good small-business receiving flow.

## 5. Receiving idempotency risk

The service validates current received quantities before posting, but the request itself does not show a caller-supplied stable idempotency key.

Potential failure mode to test locally:

```text
client submits receipt
server commits
network response is lost
client retries same business intent
```

If the retry is interpreted as a new receipt and remaining quantity still permits it, inventory can be posted twice relative to the user's original intent.

This is especially important once receiving is driven by mobile scan, API integration or automatic jobs rather than a careful single operator click.

### Recommendation

Require a stable receipt operation key, e.g.:

```text
receiving_request_id UNIQUE
```

or a client-generated UUID tied to the receipt event. Replaying it should return the original result rather than create a new receipt.

## 6. Landed-cost allocation issue to examine

On each receipt, source computes:

```text
base = sum(current received qty * PO unit price)
extra = PO freight_amount + other_amount
allocation = line share of extra
```

This appears to allocate the **full PO freight/other amount on every receiving event**, not only a remaining/unallocated share.

If a PO is received in multiple partial receipts, there is a plausible risk that freight/other charges are repeatedly allocated into purchase-price history for each receipt.

This is a strong candidate finding, but it should be confirmed with a local fixture before labeling it a production accounting defect.

### Required local test

Create a PO:

```text
line value = 1000
freight = 100
receipt 1 = 50%
receipt 2 = 50%
```

Then verify total allocated freight across both receipts equals 100, not 200.

### Better model

Use one of:

- receipt-specific freight/other costs captured at each receipt;
- a PO landed-cost allocation record with allocated/unallocated balance;
- final landed-cost adjustment after PO completion.

## 7. Currency and tax limitations

Currency is stored on PO and purchase-price history, but no foreign-exchange rate/value-date model was found in the reviewed procurement path.

For import purchasing, future cost needs:

- transaction currency;
- base currency;
- exchange rate and rate source/date;
- customs/duty;
- freight/insurance;
- broker fees;
- tax recoverability;
- allocation method.

Do not add full finance ERP prematurely; these can initially be operational landed-cost fields.

## 8. Electronics-specific procurement gaps

### P1 — item sourcing

Need:

- manufacturer;
- MPN;
- supplier part number;
- approved supplier/manufacturer status;
- alternates;
- package form (reel/tray/tube/cut tape);
- MOQ;
- order multiple;
- standard lead time;
- price breaks;
- preferred source;
- lifecycle/EOL/NRND.

### P1 — receiving quality

Need optional incoming inspection:

```text
receipt -> receiving/staging -> IQC
                     ├─ accepted -> available/putaway
                     ├─ quarantine -> hold
                     └─ rejected -> return/NCR
```

Useful electronics evidence:

- manufacturer lot;
- date code;
- COC;
- supplier lot;
- received packaging;
- visual/measurement inspection;
- MSL/ESD condition where relevant.

### P1 — demand linkage

Each PO line should eventually be able to explain **why it exists**:

- safety-stock replenishment;
- sales order shortage;
- prototype/project requirement;
- work order/MRP demand;
- manual strategic buy.

This demand pegging is essential for shortage prioritization.

## 9. Supplier performance

The current data is sufficient to begin deriving a lightweight supplier scorecard once receipt dates and expected dates are reliable.

Future metrics:

- on-time delivery;
- promised vs actual lead time;
- quantity shortage rate;
- incoming defect rate;
- price variance;
- response/quote turnaround;
- emergency-order share;
- return/NCR rate.

Do not hard-code one composite score before business weights are chosen. Store component metrics first.

## 10. Procurement automation

Useful automation independent of GitHub Actions:

```text
server-side scheduled planning job
 -> low-stock / MRP demand
 -> suggested purchase lines
 -> supplier/source recommendation
 -> operator review
 -> PO draft
```

Rules should generate suggestions, not silently place purchase orders by default.

Other automation:

- overdue PO reminders;
- partial receipt follow-up;
- price-change alerts;
- EOL/high-risk-source warnings;
- supplier lead-time drift;
- missing IQC/COC evidence.

Run these through application workers/systemd timers/cron + durable DB job state, never through required GitHub Actions workflows.

## 11. Recommended future entities

```text
manufacturers
manufacturer_parts
supplier_parts
supplier_part_prices
supplier_part_lead_times
rfqs
rfq_lines
supplier_quotes
purchase_demands / demand_pegging
purchase_receipt_events
incoming_inspections
landed_cost_documents
landed_cost_allocations
```

Not all should be built at once.

## 12. Priority roadmap

### P0

1. add receiving idempotency key;
2. locally verify multi-partial-receipt landed-cost allocation;
3. make money/quantity precision policy explicit;
4. add database constraints/orphan checks for purchasing relationships;
5. ensure PO state transitions are canonical and tested.

### P1

1. supplier-part + manufacturer/MPN model;
2. MOQ/order-multiple/lead-time/price-break fields;
3. shortage/demand linkage;
4. IQC/quarantine receipt option;
5. supplier performance metrics.

### P2

1. RFQ/quote comparison;
2. automated replenishment suggestion;
3. advanced landed cost/import purchasing;
4. supplier portal/integration if business volume justifies it.

## 13. Local verification — no Actions

Required repository-local tests:

```bash
python3 tools/test_procurement.py
python3 tools/test_purchase_receipt_idempotency.py
python3 tools/test_purchase_landed_cost.py
```

Scenarios:

- draft/submit/approve permission matrix;
- receive before approval fails;
- partial receive then complete;
- receive over remaining quantity fails;
- retry same receipt key posts once;
- two concurrent receipt attempts do not over-receive;
- multi-receipt landed costs allocate exactly once;
- stock ledger and PO received quantity reconcile;
- disabled supplier cannot be newly ordered;
- wrong warehouse permission fails.

The test commands themselves are authoritative; GitHub Actions is optional and unnecessary.

## 14. Static maturity score

0–5:

- supplier master: **3.5/5**
- PO lifecycle: **4/5**
- partial receiving: **4/5**
- landed-cost foundation: **3/5**
- receiving idempotency: **2/5**
- electronics supplier-part sourcing: **1/5**
- IQC integration: **1/5**
- demand/MRP linkage: **0.5/5**
- supplier performance: **1/5**
- overall small-business procurement: **3.5/5**
- overall electronics manufacturing procurement readiness: **2/5**

## 15. Core judgment

Do not replace this procurement module. It already has a useful execution spine.

Evolve it from:

`Supplier -> PO -> Receipt -> Inventory + Cost`

into:

`Demand -> Approved Source/MPN -> PO -> Receipt -> IQC/Status -> Putaway -> Cost/Performance -> Traceability`

while keeping operator control and simple deployment.