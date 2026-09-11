# TASK_INV_AUDIT_MOBILE_OFFLINE_SYNC_01 — Mobile, PWA, Offline and Synchronization Experience Audit

## 0. Scope and evidence boundary

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `mobile/`, `mobile-offline/`, Android/iOS wrapper context, prior UX audit and service-worker/offline JavaScript behavior.

This is a static source/architecture audit. Device usability, camera performance and real weak-network behavior still require device tests.

## 1. Executive conclusion

The repository currently contains **two fundamentally different mobile data models**:

1. `mobile/` — online PWA/client with a network-first service worker; static assets can fall back to cache, but `/api/` requests are explicitly excluded from service-worker caching.
2. `mobile-offline/` — standalone local application storing its own users, warehouses, materials, inventory, orders, shipments, transfers and logs in browser `localStorage`, with JSON import/export-style synchronization.

These must not be described as one seamless offline capability.

The online PWA is the safer long-term foundation for authoritative operations. The legacy offline app demonstrates useful emergency/offline workflows, but its current local database/role/synchronization design is not sufficient for authoritative multi-user inventory mutation without a major conflict, identity and security redesign.

Preliminary maturity:

- online mobile workflow breadth: 4/5
- weak-network/static-cache UX: 3.5/5
- scan/task suitability: 3/5
- true offline read capability: 2.5/5
- safe offline write synchronization: 1/5
- conflict resolution: 0.5/5
- offline identity/auth security: 0.5–1/5 in legacy app
- client-portfolio clarity: 2/5

## 2. Online PWA behavior

The `mobile/service-worker.js` uses network-first fetching for same-origin non-API assets and caches successful responses as fallback.

Important implication:

```text
App shell may open during network failure
!=
Business API data/commands work offline
```

This is a sensible design for an online operational client because it avoids silently using stale API responses for stock-changing work.

Preserve the principle that a mobile write is not considered successful until the authoritative server confirms it.

## 3. Legacy offline app behavior

`mobile-offline/app.js` stores an entire local operational dataset under a localStorage key and includes local:

- operator/admin role selection;
- warehouses;
- materials;
- inventory balances;
- orders;
- shipments;
- transfers;
- logs with `synced:false`;
- local stock adjustment;
- local order creation;
- local shipment/transfer workflows;
- JSON synchronization package export/import.

This makes it an independent local inventory system, not merely an offline cache.

That architecture creates fundamental authority questions that must be solved before production use.

## 4. Critical authority problem

Consider:

```text
Server stock = 5
Phone A goes offline and ships 4
Phone B goes offline and ships 4
Both local states remain non-negative
Later both synchronize
```

There is no conflict-free merge that can make both physical shipments valid if only five existed.

Therefore offline inventory writes cannot use “last local JSON wins” or simple log replay without central reservation/lease/policy.

## 5. Product decision required

Choose one supported direction explicitly.

### Option A — online-first mobile + offline read cache

Recommended default.

Offline can show:

- recent assigned tasks;
- material/location reference;
- cached labels/docs;
- pending locally captured photos/scans that do not mutate stock.

Stock-changing actions require server connectivity.

This is safest and simplest.

### Option B — limited offline command queue

Allow only specifically designed commands with conflict semantics, such as:

- count observation;
- photo/evidence capture;
- scan observations;
- notes;
- pre-assigned task actions backed by server-reserved stock/lease.

Commands synchronize later and may enter conflict review.

### Option C — full offline-first inventory

Requires much more:

- device identity;
- user authentication offline;
- signed/scoped data packages;
- preallocated stock/task authority;
- per-command idempotency;
- causal/version data;
- conflict engine;
- revocation/expiry;
- encrypted local storage;
- reconciliation/audit.

Not recommended unless a real business requirement justifies the complexity.

## 6. Recommended direction

For this company, use **Option A plus selected Option B**.

Warehouse/RF production normally operates on company LAN/Wi-Fi and correctness of stock/reservation matters more than pretending every action works offline.

Good offline-tolerant operations:

- view cached assigned task details;
- scan/capture evidence locally;
- draft a count observation;
- take photos;
- lookup cached material/serial data;
- queue a non-destructive note.

High-risk operations that should normally require server confirmation:

- stock adjustment;
- shipment completion;
- transfer ship/receive;
- PO receipt;
- work-order issue/output;
- quality release;
- refund/RMA disposition.

## 7. Local authentication issue

The legacy offline app allows selecting operator/admin role through local browser state rather than proving server-issued authorization. That is acceptable only for a demo/local standalone tool, not as authoritative enterprise authorization.

If any offline command capability survives, use a server-issued signed offline authorization package containing:

- user ID;
- device ID;
- permission scope;
- warehouse/task scope;
- issued/expiry time;
- package version;
- cryptographic signature.

Offline client must not self-elect admin authority.

## 8. Local storage security

`localStorage` is convenient but not appropriate for sensitive authoritative offline business state without protection.

Risks:

- data accessible to scripts in origin;
- easy user/device tampering;
- no transactional database semantics;
- storage eviction/clear;
- no encryption at rest;
- difficult large-data indexing/versioning.

If offline cache/queue becomes supported, use IndexedDB or native secure storage depending platform, encrypt sensitive data where justified and bind data to authenticated device/user context.

## 9. Demo/default credentials

Legacy offline synchronization UI contains example/default server/account values. Production-supported clients must never ship usable shared/default credentials or encourage them through prefilled password fields.

Any retained demo mode should be unmistakably separate from production configuration.

## 10. Sync package identity

A synchronization package must not be a mutable snapshot of the whole local database.

Prefer command/event envelope:

```text
sync_package
  package_id
  device_id
  user_id
  issued_at
  base_server_version/cursor
  commands[]

command
  command_id UUID
  command_type
  authoritative_object_id
  expected_version
  payload
  occurred_at_device
```

Server processes each command idempotently and returns per-command status.

## 11. Sync result states

Mobile must distinguish:

```text
LOCAL_DRAFT
QUEUED
UPLOADING
SERVER_CONFIRMED
RETRYABLE_FAILURE
REJECTED
CONFLICT_REVIEW
EXPIRED_AUTHORITY
```

Never display a queued local stock write as if authoritative server stock already changed.

## 12. Conflict classes

Define conflicts explicitly:

- object version changed;
- stock/reservation no longer sufficient;
- task reassigned/cancelled;
- permission revoked;
- lot/serial already consumed;
- duplicate command;
- server object deleted/obsolete;
- document/BOM revision changed;
- offline authorization expired.

Each conflict needs a safe resolution path; do not auto-merge stock quantities by arithmetic unless command semantics prove it is safe.

## 13. Idempotency

Every offline queued command needs globally unique `command_id`.

Re-upload after timeout/restart must return the first result rather than execute again.

This is especially important because weak networks naturally create ambiguous “did server receive it?” states.

## 14. Version/precondition

Commands should include expected object version where relevant.

Example:

```text
count observation references stock position version 128
```

If current server version is 135, server may accept it as an observation but cannot blindly overwrite current quantity.

Different commands require different conflict rules.

## 15. Reservation/lease for offline task execution

If business later requires offline picking/shipping, server must pre-authorize a bounded resource:

```text
Task T assigned to device/user
Stock reservation R for exact material/lot/qty
Lease expires at time X
```

Offline execution can consume only that reserved authority.

This does not solve every conflict but makes bounded offline execution feasible.

## 16. Scan-first mobile UX

Mobile home should prioritize:

- scan task/order/logistics;
- scan location;
- scan material/lot/serial;
- receive transfer/PO;
- count;
- quick lookup.

A scan resolves object and permitted contextual actions.

Keep manual menu navigation as fallback, not primary warehouse interaction.

## 17. Camera and scan failure UX

Required states:

- camera permission denied;
- camera unavailable;
- unreadable code;
- multiple possible objects;
- code belongs to wrong material/location/task;
- offline lookup cache missing;
- scan accepted locally but command not server-confirmed.

Allow manual code entry with appropriate validation.

## 18. Weak-network UX

The existing client already contains stale-request protection according to prior UX audit. Extend with:

- per-action request state;
- retry for safe GET;
- explicit idempotency for command retry;
- network-quality/offline indicator;
- last server-confirmed timestamp;
- no silent fallback to stale stock for mutation decisions;
- timeout message explaining whether result is unknown or definitely failed.

## 19. Cached data freshness

Every cached business object should have:

- server version/ETag/cursor;
- fetched time;
- stale indicator;
- scope/user identity.

Stock/pricing/task data should show `last confirmed` time when offline.

Do not display stale quantity without visual indication.

## 20. Logout/device loss

On logout, role change, token revocation or device loss:

- sensitive local cache should be cleared/locked according to policy;
- queued commands must retain auditable identity but require valid authorization to sync;
- another user must not inherit prior user's warehouse/customer data;
- server should be able to revoke device authorization.

## 21. Android/iOS wrappers

WebView/WKWebView wrappers should remain thin where possible.

Native responsibilities that may justify wrappers:

- camera/scanner integration;
- printing;
- secure credential storage;
- file sharing/opening;
- push notifications;
- managed app/device policies.

Do not duplicate business state machine in Java/Swift and JS unless unavoidable.

## 22. Client portfolio cleanup

Explicitly classify:

```text
mobile/               SUPPORTED online mobile
mobile-offline/       LEGACY/EXPERIMENT or LIMITED EMERGENCY MODE
android-offline-app/  rename according to actual current online behavior
-ios wrapper           SUPPORTED/defined status
```

Remove or clearly quarantine misleading demo assets only after migration/documentation and tests prove they are unused.

## 23. Offline test matrix

Device/browser-local test scenarios:

- page reload offline with cached shell;
- API GET unavailable;
- network loss before command send;
- network loss after server commit before response;
- retry same command;
- app killed with queued command;
- server object changes while phone offline;
- task cancelled/reassigned;
- permission revoked;
- two devices compete for same reserved stock;
- clock skew;
- local storage/cache cleared;
- upgrade client with pending commands.

## 24. Priority roadmap

### P0

1. formally classify client/offline product direction;
2. stop describing online static-cache fallback as offline business mutation;
3. mark legacy offline local inventory as non-authoritative unless redesigned;
4. scan-first online task flows;
5. explicit network/request/server-confirmed states;
6. no production default credentials in offline/sync UI;
7. stable mobile status/action contract with PC/server.

### P1

1. IndexedDB/native cache for scoped read data;
2. limited durable offline command queue for low-risk observations;
3. command UUID/idempotency and per-command sync result;
4. signed offline authorization scope;
5. conflict review UI;
6. device identity/revocation;
7. optional pre-reserved offline task lease.

### P2

1. richer true offline execution only if measured business need exists;
2. native scanner/printer integrations;
3. encrypted local operational store and advanced reconciliation if full offline mode is justified.

## 25. Acceptance signals

- online PWA clearly distinguishes cached shell from live authoritative API data;
- a weak-network timeout cannot cause duplicate stock mutation on retry;
- offline client cannot self-assign server-authoritative admin permission;
- cached stock displays last server-confirmed freshness;
- queued commands are idempotent and return per-command results;
- conflicts never silently overwrite newer server state;
- high-risk stock movements require live server confirmation unless covered by an explicit bounded offline reservation protocol;
- logging out/device revocation protects cached sensitive data;
- client directories/docs accurately reflect supported mode;
- no required mobile sync/retry mechanism depends on GitHub Actions.

## 26. Core recommendation

Consolidate around the **online mobile PWA as the authoritative warehouse client**, with explicit weak-network behavior and selected safe offline caching/command capture. Treat the legacy localStorage-based offline inventory as a prototype/emergency tool unless it is redesigned around signed authority, reservations, idempotent commands and conflict resolution. Offline convenience must never weaken stock truth.