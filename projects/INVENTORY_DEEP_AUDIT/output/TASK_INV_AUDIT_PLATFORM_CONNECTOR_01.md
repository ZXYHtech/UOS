# TASK_INV_AUDIT_PLATFORM_CONNECTOR_01 — Marketplace / Platform Connector Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed platform accounts/credentials/SKU mappings, order adapters, Taobao API client, synchronization path and platform sync status handling.

## 1. Executive conclusion

Inventory Lite already contains a real adapter-oriented platform foundation. It should not be characterized as a mock-only multi-platform layer: the pinned code includes a concrete Taobao API client and a Taobao order synchronization path.

However, maturity is asymmetric. Taobao is materially implemented; website/Pinduoduo/manual/image adapters mostly establish normalized order contracts, not equivalent full bidirectional connector capability.

The current platform flow is best described as **operator-triggered marketplace ingestion plus human confirmation**, not yet an omnichannel synchronization engine.

## 2. Existing architecture worth preserving

### Platform account model

`platform_accounts` tracks:

- platform type
- account/shop
- linked warehouse
- integration/status flags
- last sync time/error
- default sync mode

### Credentials separated from account metadata

`platform_api_credentials` stores provider/app key/app secret/session token/endpoint separately from ordinary account fields. API-facing configuration can mask secret values.

The long-term secret-at-rest strategy still requires improvement, but separation is a sound starting point.

### Normalized order adapters

`ORDER_ADAPTERS` defines normalized ingress contracts for:

- website API
- Taobao API
- Pinduoduo API
- manual entry
- image recognition

This is exactly the abstraction boundary that should be retained as new channels are added.

## 3. Taobao integration evidence

`TaobaoApiClient` contains a concrete API endpoint and order fields.

`PlatformAccountService.sync_taobao_orders()`:

- resolves account/client configuration;
- selects a created-time range;
- pages through results;
- normalizes marketplace data;
- checks whether a formal Taobao order already exists;
- checks whether a pending recognition/import record already exists;
- stores imported channel orders as `recognition_tasks` in `needs_confirmation` state;
- updates account sync success/error metadata;
- writes operation logs.

This is a sensible safety-first ingress model.

## 4. Duplicate protection is useful but not yet a universal ingestion ledger

For Taobao, duplicate avoidance uses formal order lookup plus a synthetic raw key such as:

```text
taobao_api:<order_no>
```

inside recognition-task data.

That is better than blindly inserting every synchronization result.

For long-term reliability, create a dedicated immutable external-event/import identity:

```text
platform_account_id
external_object_type
external_object_id
external_version_or_modified_at
payload_hash
first_seen_at
last_seen_at
processing_status
canonical_object_id
```

with a unique business key.

This avoids overloading recognition fields as connector state and allows safe replay/update detection.

## 5. Required omnichannel dimensions not yet complete

A mature commerce connector layer must independently model:

### Inbound order synchronization

- new orders
- paid/unpaid
- cancelled
- modified address
- quantity/SKU changes where platform permits
- partial shipment
- platform-closed orders

### Outbound fulfilment synchronization

- logistics company/tracking number
- shipment acknowledgement
- retry/error state
- platform acceptance response

### Inventory publication

- local physical stock
- reservable ATP
- channel stock cap
- safety buffer
- per-channel allocated quantity
- publish success/failure/version

### Refund/return synchronization

- refund application
- refund completion
- return received
- exchange/reshipment
- financial reconciliation

### Product/SKU mapping

- marketplace product ID
- platform SKU ID
- enterprise SKU
- bundle/component mapping
- lifecycle/disabled state
- mapping revision/conflict state

Current schema has a useful `platform_sku_mappings` foundation, but the full lifecycle above is not yet closed.

## 6. Critical architecture decision: synchronization must become background work

Current operator-triggered sync is appropriate at today's maturity. As platform automation increases, synchronous HTTP-triggered synchronization becomes fragile.

Reuse the OCR durable-worker pattern:

```text
platform_sync_job
  -> durable DB record
  -> worker claims job
  -> fetches page/window
  -> stores raw external observations
  -> normalizes idempotently
  -> creates/updates review items
  -> records cursor/error/retry
```

Scheduler options:

- systemd timer
- server-side long-running worker
- cron for low frequency

GitHub Actions is explicitly forbidden as a required synchronization scheduler.

## 7. Cursor strategy

Time-window polling alone becomes risky with large order volumes or platform clock/update behavior.

For each connector store:

- last successful cursor/window
- overlap safety window
- last remote modified timestamp
- page/cursor token if supported
- last full reconciliation time

Always make reads replay-safe so overlap does not create duplicates.

## 8. Source-of-truth policy

Before adding bidirectional sync, define field ownership.

Example:

| Data | Authority |
| --- | --- |
| marketplace order ID/status | platform observation |
| internal warehouse assignment | Inventory Lite |
| internal material mapping | Inventory Lite |
| tracking number | Inventory Lite then acknowledged by platform |
| published channel stock | calculated locally, remote acknowledgement recorded |
| receiver/address before fulfilment | platform, with immutable snapshot at shipment |

Without ownership rules, two-way synchronization can create update loops.

## 9. Stock publication must wait for reservation semantics

Do not automatically publish `quantity_available` as channel sellable stock.

Future sellable/ATP calculation needs at least:

```text
physical usable stock
- reservations
- quality hold
- safety buffer
- other channel commitments
- production/project allocations where applicable
= channel publishable quantity
```

This dependency links the connector task directly to the stock-model redesign.

## 10. Error and reconciliation model

Each outbound/inbound operation needs:

- pending
- processing
- succeeded
- retryable failure
- permanent/manual-review failure
- attempt count
- next retry time
- last error code/message
- remote response/reference
- idempotency key

Periodic reconciliation should compare local canonical state against remote state rather than trusting only incremental callbacks/polls.

## 11. Security

Priorities:

- encrypt/protect API secrets at rest;
- mask them in reads/logs;
- record rotation/expiry where platform supports it;
- restrict credential-management permission separately from ordinary account viewing;
- never copy platform secrets into job payloads/log files;
- bound API timeouts and retries.

## 12. Priorities

### P0

1. document Taobao as implemented versus other adapters as partial/contract-only;
2. create durable external-object/import identity rather than using recognition raw text as long-term sync ledger;
3. server-side idempotency for connector ingest and fulfilment acknowledgement;
4. do not publish raw available quantity until reservation/ATP model exists;
5. move recurring sync ownership to an independent server worker/timer.

### P1

1. standardized connector interface: authenticate/test/pull orders/push fulfilment/publish inventory/reconcile;
2. connector-specific cursor/checkpoint state;
3. retry/error/dead-letter workflow;
4. SKU mapping conflict UI;
5. channel inventory buffer/cap rules.

### P2

1. Pinduoduo/website connector implementations to parity where business value justifies them;
2. webhook ingestion where supported;
3. refunds/returns reconciliation;
4. channel economics ingestion for contribution margin.

## 13. Acceptance signals

Repository-local tests should prove:

- replaying the same external order never creates a second canonical order;
- a changed remote order is detected as a revision/update rather than silently duplicated;
- failed sync can retry after process restart;
- checkpoint advances only after durable successful processing;
- stock publication uses ATP policy rather than raw balance;
- no required scheduler or test depends on GitHub Actions.

## 14. Preliminary maturity

- adapter boundary: 4/5
- Taobao inbound implementation: 3.5/5
- other channel implementation parity: 1.5–2/5
- duplicate protection: 3/5
- durable generic sync ledger: 1/5
- background scheduling/retry: 1.5/5
- bidirectional fulfilment/inventory sync: 1.5/5
- reconciliation/refunds: 1/5

## 15. Core recommendation

Keep the adapter architecture and human-confirmation safety boundary. Evolve it into a durable, replay-safe connector worker system one capability at a time; do not create a giant omnichannel rewrite.