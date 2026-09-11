# TASK_INV_IMPL_E08 — MRP Planning, Recommendations and Subcontract / External WIP

## Status

`DESIGN_READY_BLOCKED_BY_E07_GATE`

E08 is design-only while earlier runtime gates remain open.

## 1. Objective

Add explainable time-phased material planning and controlled subcontract manufacturing after inventory, released MBOM, work-order and quality truth are trustworthy.

E08 is intentionally two related planning/manufacturing capabilities:

```text
A. MRP
   typed dated demand/supply
   -> released MBOM explosion
   -> time-phased netting
   -> explainable recommendations/exceptions
   -> planner-approved PO/WO/transfer

B. Subcontract
   released manufacturing authority
   -> reserve/dispatch company-owned material
   -> external WIP at supplier
   -> partial return/output
   -> quality/reconciliation
   -> processing cost evidence
```

## 2. Domain boundaries

```text
E02 = stock / reservation / movement truth
E04 = supplier part / AML / sourcing identity
E05 = released/effective MBOM + manufacturing package
E06 = internal WO execution
E07 = usable quality state + lot/serial genealogy
E08 = planning calculation + subcontract operational transformation
Procurement = PO/commercial commitment
E11 = economics/cost/settlement
```

MRP does not own stock and subcontract does not create a second inventory ledger.

## 3. Planning equation

Do not equate `quantity_available` with usable planning supply.

For each material/site/time bucket:

```text
Projected Available Balance(t)
 = prior PAB
 + qualified scheduled receipts
 + firm planned receipts where policy permits
 - gross requirements
```

Safety-stock/policy violations generate recommendations/exceptions.

Conceptual net requirement:

```text
gross requirement
- qualified/nettable on-hand
- scheduled firm supply by need date
+ safety/policy requirement
= shortage/net requirement
```

## 4. Supply eligibility

Potential supply:

- E07 ACCEPTED/nettable on-hand;
- open approved PO remaining quantity on expected date;
- released WO planned/completion supply where policy counts it;
- confirmed transfer inbound;
- subcontract scheduled return;
- firm planned order after planner approval if policy allows.

Exclude by default:

- quarantine/rejected/rework/scrap;
- engineering/golden sample/non-saleable stock;
- reservations belonging to other demand;
- unapproved substitute;
- draft PO/WO;
- expired/restricted lot;
- owner/consignment stock not usable for this demand.

## 5. Typed demand

Demand should be explicit rather than inferred ad hoc.

Initial demand classes:

```text
work_order_requirement
planned_production
firm_sales_order where make-to-order policy applies
prototype/project demand
service/RMA demand later
safety_stock_target
dependent MBOM demand
```

Every demand carries:

```text
material
site/warehouse
quantity
need date
demand type
reference document
firm/planned status
priority
```

## 6. Planning policy

Suggested:

```text
planning_policies
  material_id
  warehouse/site_id
  procurement_type      buy|make|transfer|mixed
  safety_stock
  lot_size_policy
  lead_time_days
  manufacturing_lead_time_days
  min_order_qty
  order_multiple
  preferred_source_id
  planning_horizon_days
  enabled
```

Do not overload the legacy material safety-stock field with every planning assumption.

## 7. Sourcing inputs

Reuse E04 supplier sources/AML.

Planning source selection must understand:

- approved supplier source;
- lead time;
- MOQ;
- order multiple;
- preferred rank;
- validity/effectivity;
- optional price reference;
- no-approved-source exception.

MRP may suggest an alternate candidate but cannot approve an E04 substitute.

## 8. Released MBOM explosion

Dependent production demand explodes only:

```text
released + effective E05 MBOM revision
```

Explosion supports:

- multi-level recursion;
- cycle prevention;
- quantity propagation;
- UOM;
- DNF/variant applicability;
- scrap/yield factor;
- phantom/subassembly when implemented;
- date/effectivity;
- exact revision evidence.

Never explode sales BOM or mutable draft EBOM into procurement recommendations.

## 9. Time buckets

P0 uses daily dates/buckets.

Do not begin with enterprise calendars/capacity scheduling.

Planning horizon is explicit per run/policy.

## 10. MRP run reproducibility

Suggested:

```text
mrp_runs
  id
  run_no
  horizon_start/end
  site scope
  parameters_json
  source_snapshot_at
  status
  started_by/at
  completed_at

mrp_run_inputs / snapshot references
mrp_recommendations
mrp_pegging_links
mrp_exceptions
```

A historical recommendation must remain explainable after stock/orders change.

Full byte-for-byte database snapshot is unnecessary; preserve the relevant source IDs/quantities/revisions/assumptions used.

## 11. Recommendations first

MRP outputs proposals, not autonomous orders.

Actions:

```text
BUY
MAKE
TRANSFER
RESCHEDULE_IN
RESCHEDULE_OUT
CANCEL/REDUCE
REVIEW_SUBSTITUTE
```

Recommendation lifecycle:

```text
proposed
 -> reviewed
 -> accepted / rejected / superseded
 -> converted to PO/WO/transfer request
```

Conversion is an explicit E01 idempotent business action.

## 12. Explainability / pegging

Every recommendation explains:

- shortage date/quantity;
- demand source(s);
- supply counted/excluded;
- selected MBOM revision;
- source/lead-time/MOQ/order multiple;
- suggested release/due date;
- excess caused by MOQ/lot sizing;
- substitute/source issue when applicable.

Basic pegging:

```text
component shortage
 -> parent WO/planned order
 -> source sales/project demand where known
```

## 13. Exceptions

High-value exceptions:

- shortage by need date;
- overdue suggested release;
- PO/WO late to demand;
- no approved source/AML;
- invalid/unreleased MBOM;
- quarantine/quality loss causes shortage;
- MOQ creates excess;
- demand cancellation leaves excess;
- long-lead item beyond horizon;
- substitute requires engineering approval;
- transfer conflict.

Prioritize actionable exceptions over dashboard decoration.

## 14. Subcontract identity

Outside processing is not a normal internal transfer.

Suggested:

```text
subcontract_orders
  id
  subcontract_no
  supplier_id
  source_work_order_id
  output_material_id
  product_revision_id
  mbom_revision_id
  release_package_id
  planned_quantity
  expected_return_at
  status
  processing_currency
  created_by/approved_by
```

Lifecycle:

```text
draft
 -> approved
 -> material_prepared
 -> sent
 -> partially_returned
 -> returned
 -> quality_closed
 -> operationally_closed
```

Financial close remains E11/procurement/accounting concern.

## 15. Material ownership modes

Distinguish:

```text
supplier_owned_input
company_consigned_input
mixed
```

Company-owned stock sent externally:

- leaves local ATP;
- remains company-owned asset/WIP;
- retains lot/serial identity where required;
- is visible by subcontractor/order;
- must reconcile before close.

Do not simply create a normal internal warehouse and hide external ownership semantics.

## 16. Consigned material reconciliation

Per company-owned line:

```text
sent quantity
= consumed
+ returned unused
+ accepted process loss
+ scrap
+ approved variance
+ unresolved variance
```

Final close requires unresolved variance = 0 unless a specific approved disposition exists.

## 17. Subcontract output

Returned output may be:

- same material after process;
- subassembly;
- finished product;
- partial quantity;
- rejected/rework quantity.

Receipt references exact subcontract order/released package and enters E07 quality state according to policy, typically PENDING_INSPECTION before acceptance.

## 18. Subcontract genealogy

For trace-controlled items preserve honestly:

```text
company supplied lot/serial
 -> subcontract dispatch/external WIP
 -> returned output lot/serial
 -> later internal WO/finished serial
```

Supplier-provided component lot data is captured only where actually supplied/required.

## 19. Subcontract commercial boundary

Subcontract order = operational/material transformation authority.

Purchase order/service line = commercial commitment/payment authority.

They may be linked one-to-one initially but remain distinct IDs.

Processing cost lines can include:

- unit processing fee;
- setup/NRE/tooling;
- supplier-provided material;
- testing;
- freight;
- expedite;
- scrap/rework charge.

E11 handles actual cost/economics; E08 records operational evidence and linked commercial source.

## 20. MRP integration with subcontract

MRP may treat:

- subcontract component kit demand as demand;
- confirmed external-WIP return as scheduled supply;
- overdue return as exception;
- consigned material as company-owned but non-local/nettable according to planning policy.

## 21. No automatic purchasing

Even after MRP is trustworthy:

- no silent PO creation without planner/purchasing review;
- no AI auto-buy;
- no unapproved alternate source;
- no GitHub Actions scheduler.

Scheduled MRP runs may use E01 durable jobs/systemd-owned execution.

## 22. Required tests

### Planning inputs

- sales/WO/project reservation not double-counted;
- quarantine/non-saleable stock excluded;
- open PO remaining qty counted on expected date;
- cancelled/draft supply excluded;
- released effective MBOM identity frozen in explosion.

### Netting

- daily PAB deterministic;
- shortage date/quantity correct;
- MOQ/order multiple applied and excess explained;
- lead-time release date correct;
- demand cancellation creates explainable reschedule/excess result.

### Recommendation

- every recommendation has pegging/explanation;
- conversion creates exact one PO/WO/transfer command through idempotency;
- rejected recommendation creates no executable order;
- unapproved source/substitute cannot convert.

### Subcontract

- sent company-owned material leaves local ATP but remains company-owned external WIP;
- partial returns do not close unresolved quantity;
- reconciliation equation enforced;
- returned output enters correct E07 quality state;
- genealogy preserves actual captured level;
- close blocked with unexplained company stock;
- processing cost not double-counted as purchased company-owned material.

## 23. Definition of done

E08 is complete only when:

- MRP uses typed dated demand/supply and released MBOMs;
- nettable stock respects reservations/quality/ownership;
- recommendations are time-phased and explainable;
- planner explicitly accepts/rejects/converts suggestions;
- source/MOQ/lead-time assumptions are visible;
- subcontract company-owned material is external WIP, not lost/local ATP;
- dispatch/return/output quantities reconcile;
- returned output follows E07 quality/genealogy;
- MRP sees scheduled subcontract supply;
- no required planning/scheduling/runtime path depends on GitHub Actions.
