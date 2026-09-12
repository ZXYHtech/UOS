# E11 Slice B Execution Packet — Floor Price / Override Safety

## Status

`READY_TO_IMPLEMENT_AFTER_E11_SLICE_A`

This packet turns `TASK_INV_IMPL_E11_S02.md` into a code-level implementation handoff.

## Entry gate

Do not implement until:

```text
E00 merged
AND E01 Action Policy + idempotency merged
AND E11 Slice A pricing semantics merged
AND pricing domain extraction exists
AND current main passes tools/verify_release.py
```

Recommended branch:

```text
impl/e11-floor-safety
```

## Confirmed current code facts

Current pricing already provides:

```text
material_prices.price_type includes "floor"
PricingService.record_deal_price(...)
order_item_price_revisions
operation_logs
pricing.manage
```

Current deal-price write:

```text
load order item
 -> require change_reason
 -> validate non-negative list/deal price
 -> update order_items price snapshot
 -> append order_item_price_revisions
 -> write pricing.deal.update operation log
```

Missing controls:

- no authoritative server-side floor resolution before commit;
- no dedicated below-floor override authority;
- no immutable floor-decision evidence in the price revision;
- no E01 business-operation replay protection around the write.

## Migration ownership

### Proposed Migration 6

Migration 6 is a **permission data migration only**:

```text
insert permission definition:
  pricing.floor_override
```

Rules:

- do not auto-grant it to any existing role;
- preserve all existing role permissions;
- migration is idempotent/immutable/checksummed;
- rollback never deletes historical price/audit evidence;
- an operator must explicitly grant the permission later through the normal access-management path.

No new pricing evidence table is required in this slice; current immutable revision JSON + operation log + E01 business-operation receipt are sufficient.

If the then-current permission system has already introduced an equivalent dedicated capability, reuse it rather than creating a duplicate permission code.

## Action Policy contract

Add an explicit high-risk action, e.g.:

```text
pricing.deal.override_floor
```

Policy requirements:

```text
authenticated = true
permission = pricing.floor_override
authoritative target = order_item + parent order
idempotency = required
audit = required
reason = required
```

Ordinary `pricing.manage` continues to allow normal price editing but **does not imply** below-floor authority.

## Server-side floor resolver

Create a deterministic pricing-domain function, for example:

```python
resolve_floor_price(
    conn,
    *,
    material_id,
    quantity,
    price_list_id,
    on_date,
)
```

Optional channel/customer context may be included if the current pricing-list model uses it.

### Initial authoritative source

Use effective `material_prices` rows where:

```text
price_type = floor
material_id matches
price_list_id matches the authoritative quote/order pricing context
row is enabled
valid_from/valid_to include decision date
min_quantity <= quantity
```

Do not trust a client-submitted floor amount.

### Deterministic precedence

Within the same authoritative price-list context:

```text
priority DESC
min_quantity DESC
updated_at DESC
id DESC
```

The resolver returns evidence, not only a number:

```json
{
  "configured": true,
  "amount": 92.0,
  "currency": "CNY",
  "source_type": "material_price_floor",
  "source_id": 123,
  "price_list_id": 8,
  "valid_from": "...",
  "valid_to": "...",
  "priority": 10,
  "resolved_at": "..."
}
```

### No configured floor

Do not invent a floor from cost.

Return an explicit state such as:

```text
NO_FLOOR_CONFIGURED
```

Whether production policy later requires every sellable item to have a floor is an operator/business decision, not something this slice should silently assume.

## Decision model

Use a machine-readable result:

```text
PASS
NO_FLOOR_CONFIGURED
OVERRIDE_REQUIRED
OVERRIDDEN
BLOCK
```

### PASS

```text
deal_price >= effective_floor
```

### NO_FLOOR_CONFIGURED

No applicable configured floor exists. Preserve explicit evidence that no floor was available; do not present this as “floor passed”.

### OVERRIDE_REQUIRED

```text
deal_price < floor
AND caller lacks completed authorized override evidence
```

### OVERRIDDEN

```text
deal_price < floor
AND pricing.floor_override is authorized
AND non-empty reason is supplied
```

### BLOCK

Invalid context, currency mismatch, locked order state, stale/deleted target or other deterministic policy failure.

## Commit-time revalidation

Quote-side floor evidence is advisory only.

When `record_deal_price` commits:

```text
load authoritative order item + order
 -> resolve current pricing context
 -> resolve current floor again
 -> evaluate current permission/action policy
 -> commit price/revision/audit/idempotency receipt
```

Never trust:

- client floor amount;
- stale quote decision;
- old browser permission state;
- old floor source id without re-resolution.

## Order-state safety

Normal deal-price editing must not silently rewrite commercial history after fulfillment is final.

At implementation time, characterize current order/shipment states and define explicit editable states.

Conservative rule:

```text
completed / cancelled / deleted / archived-like terminal states
 -> normal price edit BLOCK
```

If historical correction is required, create a distinct controlled correction action rather than weakening ordinary editing.

Do not guess terminal-state semantics; add deterministic tests from current order lifecycle fixtures.

## E01 idempotency integration

Consequential price commit is Class A / `atomic_local`.

One SQLite transaction must contain:

```text
BEGIN IMMEDIATE
 -> business_operations admission
 -> load authoritative order item/order
 -> re-resolve floor
 -> permission / action policy
 -> update order_items price snapshot
 -> append order_item_price_revisions
 -> operation log
 -> business_operations succeeded receipt
COMMIT
```

No second connection may perform the price mutation.

Replay with the same operation key/fingerprint returns the original receipt and writes no second revision.

Same operation key with changed deal price or changed override reason must conflict.

## Price snapshot evidence

Extend the existing immutable `after_json` / `price_snapshot_json` evidence additively:

```text
pricing_semantics_version
floor_state
floor_amount
floor_currency
floor_source_type
floor_source_id
floor_price_list_id
floor_resolution_snapshot
below_floor
floor_override_required
floor_override_by
floor_override_reason
floor_override_at
business_operation_id / operation key reference where appropriate
```

Historical revisions stay unchanged. Do not backfill fake floor evidence.

Old rows may legitimately show:

```text
floor_state = UNKNOWN_HISTORICAL
```

## Existing audit reuse

Preserve:

```text
order_item_price_revisions
operation_logs
```

Do not introduce a mutable “current override” record that replaces revision history.

`operation_logs` describes the action; the immutable price revision describes the commercial before/after evidence; E01 `business_operations` provides replay identity/result receipt.

## API / UI behavior

Quote and order-edit responses should expose:

```text
suggested/deal price
effective floor
floor state
delta to floor
override required
legacy/new pricing semantics
```

When override is required, UI may request:

```text
override reason
```

but the server remains authoritative.

Display textual state, not color alone.

## Implementation order

### B1 — Migration 6 permission only

Add `pricing.floor_override` definition with no default role grant.

Run migration/integrity tests.

### B2 — Floor resolver

Implement deterministic resolution and tests with multiple candidate rows.

### B3 — Decision function

Pure-ish domain policy that compares deal price versus resolved floor and caller authority.

### B4 — Quote-side evidence

Expose PASS/NO_FLOOR/OVERRIDE_REQUIRED without committing anything.

### B5 — Commit enforcement

Integrate into `record_deal_price` through E01 Action Policy/idempotency.

### B6 — UI override interaction

Only after server enforcement is working.

### B7 — full Release Gate

No shadow-only completion claim; story is complete only after server-side enforcement is active.

## Deterministic tests

Create a focused suite, e.g.:

```text
tools/test_pricing_floor_safety.py
```

Must prove:

1. above-floor price passes;
2. equal-to-floor passes;
3. below-floor price fails for ordinary `pricing.manage` user;
4. `pricing.floor_override` is not implicitly inherited by every price editor;
5. below-floor succeeds with dedicated permission + explicit reason;
6. override writes immutable floor evidence to price revision;
7. operation log and idempotency receipt are written once;
8. same idempotency key/same payload writes no duplicate revision;
9. same key/different price conflicts;
10. same key/different override reason conflicts;
11. client-supplied fake floor is ignored;
12. floor change between quote and commit is re-resolved at commit;
13. deterministic precedence chooses the documented floor row;
14. `NO_FLOOR_CONFIGURED` remains explicit;
15. historical revisions remain readable without fabricated evidence;
16. terminal/locked order state rejects ordinary deal-price editing;
17. full `tools/verify_release.py` passes.

## Concurrency tests

Two simultaneous below/at-floor edits against the same order item must not create ambiguous latest state.

Use E01 idempotency + explicit SQLite transaction ownership.

For same operation key:

```text
exactly one revision
exactly one operation receipt
same returned result
```

For different operation keys racing on the same item, define and test current-state ordering/lock behavior. Do not rely on last-writer-wins without evidence.

If necessary, require expected revision/version in the command to detect stale edits rather than silently overwriting a newer commercial decision.

## Rollback

Schema impact is additive permission data only.

On application rollback:

- preserve permission definition;
- preserve floor evidence in revision JSON;
- preserve override audit/history;
- old readers may ignore additive JSON keys but must not destroy them;
- never delete override evidence merely because older code cannot display it.

If a rollback target does not enforce floor policy, production rollback must be treated as a commercial-control regression and require explicit approval or temporary write disablement.

## Review checklist

- [ ] dedicated override permission exists and is not auto-granted;
- [ ] floor resolver uses authoritative DB rows, never client amount;
- [ ] deterministic precedence is tested;
- [ ] floor is distinct from cost;
- [ ] quote result cannot authorize commit by itself;
- [ ] commit re-resolves current floor;
- [ ] ordinary price edit cannot bypass terminal-state rules;
- [ ] idempotency covers revision/audit/result receipt in one transaction;
- [ ] historical rows remain untouched;
- [ ] full Release Gate passes.

## Exit gate

Slice B is complete only when a normal price editor can no longer silently commit below a configured floor, while explicitly authorized exceptions remain possible and fully auditable.

Then mandatory next wave:

```text
E02 Stock Ledger / Reservation / ATP
```
