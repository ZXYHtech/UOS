# TASK_INV_IMPL_E09_S04 — Central ATP & Channel Inventory Publication

## Status
`DESIGN_READY_BLOCKED_BY_E02_GATE`

## Objective
Publish channel inventory only from authoritative E02 ATP plus explicit channel policy; no connector may independently calculate stock from raw balances.

## Calculation
Conceptual input:

```text
E02 publishable ATP
- account/channel holdback or safety buffer
= desired channel quantity
```

Optional policy inputs:

- fixed holdback;
- percentage holdback;
- channel maximum;
- priority channel allocation;
- low-stock freeze;
- made-to-order policy;
- high-value/serial item policy.

## Publication record
Persist per account/mapping:

- ATP source version/time;
- desired quantity;
- remote acknowledged quantity;
- status/attempt/error;
- published/acknowledged timestamps.

Desired local state and remote acknowledged state remain separate.

## Safety
- same E02 ATP pool cannot be independently over-published outside explicit allocation policy;
- stale publication is visible;
- local stock change invalidates/recalculates desired publication but does not pretend remote already changed;
- connector push uses E01 outbox/durable job idempotency;
- remote failure leaves retry/manual-review evidence.

## Tests
- one unit cannot become one unit available in two channels without configured allocation policy;
- holdback/cap rules are deterministic;
- desired != acknowledged is visible;
- retry after restart does not create duplicate publication side effect;
- quarantine/reserved stock never enters channel publishable ATP.

## Done
All shops publish from one central stock promise model, with independent proof of what the system intended and what the platform acknowledged.