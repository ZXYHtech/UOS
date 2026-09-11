# TASK_INV_IMPL_E14_S02 — AI Task Registry & Versioned Structured Output Schemas

## Status
`DESIGN_READY_BLOCKED_BY_E14_S01`

## Objective
Make every AI feature a declared task with bounded purpose, source policy, output schema and validation rather than one unrestricted general agent.

## Task registry
Each AI task definition records:

- task code/version;
- capability class C0–C3;
- allowed source/tool classes;
- required permissions/scope;
- input schema;
- output JSON schema/version;
- validators;
- action mode: read-only / draft / approval-required;
- provider/privacy policy;
- evaluation dataset/version;
- timeout/tool-call/token/cost budgets.

## Structured output
Examples include:

```text
supplier_quote_extraction
  supplier_candidate
  manufacturer_mpn
  supplier_sku
  moq
  price_breaks
  currency
  lead_time
  validity
  evidence_refs
  confidence_by_field
  unknown_fields
```

or inquiry extraction with customer candidate, requirement attributes, quantity/date/target price and source evidence.

Malformed output is rejected or routed to review; it is never best-effort written into canonical business records.

## Rules
- schema changes are versioned;
- confidence is field-level review signal, never authorization;
- unknown/missing values remain explicit rather than hallucinated defaults;
- C3 task cannot gain write authority merely through prompt text;
- prompt/template version is linked to the task execution record.

## Tests
- malformed/missing required output is rejected;
- old execution remains interpretable after schema v2 release;
- C1 extraction cannot invoke a C3 action tool;
- high confidence cannot bypass deterministic validation;
- unknown field stays unknown instead of receiving fabricated default.

## Done
Every AI capability has a testable machine-readable contract, bounded permissions and versioned behavior.