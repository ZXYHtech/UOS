# TASK_INV_IMPL_E01_S10 — Domain Module Extraction

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Reduce `server.py` / `services.py` concentration through bounded, behavior-preserving extraction while retaining the current modular-monolith deployment model.

This story is **physical modularization**, not a business redesign. E02 will redefine Inventory/Stock semantics later, so Stock must remain out of this extraction.

## Source evidence / current concentration

Current baseline `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c` still centralizes many unrelated responsibilities in `inventory_app/services.py`, while `server.py` imports a large service surface including `BackupService`, `PricingService`, `ProcurementService`, `PlatformAccountService`, `ShipmentService`, `TransferService` and others.

The existing repository already contains useful seams that should be promoted rather than rewritten:

```text
inventory_app/backup_runtime.py
inventory_app/backup_manifest.py
inventory_app/recovery_verifier.py
inventory_app/ocr_queue.py
inventory_app/image_assets.py
```

The integration area currently contains provider/adapter concepts such as:

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

The public API contract and existing service method signatures are compatibility surfaces during extraction.

## Target structure

```text
inventory_app/
  platform/
    errors.py
    request_context.py
    responses.py
    action_policy.py

  domains/
    backup/
      __init__.py
      service.py
      manifest.py
      recovery.py
      runtime.py
      routes.py

    pricing/
      __init__.py
      service.py
      formulas.py
      queries.py
      routes.py

    procurement/
      __init__.py
      service.py
      queries.py
      routes.py

    integrations/
      __init__.py
      accounts.py
      order_adapters.py
      taobao.py
      jobs.py
      outbox_handlers.py
      routes.py
```

This is a direction, not a requirement to create every file on day one. Create only files needed by moved behavior.

## Compatibility façade rule

During each extraction, old imports may temporarily remain valid through a **thin re-export only**:

```python
# services.py compatibility surface
from inventory_app.domains.pricing.service import PricingService
```

The old file must not retain a second implementation.

Allowed temporarily:

```text
old import name -> re-export -> new implementation
```

Forbidden:

```text
old implementation + copied new implementation
old route + new route both mutating the same business object
```

The compatibility façade must be deleted or deliberately retained/documented once all internal callers migrate.

## Extraction Wave 1 — Backup / Recovery

### Why first

E00 already created independent backup/recovery primitives, making this the lowest-risk proof that module movement can preserve behavior.

### Move / own

Promote the existing seams under the domain boundary without semantic changes:

```text
backup_runtime.py       -> domains/backup/runtime.py
backup_manifest.py      -> domains/backup/manifest.py
recovery_verifier.py    -> domains/backup/recovery.py
BackupService subset    -> domains/backup/service.py
backup API adapter code -> domains/backup/routes.py
```

Do not mix production-update orchestration into the domain service. `deploy/linux/*.sh` remains deployment infrastructure calling stable tools/domain primitives.

### Must remain true

- SQLite Online Backup API behavior unchanged;
- manifest/checksum semantics unchanged;
- off-host marker/fail-closed behavior unchanged;
- existing `/api/backups*` payload/status compatibility unchanged;
- E00 Release Gate still owns backup/recovery correctness.

## Extraction Wave 2 — Pricing

### Why second

Pricing is bounded and immediately supports E11-S01/S02 formula-safety work.

### Move / own

```text
PricingService                    -> domains/pricing/service.py
pure margin/markup calculations   -> domains/pricing/formulas.py
pricing read/query helpers         -> domains/pricing/queries.py
pricing HTTP adaptation            -> domains/pricing/routes.py
```

### Critical sequencing rule

Do **not** change the existing `margin_percent` behavior during the S10 move itself. First extract with parity tests. E11-S01 then changes terminology/formula behavior in a dedicated reviewable slice.

This prevents a refactor from hiding a commercial semantic change.

## Extraction Wave 3 — Procurement façade

### Move / own

```text
ProcurementService        -> domains/procurement/service.py
purchase read projections -> domains/procurement/queries.py
purchase route adapter    -> domains/procurement/routes.py
```

Keep the shared SQLite connection supplied by the request/action executor. The domain must **not** open a second connection inside a caller-owned business transaction.

The service continues to own purchase business state, while E02/E03 later own canonical stock/receiving semantics. Do not prematurely reimplement stock posting here.

## Extraction Wave 4 — Integrations

### Move / own

```text
OrderAdapter hierarchy       -> domains/integrations/order_adapters.py
TaobaoApiClient              -> domains/integrations/taobao.py
PlatformAccountService       -> domains/integrations/accounts.py
E01 durable-job handlers     -> domains/integrations/jobs.py
E01 outbox delivery handlers -> domains/integrations/outbox_handlers.py
provider-facing HTTP adapter -> domains/integrations/routes.py
```

Integration handlers depend on domain contracts and E01 job/outbox infrastructure; they must not become an alternate route to raw database mutations.

## What stays in `server.py`

After extraction, `server.py` should increasingly be limited to:

```text
HTTP server lifecycle
request parsing
session/authentication resolution
RequestContext construction
route dispatch
response serialization
static-file serving
```

It should not remain the owner of domain state machines or provider-specific business logic.

## What stays in shared database/platform code

Shared infrastructure may continue to provide:

```text
get_conn
schema/migration registry
row_to_dict / rows_to_list while still useful
now/time compatibility
low-level operation-log writer until S09 migration
```

Do not create one database repository class per table merely to imitate enterprise frameworks.

## Import-direction contract

Allowed:

```text
server/routes
  -> platform/action policy
  -> domains/*
  -> shared database primitives
```

Allowed:

```text
domains/integrations
  -> platform durable job/outbox contracts
  -> bounded domain query/command interfaces
```

Forbidden:

```text
domain module -> server.py
pricing -> procurement internals
procurement -> HTTP Handler
shared platform module -> concrete domain implementation
```

No circular import may be solved by hidden runtime imports inside functions unless explicitly documented as a temporary migration bridge.

## Transaction ownership

Module extraction must preserve transaction boundaries:

- caller supplies the existing `sqlite3.Connection` for synchronous business actions;
- domain commands operate on that connection;
- action policy/idempotency may wrap the same transaction;
- domain services must not call `commit()` when the caller owns the transaction unless the existing contract already requires it and is explicitly migrated in a separate slice;
- external side effects use Outbox, not inline network calls inside a DB transaction.

## File-level migration method

For each symbol/area:

```text
1. characterize current public/import/API behavior with tests
2. create target module
3. move implementation without semantic edits
4. add temporary re-export if required
5. redirect server/internal imports
6. run focused + full Release Gate
7. verify no duplicate implementation remains
8. only then perform any separate behavioral change
```

Never combine a large move with formula, permission, stock, state-machine or schema redesign.

## Tests / measurable acceptance

For each extraction wave:

- current public service import remains valid until deliberately retired;
- existing API regression passes unchanged;
- representative direct domain command/query test passes;
- import/startup smoke passes;
- no domain imports `server.py`;
- no duplicate class/function implementation remains;
- `tools/verify_release.py` passes;
- changed line count in `server.py` / `services.py` is a net reduction for moved behavior.

Additional structural check recommended:

```text
AST/static scan:
  fail if domains/** imports inventory_app.server
  report duplicate class names implemented in both services.py and domains/**
```

## Rollout / PR strategy

Do not implement all four waves in one PR.

Recommended sequence:

```text
S10-A backup/recovery extraction
 -> Gate
S10-B pricing extraction
 -> Gate
E11-S01/S02 pricing formula safety
 -> Gate
S10-C procurement extraction
 -> Gate
S10-D integrations extraction after S05-S09 primitives exist
 -> Gate
```

Pricing extraction may intentionally precede the rest of S10 so E11 formula safety can land on a clean boundary without waiting for every module move.

## Acceptance

S10 is complete when at least three bounded areas have a single authoritative implementation behind domain modules, central files measurably shrink, API/business behavior is unchanged, and no Stock/Inventory semantic redesign has leaked into the refactor.

## Non-goals

- no microservices;
- no network RPC between domains;
- no repository-per-domain split;
- no generic plugin marketplace;
- no ORM migration;
- no dependency-injection framework rollout;
- no Inventory/Stock extraction before E02;
- no pricing semantic change hidden inside refactoring.

## Dependencies

- E00 must be complete before runtime implementation.
- E01-S01/S02 establish common execution contracts.
- integration extraction benefits from E01-S05–S09.
- pricing extraction is the preferred bridge into E11-S01/S02.