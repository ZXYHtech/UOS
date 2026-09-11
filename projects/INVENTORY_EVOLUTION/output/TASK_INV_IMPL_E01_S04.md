# TASK_INV_IMPL_E01_S04 — Business Operation / Idempotency

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Make replay-sensitive business commands safe against double-click, client retry, proxy retry and timeout ambiguity.

## Migration ownership

**Proposed Migration 2** after E00 baseline migration 1:

```text
business_operations
  id INTEGER PK
  operation_key TEXT NOT NULL
  action_code TEXT NOT NULL
  actor_id INTEGER
  request_fingerprint TEXT NOT NULL
  correlation_id TEXT
  status TEXT NOT NULL
  result_type TEXT
  result_id INTEGER
  result_json TEXT
  error_code TEXT
  started_at TEXT NOT NULL
  completed_at TEXT

UNIQUE(action_code, operation_key)
```

Index status/started_at for stale-running diagnostics.

## Canonical request fingerprint

Fingerprint only stable business inputs after normalization:

- action code;
- authoritative target identity;
- quantities/lines/options that change effect;
- exclude timestamps, tracing metadata and presentation-only fields.

Hash with SHA-256 over canonical JSON.

## Semantics

Same key + same fingerprint:

- succeeded → return original receipt/result;
- running → deterministic in-progress/conflict response;
- retryable failure → controlled retry path;
- never execute side effect twice.

Same key + different fingerprint → hard idempotency conflict.

## Transaction rule

Where practical, operation admission + business mutation + success receipt are one SQLite transaction. Never mark success before the business mutation commits.

## Pilot actions

Apply first to one E01-S03 stock-affecting route, then expand to the remaining pilots.

## Tests

- repeated identical command mutates once;
- replay returns original result identity;
- same key/different payload rejected;
- failure before commit leaves no false success;
- simulated response loss followed by retry does not double-post;
- concurrent same-key attempts cannot both own execution.

## Rollback

Migration 2 is additive. On code rollback, table remains inert; do not destructively drop operation history from production.

## Acceptance

At least one consequential write path is provably exactly-once at the business-operation layer under deterministic retry tests.

## Dependencies

E01-S01, E01-S02; pilot route from E01-S03.
