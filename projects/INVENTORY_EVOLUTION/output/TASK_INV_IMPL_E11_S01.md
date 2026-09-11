# TASK_INV_IMPL_E11_S01 — Pricing Formula Semantics & Legacy Rule Safety

## Status

`DESIGN_READY_AFTER_E01_PRICING_EXTRACTION`

## Objective

Correct the commercial meaning of margin/markup terminology **without silently changing the result of any existing pricing rule**.

This story is intentionally placed early in the implementation tranche because the current pricing engine is useful and the semantic defect is high-impact but technically bounded.

## Confirmed current behavior

Pinned baseline evidence: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

`PricingService` currently declares:

```text
RULE_TYPES = fixed_price | discount_percent | discount_amount | margin_percent
```

and currently evaluates:

```text
margin_percent => deal = list_price * (1 + value / 100)
```

That is **not** target gross-margin pricing. It is a percentage uplift on the selected base/list price.

## Canonical formulas

The domain must define these concepts separately and test them with examples where they produce different answers.

### Discount percent

```text
selling_price = base_price × (1 - discount_pct)
```

### Markup on cost

```text
selling_price = cost × (1 + markup_pct)
```

### Markup on base/list price

Legacy current behavior:

```text
selling_price = base_price × (1 + markup_pct)
```

This is not standard cost markup; name it explicitly if retained.

### Gross margin

```text
gross_profit = selling_price - cost

gross_margin_pct = gross_profit / selling_price
```

Target gross-margin price:

```text
selling_price = cost / (1 - target_margin_pct)
```

with:

```text
0 <= target_margin_pct < 1
cost >= 0
```

### Markup versus margin proof case

For cost = 80 and 20%:

```text
20% cost markup => 96
20% target gross margin => 100
```

A regression suite must use such non-equal examples so terminology mistakes cannot hide behind coincidental values.

## Non-destructive legacy strategy

Existing stored rules using `result_type='margin_percent'` must **retain their historical/current arithmetic** until explicitly migrated by an operator-reviewed change.

Never deploy code that keeps the old stored enum but suddenly evaluates it using target-gross-margin math.

Preferred transition:

```text
legacy stored type: margin_percent
semantic alias: legacy_markup_percent_on_base_price
calculation: unchanged
new type: target_gross_margin_percent
calculation: authoritative_cost / (1 - pct)
```

New UI/API creation should stop offering ambiguous `margin_percent` once the new contract is live.

Historical rows remain readable and visibly labeled as legacy semantics.

## Pricing formula module

After E01-S10 pricing extraction, pure calculations belong in:

```text
inventory_app/domains/pricing/formulas.py
```

Suggested pure functions:

```text
apply_discount_percent(base_price, percent)
apply_discount_amount(base_price, amount)
apply_markup_on_base_price(base_price, percent)
price_for_target_gross_margin(cost, percent)
gross_margin_percent(price, cost)
markup_percent(price, cost)
```

No database/network access belongs in these functions.

Use a single money/rounding policy already compatible with the application; do not scatter Python float/round choices across routes and UI.

## Authoritative cost requirement

`target_gross_margin_percent` is invalid unless an explicit cost basis is available.

The quote result must identify at least:

```text
cost_amount
cost_source
cost_as_of / effective evidence where available
```

Current recursive BOM/purchase-derived cost is an **estimated/reference cost**, not realized order COGS. The UI/API must not label it as actual realized profit.

If no acceptable cost exists:

```text
reject target-margin rule evaluation
```

Do not silently use zero, stale placeholder cost, list price, or another price as cost.

## Schema / migration decision

This story should avoid a destructive migration.

Two safe options, in preference order:

1. If `pricing_rules.result_type` is free text without a restrictive CHECK, introduce the new enum value in application validation only and preserve legacy rows unchanged.
2. If schema validation constrains the enum, use the next immutable numbered migration to widen allowed semantics without rewriting old rows.

Do not bulk-update historical `margin_percent` rows merely to rename them unless the migration records provenance and the arithmetic remains exactly unchanged.

## API contract

Pricing quote responses should expose semantic evidence, e.g.:

```text
result_type
result_semantics_version
base_price
cost_basis (when used)
calculation_inputs
calculation_result
legacy_semantics=true/false
```

Exact payload shape may remain backward compatible by adding fields rather than removing existing ones.

## UI contract

Human-facing terms must distinguish:

```text
折扣率
基准价加价率（旧规则）
成本加成率
目标毛利率
```

Do not show all of these as “利润率/毛利率”.

Legacy rules should show a warning/badge that their historical calculation is preserved.

## Tests

Deterministic local tests must prove:

1. current legacy `margin_percent` fixture returns exactly the pre-change value;
2. cost 80 + target gross margin 20% returns 100;
3. cost 80 + cost markup 20% returns 96;
4. 20% discount on 100 returns 80;
5. target margin 100% or greater is rejected;
6. negative invalid margin/markup inputs follow explicit validation policy;
7. target-margin rule with no authoritative cost is rejected;
8. historical rule snapshot/result remains unchanged when master pricing data changes;
9. rule serialization clearly identifies legacy versus new semantics;
10. full `tools/verify_release.py` passes.

## Rollout

Recommended sequence:

```text
E01 pricing extraction with parity only
 -> S01 formula unit tests
 -> add new semantic type
 -> preserve legacy evaluator
 -> update API evidence
 -> update UI wording
 -> full Release Gate
```

## Rollback

Application rollback must remain able to read existing legacy rules.

If new `target_gross_margin_percent` rules have been created, rolling back to a version that cannot understand them requires either:

- block rollback until those rules are disabled/converted through a controlled operation, or
- keep forward-compatible parser support in the rollback target.

Never mutate the new rules silently during rollback.

## Acceptance

S01 is complete only when:

- historical pricing results do not change unintentionally;
- ambiguous `margin_percent` cannot be created as if it were target gross margin;
- target gross-margin arithmetic is mathematically correct and cost-backed;
- UI/API terminology makes margin versus markup distinguishable;
- deterministic tests and the full local Release Gate pass.

## Dependencies

- E00 complete.
- E01-S01/S02 execution contracts available.
- Prefer E01-S10 pricing extraction first so formula changes land in a bounded pricing module.

## Non-goals

- no realized order profitability ledger yet;
- no work-order actual cost;
- no channel fee accounting;
- no accounting/GL;
- no dynamic AI pricing.