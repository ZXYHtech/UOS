# E03 Slice G Execution Packet — Mobile / Handheld Guided Scan UX

## Status

`READY_AFTER_E03_A_TO_F_SERVER_CONTRACTS`

## Entry gate

Requires stable server contracts for typed scan, putaway, picking and count. Mobile work does not precede server authority.

Branch:

```text
impl/e03-mobile-scan-ux
```

Migration:

```text
NONE expected
```

## Purpose

Make common warehouse tasks fast enough to be scan-first while preserving one rule:

> client speed/cache/offline convenience never becomes stock authority.

Reuse current web/mobile surfaces. Do not create a third warehouse application solely for E03.

## Shared interaction state machine

Base sequence:

```text
TASK
 -> LOCATION
 -> MATERIAL
 -> QUANTITY
 -> CONFIRM
```

Task type may specialize the expected sequence, but the current expected scan type is always explicit.

### Putaway

```text
PUTAWAY TASK
 -> source receiving location
 -> material
 -> destination location
 -> quantity
 -> confirm
```

### Pick

```text
PICK/SHIPMENT TASK
 -> source location
 -> material
 -> quantity
 -> confirm picked evidence
```

### Transfer receive

```text
TRANSFER
 -> destination/staging location
 -> material
 -> received quantity
 -> confirm
```

Existing partial/exception semantics remain available.

### Count

```text
COUNT TASK
 -> location
 -> material
 -> observed quantity
 -> save observation
```

Observation never adjusts stock.

## Client/server contract

Client may cache:

- task display data;
- expected line IDs;
- location/material labels;
- typed scan lookup hints;
- current state-machine step.

Every consequential command sends:

```text
authoritative task ID
expected/current task version or state token where supported
idempotency key
resolved/scanned canonical IDs + raw scan evidence
quantity
```

Server reloads:

- current task state;
- user permission/scope;
- E02 reservation/balance;
- E03 location validity;
- remaining executable quantity.

Stale cache cannot authorize a write.

## Duplicate camera frame protection

Use both layers:

1. client debounce for rapid repeated camera frames;
2. server E01 idempotency for actual command execution.

Client debounce alone is never correctness evidence.

## Feedback contract

Show explicit textual state for:

```text
scan accepted
wrong object type
wrong warehouse/location
wrong material
quantity too high
already processed / replay returned prior receipt
task changed by another operator
network/server failure
manual review/exception required
```

Audio/haptic feedback may supplement text but never replace the reason.

## Offline boundary

Allowed offline:

- view cached instructions;
- hold non-authoritative draft notes/observations where explicitly supported;
- capture raw scans for operator review.

Forbidden offline authoritative actions:

- receive stock;
- putaway movement;
- shipment issue/completion;
- transfer receipt;
- inventory adjustment;
- reservation consume/release;
- approved count adjustment.

On reconnect, consequential commands are not blindly replayed from a generic queue. Client first queries operation/task status; existing idempotency receipt decides whether action already succeeded.

## Existing mobile-offline boundary

Legacy `mobile-offline` remains a convenience/read surface unless a future explicit lease protocol is designed. E03 does not grant it authoritative inventory write capability.

## Security

- server permissions and warehouse scope are authoritative;
- hidden UI controls are not authorization;
- task prefetch does not reveal cross-warehouse/customer data beyond user scope;
- raw scan values are bounded before logging/storage;
- no credentials/secrets in client cache.

## Tests

1. state machine rejects unexpected scan type;
2. duplicate camera frames lead to at most one consequential command;
3. same server idempotency key returns prior receipt;
4. stale task version/state forces refresh/reconciliation;
5. operator cannot execute a task outside warehouse scope;
6. wrong location/material error is visible and does not fake local success;
7. cache/prefetch unavailable still permits safe server-driven execution;
8. reconnect checks status before any retry;
9. count observation remains non-mutating;
10. offline queue cannot issue stock-changing API calls automatically;
11. existing mobile task flows remain usable;
12. `tools/test_client_routing.js` plus full repository Release Gate pass.

## Rollback

Revert to existing mobile/web task UX while server-side E02/E03 domain behavior remains intact. No data/schema rollback expected.

## Stop conditions

Stop if:

- client cache is treated as task/stock authority;
- generic offline replay can duplicate a consequential command;
- mobile path calls a different stock mutation API than desktop/server domains;
- task completion can be faked locally while server rejected it.

## Exit / completion

Operators can perform putaway/pick/transfer/count primarily by guided scans on current mobile surfaces, with all consequential validation remaining server-side.