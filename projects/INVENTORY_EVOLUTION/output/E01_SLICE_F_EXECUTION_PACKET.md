# E01 Slice F Execution Packet — Bounded Modular-Monolith Extraction

## Status

`READY_TO_START_ONLY_AFTER_E01_SLICE_E_MERGE`

This is a sequence of **behavior-preserving refactor PRs**, not one large rewrite.

## 1. Entry gate

Required before F1:

```text
E00 merged
E01 Slice A-E merged
full Release Gate PASS
```

Do not create one long-lived branch containing all F waves.

Recommended branches:

```text
impl/e01-domain-backup
impl/e01-domain-pricing
impl/e01-domain-procurement
impl/e01-domain-integrations
```

Each branch starts from the main that contains the prior accepted slice.

# 2. Global extraction rule

For every moved symbol:

```text
characterize current behavior with tests
 -> create target module
 -> move implementation without semantic change
 -> add thin compatibility re-export if needed
 -> redirect internal imports
 -> prove startup/API parity
 -> prove no duplicate implementation remains
 -> full Release Gate
```

Forbidden:

```text
copy old implementation and leave both copies live
change formula while moving pricing code
change purchase/stock state semantics while moving procurement
change connector business behavior while moving adapters
extract Inventory/Stock before E02
```

## 3. Import direction

Allowed:

```text
server/routes -> platform -> domains -> shared database primitives
integrations -> platform jobs/outbox + bounded domain contracts
```

Forbidden:

```text
domains/* -> inventory_app.server
platform/* -> concrete domain implementation
pricing -> procurement internals
procurement -> HTTP handler classes
```

No circular dependency may be hidden with unexplained runtime imports.

# F1 — Backup / Recovery

## 4. Purpose

Use the E00 seams as the lowest-risk proof of domain extraction.

Suggested target:

```text
inventory_app/domains/backup/
  __init__.py
  runtime.py
  manifest.py
  recovery.py
  service.py
```

Only add a routes/helper module if needed; do not manufacture files just to match a theoretical layout.

Existing authoritative primitives to move/re-export:

```text
inventory_app/backup_runtime.py
inventory_app/backup_manifest.py
inventory_app/recovery_verifier.py
BackupService subset in services.py
```

Deployment scripts/tools continue to call stable public interfaces.

## 5. F1 invariants

No change to:

- SQLite Online Backup API behavior;
- snapshot file safety;
- off-host `.inventory-backup-target` requirement;
- manifest/checksum format;
- recovery smoke/integrity semantics;
- exact server-code prechange snapshot;
- E00 production preflight order.

Existing E00 tests remain the authoritative regression set.

## 6. F1 compatibility

Temporary old imports may re-export:

```python
from inventory_app.domains.backup... import ...
```

but the original implementation body must not remain duplicated.

## 7. F1 exit

- one authoritative backup implementation;
- E00 tests unchanged/green;
- deployment tools continue to work;
- full Release Gate PASS.

# F2 — Pricing

## 8. Purpose

Create a clean commercial boundary before E11-S01/S02.

Suggested target:

```text
inventory_app/domains/pricing/
  __init__.py
  service.py
  formulas.py
  queries.py
```

Move only what is already pricing-owned:

```text
PricingService
pure arithmetic helpers
price-list/rule query helpers
```

Keep route parsing in server until a bounded route adapter move is clearly worthwhile.

## 9. Critical commercial rule

**Do not fix `margin_percent` in F2.**

F2 must prove exact parity with current behavior, including current legacy naming/arithmetic.

Only after F2 merges does E11-S01 explicitly introduce corrected terminology/new target-margin semantics.

Reason:

```text
refactor diff should answer “where is the code?”
E11 diff should answer “what does the formula mean?”
```

Do not combine these questions.

## 10. F2 tests

Characterize and preserve:

- price-list selection;
- rule priority/effectivity;
- current legacy `margin_percent` calculation;
- deal-price revision behavior;
- current API response shape;
- existing permission behavior.

Add pure formula characterization tests before moving helpers.

## 11. F2 exit / immediate bridge

After F2 PASS + merge:

```text
E11-S01 formula/terminology safety
 -> E11-S02 floor/override safety
```

Do not wait for F3/F4 if E11 early is otherwise ready; pricing safety is intentionally an early bridge before E02.

# F3 — Procurement

## 12. Purpose

Move procurement business logic behind a domain façade while preserving caller-owned transactions.

Suggested target:

```text
inventory_app/domains/procurement/
  __init__.py
  service.py
  queries.py
```

Move:

```text
ProcurementService
purchase read/query projections closely owned by procurement
```

## 13. F3 transaction rule

Existing request/Action Policy/idempotency supplies the SQLite connection.

Procurement domain must not open a second connection for:

```text
PO transition
purchase receipt
receipt items
purchase-price history
existing stock posting
operation audit
```

No hidden `commit()` may be introduced.

## 14. F3 semantic freeze

Do not change:

- purchase states;
- approval permissions;
- partial receipt behavior;
- freight/other landed-cost allocation;
- purchase-price history;
- current InventoryService posting.

E02/E03 later replace stock/receiving authority deliberately.

## 15. F3 tests

Preserve existing:

- PO create/submit/approve/reject state tests;
- partial/full receive;
- landed cost;
- purchase history;
- Slice C purchase idempotency;
- warehouse scope/permission;
- full Release Gate.

# F4 — Integrations

## 16. Purpose

Separate provider-facing code after E01 jobs/outbox exist, without changing omnichannel semantics yet.

Suggested target:

```text
inventory_app/domains/integrations/
  __init__.py
  accounts.py
  order_adapters.py
  taobao.py
  jobs.py
  outbox_handlers.py
```

Move authoritative implementations such as:

```text
OrderAdapter
WebsiteOrderAdapter
TaobaoOrderAdapter
PddOrderAdapter
ManualOrderAdapter
ImageRecognitionOrderAdapter
ORDER_ADAPTERS
TaobaoApiClient
PlatformAccountService
```

Only move worker/outbox handlers that already exist from E01 substrate/pilots.

## 17. F4 boundary

Do not implement E09 features here:

- no external-object ledger redesign;
- no central ATP publication;
- no new reconciliation policy;
- no remote-order state model rewrite;
- no connector cursor migration unless an already-existing behavior is simply relocated.

F4 answers only:

> where does provider-specific integration code live?

E09 later answers:

> what is the correct omnichannel business contract?

## 18. Secrets/network rule

Provider code must:

- obtain credentials from existing approved configuration path;
- never log secrets into jobs/outbox/errors;
- use E01 durable job/outbox for new asynchronous delivery paths;
- never mutate Stock directly as a provider-specific shortcut.

## 19. Structural tests for every F wave

Add a lightweight static/AST check if practical:

```text
fail if inventory_app/domains/** imports inventory_app.server
report duplicate moved class names still implemented in services.py
```

At minimum review and tests must prove:

- only one implementation body remains;
- compatibility façade is import-only;
- module imports at startup;
- server/API behavior remains unchanged.

## 20. Central-file reduction acceptance

Each move should produce a measurable net reduction in central concentration:

```text
services.py implementation lines decrease
server.py domain/business branching decreases where routes are moved
```

Do not move code into a new file while leaving equivalent logic in the old file and call that modularization.

## 21. Rollback per wave

Because each wave is behavior-preserving:

```text
revert the extraction PR
```

Database rollback is not expected for F1-F4 unless a separate migration was explicitly introduced; normally there should be none.

Do not remove evidence tables introduced in E01 A-E.

## 22. E01 completion rule

E01 is complete when:

```text
Slice A context/policy
Slice B idempotency
Slice C real pilots
Slice D jobs/worker/retry
Slice E outbox/correlation
Slice F bounded extraction
```

all have passed the repository-local Release Gate and merged in bounded PRs.

Then the next mandatory sequence is:

```text
E11-S01 pricing semantics
 -> E11-S02 floor/override safety
 -> E02 Stock Ledger/Reservation
```

Do not skip directly to E02 before the pricing-safety bridge.
