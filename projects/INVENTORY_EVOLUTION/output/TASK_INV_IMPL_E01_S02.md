# TASK_INV_IMPL_E01_S02 — Action Policy Registry

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Replace route-by-route bespoke authorization/state checks with declarative action metadata plus one execution wrapper.

## Proposed module

```text
inventory_app/platform/action_policy.py
```

## Action metadata

Each consequential action declares:

```text
action_code
required_permission(s)
auth_required
scope_resolver
precondition/state_resolver
idempotency_mode
audit_mode
```

Example:

```text
transfer.receive
  permission = transfer.process
  scope = destination warehouse derived from transfer object
  state = can_receive
  idempotency = required
  audit = operation/ledger receipt
```

## Required execution order

```text
authenticated actor
 -> load authoritative target
 -> permission
 -> object-derived scope
 -> business state/preconditions
 -> idempotency admission when enabled
 -> domain service
 -> audit receipt
```

Client payload fields may identify a target but never establish ownership/scope.

## Data migration

None.

## Tests

Matrix tests for one fixture action:

- no auth → denied;
- wrong permission → denied;
- correct permission + wrong warehouse scope → denied;
- correct scope + invalid target state → denied;
- valid actor/scope/state → service invoked exactly once;
- rejected requests never invoke the domain mutation;
- audit metadata includes action code and correlation placeholder.

## Acceptance

Action registry can describe read and write actions without importing HTTP-server implementation details.

## Non-goals

- no dynamic workflow builder;
- no policy rules stored in editable JSON/DB;
- no attempt to migrate all routes in one PR.

## Dependencies

E01-S01.
