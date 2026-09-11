# TASK_INV_IMPL_E09_S08 — Connector Capability, Cursor & Account Health

## Status
`DESIGN_READY_BLOCKED_BY_E01_GATE`

## Objective
Give each platform account a standard operational contract for capabilities, checkpoints, retries and health without forcing every platform to support identical APIs.

## Connector capability contract

```text
test_credentials()
pull_orders(cursor/window)
pull_order_changes(cursor/window)
push_fulfilment(event)
push_inventory(publication)
pull_refunds(cursor/window)
reconcile(scope)
```

Unsupported capabilities are explicit, not simulated.

## Checkpoint policy
Per account keep:

- last successful cursor/window;
- overlap safety window;
- last remote modified timestamp;
- last successful pull/push/reconciliation;
- last full reconciliation timestamp;
- retry/dead-letter state;
- throttling/rate-limit state where known;
- credential/auth health.

Checkpoint advances only after durable local processing succeeds.

## Webhooks
When a platform supports webhooks, treat them as fast observations into the same external-object ledger. They do not replace periodic reconciliation.

## Runtime
Polling, webhook processing, retry and reconciliation run through E01 durable jobs/workers/systemd-owned runtime. No GitHub Actions dependency.

## Operator view
Per account show at least:

- credential health;
- last order sync;
- last fulfilment push;
- last inventory publish;
- pending/retrying/dead-letter jobs;
- unmapped/ambiguous SKU count;
- reconciliation mismatch count;
- rate-limit/API error status.

## Tests
- checkpoint never advances past failed durable processing;
- overlapping pull windows do not duplicate canonical objects;
- unsupported capability returns explicit state;
- webhook replay is idempotent;
- account health changes on auth/rate-limit/retry/recovery events.

## Done
Every platform account has an observable, restart-safe sync lifecycle and clear capability boundaries.