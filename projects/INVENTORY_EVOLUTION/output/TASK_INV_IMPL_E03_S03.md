# TASK_INV_IMPL_E03_S03 — Typed Scan Resolution

## Status

`DESIGN_READY_BLOCKED_BY_E02_LOCATION_IDENTITY`

## Objective

Promote the existing strong material matcher into a shared typed scan resolver that identifies canonical warehouse objects before any action occurs.

## Existing strength to reuse

Current material matching already supports concepts such as:

- material code priority;
- aliases;
- barcode/QR;
- normalized exact code;
- variant protection;
- explicit selection for ambiguity;
- stock context.

Do not rebuild this separately for mobile/WMS.

## Target contract

```python
resolve_scan(raw, context) -> ScanResolution
```

Resolution includes:

```text
raw input
normalized representation
candidate entity type
canonical entity ID
match reason
confidence class (exact / alias / contextual / ambiguous)
context compatibility
permitted next action hints
```

Action hints are informational only; Action Policy still authorizes the real command.

## Initial entity types

```text
MATERIAL
LOCATION
SHIPMENT_TASK
TRANSFER
PURCHASE_ORDER
PURCHASE_RECEIPT
PUTAWAY_TASK
COUNT_TASK
UNKNOWN
```

Reserved but not implemented yet:

```text
LOT
SERIAL
WORK_ORDER
RMA
PACKAGE
```

## Identifier registry

Suggested additive table:

```text
scan_identifiers
  id
  namespace
  code_value
  entity_type
  entity_id
  active
  source
  created_at
  retired_at
```

Constraint:

```text
UNIQUE(namespace, code_value)
```

Internal namespace identities must be deterministic. External supplier/manufacturer barcodes require explicit namespace/parser rules rather than assuming global uniqueness.

## Context safety

Examples:

### Putaway task

Expected context accepts:

- source receiving location;
- expected material;
- allowed destination location.

A scanned shipment or unrelated material may still resolve globally, but the task command rejects it as context-incompatible.

### Pick task

A correct material in the wrong location is not “close enough”.

### Count task

A scanned material/location records an observation target only; it never adjusts stock directly.

## Ambiguity policy

- exact typed identity can auto-resolve;
- two active exact identities are a data defect and must block;
- fuzzy candidates never auto-trigger a stock-changing action;
- detailed material code cannot silently degrade to a parent/base code;
- unknown scan is retained as an exception/lookup opportunity, not auto-created as master data.

## Hardware neutrality

Resolver accepts plain text and does not depend on scanner hardware.

Supported clients can include:

- USB/Bluetooth keyboard wedge;
- phone camera;
- Android native scanner later.

## Tests

- exact material barcode resolves canonical material;
- alias resolution preserves match explanation;
- exact location scan resolves location and warehouse;
- wrong task-context type rejected;
- ambiguous candidates require explicit selection;
- duplicate active code identity rejected;
- retired identifier cannot be used for new execution;
- scan resolution alone performs zero stock mutation;
- server still enforces permission/scope/state/idempotency after resolution.

## Acceptance

One shared typed resolver powers warehouse scan workflows without duplicating matching logic or allowing scan confidence to bypass business authority.
