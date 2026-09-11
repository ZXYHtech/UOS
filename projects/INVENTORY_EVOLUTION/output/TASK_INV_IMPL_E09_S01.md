# TASK_INV_IMPL_E09_S01 — External Object Ledger & Account-scoped Identity

## Status
`DESIGN_READY_BLOCKED_BY_E01_E02_GATES`

## Objective
Create replay-safe durable identity for every remote marketplace object before it touches canonical business state.

## Identity
Canonical remote key:

```text
platform_account_id + object_type + external_id
```

Supported initial object types: order, order_line, shipment, refund, product, sku, inventory_publication.

## Ledger evidence
Persist external version/remote modified timestamp, payload hash, raw payload reference where retained, first/last seen time, processing status and canonical internal reference.

## Rules
- identical replay is a no-op/idempotent observation;
- changed payload/version produces a new observation/revision path;
- two shops on the same platform cannot collide;
- a remote object may be observed before canonical mapping succeeds;
- raw payload retention follows privacy/retention policy and is checksum-bound when stored as artifact.

## Tests
- replay same order twice -> one canonical order;
- same external order id in two accounts -> two distinct external identities;
- changed remote version is detected;
- failed canonical processing can resume without losing observation;
- checkpoint is not advanced before durable processing succeeds.

## Done
Every connector event can be replayed and reconciled without guessing whether the remote object was already processed.