# Purchase Partial Receipt Landed-cost Safety Review

## Status

`STATIC_RISK_CONFIRMED_CODE_PATH_REQUIRES_RUNTIME_FIXTURE_BEFORE_E02_H`

This is a bounded commercial/cost correctness review discovered while preparing E02-H procurement-stock migration.

It must not be hidden inside the stock-ledger refactor.

## 1. Observed current code behavior

The audited `ProcurementService.receive()` flow currently does, for each receipt transaction:

```text
base = sum(current_receipt_qty * PO_line_unit_price)
extra = purchase_order.freight_amount + purchase_order.other_amount

for each current receipt line:
  allocation = current_receipt_line_base / current_receipt_base * extra
  landed_unit_cost = unit_price + allocation / current_receipt_qty
  insert purchase_receipt_item
  insert material_purchase_prices(... landed_unit_cost ...)
```

The `freight_amount` and `other_amount` values are PO-header values and the current receive path does not appear to decrement a remaining allocable amount after a partial receipt.

## 2. Static risk

For a PO received in more than one partial receipt, this code shape can allocate the **full PO-level freight/other amount on every receipt**.

Example:

```text
PO goods value = 1000
PO freight = 100

receipt 1 = half the goods
receipt 2 = remaining half
```

If each receipt allocates the full `100` header freight, recorded landed acquisition cost may include `200` freight in total.

That would overstate:

- `material_purchase_prices.landed_unit_cost`;
- reference purchase cost;
- later product cost estimates;
- margin/profitability evidence that consumes those values.

## 3. Why E02-H must not silently fix this

E02-H owns **physical stock receipt truth**.

Changing commercial cost allocation in the same PR would mix:

```text
stock-ledger migration
+
commercial cost formula change
```

and make rollback/review ambiguous.

Therefore E02-H must either:

1. enter only after a separate landed-cost safety fix is merged, or
2. prove with deterministic fixtures that the current interpretation is actually intentional/correct.

Do not casually preserve a known duplicated cost bug merely for parity if it contaminates new authoritative evidence.

## 4. Required fixture before E02-H

Create a deterministic local test with:

```text
PO with >= 2 lines or one line
ordered quantity split across >= 2 receipts
non-zero freight_amount
non-zero other_amount optional
```

Assert final total acquisition allocation according to approved policy.

At minimum compute:

```text
sum(receipt item allocated_cost)
```

and compare against the intended PO-level allocable amount.

The test must also cover:

- first partial receipt;
- second/final receipt;
- retry/idempotency;
- receipt reversal/correction policy if currently supported;
- zero base-value edge case.

## 5. Policy decision needed

Before fixing, define how PO-level freight/other cost should be allocated when receipts are partial.

Safe common options include:

### Option A — allocate proportionally to ordered/commercial line base across PO

Each receipt receives only the fraction of PO-level extra cost corresponding to the receipt's share of the final ordered base.

### Option B — allocate on final receipt after actual total known

Earlier receipts use provisional/direct price; final close distributes/adjusts acquisition cost.

### Option C — receipt-specific actual charge evidence

If freight/other values are actually receipt-level charges, move/record them at receipt/landed-cost allocation identity rather than repeatedly reading one PO-header amount.

The application must not guess accounting policy.

## 6. Recommended implementation boundary

Create a dedicated small branch/PR before E02-H, for example:

```text
impl/purchase-landed-cost-partial-receipt-safety
```

Scope only:

- deterministic allocation policy;
- partial receipt regression fixture;
- existing historical data remains unchanged unless an explicit reviewed repair tool is added;
- no stock-ledger migration in this PR.

No new Epic is required; this is a prerequisite defect/safety correction discovered by implementation preparation.

## 7. Historical evidence

Do not automatically rewrite old `material_purchase_prices` rows.

If the fixture confirms historical duplication is possible, add a read-only audit report:

```text
PO
receipts
PO header freight/other
sum allocated receipt cost
expected allocation under approved policy
potential over-allocation
```

Then decide separately whether historical repair is worth doing.

Any repair must be explicit, auditable and backed up first.

## 8. E02-H gate

E02-H may start only when one of these is recorded:

```text
LANDED_COST_FIXTURE = PASS / current semantics intentionally correct
```

or

```text
LANDED_COST_FIX = merged + Release Gate PASS
```

Do not let stock migration make this cost ambiguity harder to isolate later.
