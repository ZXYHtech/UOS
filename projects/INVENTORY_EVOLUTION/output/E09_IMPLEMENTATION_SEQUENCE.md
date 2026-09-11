# E09 Implementation Sequence — Omnichannel Reconciliation

## Status
`DESIGN_READY_BLOCKED_BY_E01_E02_GATES`

## Preconditions
Runtime E09 waits for:

- E01 idempotency/jobs/outbox/retry/correlation;
- E02 reservation/ATP authority;
- production backup/recovery policy and local Release Gate;
- current platform adapters kept operational during migration.

## Slice A — External-object ledger
Implement E09-S01 additively. Existing ingestion remains authoritative while ledger shadows observations.

STOP if replay/account identity cannot be proven deterministic.

## Slice B — SKU mapping lifecycle
Implement E09-S02 without rewriting existing order history.

STOP if remapping can mutate historical canonical line identity.

## Slice C — Inbound order revision policy
Implement E09-S03 first in observe/exception mode for conflicting late changes.

STOP if shipped snapshots can be overwritten.

## Slice D — Central ATP publication calculation
Implement E09-S04 desired quantity calculation/read model without remote push.

Compare desired publication to current manual/operator policy before enabling writes.

## Slice E — Inventory publication outbox pilot
Enable one platform/account using E01 outbox/jobs and remote acknowledgement records.

STOP on duplicate publication, unexplained desired/ack drift or ATP over-publication.

## Slice F — Fulfilment outbox pilot
Implement E09-S05 for one existing connector, preserving local shipment authority.

STOP on any remote duplicate-shipment path or ambiguous timeout without reconciliation.

## Slice G — Cancellation/refund policy
Implement E09-S06 with explicit state fixtures for unreserved/reserved/picking/shipped cases.

## Slice H — Periodic reconciliation
Implement E09-S07 read/exception-first. No automatic winner.

## Slice I — Connector capability/cursor/health framework
Implement E09-S08 and migrate current Taobao connector behind the standard contract without feature regression.

## Slice J — Additional channel parity
Only after the common contract is stable, add/upgrade Pinduoduo/website/other channels according to actual business value.

## Required gates per slice

```text
migration tests where applicable
+ connector replay/idempotency fixtures
+ E02 ATP/reservation regression
+ existing order/shipment regressions
+ E00 Release Gate
```

Use recorded/synthetic connector fixtures for deterministic tests. Production credentials are never required for unit correctness.

## Authority rule

```text
remote observation -> E09 reconcile/normalize
local business action -> existing domain/E02 authority
external side effect -> E01 outbox/worker
```

E09 must never become a second inventory/order truth store.