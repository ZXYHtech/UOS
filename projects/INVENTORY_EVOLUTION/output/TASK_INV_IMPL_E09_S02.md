# TASK_INV_IMPL_E09_S02 — SKU Mapping Lifecycle, Conflict & Historical Freeze

## Status
`DESIGN_READY_BLOCKED_BY_E01_E02_GATES`

## Objective
Turn `platform_sku_mappings` from a lookup table into a controlled lifecycle without rewriting historical orders when a marketplace SKU changes.

## States

```text
unmapped
matched
ambiguous
manually_overridden
invalid
retired
```

## Required evidence
Each mapping preserves platform account, remote product/SKU IDs, current internal material/sales-BOM target, confirmation source, actor/time, remote observation metadata and conflict/override reason.

## Rules
- one mapping decision is account-scoped;
- ambiguous candidates require explicit resolution;
- variant/detail code may not silently fall back to a base material;
- manual override is audited;
- mapping changes do not retroactively alter canonical identity snapshots on historical order lines;
- retired/invalid mapping blocks new automatic conversion but historical references remain readable.

## Tests
- ambiguous remote SKU cannot auto-confirm;
- manual override records actor/reason;
- remapping today leaves yesterday's order-line material snapshot unchanged;
- retired mapping no longer auto-resolves new orders;
- duplicate active conflicting mapping is rejected or surfaced explicitly.

## Done
Remote SKU identity can evolve without corrupting already accepted orders or silently choosing the wrong internal part.