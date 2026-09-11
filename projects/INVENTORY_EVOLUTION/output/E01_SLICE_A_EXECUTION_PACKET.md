# E01 Slice A Execution Packet — Shared Context + Action Policy

## Status

`READY_TO_START_ONLY_AFTER_E00_PASS_AND_PR3_MERGE`

This packet is the first actual post-E00 implementation handoff. It intentionally contains **no database migration** and **no production consequential-route migration**.

## 1. Entry gate

All must be true:

```text
E00 real checkout Release Gate = PASS
Inventory PR #3 merged to main
new branch created from that merged main
```

Suggested branch:

```text
impl/e01-platform-policy
```

Do not branch from the old pre-E00 baseline.

## 2. Purpose

Create the smallest reusable execution boundary needed before idempotency and stock-affecting pilots:

```text
authenticated server context
 -> RequestContext
 -> action metadata
 -> authoritative target loader
 -> permission
 -> object-derived scope
 -> domain precondition/service
 -> explicit audit mode
```

This slice centralizes composition. It does **not** replace existing permission truth or domain state machines.

## 3. Existing code seams to preserve

Current baseline/reviewed source has important working helpers in `inventory_app/server.py`:

```text
user_context(conn, user_id)
has_perm(ctx, perm)
require_perm(ctx, perm)
warehouse_scope(ctx)
require_warehouse_access(...)
```

Current tests import `user_context` directly from `inventory_app.server` in at least:

```text
tools/test_auth_security.py
tools/test_core_workflows.py
```

Therefore compatibility imports/delegation are required during extraction. Do not simply move/delete helpers and break test/application imports.

## 4. Target files

Add:

```text
inventory_app/platform/__init__.py
inventory_app/platform/errors.py
inventory_app/platform/request_context.py
inventory_app/platform/responses.py
inventory_app/platform/action_policy.py
```

Expected bounded edits:

```text
inventory_app/server.py
```

Tests:

```text
tools/test_platform_request_context.py
tools/test_action_policy.py
```

Existing required regression suites remain:

```text
tools/test_auth_security.py
tools/test_core_workflows.py
tools/verify_release.py
```

Do not edit stock schema/tables in this slice.

## 5. RequestContext contract

Suggested immutable-ish structure:

```text
user_id
roles
permissions
warehouse_scope
correlation_id
request_source
bounded request_metadata
```

Authoritative source:

```text
existing server/database user context
```

Never grant authority from payload values such as:

```text
warehouse_id
owner_id
roles
permissions
status
```

Payload may request a target; server reloads ownership/scope/state.

## 6. Correlation placeholder

Slice A creates/generates a bounded correlation ID in memory/request context only.

Rules:

- deterministic validation of inbound format/length;
- generate when absent;
- not a permission key;
- not an idempotency key;
- no DB migration yet;
- persistent propagation waits for E01 later Slice E.

## 7. Shared error contract

`platform/errors.py` should expose stable categories without forcing an API version rewrite:

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

Compatibility requirement:

- current routes not migrated still behave as before;
- existing `AppError`-style response/status behavior remains supported;
- do not globally convert historical HTTP payloads in this PR.

## 8. Action Policy registry

Code-owned static policy only.

Minimum metadata:

```text
action_code
required_permissions
auth_required
target_loader
scope_resolver
precondition/service boundary
idempotency_mode
audit_mode
```

Supported audit modes initially:

```text
service_owned_audit
wrapper_owned_audit
none/read_only
```

Supported idempotency metadata initially:

```text
none
optional
required
```

Important: `required` is metadata only until E01 Slice B implements durable business operations. Slice A must not claim replay safety.

## 9. Execution ordering invariant

For consequential-style policy fixtures:

```text
RequestContext
 -> policy lookup
 -> authoritative target load
 -> permission check
 -> target-derived scope check
 -> state/precondition
 -> invoke service exactly once
 -> audit according to explicit mode
```

Why target load comes first:

- warehouse/object authority must be derived from server state;
- client-provided warehouse IDs cannot widen access.

## 10. First registry entries

Policies may be registered for future pilots:

```text
transfer.receive
purchase.receive
shipment.complete
```

But Slice A must **not route production writes through them yet**.

Use fixture/read-only/isolated test action to prove the wrapper.

## 11. Explicit non-goals

Do not include:

- Migration 2 / `business_operations`;
- production idempotency;
- durable jobs/outbox;
- Stock Position/Reservation changes;
- pricing formula fixes;
- all-route migration;
- dynamic policy editor/DB rules;
- OPA/Rego/general workflow engine;
- frontend rewrite.

If implementation starts to require any of these, stop and split the PR.

## 12. Required tests

### RequestContext parity

Prove:

- roles equal current `user_context` roles;
- permissions equal current semantics;
- admin/super-admin behavior unchanged;
- normal warehouse-scoped user cannot escape scope;
- payload-supplied warehouse cannot expand authority;
- generated/inbound correlation validation deterministic.

### Action registry

Prove:

- duplicate action code rejected;
- malformed/missing metadata rejected;
- unknown action code rejected;
- no-auth denied;
- wrong permission denied;
- correct permission/wrong object scope denied;
- missing target denied;
- invalid state/precondition never reaches mutation callback;
- valid fixture invokes callback exactly once;
- service-owned audit is not duplicated.

### Architecture boundary

Prove/import-review:

- `action_policy.py` has no `BaseHTTPRequestHandler` dependency;
- policies do not contain direct stock SQL;
- policies do not trust payload-derived scope;
- domain service remains owner of business state transitions.

### Full regression

```bash
python3 tools/test_auth_security.py
python3 tools/test_core_workflows.py
python3 tools/test_platform_request_context.py
python3 tools/test_action_policy.py
python3 tools/verify_release.py
```

On Linux release workstation:

```bash
python3 tools/verify_release.py --require-bash
```

## 13. PR review checklist

Reviewer answers yes/no:

```text
[ ] based on post-E00 main
[ ] no DB migration
[ ] no production stock/write route migrated
[ ] old user_context/auth imports remain compatible
[ ] no permission broadening
[ ] object scope is server-derived
[ ] state machine remains in domain/service
[ ] no duplicate audit rows
[ ] no claim of idempotency before Slice B
[ ] all required tests PASS
[ ] full Release Gate PASS
```

Any `no` blocks merge.

## 14. Rollback

Pure code rollback:

```text
revert Slice A commit/PR
```

No DB rollback, no data cleanup, no operation evidence deletion.

Because production writes are not migrated in Slice A, rollback risk should remain low.

## 15. Exit / unlock

Slice A complete when:

```text
shared context + static Action Policy merged
+ existing auth/security semantics unchanged
+ no production write semantics changed
+ full Release Gate PASS
```

Then unlock:

```text
E01 Slice B — Migration 2 / Business Operation Idempotency
```

Do not skip directly to Stock/Reservation.
