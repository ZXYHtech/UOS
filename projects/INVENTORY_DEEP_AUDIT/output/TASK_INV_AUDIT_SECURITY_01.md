# TASK_INV_AUDIT_SECURITY_01 — Security, Secrets and Deployment Hardening Audit

## 0. Scope and evidence boundary

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed authentication/authorization findings, database credential fields, browser-token design, server/deployment patterns, backup exposure, upload/resource paths and existing local security test assets.

This is a static architecture/source review, **not a penetration test**. Absence of a string in repository search is not proof that a production reverse proxy does not supply that control.

This report does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite has a materially stronger security foundation than a typical internal CRUD tool: randomized bearer sessions, hashed session-token persistence, idle/absolute expiry, password recovery/session revocation, role/permission/user overrides, warehouse scope and local auth-security tests already exist.

The most important security risks now come from **coverage and secret/browser exposure**, not total absence of controls:

1. `server.py` is large, so every sensitive route must consistently compose authentication, permission, warehouse/object scope and state checks;
2. browser bearer credentials are stored in `localStorage`, increasing the impact of any XSS;
3. platform API credentials are modeled as database `TEXT` fields (`app_secret`, `session_token`), so stronger at-rest secret protection is required before treating DB backups as low sensitivity;
4. repository search did not find a Content-Security-Policy string, so browser hardening ownership must be made explicit in app or reverse-proxy configuration;
5. file upload/download and path handling need deterministic adversarial tests;
6. operation logs are useful audit evidence but are not inherently tamper-evident;
7. backups contain sensitive operational/customer/auth-related data and require their own access/encryption policy.

Preliminary static maturity:

- authentication: 4/5
- RBAC/warehouse scope concept: 4/5
- route-policy structural safety: 2.5/5
- secret-at-rest protection: 1.5–2/5
- browser/XSS hardening evidence: 2/5
- upload/download hardening evidence: 2/5 pending tests
- audit integrity: 2.5/5
- deployment hardening: 2.5/5

## 2. Authentication strengths

Preserve the existing principles:

- raw session tokens are not stored directly in session table;
- session expiry distinguishes idle and absolute lifetime;
- session revocation exists;
- password change/recovery can revoke sessions;
- password hashing uses PBKDF2-SHA256 with salt for current hashes;
- login-attempt tracking exists;
- local auth-security test script exists.

Do not weaken these while modularizing the server.

## 3. Browser session risk

The current browser architecture uses bearer credentials in `localStorage` according to the prior API/security audit.

Risk chain:

```text
DOM/script injection
 -> malicious JavaScript executes in origin
 -> reads localStorage bearer token
 -> token can be replayed until revoked/expired
```

This does not mean the architecture is automatically compromised. It means XSS prevention becomes a P0 control.

Required defenses:

- avoid unsafe HTML interpolation of untrusted content;
- centralized escaping/sanitization for HTML-rendered data;
- no `eval`/dynamic script execution;
- restrictive Content Security Policy;
- `X-Content-Type-Options: nosniff`;
- frame-ancestor/frame protection as appropriate;
- sensible Referrer-Policy;
- no secrets embedded in client JS/config;
- short-enough session lifetime and easy revocation.

Longer term, evaluate HttpOnly/SameSite cookie sessions if architecture permits, but do not migrate authentication mechanism without considering CSRF and mobile/WebView clients.

## 4. CSRF versus bearer model

Bearer token in an Authorization header is less exposed to classic cross-site form CSRF than ambient cookies, but it is more exposed to token theft if script injection occurs.

If later moving to cookies:

- SameSite policy;
- CSRF token/origin checking;
- secure/HttpOnly flags;
- WebView compatibility;

must be designed together.

Do not add a CSRF token mechanically to the current bearer-header model and assume all browser threats are solved.

## 5. Route authorization coverage

The current model has good helpers such as permission and warehouse-scope checks, but route concentration creates omission risk.

Target every mutating route/action should declare:

```text
authentication
permission
object/warehouse scope
business transition
idempotency class
audit policy
```

A declarative action registry/wrapper would allow a local security test to enumerate sensitive endpoints and prove policy coverage.

Server-side checks remain authoritative; frontend menu/button hiding is never a security boundary.

## 6. Object-level authorization

High-risk pattern to prevent:

```text
user has generic permission
 -> supplies object ID from another warehouse/customer/account
 -> endpoint mutates object without authoritative scope check
```

Tests must cover IDOR-style cross-scope attempts for:

- inventory/warehouse/location;
- orders/shipments;
- transfers;
- purchase orders;
- platform accounts/credentials;
- backups;
- future work orders, RMA, customer cases and financial settlements.

Load the object first, derive its authoritative scope, then authorize.

## 7. Platform/API secrets

The inspected schema stores fields such as:

```text
app_key TEXT
app_secret TEXT
session_token TEXT
```

Separation from ordinary platform account metadata is good, but plain application DB fields make DB compromise/backup exposure highly consequential.

Recommended staged strategy:

### P0

- strict permission separation for credential read/write;
- never return full secret through ordinary GET/list APIs;
- mask values in UI/logs;
- never put secrets into job payloads, operation logs or error messages;
- record rotation/expiry/last-tested metadata;
- file permissions and backup restrictions.

### P1

Use envelope encryption or OS-managed secret storage:

```text
DB stores encrypted secret blob + key version
master key lives outside DB/backups
```

Possible master-key ownership:

- systemd credential/environment file with restricted mode;
- OS secret store;
- external KMS later if business/hosting justifies it.

Do not store encryption key next to encrypted DB in the same backup bundle.

## 8. AI service credentials

Apply the same rules to AI API keys:

- separate management permission;
- masking;
- rotation;
- timeout/egress restrictions;
- no customer/order data sent externally without explicit provider/data-policy decision;
- log metadata, not prompts containing secrets or unnecessary PII.

AI integration is also a data-boundary issue, not merely a secret-storage issue.

## 9. Default/bootstrap credentials

The existing bootstrap/recovery design creates operational risk if initial credentials remain active.

Production acceptance should deterministically check:

- bootstrap password file absent or protected after setup;
- default/generated passwords changed;
- unnecessary default users disabled;
- recovery utility accessible only to server administrators;
- recovery action revokes sessions and is logged locally where possible.

Never expose default credentials in the web login UI or documentation shipped publicly.

## 10. Input validation and SQL injection

The inspected service examples generally use parameterized SQLite queries, which is positive.

Still audit all dynamic SQL sites, particularly:

- import/export column/table selection;
- administrative search/sort/filter construction;
- dynamic table utility methods;
- report/query builders;
- future natural-language query features.

Whitelist structural SQL identifiers. Parameters only protect values, not dynamically concatenated table/column/order expressions.

## 11. File upload / attachment security

Required adversarial tests:

- `../` and encoded path traversal filenames;
- absolute paths;
- duplicate/collision names;
- oversized body/file;
- MIME/extension mismatch;
- malformed images;
- decompression bombs;
- unsupported archive types;
- symbolic-link escape if filesystem operations permit it;
- unauthorized attachment ID retrieval;
- private document cross-scope download;
- stored HTML/SVG/script content rendered inline;
- content-disposition safety.

Store server-generated opaque filenames/keys and keep original filename as metadata only.

Never derive filesystem destination directly from untrusted original filename.

## 12. Image/OCR processing risk

Image processing and OCR handle potentially untrusted binary data and may invoke native libraries/processes.

Controls:

- file-size and pixel-dimension limits;
- worker resource limits;
- timeout;
- process isolation where practical;
- no shell interpolation with user filenames;
- safe temp directories;
- cleanup;
- queue/backpressure;
- dependency patch process.

Existing systemd memory controls are useful resilience/security hardening and should remain.

## 13. XSS review priority

Because PC/mobile clients have large JS render surfaces and bearer token storage, audit all HTML construction patterns.

Classification:

- static trusted template;
- text-only insertion (`textContent`) — preferred;
- escaped HTML helper;
- raw server/user data interpolated into `innerHTML` — high review priority;
- user-controlled URL/href/src — scheme validation required.

Add local regression payloads such as benign marker tags/scripts to verify they render as text, not execute. Do not rely on manual code review alone.

## 14. CORS and origin policy

Define explicit policy even if application is intended same-origin.

If no cross-origin API is needed:

- do not emit permissive `Access-Control-Allow-Origin: *` for authenticated APIs;
- reject unexpected origins where appropriate;
- document WebView/mobile access path.

If cross-origin clients are needed later, allow only configured origins and never combine wildcard origin with credential-bearing cookie flows.

## 15. Security headers / TLS

Repository search did not locate CSP text, while deployment scripts include HTTPS configuration capabilities. Production security baseline should explicitly own:

- HTTPS redirect;
- TLS certificate renewal;
- HSTS when deployment is ready for it;
- CSP;
- X-Content-Type-Options;
- frame policy;
- Referrer-Policy;
- cache policy for sensitive responses.

Whether headers live in app or reverse proxy, add a server-local verification command that tests the deployed endpoint.

## 16. Audit-log integrity

`operation_logs` with before/after evidence is valuable, but an administrator/database writer can alter ordinary rows.

For high-risk events consider stronger controls:

- append-only service API;
- no ordinary UI delete/edit;
- sequence/event ID;
- actor/session/request correlation;
- periodic signed/hash-chained export if tamper evidence is important;
- off-host log shipping for critical deployments.

Do not claim regulatory-grade immutability unless those guarantees are actually implemented.

## 17. PII and customer data

Orders may contain names, phone numbers and addresses. Future CRM/support/RMA adds more personal data.

Apply data minimization:

- role-scoped visibility;
- masked display where full value is unnecessary;
- retention policy for old customer/order artifacts;
- avoid PII in debug logs;
- protect backups/exports;
- secure deletion policy consistent with business/legal retention requirements.

Do not put production customer data into test fixtures.

## 18. Backup security

Backups can contain essentially the entire trust boundary.

Controls:

- restrictive file owner/mode;
- off-host encryption where appropriate;
- key separation;
- backup inventory/retention;
- restore authorization;
- download permission;
- audit of backup export;
- no public/static web-directory placement;
- integrity hash/manifest.

A backup endpoint should require stronger privilege than ordinary read-only inventory access.

## 19. Dependency and supply-chain baseline

Without requiring GitHub Actions:

- pin/record direct Python/JS/native dependencies;
- repository-local dependency inventory command;
- periodic vulnerability review using locally runnable tooling;
- verify downloaded release/artifact checksums where appropriate;
- minimize native OCR/image package attack surface;
- document upgrade cadence.

Optional external scanners may supplement but cannot be the sole required release gate.

## 20. Security test suite

Build on existing `tools/test_auth_security.py`.

Recommended local commands:

```text
python3 tools/test_auth_security.py
python3 tools/test_api_permissions.py
python3 tools/test_security_headers.py --base-url ...
python3 tools/test_upload_security.py
python3 tools/test_idempotency_security.py
node tools/test_xss_rendering.js
```

Actor matrix must cover:

- unauthenticated;
- read-only;
- warehouse-limited;
- permission without warehouse;
- explicit deny override;
- admin;
- credential administrator.

## 21. Priority roadmap

### P0

1. complete sensitive-route auth/permission/scope inventory;
2. CSP/security-header ownership and deployed verification;
3. XSS regression audit because token is in localStorage;
4. upload/path/MIME/size adversarial tests;
5. credential API masking and least privilege;
6. production bootstrap credential check;
7. backup access/permissions;
8. idempotency and state-transition tests for critical mutations.

### P1

1. encrypt platform/AI secrets with key outside DB;
2. declarative route/action policy registry;
3. stronger audit tamper evidence;
4. PII retention/masking policy;
5. rate limiting for auth/expensive APIs;
6. dependency/vulnerability inventory.

### P2

1. external secret manager/KMS if hosting/scale justifies it;
2. centralized log/SIEM integration;
3. formal threat modeling/security review before internet-wide exposure;
4. periodic independent penetration testing.

## 22. Acceptance signals

- unauthorized and wrong-warehouse actors are denied for every sensitive route;
- browser-rendered adversarial strings cannot execute script in tested surfaces;
- production response has the intended security headers;
- path traversal/oversized/malformed upload tests fail safely;
- API list/detail never returns unmasked stored platform/AI secrets to unauthorized callers;
- DB backup alone does not reveal master decryption key after secret encryption rollout;
- default/bootstrap credentials cannot remain silently active in production acceptance;
- critical repeated requests do not duplicate stock/financial events;
- sensitive backup/export actions are privilege-gated and audited;
- all required security checks run directly from a checkout/server without GitHub Actions.

## 23. Core recommendation

Preserve the existing authentication/RBAC foundation, but shift security engineering toward **systematic coverage**: declarative route policies, XSS/browser hardening, secret-at-rest separation, adversarial file/API tests and reproducible deployment checks. The biggest risk is no longer a missing login screen; it is a growing application where one new route/render/upload path can bypass an otherwise good security model.