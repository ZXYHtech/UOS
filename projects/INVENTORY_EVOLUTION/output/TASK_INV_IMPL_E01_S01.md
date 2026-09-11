# TASK_INV_IMPL_E01_S01 — Shared API / Domain Primitives

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Extract the minimum reusable request/domain scaffolding needed by later E01 stories without creating another giant utility module.

## Target modules

```text
inventory_app/platform/
  __init__.py
  errors.py
  request_context.py
  responses.py
```

## Contract

`RequestContext` carries only authoritative execution context:

- authenticated `user_id`;
- resolved permission set / role context;
- allowed warehouse scope;
- correlation ID placeholder;
- source/request metadata.

It must not trust client-supplied warehouse ownership or business state.

`errors.py` defines stable domain error classes/codes for:

- authentication required;
- permission denied;
- scope denied;
- invalid business state;
- conflict;
- validation error;
- idempotency conflict;
- retryable technical failure.

HTTP mapping remains an adapter concern; domain/service code must not return ad-hoc HTTP dictionaries.

## Data migration

None.

## Compatibility

Existing API payloads/status codes remain unchanged for routes not yet migrated. This story creates primitives only.

## Tests

- error → API status/code mapping is deterministic;
- request context cannot gain warehouse scope from request payload alone;
- correlation ID input is validated/bounded;
- existing auth/security regression still passes.

## Acceptance

At least one low-risk read route can use the shared response/error/context helpers with no observable API behavior change.

## Rollback

Pure code extraction. Revert module use; no database rollback required.

## Entry gate

Implementation starts only after E00 local Release Gate passes and Inventory PR #3 is reviewed/merged.
