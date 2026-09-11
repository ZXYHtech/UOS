# TASK_INV_IMPL_E11_S02 — Floor Price, Deal-price Override & Commercial Approval Safety

## Status

`DESIGN_READY_AFTER_E11_S01`

## Objective

Prevent a manually entered or rule-derived selling price from crossing a configured commercial floor without explicit authority, reason and audit evidence.

This story builds on the current useful price-revision behavior instead of replacing it.

## Confirmed current behavior

Pinned baseline: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Current pricing already supports a `floor` material price type and `PricingService.record_deal_price()` already requires a `change_reason` and writes immutable `order_item_price_revisions` plus an operation log.

Current manual deal-price write roughly does:

```text
load order item
 -> require change_reason
 -> validate non-negative list/deal price
 -> update order item price snapshot
 -> append order_item_price_revisions
 -> log pricing.deal.update
```

What is missing is a deterministic floor-resolution and approval policy before the price is accepted.

## Core commercial invariant

For each consequential quote/deal price:

```text
resolved selling price
>= effective commercial floor
```

unless all of the following are true:

```text
explicit override permission
+ explicit override reason
+ explicit floor evidence snapshot
+ explicit actor/time/audit trail
```

A user being allowed to edit prices is not automatically sufficient authority to sell below floor.

## Floor resolution

The pricing domain should expose one deterministic function/service contract:

```text
resolve_floor_price(material_id, quantity, price_list/channel/customer context, on_date)
```

Resolution output must identify:

```text
floor_amount
currency
source_type
source_id
validity/effective evidence
resolution_reason
```

If multiple floor records can apply, use a documented deterministic precedence rule. Never select an arbitrary row based on database return order.

## Floor versus cost

A commercial floor is not the same thing as product cost.

Examples:

```text
reference cost = 80
commercial floor = 92
target margin price = 100
```

The floor may incorporate policy/risk/channel strategy. Do not derive a hidden floor from cost unless a future explicit policy says so.

S01 owns margin/markup formulas; S02 owns price-acceptance control.

## Permission model

Keep existing broad permissions for ordinary price management where possible, but add a dedicated high-risk capability, e.g.:

```text
pricing.floor_override
```

Do not overload `pricing.manage` so every price editor automatically gets below-floor authority.

Action Policy should describe the consequential override action explicitly, e.g.:

```text
pricing.deal.override_floor
  auth = required
  permission = pricing.floor_override
  target = authoritative order item / quote line
  state = price still editable
  audit = required
  idempotency = required for API retry safety
```

## Decision states

A price evaluation should produce a machine-readable decision:

```text
PASS
WARN
BLOCK
OVERRIDE_REQUIRED
OVERRIDDEN
```

Suggested semantics:

- `PASS`: price meets/exceeds floor.
- `WARN`: non-blocking policy notice unrelated to floor breach.
- `BLOCK` / `OVERRIDE_REQUIRED`: price is below floor and caller lacks completed override evidence.
- `OVERRIDDEN`: below-floor price accepted with authorized evidence.

The UI must not implement the decision by itself; server/domain policy is authoritative.

## Snapshot / audit evidence

When a deal price is recorded, extend the price snapshot/revision evidence additively with fields such as:

```text
floor_amount
floor_currency
floor_source_type
floor_source_id
floor_resolution_snapshot
below_floor
floor_override_required
floor_override_by
floor_override_reason
floor_override_at
pricing_semantics_version
```

Historical price revisions remain immutable.

Do not retroactively invent floor evidence for old orders. Old rows can remain `floor_evidence = NULL/unknown`.

## Existing revision history must be preserved

The current `order_item_price_revisions` mechanism is a strong foundation.

S02 should strengthen it, not replace it with mutable “latest approval” fields only.

For every accepted price change:

```text
before price snapshot
+ after price snapshot
+ change reason
+ floor decision evidence
+ override evidence if applicable
```

must survive as append-only history.

## Quote path and order-item path

Apply the same domain policy to both:

1. pricing quote result used to propose a price;
2. actual order-item deal-price recording.

A quote may surface an `OVERRIDE_REQUIRED` proposal, but committing that price to an order must independently validate the current floor again. Do not trust stale client-side quote results.

## Stale decision protection

If the floor changes between quote and order-price commit:

```text
server re-resolves floor at commit time
```

The stored snapshot records the floor used for the final decision.

Do not let the client submit a floor amount as authoritative input.

## Idempotency / transaction rule

Once E01-S04 exists, consequential price commits use business-operation idempotency.

Within one SQLite transaction:

```text
idempotency admission
+ load authoritative order item/state
+ resolve current floor
+ permission/policy decision
+ update order price snapshot
+ append price revision
+ operation log
+ operation result receipt
COMMIT
```

Replay returns the original receipt rather than writing a duplicate price revision.

## Validation

At minimum reject:

- negative prices;
- invalid currency/context mismatch;
- missing required override reason;
- below-floor price without override permission;
- stale/deleted order item;
- price change in a business state where pricing is locked;
- client-supplied fake floor evidence.

The exact lock point for completed/fulfilled orders must be explicitly derived from current order lifecycle; if historical correction is required, it should be a separate controlled correction action rather than normal editing.

## Tests

Deterministic tests must prove:

1. price above floor succeeds without override;
2. price equal to floor succeeds;
3. price below floor is rejected for ordinary `pricing.manage` user;
4. below-floor price succeeds only with `pricing.floor_override` + reason;
5. accepted override writes revision + audit + floor snapshot;
6. replay with same operation key writes no second revision;
7. same operation key with a different price/reason conflicts;
8. client-submitted floor amount cannot override server resolution;
9. changing master floor after a historical order does not rewrite old floor evidence;
10. stale quote floor is re-resolved at commit;
11. old historical price revisions remain readable with unknown floor evidence;
12. full `tools/verify_release.py` passes.

## UI requirements

Show clearly:

```text
建议/成交价
有效底价
与底价差额
是否需要审批
审批人/原因（如已覆盖）
```

Avoid generic red/green styling without text/state because operators need to understand *why* a price is blocked.

## Rollout

Recommended order:

```text
S01 formula terminology safety
 -> floor resolver + tests
 -> dedicated override permission
 -> quote-side decision evidence
 -> order-item commit enforcement
 -> idempotency integration
 -> UI state
 -> full Release Gate
```

Start in warning/shadow mode only if production data quality needs observation, but do not call the story complete until server-side enforcement is actually active.

## Rollback

On application rollback:

- keep new audit/revision data intact;
- do not delete override evidence;
- if old code cannot interpret new decision fields, it may ignore additive JSON fields but must not overwrite them destructively;
- if dedicated permission rows were added, preserve them unless a controlled reverse migration is explicitly required.

## Acceptance

S02 is complete when below-floor selling can no longer occur silently through normal manual price editing or quote application, while legitimate authorized exceptions remain possible and fully auditable.

## Dependencies

- E00 complete.
- E01 Action Policy / idempotency available for final consequential-write integration.
- E11-S01 formula semantics complete.
- Prefer pricing domain extraction from E01-S10 first.

## Non-goals

- no full quote-approval workflow engine;
- no channel settlement ledger yet;
- no realized order-profit accounting;
- no AI auto-pricing;
- no automatic floor derivation from future work-order actual cost.