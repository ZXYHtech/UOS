# TASK_INV_IMPL_E01_S01 — Shared API / Domain Primitives

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Extract the minimum reusable request/domain scaffolding needed by later E01 stories without creating another giant utility module or a second competing authorization model.

This design is grounded in the audited current implementation at:

`ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`

## Current primitives to preserve

The current server already has working concepts that should be extracted/generalized rather than rewritten:

```text
user_context(conn, user_id)
  -> roles
  -> permissions
  -> warehouses

has_perm(ctx, perm)
require_perm(ctx, perm)
warehouse_scope(ctx)
require_warehouse_access(ctx, row, *fields)
```

Current `warehouse_scope(ctx)` behavior explicitly treats `super_admin` / `admin` as unrestricted and otherwise derives allowed warehouse IDs from the authenticated user's context.

Current audit evidence is written through `database.log_operation(...)` into `operation_logs`.

E01-S01 must preserve these semantics first, then relocate ownership behind stable modules.

## Target modules

```text
inventory_app/platform/
  __init__.py
  errors.py
  request_context.py
  responses.py
```

Later E01 stories add:

```text
  action_policy.py
  idempotency.py
  jobs.py
  outbox.py
  correlation.py
```

## RequestContext contract

`RequestContext` carries authoritative execution context only:

```text
user_id
roles
permissions
warehouse_scope
correlation_id
request_source
request_metadata (bounded)
```

The initial adapter should be built from the current authenticated `user_context(...)` result so existing role/permission/warehouse semantics do not drift.

It must **not** gain authority from client payload fields such as:

```text
warehouse_id
from_warehouse_id
to_warehouse_id
owner_id
role
permission
status
```

A payload may identify a requested target, but ownership/scope/state must be resolved again from authoritative server data.

## Compatibility/extraction strategy

Do not immediately delete the old helpers.

Recommended transition:

```text
Step 1
  add RequestContext + shared errors/response helpers

Step 2
  adapt one low-risk route from current user_context result

Step 3
  make old server helpers delegate to shared primitives where practical

Step 4
  move pilot write routes through Action Policy

Step 5
  remove duplicate helper implementations only after regression parity
```

This minimizes risk to the existing auth/security test suite.

## Error contract

`errors.py` defines stable application/domain errors for:

```text
authentication_required
permission_denied
scope_denied
invalid_state
conflict
validation_error
idempotency_conflict
retryable_technical_failure
```

HTTP status/payload mapping remains an API-adapter concern.

During migration, existing `AppError` behavior must remain compatible for routes not yet converted.

## Response contract

`responses.py` should centralize only repetitive success/error envelope mechanics already used by the API.

It must not:

- reinterpret domain values;
- change route payload shape globally;
- introduce a new versioned API in E01-S01;
- hide domain exceptions as HTTP 200.

## Correlation placeholder

S01 establishes a bounded `correlation_id` field in RequestContext, but does not yet add DB schema.

Rules:

- accept a syntactically valid bounded inbound value or generate one;
- never use it for authorization or idempotency;
- never trust arbitrary unbounded client strings;
- S09 later propagates it into `operation_logs`, jobs and outbox evidence.

## Data migration

None.

## Tests

### Context construction

- context built from current `user_context(...)` preserves roles/permissions/warehouse scope;
- admin/super-admin unrestricted warehouse behavior remains unchanged;
- scoped user remains scoped;
- request payload cannot expand warehouse authority.

### Errors / response mapping

- shared error → API status/code mapping is deterministic;
- existing route error payloads remain compatible during migration;
- rejected requests do not silently become success envelopes.

### Correlation input

- generated ID exists when absent;
- valid bounded inbound ID is preserved;
- oversized/invalid values are rejected or replaced according to one deterministic rule.

### Regression

- existing `tools/test_auth_security.py` remains green;
- existing core workflow tests that import/use `user_context` remain green.

## Acceptance

1. shared primitives exist without changing DB schema;
2. current auth/permission/warehouse semantics remain intact;
3. one low-risk read route can use RequestContext/shared response/error plumbing with no observable API change;
4. no consequential write route is migrated until S02 policy wrapper is ready.

## Rollback

Pure code extraction. Revert module use; no database rollback required.

## Entry gate

Implementation starts only after:

```text
E00 real-checkout Release Gate = PASS
AND Inventory PR #3 reviewed/merged
```
