# UOS Extraction & Sync Policy

## 1. Canonical direction

`ZXYHtech/UOS` is the canonical upstream for generic UOS Kernel artifacts.

Default sync direction:

```text
UOS upstream -> versioned release/pin -> AI_book consumer
```

If a generic UOS bug is discovered while running AI_book, the preferred flow is:

```text
AI_book evidence
-> UOS issue/problem/task
-> fix + regression in UOS
-> UOS version bump
-> sync/pin into AI_book
```

Emergency compatibility fixes may land in AI_book first only when necessary to keep the active project safe. They must then be backported to UOS before the next normal sync.

## 2. Four classes of files

### A. KERNEL_SYNC

Generic control-plane code and protocol artifacts. These belong upstream in UOS and may be synced into consumers.

Examples:
- provider-neutral CLI and deterministic broker/reconcile code
- repository identity protocol/adapter
- claim, lease, fencing, handoff, completion logic
- path authority, resource admission, work market
- project graph, intent, interrupt, quality-adapter framework
- generic validation/regression tests
- generic operator/agent protocol documentation

### B. PROJECT_TEMPLATE

Reusable project/task templates. UOS owns the template; consumers instantiate local copies.

Examples:
- project manifest template
- task catalog template
- task output/review layout
- quality adapter registration template

### C. RUNTIME_LOCAL

Canonical runtime state. **Never synchronize between repositories.**

Examples:
- `coordination/claims/`
- `coordination/claim_requests/`
- `coordination/claim_grants/`
- `coordination/work_sessions/`
- `coordination/completed/`
- `coordination/runtime/`
- generated progress/dispatch state
- repository-specific leases, fencing tokens and outbox receipts

### D. PROJECT_PRIVATE / PROJECT_SPECIFIC

Project content and history. Never export from AI_book merely because it shares a repository with UOS.

Examples:
- AI_BOOK task catalog/history
- book text, research corpus, game code/assets
- AI_book-specific quality rules and private outputs
- credentials, secrets, environment-specific values

## 3. Version pinning

Every consumer should eventually carry a small pin file such as:

```yaml
Schema: UOS_PIN_V1
Upstream: ZXYHtech/UOS
Version: UOS_Vx.y
Commit: <exact upstream commit>
ExecutionEpoch: <epoch>
SyncedAt: <UTC time>
```

The pin is evidence of what UOS version a consumer runs. Runtime state does not move with the pin.

## 4. Migration stages

### P0 — Bootstrap upstream
- initialize standalone UOS repository
- define canonical ownership and sync policy
- create self-hosted UOS_CORE migration tasks

### P1 — Extract generic Kernel
- move/copy generic orchestration docs and tools from AI_book
- remove AI_BOOK assumptions from generic code
- keep paths stable where possible to reduce migration risk

### P2 — Standalone project/task bootstrap
- add `uos project init`
- add `uos task publish` or equivalent deterministic publisher
- create project/task templates
- prove UOS can create and publish work without AI_book data

### P3 — Self-host UOS_CORE
- UOS repository boots its own control plane
- UOS_CORE tasks can be published, claimed, renewed, completed and reconciled here

### P4 — Consumer sync
- add UOS release/version metadata
- add deterministic kernel export/sync manifest
- pin AI_book to an exact UOS release/commit
- keep AI_book runtime state local

### P5 — Standalone acceptance
Prove with provider automation disabled:
- fresh clone bootstrap
- project init
- publish tasks
- 1/2/5/10/30 Agent claim contention
- unique ownership
- stale/fenced reclaim
- interruption/restart recovery
- completion + reconcile
- project pivot/spawn/reopen
- update UOS then sync a pinned version into a consumer

## 5. Anti-fork rule

Do not make both UOS and AI_book independently authoritative for the same Kernel file. That creates semantic drift.

For every synchronized Kernel artifact there must be one upstream owner: `ZXYHtech/UOS`.

AI_book may carry a snapshot for compatibility and local execution, but its normal changes to those files are downstream patches waiting to be upstreamed, not a second permanent source of truth.
