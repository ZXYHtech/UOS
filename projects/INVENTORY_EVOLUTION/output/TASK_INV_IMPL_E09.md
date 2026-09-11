# TASK_INV_IMPL_E09 — Omnichannel Durable State Reconciliation

## Status
`DESIGN_READY_BLOCKED_BY_E02_E01_GATES`

E09 is design-only while earlier runtime gates remain open.

## Objective
Evolve the existing `ORDER_ADAPTERS`, platform accounts, SKU mappings and Taobao sync into a durable multi-account omnichannel reconciliation layer.

Target sequence:

```text
remote observation
 -> external-object ledger
 -> canonical internal order / mapping
 -> E02 reservation + ATP
 -> durable outbox publication/fulfilment
 -> remote acknowledgement
 -> periodic reconciliation
 -> actionable exception
```

## Existing assets to preserve
- `platform_accounts` and separated credentials;
- `platform_sku_mappings`;
- normalized `ORDER_ADAPTERS` and `normalize_order_payload(...)`;
- current Taobao integration;
- human confirmation for uncertain OCR/manual order paths;
- shipment/order operation logs.

## Core boundaries

```text
E01 = idempotency / durable jobs / outbox / retry
E02 = stock reservation and ATP truth
E09 = remote identity, connector state, publication and reconciliation
E10 = customer-service / RMA workflow
E11 = channel settlement/economics
```

Connectors never calculate their own authoritative stock from raw inventory rows.

## Canonical external identity
Use durable account-scoped identity:

```text
platform_account_id + object_type + external_id
```

For orders/lines, never rely only on platform type + displayed order number.

## External object ledger
Target `external_objects` stores:

- platform account;
- object type;
- external id/version;
- remote modified time;
- payload hash/raw payload reference;
- first/last seen timestamps;
- processing status;
- canonical internal reference.

Replay of the same observation is safe; changed payload becomes a new observation/revision, not a duplicate business row.

## SKU mapping lifecycle
Mapping states:

```text
unmapped
matched
ambiguous
manually_overridden
invalid
retired
```

Historical order lines keep the mapping/identity used at ingestion time. A later SKU remap does not rewrite old orders.

## Order state reconciliation
Normalize remote order events such as created/paid/address-change/cancelled/closed/refund. Local state-transition policy decides what is still mutable.

A late remote address change must never rewrite a shipment already committed.

## Central ATP and channel publication
Only E02 can calculate authoritative ATP. E09 applies per-account/channel publication policy:

```text
publishable ATP
- channel holdback/buffer
-> desired remote quantity
```

Persist desired quantity separately from remote acknowledged quantity and publication status.

## Outbound fulfilment
Local shipment commits first, then E01 outbox/worker performs remote fulfilment API calls. Remote failure does not roll back local stock history.

Every outbound action has a stable idempotency key and acknowledgement record.

## Cancellation/refund/return
Cancellation policy branches by local state: unreserved/reserved/picking/shipped.

Financial refund and physical return remain separate. Physical return routes to E10 RMA/returns once implemented.

## Reconciliation
Periodic account reconciliation covers:

- open order state;
- shipment acknowledgement;
- refund state;
- SKU mapping conflicts;
- desired vs acknowledged remote stock;
- listing/product enabled state where supported.

Differences become explicit exceptions; reconciliation does not silently overwrite whichever side differs.

## Connector contract
Standard capability-oriented interface:

```text
test_credentials
pull_orders / pull_changes
push_fulfilment
push_inventory
pull_refunds
reconcile
```

Capabilities may differ by platform; unsupported operations are explicit.

## Runtime
Use E01 durable jobs and server-owned workers/systemd/cron. No required connector path depends on GitHub Actions.

## Definition of done
- remote replay cannot duplicate canonical orders/actions;
- multiple shops on one platform cannot collide on order identity;
- one unit of E02 ATP cannot be independently published as free stock to several channels outside policy;
- fulfilment retry survives restart without duplicate remote shipment;
- local desired stock and remote acknowledged stock are separately visible;
- remote cancellation branches safely by local fulfilment state;
- reconciliation surfaces mismatches with source evidence;
- connector health/cursor/retry state is visible per platform account.