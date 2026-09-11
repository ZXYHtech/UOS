# TASK_INV_IMPL_E10_S02 — Technical Requirements & Product / Custom Candidate Evaluation

## Status
`DESIGN_READY_BLOCKED_BY_E04_E05_FOUNDATIONS`

## Objective
Capture RF/electronics requirements in a structured but extensible way and compare them to real product/revision evidence.

## Requirement model
Use typed requirement attributes plus free-form notes. Examples:

- frequency range;
- gain / insertion loss;
- noise figure;
- output power / linearity;
- impedance/interface;
- connector/control interface;
- supply voltage/current;
- dimensions/enclosure;
- quantity;
- environmental/test/document requirements;
- target price / requested delivery.

Do not add one opportunity column for every RF parameter.

## Candidate evaluation
An opportunity may reference multiple candidates:

- existing internal material/product revision;
- configuration/variant;
- custom/new-product candidate.

Each candidate records fit/gap summary, engineering-required flag and preferred state.

## Rules
- E04 parametrics help rank candidates but do not manufacture missing specifications;
- candidate similarity is not an engineering approval or guarantee;
- quote must snapshot the chosen technical description/revision;
- custom candidate may later link to R&D/project workflow without pretending a released product already exists.

## Tests
- typed requirements are searchable/filterable;
- multiple candidates can coexist;
- custom candidate remains distinct from released SKU;
- changing current product specs does not rewrite an already-sent quote snapshot.

## Done
Sales can explain why a product was proposed and which customer requirements were or were not met.