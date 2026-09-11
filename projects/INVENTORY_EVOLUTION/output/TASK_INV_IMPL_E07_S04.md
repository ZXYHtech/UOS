# TASK_INV_IMPL_E07_S04 — NCR, MRB-lite, Rework and Scrap

## Status

`DESIGN_READY_BLOCKED_BY_E07_S03`

## Objective

Turn failed/uncertain quality evidence into a controlled nonconformance and disposition workflow instead of free-form remarks or direct stock edits.

## Suggested objects

```text
ncr_records
  id
  ncr_no
  source_type
  source_id
  material_id
  lot_id
  serial_id
  work_order_id
  defect_category
  defect_description
  quantity_affected
  severity
  status
  owner_user_id
  opened_by/at
  closed_by/at

ncr_dispositions
  id
  ncr_id
  disposition
  quantity
  engineering_authority_id
  quality_authority_id
  approved_by/at
  reason
  movement_operation_id
```

## Dispositions

Initial:

```text
use_as_is
rework
return_to_vendor
scrap
sort
engineering_deviation
```

A single NCR may split quantity across dispositions. Sum may not exceed affected quantity.

## MRB-lite

A small RF company does not need a committee workflow engine.

Use explicit required roles based on severity/disposition, e.g.:

- quality;
- engineering for technical concession/use-as-is;
- procurement for RTV;
- production for rework execution.

Server-side policy determines who may approve each disposition.

## Rework

Suggested evidence:

```text
rework_orders
  id
  ncr_id
  serial_id/lot_id
  work_order_id
  instruction_document_revision_id
  status
  assigned_user_id
  started_at/completed_at
  outcome

rework_material_events
  rework_id
  E02 movement/reference
  material/quantity
```

Rework can consume material and may change firmware/configuration under E05 authority.

Required retest is explicit.

## Scrap

Scrap posts authoritative E02 disposition/movement and retains lot/serial identity as historical scrapped evidence.

Never delete a serial/lot row to represent scrap.

## Return to vendor

RTV preserves:

- supplier/PO/receipt/lot identity;
- NCR/disposition;
- quantity;
- outbound movement/reference;
- later supplier credit/replacement handling in procurement/economics domains.

## Use-as-is / deviation

Requires explicit E05 deviation/engineering authority when technical requirements are knowingly waived.

A warehouse user cannot make quarantined/rejected stock usable by changing location or quantity.

## Reopen/correction

Closed NCR is append-only under normal workflow.

A correction/reopen action records reason, actor and new evidence; it does not overwrite the old decision.

## Tests

- failed inspection can open linked NCR;
- disposition quantity split bounded by affected quantity;
- warehouse-only user cannot approve use-as-is;
- valid engineering deviation required where policy says so;
- rework preserves original failure and requires retest when configured;
- scrap posts one movement and serial remains historical;
- RTV remains linked to source receipt/supplier lot;
- closed NCR cannot be destructively edited;
- duplicate disposition replay exact-once.

## Acceptance

Every material/product nonconformance has an accountable owner, affected quantity, approved disposition and immutable link to the stock/test/inspection evidence that caused it.
