# TASK_INV_AUDIT_OMNICHANNEL_01 — Omnichannel Order, Inventory and SKU Synchronization Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed the existing order adapters, Taobao connector, platform account/SKU mapping model, order fulfilment, pricing and stock semantics together with W2 findings on platform integration and reservation gaps.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite already has the right architectural seed for omnichannel commerce: a normalized order-adapter boundary, real Taobao ingestion, platform-account metadata, SKU mapping and explicit shipment sync state. The current weakness is that those pieces are still oriented around **operator-triggered ingestion plus later fulfilment**, not around a durable cross-channel state machine.

A mature omnichannel layer must coordinate five independent concerns:

1. external order observations;
2. canonical internal order state;
3. reservation/ATP and channel stock publication;
4. outbound fulfilment/refund state;
5. periodic reconciliation.

The largest blocker is still authoritative reservation/ATP. The system should not publish raw `quantity_available` to multiple channels because the same physical quantity can otherwise be promised several times.

Preliminary omnichannel maturity: **2.0/5**.

## 2. Existing strengths worth preserving

Keep these concepts:

- `platform_accounts` for shop/account identity;
- `platform_api_credentials` separated from ordinary account metadata;
- `platform_sku_mappings` for remote-product/SKU to internal-material mapping;
- `ORDER_ADAPTERS` normalized ingest contract;
- concrete Taobao API client and sync logic;
- manual/image/website/Pinduoduo adapter contracts;
- human-confirmation boundary before uncertain recognized orders become formal orders;
- `platform_sync_status` style states on fulfilment paths;
- operation logs and shipment-ledger references.

Do not replace these with platform-specific branches scattered through the whole application.

## 3. Canonical external-object ledger

The connector layer needs a generic durable identity independent of OCR/recognition tasks.

```text
external_objects
  id
  platform_account_id
  object_type: order | order_line | refund | shipment | product | sku | inventory
  external_id
  external_version
  modified_at_remote
  payload_hash
  raw_payload_ref
  first_seen_at
  last_seen_at
  processing_status
  canonical_type/id

UNIQUE(platform_account_id, object_type, external_id)
```

This makes repeated polling/webhooks replay-safe and allows a changed remote object to be processed as a revision rather than a duplicate.

## 4. Inbound order state

The internal order model should preserve both:

- the latest known marketplace state;
- the immutable history of observations that caused internal changes.

Important remote events:

- created;
- paid/unpaid;
- address changed;
- SKU/quantity changed where allowed;
- cancelled;
- partially fulfilled;
- closed;
- refund requested/completed.

Do not let a late remote update silently overwrite an already shipped address snapshot or fulfilled line. State-transition policy must decide what is still mutable.

## 5. Shop/account identity

Order uniqueness should always include the platform account/shop boundary.

Recommended canonical identity:

```text
platform_account_id + external_order_id
```

and, where needed:

```text
platform_account_id + external_order_id + external_line_id
```

This is safer than using `platform_type + order_no` alone because one platform may contain multiple shops with overlapping numbering conventions.

## 6. SKU mapping lifecycle

SKU mapping is not a one-time lookup. Add controlled states:

```text
unmapped
matched
ambiguous
manually_overridden
invalid
retired
```

Mapping records should preserve:

- remote product/SKU;
- internal enterprise SKU/material;
- bundle/sales-BOM relation;
- effective time/revision if mappings can change;
- who confirmed override;
- last remote observation;
- conflict reason.

A changed marketplace SKU must not silently remap historical orders.

## 7. Reservation and ATP

Omnichannel inventory publication must depend on one common ATP calculation.

Suggested model:

```text
qualified physical stock
- sales reservations
- work-order/project reservations
- quarantine/non-saleable stock
- safety buffer
- channel-specific holdback
= global publishable ATP
```

Then allocate channel publication policy:

```text
channel_publish_qty = min(global ATP policy share, channel cap)
```

The system should never let each connector independently calculate stock from raw warehouse quantity.

## 8. Channel stock publication

Introduce a durable publication record:

```text
channel_inventory_publications
  platform_account_id
  mapping_id
  calculated_at
  source_inventory_version
  desired_qty
  remote_ack_qty
  status
  attempt_count
  last_error
  published_at
```

This enables queries such as:

- what did we intend to publish?
- what did the platform acknowledge?
- is the remote quantity stale?
- which local stock event invalidated the last publication?

## 9. Inventory buffers and risk policy

Support per-channel rules:

- fixed safety buffer;
- percentage holdback;
- channel maximum stock;
- priority channel;
- low-stock freeze;
- made-to-order listing policy;
- serial/high-value product policy.

Do not encode these as one global `platform_stock_cap` if several shops/channels need different strategies.

## 10. Outbound fulfilment synchronization

Shipping should create a durable outbox event after local transaction commit.

```text
local shipment commit
 -> integration_outbox
 -> connector worker
 -> remote shipment API
 -> acknowledgement
 -> success / retry / manual review
```

Required idempotency key example:

```text
platform_account_id:shipment_id:generation
```

Remote API failure must never roll back already committed local stock history.

## 11. Cancellation conflicts

Critical scenario:

```text
remote cancellation arrives
while local order is reserved/picking/shipped
```

Policy should branch:

- before reservation: cancel order;
- reserved: release reservation;
- picking: stop task and reconcile picked stock;
- shipped but remote says cancelled: after-sales/return exception;
- platform refund without physical return: financial event only unless policy says otherwise.

Do not process all cancellations with one delete/reset action.

## 12. Refund and return synchronization

Separate financial refund from physical return.

Possible sequence:

```text
refund requested
 -> approved/rejected
 -> refund paid

return requested
 -> parcel in transit
 -> received
 -> inspection
 -> restock/quarantine/repair/scrap
```

The two may occur together or separately depending on platform rules. Omnichannel integration should normalize both into the internal RMA/returns domain.

## 13. Reconciliation

Incremental sync alone is insufficient.

Run periodic reconciliation on:

- open order states;
- shipment acknowledgement;
- refund status;
- SKU mapping state;
- published stock quantity;
- remote product enabled/disabled state.

Store reconciliation differences as actionable exceptions rather than silently overwriting whichever side differs.

## 14. Connector worker architecture

Standard interface:

```text
Connector
  test_credentials()
  pull_orders(cursor)
  pull_order_changes(cursor)
  push_fulfilment(event)
  push_inventory(publication)
  pull_refunds(cursor)
  reconcile(scope)
```

Workers own retries/cursors and are executed through server-local mechanisms such as systemd/cron/long-running worker. Required operation must not depend on GitHub Actions.

## 15. Cursor/checkpoint policy

Each account needs:

- last successful cursor/window;
- overlap safety window;
- last remote modified timestamp;
- last full reconciliation timestamp;
- retry/dead-letter state;
- health status.

Advance checkpoint only after durable local processing succeeds.

## 16. Observability

Per account dashboard should show:

- last successful pull;
- last successful fulfilment push;
- last stock publication;
- pending outbox count;
- retrying/dead-letter count;
- unmapped SKU count;
- reconciliation mismatch count;
- credential expiry/error;
- remote API throttling state.

This is more valuable than a single `sync_status` badge.

## 17. Priority roadmap

### P0

1. canonical external-object ledger;
2. account-scoped order identity;
3. durable sync outbox and idempotency;
4. authoritative reservation/ATP dependency;
5. channel publication records;
6. cancellation/refund state normalization;
7. reconciliation exceptions.

### P1

1. standardized connector interface;
2. per-account cursor/health;
3. Pinduoduo/website connector parity based on business value;
4. stock buffer/cap policies;
5. SKU mapping conflict UI;
6. webhook ingestion where available.

### P2

1. intelligent channel allocation based on margin/service level;
2. automatic listing pause on quality/stock risk;
3. cross-channel promotion coordination;
4. richer product-content synchronization.

## 18. Acceptance signals

- replaying the same remote event never creates duplicate canonical business records;
- two shops on the same platform cannot collide on order identity;
- remote order changes are detected as revisions/events;
- one unit of ATP cannot be independently promised to several channels;
- a shipment push failure retries after process restart without duplicate remote shipment;
- a remote cancellation releases reservation or creates after-sales exception according to local state;
- local desired stock and remote acknowledged stock are independently visible;
- periodic reconciliation can surface mismatches;
- no required sync/scheduler/retry/test path depends on GitHub Actions.

## 19. Core recommendation

Evolve the current adapter layer into a **durable omnichannel state-reconciliation system**. The key architectural sequence is external-object identity -> canonical order -> reservation/ATP -> outbox synchronization -> reconciliation, rather than adding more synchronous API calls inside the existing order handler.