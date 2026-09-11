# TASK_INV_IMPL_E06_S08 — Engineering Prototype / Trial-build Mode

## Status

`DESIGN_READY_BLOCKED_BY_E06_CORE_E02`

## Objective

Support R&D prototype/trial builds without pretending they are released production work orders and without creating a separate inventory universe for engineering stock.

## Why separate mode is required

Engineering builds may legitimately use:

- draft/review BOM snapshots;
- unresolved/conditional substitutions under engineering authority;
- one-off component quantities;
- destructive tuning/test consumption;
- non-saleable prototype output;
- project/cost-center demand.

Those freedoms must not weaken production WO controls.

## Order type

Use explicit:

```text
order_type = engineering_prototype
```

or a dedicated `prototype_build` aggregate built on the same execution primitives.

Do not infer prototype status from warehouse name, remark or zero price.

## Configuration snapshot

Prototype may snapshot:

- draft/review E05 EBOM/MBOM candidate where engineering policy permits;
- source EDA/import revision/hash;
- internal product/material candidate;
- engineering change/deviation context;
- planned quantity.

It must store the exact snapshot/IDs used and never follow later draft edits retrospectively.

If a draft BOM itself is mutable, freeze a build-specific immutable requirement snapshot at prototype release/start.

## Stock behavior

Prototype materials still use:

```text
E02 reservations
E03 allocation/scan
E02 issue / return / scrap movements
```

No special direct inventory adjustment path.

Engineering/project reservations reduce ATP according to policy.

## Custody / project context

Optional structured references:

```text
project_id / project_code
engineering_owner
custodian
cost_center
purpose
```

A lab shelf is physical location, not project ownership.

## Prototype output

Output is explicitly:

```text
engineering / non-production
```

by default.

It must not automatically enter normal saleable finished-goods ATP.

Future E07 can attach prototype serial/test evidence; future sample/evaluation flow may explicitly transfer an engineering unit into a controlled sample/loan process.

## Consumption accounting

Track:

- planned requirement snapshot;
- actual issue;
- returns;
- scrap/damage;
- substitutions;
- output quantity.

This gives planned-vs-actual prototype material cost later without requiring full accounting.

## Promotion to production

Never “convert” a prototype WO by changing its type to production after execution.

Production requires:

```text
released E05 configuration
 -> new production WO
```

The production WO may reference the prototype as validation/history evidence.

## Customer samples / loans

Do not overload prototype build itself with customer commercial disposition.

A built prototype may later be:

- retained as lab/golden reference;
- gifted sample;
- loaned evaluation unit;
- scrapped;
- retained for test.

Those dispositions are separate typed workflows, with E10/sample/RMA or a later engineering-asset module as appropriate.

## Tests

- prototype can use explicitly authorized draft snapshot without making it released;
- production WO still rejects draft configuration;
- prototype issue/return/scrap uses E02 and is auditable;
- prototype stock reservation reduces ATP according to policy;
- prototype output excluded from normal saleable ATP by default;
- later draft BOM edits do not rewrite build snapshot;
- changing prototype type to production after execution rejected;
- production WO can reference prototype evidence without inheriting mutable draft authority.

## Acceptance

R&D can build and cost experimental units with controlled stock evidence while production configuration control remains strict and prototype output cannot silently masquerade as released saleable product.
