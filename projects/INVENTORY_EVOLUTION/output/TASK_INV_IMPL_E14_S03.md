# TASK_INV_IMPL_E14_S03 — Constrained Read Tools, Search & Governed Natural-language Analytics

## Status
`DESIGN_READY_BLOCKED_BY_E12_METRIC_REGISTRY`

## Objective
Let AI answer operational/natural-language questions through registered business read functions rather than unrestricted SQL or database access.

## Tool style
Expose constrained functions such as:

```text
search_materials(query, scope)
get_material(id)
get_stock(material_id, scope)
get_open_demand(material_id, scope)
get_supplier_history(material_id)
get_serial_history(serial_id)
get_test_runs(serial_id)
get_governed_metric(metric_code, filters, period)
```

Never expose `execute_sql`, raw credentials or arbitrary filesystem/network execution.

## Natural-language analytics
Flow:

```text
question
 -> entity/metric/filter/time plan
 -> E12 metric registry + registered query functions
 -> deterministic query result
 -> AI explanation with formula/scope/freshness/evidence
```

Terms such as 毛利率、RMA率、库存周转、准时交付 must resolve to governed metric codes, not model-invented formulas.

## Search behavior
Use E03/E04 typed search rules:
- exact identity outranks fuzzy similarity;
- ambiguous entity match is surfaced;
- AI may rank/explain but cannot silently merge/select a consequential identity;
- returned objects remain canonical database identities.

## Limits
Tool call enforces max result count, time period, domain scope and allowed fields. Large result sets use aggregate/read-model paths rather than dumping raw rows into model context.

## Tests
- NL query cannot bypass metric registry with a custom hidden formula;
- ambiguous MPN/material result is not silently auto-selected;
- unauthorized filters/entities are rejected server-side;
- raw SQL syntax in user prompt/document cannot cause SQL execution;
- result explanation states metric definition/time scope/freshness.

## Done
Natural-language access improves usability while all factual retrieval remains deterministic, permission-scoped and governed.