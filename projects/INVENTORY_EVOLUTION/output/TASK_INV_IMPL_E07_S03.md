# TASK_INV_IMPL_E07_S03 — IQC/IPQC/FQC Inspection and Quality Release

## Status

`DESIGN_READY_BLOCKED_BY_E07_S02_E05`

## Objective

Create configurable inspection evidence and controlled quality release without hard-coding one global sampling standard or conflating physical receipt/process completion with acceptance.

## Suggested objects

```text
inspection_plans
  id
  plan_code
  inspection_type
  material/category/product scope
  revision_code
  status
  sampling_policy
  controlled_document_revision_id
  released_by/at

inspection_characteristics
  plan_id
  item_code
  name
  method_snapshot/template
  unit
  lower/upper/enum rule
  criticality
  evidence_required

inspection_orders
  id
  inspection_no
  inspection_type
  source_type/id
  material_id
  lot_id
  serial_id
  work_order_id
  quantity_presented
  plan_revision_id
  status
  inspector_id
  started_at/completed_at

inspection_results
  inspection_id
  characteristic_id
  characteristic_snapshot
  method_snapshot
  limit_snapshot
  sampled_quantity
  defect_quantity
  measured_value/result_json
  result
  evidence_attachment_id
```

## Inspection types

Initial:

```text
IQC
IPQC
FQC
OQC
```

P0 may implement IQC + FQC first, with schema ready for other types.

## Sampling policy

Do not globally hard-code ISO/AQL assumptions.

P0 supports:

```text
inspect_all
fixed_sample_quantity
external_plan_reference
```

If a recognized sampling standard is used later, store exact standard/version/plan selection as evidence.

## Electronics characteristics

Configurable examples:

- manufacturer/MPN marking;
- package/appearance;
- supplier/date code;
- PCB revision/dimensions/finish;
- key DC/RF spot value;
- certificate presence;
- moisture/packaging condition;
- mechanical dimensions.

Do not add one receipt column per quality characteristic.

## Partial disposition

One inspection may result in quantities such as:

```text
presented 100
accepted 95
quarantine 5
```

Disposition posts E02 quality-state movements in exact quantities.

## Final quality release

For finished output requiring test/inspection:

```text
E06 output
 -> pending quality
 -> required inspection/test evidence
 -> quality release
 -> ACCEPTED/saleable stock
```

E07-S08/S09 test evidence integrates into this decision.

## Separation of duties

Default policy should not allow receiver to self-approve own IQC unless explicitly configured for low-risk material.

Server-side Action Policy enforces inspector/release roles.

## Tests

- plan revision immutable after release;
- exact plan/limits snapshot retained on historical inspection;
- partial accept/quarantine sums to presented quantity;
- quality release posts controlled E02 state transition;
- current plan changes do not rewrite old result;
- missing mandatory characteristic/evidence blocks completion;
- receiver self-release blocked by default policy;
- failed required inspection cannot make stock ACCEPTED without explicit NCR/deviation authority.

## Acceptance

The system can prove what inspection rules were used, what was measured/observed, what quantity was accepted or held, and which authoritative transition made the stock usable.
