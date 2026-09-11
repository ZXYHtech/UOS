# TASK_INV_AUDIT_API_PERMISSION_01 — API, Authentication, Authorization & Warehouse Scope Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Evidence is from `inventory_app/server.py`, `inventory_app/database.py`, `inventory_app/services.py`, tests and development documentation. No GitHub Actions execution is used or required.

## 1. Executive conclusion

Inventory Lite has moved well beyond a UI-only permission model. The server contains explicit authentication/session resolution, permission helpers, user overrides and warehouse-scope helpers. This is a strong foundation.

The main risk is no longer “there is no permission system”; it is **coverage complexity**. `server.py` is a very large central HTTP router. As APIs and roles have expanded, correctness depends on each route consistently composing four separate controls:

1. authenticated actor;
2. permission code;
3. warehouse/object scope;
4. valid business-state transition.

For stock-changing or externally synchronized operations a fifth control is required:

5. idempotency / replay protection.

The long-term security goal should therefore be to make these controls declarative or domain-local rather than repeatedly hand-written in one giant route handler.

## 2. Authentication model

Observed behavior:

- login produces a random token;
- only a SHA-256 token hash is persisted in `auth_sessions`;
- session records contain idle expiry and absolute expiry;
- password change/recovery can revoke active sessions;
- login attempt tracking exists;
- server resolves requests from `Authorization: Bearer <token>`;
- browser credentials are stored in `localStorage` according to server comments.

### Positive findings

- raw session tokens are not stored in the database;
- idle and absolute lifetime are distinct;
- revocation is supported;
- password hashing uses PBKDF2-SHA256 with per-user random salt for new hashes, while legacy hashes remain readable for migration;
- a dedicated local admin recovery utility revokes sessions after reset.

### Risks / follow-up

#### A. localStorage bearer token increases XSS consequence

Because the browser token is stored in `localStorage`, a successful script injection can exfiltrate the bearer token. The correct security priority is therefore strong XSS prevention, output escaping, safe HTML construction and preferably a restrictive Content Security Policy.

This architecture is not automatically unsafe, but it makes front-end injection defense more important than in an HttpOnly-cookie design.

#### B. static search did not find standard security-header strings

A repository search did not find `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options` or `Access-Control-Allow-Origin` strings in the pinned tree. This is not proof that a reverse proxy does not add them, but application/repository ownership is currently unclear.

Later security audit should inspect `deploy/linux` reverse-proxy configuration and production deployment behavior.

#### C. default local accounts remain an operational risk

The database bootstrap writes a local file containing initial admin/east/south account credentials and instructs the operator to rotate them. This is better than displaying them on the login screen, but production acceptance should include a deterministic “default credentials rotated/disabled” check.

## 3. Authorization model

Observed permission families include:

- `user.manage`
- `warehouse.manage`
- `location.manage`
- `material.manage`
- `inventory.view`
- `inventory.adjust`
- `inventory.count`
- `order.manage`
- `shipment.process`
- `transfer.process`
- `log.view`
- `setting.manage`
- `production.material.manage`
- `project.bom.manage`
- `purchase.manage`
- `purchase.approve`
- `cost.view`
- `cost.manage`
- `pricing.view`
- `pricing.manage`

The model supports:

`role defaults + per-user permission overrides + warehouse membership`

This is more appropriate than hard-coded UI-only roles.

## 4. Warehouse scope model

Important helpers found in `server.py`:

- `warehouse_scope(ctx)`
- `require_warehouse_access(ctx, row, *fields)`
- `filter_warehouse_rows(rows, ctx, *fields)`
- `require_location_manage(ctx, warehouse_id)`
- `inventory_read_warehouse_scope(ctx, inventory_usage)`
- `shipment_rows_for_context(rows, ctx)`

Behavioral intent:

- super-admin/admin can operate globally;
- ordinary warehouse users are scoped to assigned warehouses;
- product inventory has an intentional cross-warehouse read policy;
- production inventory has a different visibility rule;
- location management still requires permission plus warehouse access;
- open-pool shipment tasks can have special visibility.

### Assessment

This is a sensible business model, but it is complex enough that helper-level correctness is not enough. Every route that receives an object ID or warehouse ID must call the right scope check after loading the authoritative object.

A common future failure pattern would be:

`permission present -> endpoint loads ID supplied by caller -> operation executes -> warehouse scope check forgotten`

Therefore the next refactor should reduce manual route-by-route composition.

## 5. Representative route evidence

Static source confirms explicit permission gates on business APIs. Examples include:

- purchase-order endpoints requiring `purchase.manage`;
- project BOM binding requiring `project.bom.manage`;
- price-list writes requiring `pricing.manage`;
- backup/settings endpoints requiring `setting.manage`;
- AI configuration endpoints requiring `setting.manage`.

The development index further states that backend `require_perm`, `warehouse_scope` and `require_warehouse_access` are the security boundary, while front-end page permissions are only experience controls.

This is the correct design principle and should remain normative.

## 6. Missing structural protections

### 6.1 No declarative route policy table

The current architecture appears to encode permission/scope requirements inline in a large handler. That makes audits expensive and increases the chance of a future endpoint missing one gate.

Recommended target:

```text
route/action
 -> auth required
 -> permission(s)
 -> scope resolver
 -> state transition
 -> idempotency class
 -> audit action
```

This can be implemented without a web framework and without GitHub Actions. A small route registry/decorator/helper is enough.

### 6.2 Permission and state checks are separate concepts

Having `purchase.manage` should not mean any purchase order can transition to any state. Likewise `shipment.process` should not mean an already completed shipment can be replayed.

For every mutating aggregate, define an explicit transition matrix independent of permission checking.

### 6.3 Idempotency is not yet a universal API primitive

Stock-changing operations that deserve explicit replay keys include:

- purchase receive;
- shipment complete;
- transfer ship;
- transfer receive/partial receive;
- platform order import/sync;
- refund/return when implemented;
- production issue/complete when implemented.

A UI button lock or client timeout does not guarantee server idempotency.

Recommended pattern:

`business_operation_key` or `idempotency_key` stored with the resulting event/transaction and rejected/replayed deterministically.

## 7. Audit/logging requirement

The project already has `operation_logs` with before/after JSON and an explicit rule that key actions must be logged. This should be elevated into an API policy:

Every mutation should declare one of:

- `AUDIT_REQUIRED`
- `AUDIT_DERIVED_FROM_LEDGER_EVENT`
- `NO_AUDIT_REQUIRED` with documented reason

This prevents new APIs from silently bypassing history.

## 8. Recommended API architecture evolution

Do not rewrite to microservices. Split responsibilities inside a modular monolith.

### Phase A — current HTTP server, stronger registry

Keep the existing HTTP server but introduce reusable action wrappers:

```text
authenticated_action(
  permission=...,
  scope=...,
  transition=...,
  idempotency=...,
  audit=...
)
```

### Phase B — domain APIs

Move route-specific business orchestration into domain modules:

- inventory_api/domain
- purchasing_api/domain
- orders_api/domain
- transfer_api/domain
- pricing_api/domain
- manufacturing_api/domain

The central handler should parse HTTP and delegate, not own business behavior.

### Phase C — optional framework migration only when justified

FastAPI/Django Ninja could improve schema generation, validation and dependency injection later, but framework migration should not be used as a substitute for fixing domain boundaries.

## 9. Security priorities

### P0

1. route-by-route mutation inventory;
2. prove every mutation has auth + permission + object/warehouse scope + transition check;
3. add server-side idempotency to irreversible stock changes;
4. verify secrets are never returned by configuration APIs unless masked;
5. add/verify application or reverse-proxy security headers;
6. ensure default accounts are rotated/disabled in production;
7. test file upload path traversal, content type and size limits.

### P1

1. declarative action policy/route registry;
2. stronger secret-at-rest strategy;
3. append-only/tamper-evident audit options for high-risk actions;
4. scoped service credentials and rotation records;
5. rate limits for authentication, OCR, platform sync and other expensive endpoints.

## 10. Required local/server verification — no Actions dependency

Create a repository-contained permission test runner that can be run from a fresh checkout, e.g.:

```bash
python3 tools/test_auth_security.py
python3 tools/test_api_permissions.py
```

The new permission suite should generate an actor matrix:

- super admin
- admin
- warehouse manager/operator
- production manager
- read-only user
- explicit deny override
- user with no warehouse

For each sensitive endpoint it should test:

- unauthenticated -> denied;
- authenticated without permission -> denied;
- permission but wrong warehouse -> denied;
- correct permission + correct warehouse + valid state -> allowed;
- invalid state -> denied;
- replay same idempotency key -> no duplicate stock mutation;
- audit entry produced exactly once.

This suite must run directly with Python/local server. GitHub Actions may never be required for correctness.

## 11. Preliminary score

Static maturity only, 0–5 scale:

- Authentication primitives: **4/5**
- Permission model: **4/5**
- Warehouse scope concept: **4/5**
- Route policy maintainability: **2.5/5**
- State-transition centralization: **2.5/5**
- Idempotency as a platform primitive: **2/5**
- Audit concept: **3.5/5**
- Browser token/XSS hardening evidence: **2.5/5**

These are architecture audit scores, not penetration-test results.

## 12. Next evidence required

Later tasks must verify:

- exact route inventory and any missing scope gate;
- upload security limits;
- platform credential masking and storage;
- backup authorization and restore safeguards;
- cross-warehouse visibility behavior;
- stock-changing replay behavior under timeout/retry/concurrency.
