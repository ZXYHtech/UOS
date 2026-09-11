# TASK_INV_IMPL_E01_S02 — Action Policy Registry

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Replace route-by-route bespoke authorization/scope wiring with declarative action metadata plus one execution wrapper, while preserving the current working backend security model.

This is **not** a new permission system and not a generic workflow engine.

## Current behavior to preserve

The audited server already relies on:

```text
user_context
has_perm / require_perm
warehouse_scope
require_warehouse_access
existing service-layer state validation
database.log_operation -> operation_logs
```

The problem is primarily that these checks are repeated and manually composed across many route branches in `server.py`. As the system grows, omission risk grows with it.

E01-S02 centralizes composition; it does not replace the underlying truth.

## Proposed module

```text
inventory_app/platform/action_policy.py
```

## Action metadata

Each consequential action declares a static code-owned policy:

```text
action_code
required_permission(s)
auth_required
target_loader
scope_resolver
precondition/state_resolver
idempotency_mode
audit_mode
```

Example:

```text
transfer.receive
  permission = transfer.process
  target_loader = transfer by id
  scope = loaded transfer.to_warehouse_id
  state = existing TransferService receive preconditions
  idempotency = required
  audit = existing operation/stock evidence
```

Policies remain version-controlled Python definitions in E01. Do not move them into editable DB/JSON rules.

## Required execution order

```text
1. resolve authenticated actor / RequestContext
2. locate policy by action_code
3. load authoritative target object
4. permission check
5. object-derived warehouse/object scope check
6. state/business precondition check
7. idempotency admission when enabled
8. call existing domain/service method
9. commit existing business/audit evidence
10. return operation receipt / current API response adapter
```

The target must be loaded **before** scope authorization when scope depends on the target.

Client payload fields may identify a target but never establish its owner/warehouse/state.

## Scope semantics

The first implementation should adapt the current `warehouse_scope(...)` / `require_warehouse_access(...)` behavior rather than inventing a parallel ACL language.

Policy scope resolvers should return authoritative warehouse IDs or equivalent scope facts from the loaded object.

Examples:

```text
transfer.receive
 -> transfer.to_warehouse_id

purchase.receive
 -> purchase_order.warehouse_id

shipment.complete
 -> shipment_task.warehouse_id
```

A later domain can add a different resolver type only when genuinely needed.

## Permission semantics

Support:

```text
one required permission
OR a small explicit tuple/set where the current route already has an OR rule
```

Do not add wildcard permission expressions or a policy DSL.

Super-admin/admin behavior should remain whatever current backend helpers define; Action Policy must not silently broaden it.

## State/precondition ownership

Critical rule:

> Action Policy may decide **whether to invoke** a domain operation, but must not become a second copy of the domain state machine.

Where current `TransferService`, `ProcurementService`, `ShipmentService`, etc. already enforce state transitions, those service checks remain authoritative.

A lightweight policy precondition may reject obviously invalid/absent targets early, but business transition rules stay in the domain service until that domain is explicitly refactored.

## Audit behavior

Current `database.log_operation(...)` / `operation_logs` remains valid audit evidence.

S02 should attach policy metadata such as:

```text
action_code
actor_id
target_type/target_id
correlation_id placeholder
```

without duplicating a second audit row if the existing service already writes the authoritative operation log.

Recommended modes:

```text
service_owned_audit
wrapper_owned_audit
none/read_only
```

The wrapper must know which mode applies so one successful action does not generate accidental duplicate audit evidence.

S09 later adds persistent correlation propagation.

## Idempotency integration boundary

S02 defines metadata only:

```text
idempotency = none | optional | required
```

S04 owns the durable `business_operations` implementation.

Until S04 is present, an action marked `required` must not be presented as production replay-safe merely because S02 exists.

## API adapter contract

`server.py` should eventually shrink toward:

```text
parse route / body
 -> RequestContext
 -> execute_action(action_code, target_id, payload, ctx)
 -> map result to existing API response
```

The wrapper itself must not depend on `BaseHTTPRequestHandler` or direct socket objects.

## Data migration

None.

## Pilot registry entries

Initial policies after S01/S02 are ready:

```text
transfer.receive
purchase.receive
shipment.complete
```

Precise route/service bindings are defined in `TASK_INV_IMPL_E01_S03.md`.

## Tests

### Policy registration

- duplicate action code rejected at import/startup/test time;
- missing required metadata rejected;
- unknown action code rejected deterministically.

### Authorization matrix

For one representative fixture action:

- no auth -> denied;
- wrong permission -> denied;
- correct permission + wrong warehouse scope -> denied;
- correct scope + missing target -> denied;
- correct scope + invalid business state -> existing domain/precondition denial;
- valid actor/scope/state -> service invoked exactly once.

### Mutation safety

- rejected requests never invoke domain mutation;
- wrapper failure before invocation produces no stock/business side effect;
- existing service-owned audit remains exactly once;
- policy wrapper does not duplicate operation logs.

### Architecture boundary

- `action_policy.py` does not import HTTP handler classes;
- policy metadata does not execute SQL directly except through explicit target-loader/service abstractions;
- no policy definition trusts payload-supplied warehouse authority.

## Acceptance

1. registry can describe both read and consequential write actions without HTTP implementation details;
2. it reuses current backend permission/warehouse semantics;
3. a fixture action proves ordering: target load -> permission -> scope -> precondition -> service;
4. denied actions never reach the mutation service;
5. audit behavior is explicit and non-duplicating.

## Non-goals

- no dynamic workflow builder;
- no policy editor UI;
- no policy rules stored in DB/JSON;
- no Rego/OPA-style policy engine;
- no mass migration of all routes in one PR;
- no replacement of domain state machines;
- no Stock Position / Reservation redesign.

## Dependencies

E01-S01.

Runtime implementation remains blocked until:

```text
E00 real-checkout Release Gate = PASS
AND Inventory PR #3 reviewed/merged
```
