# TASK_INV_IMPL_E05_S08 — Legacy BOM Compatibility, Where-used and Cost-source Safety

## Status

`DESIGN_READY_BLOCKED_BY_E05_CONTROLLED_BOM`

## Objective

Introduce controlled EBOM/MBOM without breaking current fulfilment/cost behavior, while making every BOM-based query explicit about which BOM semantics/revision it uses.

## Legacy roles

### `material_bom`

Keep as sales/fulfilment bundle semantics during E05.

It answers roughly:

```text
what stock components are required when a sellable SKU ships?
```

It is not automatically migrated to EBOM/MBOM.

### `project_bom_lines`

Keep as project/import/cost-oriented historical source/staging.

Rows may become reviewed candidates for draft EBOM import, but are never silently marked released.

## Compatibility adapters

During coexistence expose explicit APIs/services such as conceptually:

```text
get_sales_bom(...)
get_engineering_bom(revision_id=...)
get_manufacturing_bom(revision_id=...)
```

Ban ambiguous new calls such as generic `get_bom(parent)` when business meaning matters.

## Cost-source naming

Every cost result must name source semantics:

```text
sales_bundle_estimate
engineering_ebom_estimate
manufacturing_mbom_standard_estimate
work_order_actual   [later E06/E11]
```

Do not show all as one generic `total_cost` without source/revision metadata.

A controlled BOM estimate includes exact `bom_revision_id`.

## Where-used

Provide deterministic reverse query:

```text
component material
 -> BOM revision lines
 -> EBOM/MBOM revision
 -> parent material / part revision
 -> released/draft/effective status
```

Filters:

- engineering vs manufacturing;
- current effective vs historical;
- released vs draft;
- parent product.

Where-used becomes a required input to ECO impact analysis.

## Sales/engineering divergence

It must be possible for:

```text
sales kit changes
```

to occur without changing:

```text
released EBOM/MBOM
```

and vice versa.

Tests must protect this separation.

## Migration dashboard/report

Provide read-only classification of current BOM data:

```text
sales/fulfilment confirmed
engineering candidate
ambiguous
project/import only
```

Human review determines whether a controlled EBOM seed is created.

No historical release date/revision is invented.

## API/UI labeling

Screens/reports must visibly label:

- BOM type;
- revision;
- status;
- effective state;
- source/ancestry;
- whether data is legacy/uncontrolled.

Do not display legacy `material_bom` beside a released MBOM without semantic labeling.

## Tests

- current shipment sales-BOM regression unchanged until intentional migration;
- controlled EBOM/MBOM edit does not modify `material_bom`;
- sales BOM edit does not modify released controlled BOM;
- cost API returns source type + exact revision;
- where-used includes historical and current revisions correctly;
- project BOM row does not become released without review;
- legacy ambiguous classification never auto-selects engineering truth.

## Acceptance

Controlled configuration can be introduced incrementally while existing sales fulfilment remains stable and users can always tell which BOM type/revision a cost, where-used or planning result came from.
