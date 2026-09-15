# TASK_INV_AUDIT_RETURNS_RMA_01 — Returns, Refund, RMA, Repair and Warranty Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed order fulfilment, shipment/reversal patterns, inventory ledger, operation logs, platform connector findings, W3 serial/lot genealogy, quality/NCR/test-record requirements and current absence of dedicated refund/RMA semantics in the inspected service layer.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

The current system has a good **reversal principle** in fulfilment—stock changes can be compensated with new movements rather than erasing history—but it does not yet have a first-class after-sales lifecycle covering return authorization, refund, exchange, repair, warranty and serial history.

For an electronics/RF business, after-sales must not be modeled as `negative sale + positive stock`. A returned RF module may be:

- unopened and restockable;
- physically damaged;
- customer-misused;
- functionally failed;
- repairable;
- needing firmware update;
- awaiting engineering analysis;
- warranty-covered or chargeable;
- exchanged before the original unit returns;
- refunded without physical return;
- returned with accessories missing;
- scrapped after diagnosis.

Preliminary maturity: **0.5/5** for structured RMA/warranty, while the underlying order/shipment/ledger foundation is materially stronger.

## 2. Separate four concepts

Do not collapse these into one `return status`:

1. **Commercial refund** — money movement/credit decision.
2. **Physical return** — product/package movement back to company.
3. **Technical RMA/repair** — diagnosis, repair, retest and disposition.
4. **Warranty decision** — who bears the cost and why.

They may be linked, but each has its own state and timing.

## 3. Return authorization

Introduce an RMA/return authorization before physical processing where practical.

```text
rma_cases
  id
  rma_no
  customer_id
  order_id
  shipment_id
  platform_account_id
  case_type: return | repair | exchange | refund_only | warranty
  status
  requested_at
  authorized_at
  received_at
  closed_at
  owner_user_id
```

For platform-originated returns, preserve remote return/refund IDs and events separately from internal case identity.

## 4. RMA line identity

A return must specify what is expected back.

```text
rma_lines
  rma_id
  original_order_line_id
  material_id
  serial_id
  expected_qty
  received_qty
  reason_code
  customer_description
  warranty_claimed
```

For serialized RF modules, serial number should be mandatory when known and should resolve:

```text
serial -> original shipment -> order -> product revision -> test/work-order history
```

## 5. Return reason taxonomy

Use structured codes plus free-form notes.

Suggested categories:

- wrong item shipped;
- not as described/spec mismatch;
- no longer needed;
- damaged in transit;
- dead on arrival;
- intermittent failure;
- performance out of spec;
- connector/mechanical damage;
- over-voltage/reverse polarity/user damage;
- firmware/configuration issue;
- missing accessory;
- duplicate order;
- logistics delay;
- suspected manufacturing defect;
- unknown/needs diagnosis.

Reason codes drive analytics but must not predetermine warranty responsibility before inspection.

## 6. Physical receipt

Returned product should enter a controlled state:

```text
RETURN_IN_TRANSIT
 -> RETURN_RECEIVED_QUARANTINE
```

Never return incoming RMA goods directly to normal available stock.

Receipt should capture:

- parcel/tracking;
- received quantity;
- serial/lot;
- packaging/accessories;
- visual condition;
- photos/evidence;
- received by/time.

## 7. Inspection and disposition

Post-receipt disposition should support:

```text
RESTOCK
REPAIR
REWORK
RETURN_TO_CUSTOMER_NO_FAULT_FOUND
EXCHANGE
SCRAP
HOLD_FOR_ENGINEERING
RETURN_TO_SUPPLIER
```

Each quantity/serial must end with one explicit disposition.

For unopened accessories/components, restock may be simple. Serialized finished RF products should generally require at least verification/test before saleable release.

## 8. Warranty eligibility

Warranty should be rule + evidence, not only a checkbox.

Potential factors:

- shipment/purchase date;
- warranty term applicable to product/customer;
- serial identity;
- customer/contract exceptions;
- prior repair history;
- damage/abuse indicators;
- product revision/known issue;
- returned unit authenticity;
- engineering/quality finding.

Store decision:

```text
warranty_decisions
  rma_id
  status: covered | not_covered | partial | goodwill
  decision_code
  explanation
  decided_by
  decided_at
```

Do not encode legal warranty rules globally without jurisdiction/customer contract context; keep policy configurable.

## 9. Diagnosis

For RF modules, diagnosis should connect to structured test evidence.

```text
RMA received
 -> diagnostic test run
 -> failure symptom/category
 -> root cause if known
 -> repair action
 -> retest
 -> final disposition
```

Examples:

- gain low;
- S11/S22 out of spec;
- high noise figure;
- excessive current;
- no RF output;
- digital control failure;
- connector damage;
- firmware/configuration mismatch.

Do not force all diagnoses into one text field; preserve test-run IDs and structured defect/root-cause codes when known.

## 10. Repair history

For serialized products:

```text
repair_orders
  rma_id
  serial_id
  repair_no
  status
  assigned_user
  work_instruction_revision
  started/completed_at
```

Repair actions may capture:

- components replaced;
- firmware changed;
- tuning/calibration performed;
- labor/time;
- external repair/subcontract;
- resulting product configuration/revision exception;
- final test run.

This history must remain attached to the serial permanently.

## 11. Replacement and exchange

Exchange requires two independently traceable sides:

- returned original unit;
- replacement shipment.

A cross-reference should allow:

```text
RMA -> replacement order/shipment -> replacement serial
```

Advance replacement before return is possible; the original remains an open receivable asset/exception until received or written off.

Do not close an exchange case merely because the replacement shipped.

## 12. Refunds

Refund lifecycle:

```text
requested
approved
submitted_to_platform/payment
completed
failed/retry
```

Store:

- gross refund;
- partial line amount;
- shipping refund;
- coupon/platform subsidy implications where known;
- payment/platform refund ID;
- remote acknowledgement;
- reason;
- actor/time.

Physical stock movement must not depend on refund completion if the unit has already been received, and refund completion must not imply a physical return occurred.

## 13. Platform synchronization

Omnichannel connectors should normalize platform after-sales objects into canonical internal records.

Need durable identities for:

- remote refund ID;
- remote return ID;
- dispute/case ID;
- status changes;
- refund amount revisions;
- tracking/receipt events.

Use replay-safe external-object ledger and reconciliation from W4 omnichannel design.

## 14. Restock eligibility

Returned goods should only re-enter ATP after the appropriate quality gate.

For finished RF modules:

```text
returned quarantine
 -> inspection/diagnostic
 -> required retest
 -> accepted
 -> saleable/refurbished/service stock
```

Consider distinct condition grades if business uses refurbished units:

- new;
- opened/verified;
- refurbished;
- service spare;
- non-saleable reference.

Do not mix refurbished stock with new product silently.

## 15. RMA-to-NCR/CAPA linkage

A single customer return is not automatically a production NCR, but repeated or severe defects should create/associate quality records.

Useful rules:

- repeated failure code above threshold -> quality review;
- same component lot implicated -> traceability impact analysis;
- known design issue -> engineering change/ECO candidate;
- supplier component root cause -> supplier NCR/SCAR.

After-sales data should feed engineering and supplier quality rather than end at refund closure.

## 16. Cost capture

RMA actual economics may include:

- refund amount;
- replacement product cost;
- return freight;
- outbound replacement freight;
- repair components;
- repair labor;
- retest/calibration;
- scrap loss;
- supplier recovery/credit;
- platform penalties/fees.

Connect these to channel-finance/order-economics domain so true contribution margin can reflect after-sales burden.

## 17. SLA and exception control

Track timestamps and owners for:

- awaiting customer shipment;
- return in transit;
- received awaiting inspection;
- awaiting engineering diagnosis;
- repair in progress;
- awaiting part;
- awaiting refund approval;
- waiting customer confirmation;
- replacement pending;
- overdue return of advance replacement.

Aging should drive customer-service work queues.

## 18. Minimal lifecycle

A practical core lifecycle:

```text
OPEN
AUTHORIZED
AWAITING_RETURN
RECEIVED
INSPECTION
REPAIR / REFUND / EXCHANGE / RESTOCK_DECISION
RESOLVED
CLOSED
```

Keep sub-statuses in the relevant physical/financial/repair objects to avoid a single giant status enum.

## 19. Priority roadmap

### P0

1. RMA case + line identity;
2. original order/shipment/serial linkage;
3. return quarantine receipt;
4. inspection/disposition;
5. refund record separate from physical return;
6. exchange/replacement linkage;
7. warranty decision and reason;
8. RMA aging/owner.

### P1

1. repair order and component replacement history;
2. diagnostic/retest integration;
3. platform refund/return sync;
4. restock condition grades;
5. RMA cost/economics;
6. recurring defect/root-cause analytics.

### P2

1. customer self-service RMA portal;
2. automated known-issue detection;
3. warranty reserve/failure-rate analytics;
4. supplier recovery automation.

## 20. Acceptance signals

- a refund can exist without falsely creating returned stock;
- a returned unit enters quarantine rather than normal ATP;
- serialized return resolves original shipment/product/test history;
- every received RMA line reaches an explicit disposition;
- exchange preserves both original serial and replacement serial;
- a repair preserves components/actions/retest rather than overwriting original history;
- warranty decision records reason and actor;
- repeated defect patterns can be aggregated by product revision/component lot/root cause;
- after-sales cost can feed realized contribution margin;
- no required sync/reminder/repair/test path depends on GitHub Actions.

## 21. Core recommendation

Build after-sales around a **serial-aware RMA case that separates physical return, technical diagnosis/repair, warranty decision and financial refund**. Reuse the existing compensating-ledger pattern and W3 test/quality genealogy so returns become product-quality intelligence rather than opaque inventory corrections.