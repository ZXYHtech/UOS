# TASK_INV_IMPL_E03_S07 — Mobile / Handheld Scan Execution UX

## Status

`DESIGN_READY_BLOCKED_BY_E03_SCAN_AND_TASK_CONTRACTS`

## Objective

Provide a fast guided mobile/handheld workflow for receiving, putaway, picking, transfer and counting while keeping authoritative validation on the server.

## Principle

Fast UX does not mean offline authoritative stock writes.

The mobile client may cache task context and lookup data for responsiveness, but every consequential warehouse command is confirmed by server-side Action Policy + state + scope + idempotency + E02 movement/reservation checks.

## Interaction model

The same scan field should remain focused through the task and use a state machine such as:

```text
TASK
 -> LOCATION
 -> MATERIAL
 -> QUANTITY
 -> CONFIRM
```

The expected next scan type is explicit and context-sensitive.

## Initial flows

### Putaway

```text
open/scan putaway task
 -> scan receiving location
 -> scan material
 -> scan destination location
 -> confirm quantity
 -> server posts E02 movement
```

### Pick

```text
open/scan shipment/pick task
 -> scan suggested source location
 -> scan material
 -> confirm quantity
 -> server records pick evidence
```

### Transfer receive

```text
open/scan transfer
 -> scan destination/staging location
 -> scan material
 -> confirm received quantity
 -> preserve existing discrepancy/partial-receipt path
```

### Count

```text
open count task
 -> scan location
 -> scan material
 -> enter observed quantity
 -> save observation
```

Count never directly edits stock.

## Feedback

Provide immediate clear feedback for:

- accepted scan;
- wrong object type;
- wrong location;
- wrong material;
- duplicate scan/replay;
- quantity exceeds expected/eligible;
- server/network failure;
- task state changed by another operator.

Audio/haptic cues may supplement text, but error reason must remain visible.

## Performance

Allow safe client optimizations:

- prefetch expected task lines;
- prefetch valid location/material IDs for current task;
- retain task context;
- debounce camera duplicate frames;
- local exact lookup hints.

Never let stale client cache authorize final stock mutation.

## Offline boundary

Permitted bounded offline behavior:

- view previously cached task instructions;
- capture draft observations/scans for later review where explicitly allowed;
- queue no-op/local notes.

Not permitted without a future explicit lease/reservation protocol:

- authoritative receipt;
- authoritative putaway movement;
- shipment completion;
- inventory adjustment;
- reservation consumption.

## Existing clients

Do not create a third independent warehouse application.

Reuse current mobile/web surfaces and shared scan resolver/API contracts. The legacy local `mobile-offline` application is not an authoritative production stock client.

## Tests

- state machine only accepts expected scan types;
- duplicate camera frame does not double-submit command;
- server rejection is surfaced and local UI does not fake success;
- stale task version forces refresh/reconciliation;
- warehouse scope respected;
- prefetch/cache failure does not bypass server validation;
- count draft/observation remains non-mutating;
- online reconnect does not blindly replay already-succeeded consequential commands.

## Acceptance

A warehouse operator can complete common tasks primarily by scan with minimal typing, while the server remains the sole authority for stock-changing decisions.
