# E11 Slice A Execution Packet — Pricing Semantics / Margin vs Markup Safety

## Status

`READY_TO_IMPLEMENT_AFTER_E01_PRICING_EXTRACTION`

This packet turns `TASK_INV_IMPL_E11_S01.md` into a code-level implementation handoff.

## Entry gate

Do not implement until:

```text
E00 Release Gate = PASS and merged
AND E01 Action Policy / idempotency primitives are merged
AND E01 pricing extraction is merged with behavior parity
AND current main passes tools/verify_release.py
```

Start from then-current `main`.

Recommended branch:

```text
impl/e11-pricing-semantics
```

## Confirmed current code facts

Pinned baseline behavior:

```python
PricingService.RULE_TYPES = {
    "fixed_price",
    "discount_percent",
    "discount_amount",
    "margin_percent",
}
```

Current rule evaluation:

```text
margin_percent
 -> deal = list_price * (1 + value / 100)
```

Therefore the existing stored type is **legacy markup on the selected base/list price**, not target gross margin.

Current `pricing_rules.result_type` is free `TEXT`; there is no schema CHECK requiring a migration merely to accept a new semantic type.

Current `CostService.material_cost()` returns a reference/engineering estimate with fields including:

```text
total_cost
cost_source = bom | purchase_average
last_purchase_at
components
operations
```

It is not realized order COGS and must never be labeled that way.

## Hard compatibility invariant

Historical rows with:

```text
result_type = margin_percent
```

must produce the **exact same numeric result** before and after this slice.

Forbidden:

```text
keep stored enum = margin_percent
but silently change formula to cost / (1 - pct)
```

That would silently rewrite commercial history.

## Target pricing semantic vocabulary

Read compatibility must understand:

```text
fixed_price
discount_percent
discount_amount
margin_percent                         # historical stored enum only
legacy_markup_percent_on_base_price    # explicit semantic alias for display/API evidence
target_gross_margin_percent            # new authoritative semantic
cost_markup_percent                    # explicit optional cost-backed semantic
```

### Creation policy

New API/UI creation must **not** offer ambiguous `margin_percent`.

Recommended creatable types:

```text
fixed_price
discount_percent
discount_amount
target_gross_margin_percent
cost_markup_percent
```

Historical `margin_percent` remains editable only through a deliberate legacy-compatibility path that keeps its arithmetic unchanged and visibly labels it as legacy.

## Pure formula module

After E01 pricing extraction, own all formula math in:

```text
inventory_app/domains/pricing/formulas.py
```

Functions:

```python
apply_discount_percent(base_price, percent)
apply_discount_amount(base_price, amount)
apply_markup_on_base_price(base_price, percent)
apply_markup_on_cost(cost, percent)
price_for_target_gross_margin(cost, percent)
gross_margin_percent(price, cost)
markup_percent(price, cost)
```

No SQL, HTTP or provider access is allowed in this module.

### Formula definitions

```text
discount_percent:
  selling = base * (1 - pct/100)

legacy markup on base:
  selling = base * (1 + pct/100)

cost markup:
  selling = cost * (1 + pct/100)

target gross margin:
  selling = cost / (1 - pct/100)
```

Proof fixture:

```text
cost = 80
20% cost markup = 96
20% target gross margin = 100
```

The test suite must contain this pair.

## Money / rounding policy

Do not use this slice to silently alter historical rounding.

For legacy paths, preserve the current application-compatible `money()` behavior unless a separately reviewed monetary-precision migration is approved.

Pure formula tests must assert exact application outputs at the existing 4-decimal boundary.

Do not combine a Decimal/UOM accounting rewrite with this safety fix.

## Cost-basis resolver

Create a bounded pricing helper, for example:

```text
resolve_reference_cost(conn, material_id, on_date=None)
```

Output:

```json
{
  "amount": 80.0,
  "currency": "CNY",
  "basis_type": "reference_estimate",
  "source": "bom",
  "source_as_of": "...",
  "evidence": {...}
}
```

Initial implementation may adapt `CostService.material_cost()` but must label the result accurately:

```text
REFERENCE_ESTIMATE
```

Never:

```text
ACTUAL_COGS
REALIZED_MARGIN
```

### Missing/invalid cost behavior

For `target_gross_margin_percent` and `cost_markup_percent`:

```text
no acceptable cost basis
 -> deterministic BLOCK / AppError
```

Do not substitute:

- zero;
- list price;
- stale UI value;
- client-supplied cost;
- an unrelated material price.

## Service evaluation contract

Pricing quote evaluation should normalize each rule into an explicit semantic contract before calculating.

Conceptually:

```python
semantic = normalize_rule_semantics(rule)
```

For historical rows:

```json
{
  "stored_result_type": "margin_percent",
  "semantic_type": "legacy_markup_percent_on_base_price",
  "semantics_version": 1,
  "legacy_semantics": true
}
```

For new target-margin rule:

```json
{
  "stored_result_type": "target_gross_margin_percent",
  "semantic_type": "target_gross_margin_percent",
  "semantics_version": 2,
  "legacy_semantics": false
}
```

## Quote API additive evidence

Do not remove existing response fields.

Add evidence such as:

```text
result_type
semantic_type
pricing_semantics_version
legacy_semantics
calculation_inputs
calculation_result
cost_basis (only when used)
```

Existing callers that only use `deal_unit_price` remain compatible.

## Rule creation / editing behavior

### New rule

Reject:

```text
result_type = margin_percent
```

with a clear message directing the caller to an explicit type.

### Existing legacy rule

An operator may read it and, if legacy maintenance remains necessary, update non-semantic fields while preserving:

```text
stored type = margin_percent
formula = base-price uplift
```

Do not automatically convert it to target margin.

A future explicit migration/conversion action may create a new rule version after human review.

## UI wording

Use explicit Chinese labels:

```text
折扣率
基准价加价率（旧规则）
成本加成率
目标毛利率
```

Legacy rows display a visible compatibility badge/warning.

Do not label `margin_percent` as “目标毛利率”.

## No schema migration in Slice A

Expected migration impact:

```text
NONE
```

Reason:

- `pricing_rules.result_type` is already free text;
- historical rows must remain unchanged;
- formula/API/UI changes are sufficient for the new semantic type.

If implementation discovers an unanticipated restrictive schema in the then-current main, stop and split a migration PR rather than silently changing this packet.

## Exact implementation order

### A1 — parity characterization

Before changing formulas, add tests proving current behavior:

```text
legacy margin_percent 20% on list 100 => 120
```

### A2 — pure formulas

Create `formulas.py` and deterministic unit tests.

### A3 — semantic normalization

Introduce legacy alias + semantics versioning without enabling new rule creation yet.

Run full gate.

### A4 — cost basis adapter

Add reference-cost resolver and rejection behavior when cost is unavailable.

### A5 — new explicit rule types

Enable:

```text
target_gross_margin_percent
cost_markup_percent
```

Block new ambiguous `margin_percent` creation.

### A6 — API/UI evidence

Add labels/evidence without removing legacy fields.

### A7 — full regression

Run focused tests + complete Release Gate.

## Deterministic tests

Create a focused test module, e.g.:

```text
tools/test_pricing_semantics.py
```

Must prove:

1. legacy `margin_percent` result is byte-for-byte/numerically compatible at the existing money precision;
2. base 100 + legacy 20% => 120;
3. cost 80 + cost markup 20% => 96;
4. cost 80 + target gross margin 20% => 100;
5. base 100 - discount 20% => 80;
6. target margin >= 100% is rejected;
7. negative/invalid percentages follow explicit validation;
8. target-margin evaluation without cost basis is rejected;
9. new ambiguous `margin_percent` creation is rejected;
10. historical legacy rule remains readable/editable without semantic mutation;
11. API evidence distinguishes stored type from semantic type;
12. existing core pricing workflow regression remains unchanged;
13. `tools/verify_release.py` passes.

## Rollback safety

The dangerous rollback case is:

```text
new target_gross_margin_percent rows exist
 -> deploy old application that does not understand them
```

Old baseline behavior could silently fall through and return list price.

Therefore before new semantic types are used in production, one of these must be true:

1. rollback target already contains read/evaluation support for the new type; or
2. deployment rollback preflight detects active new types and blocks rollback until a controlled compatibility decision is made.

Never silently rewrite new rules back to `margin_percent`.

## Review checklist

Reviewer must verify:

- [ ] legacy `margin_percent` formula unchanged;
- [ ] no historical rows bulk-updated;
- [ ] new creation cannot use ambiguous `margin_percent`;
- [ ] target margin is cost-backed;
- [ ] cost basis is labeled estimate/reference, not actual COGS;
- [ ] formulas are pure and deterministic;
- [ ] no DB migration hidden in this slice;
- [ ] existing API fields remain compatible;
- [ ] rollback compatibility is explicitly checked;
- [ ] full Release Gate passes.

## Exit gate

Slice A is complete only when historical prices are unchanged, new margin/markup semantics are mathematically explicit, missing cost cannot be guessed, and full local regression passes.

Then unlock:

```text
E11 Slice B — Floor / Override Safety
```
