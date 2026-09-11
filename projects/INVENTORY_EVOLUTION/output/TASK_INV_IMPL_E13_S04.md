# TASK_INV_IMPL_E13_S04 — Observe-only Simulation & Safe Rule Enablement

## Status
`DESIGN_READY_BLOCKED_BY_E13_S01_S02_S03`

## Objective
Require evidence of trigger frequency/impact before broad or consequential automation is enabled.

## Observe-only mode
A rule can evaluate real/historical events without creating business mutations. Record:

- number of evaluations/fires;
- affected objects;
- condition traces;
- proposed actions;
- estimated quantity/value/cash impact where relevant;
- false-positive/override review notes.

## Enablement gates
At minimum require:

- valid condition/action schema;
- owner and review date;
- risk/approval/reversal definition;
- observe-only evidence for broad A2/A3 rules;
- rate/volume limits;
- explicit scope (warehouse/account/product/etc.);
- approval to enable.

## Tests
- observe-only can never call mutating command;
- simulated action count/value is reproducible for same event set;
- enabling high-impact rule without required review evidence is blocked;
- later rule version returns to observe-only unless policy explicitly allows controlled rollout.

## Done
No broad automation jumps directly from configuration to silent production mutation.