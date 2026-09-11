# TASK_INV_IMPL_E09_S05 — Fulfilment Outbox, Remote Acknowledgement & Replay Safety

## Status
`DESIGN_READY_BLOCKED_BY_E01_E02_GATES`

## Objective
Decouple committed local shipment truth from unreliable remote platform APIs.

## Flow

```text
local shipment committed
 -> E01 outbox event
 -> connector delivery job
 -> remote fulfilment API
 -> acknowledgement / retry / manual review
```

Local stock history is never rolled back merely because the remote API is temporarily unavailable.

## Idempotency
Use stable outbound action identity based on account + local shipment + generation/event identity. Replaying a job after process/server restart must not duplicate remote fulfilment.

## Evidence
Persist:

- local shipment reference;
- platform account/external order;
- outbound event identity;
- request/response summary or artifact reference;
- attempt history;
- remote acknowledgement identifier/time;
- terminal/manual-review reason.

## Retry boundary
Safe network/429/5xx failures may retry under E01 policy. Ambiguous timeout after possible remote acceptance must reconcile before sending a second consequential request when the platform lacks a strong idempotency contract.

## Tests
- local shipment remains committed through remote outage;
- worker restart resumes delivery;
- repeated job cannot double-ship remotely;
- ambiguous timeout routes to reconciliation/manual review when needed;
- acknowledgement links back to exact local shipment.

## Done
Remote fulfilment is eventually consistent and replay-safe without coupling marketplace availability to the local stock transaction.