# TASK_INV_AUDIT_DOC_TRUTH_01 — Documentation-to-Code Truth Alignment

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Compared:

- `README.md`
- `AGENTS.md`
- `docs/应用开发索引.md`
- `docs/项目总览与编译说明.md`
- `docs/architecture.md`
- `docs/迭代执行记录.md`
- Android/iOS README files
- pinned source tree and schema

No GitHub Actions status is considered authoritative evidence.

## 1. Executive conclusion

Inventory Lite has a documentation-quality problem caused by **rapid feature growth plus multiple generations of overview documents**.

The repository does have a good principle: `AGENTS.md` points developers to `docs/应用开发索引.md`, and that index explicitly says current schema/services/server code override stale documentation. That should remain the source-of-truth rule.

However, other high-visibility documents still describe materially older product states. This can mislead a new developer/Agent into building against the wrong client model, wrong database expectation or wrong feature set.

## 2. Source-of-truth ranking

Recommended canonical ranking for the pinned project:

1. current source code at pinned commit;
2. `inventory_app/database.py` current schema + migrations;
3. `inventory_app/services.py` business invariants;
4. `inventory_app/server.py` auth/permission/API behavior;
5. current client code;
6. `docs/迭代执行记录.md` for recent change evidence;
7. `docs/应用开发索引.md` as navigation map;
8. domain design documents;
9. broad historical overview documents;
10. README marketing/quick-start summary.

This ranking is already close to what the development index states and should be made explicit in one canonical project manifest.

## 3. Confirmed drift examples

### Drift A — Android app is described both as offline and online

`docs/项目总览与编译说明.md` says:

- Android APK contains the offline page;
- directory is an Android offline APK project;
- expected artifact is `InventoryLiteOffline-debug.apk`.

But `android-offline-app/README.md` says the opposite:

- it is now an **online WebView APK**;
- it no longer contains offline inventory/local-data functionality;
- business data always lives on the server;
- its debug artifact is `InventoryLiteOnline-debug.apk`.

This is a direct documentation conflict, not a subtle wording issue.

Impact:

- a developer can test the wrong offline behavior;
- release instructions can target the wrong artifact name;
- future cleanup may preserve obsolete bundled assets because the overview says they are required.

Recommendation:

- make Android current mode a single canonical statement;
- rename `android-offline-app` to a neutral/current name only in a planned implementation task;
- mark historical offline bundle instructions as obsolete rather than silently leaving both.

### Drift B — architecture document describes an older MVP surface

`docs/architecture.md` lists a smaller foundational schema/API set and presents PostgreSQL as a straightforward future replacement.

The current SQLite schema now includes many additional domains not represented in that old architecture summary, including procurement, price lists/rules/revisions, material specifications/resources, classification, stock count, recognition revision/correction, notification, more detailed transfer handling, sessions/security and other migrations.

Impact:

- architecture review based on this file understates actual coupling and migration cost;
- PostgreSQL readiness can be overestimated;
- new tables can be added without updating the conceptual data map.

Recommendation:

Replace the single static architecture narrative with generated/maintained sections:

- current domain map;
- canonical schema version;
- current API domains;
- supported clients;
- deployment modes;
- explicit future/not-yet-supported items.

### Drift C — PostgreSQL scripts lag current SQLite source

This is partly code drift rather than documentation drift, but docs still present `deploy/postgres/schema.sql` as an available PostgreSQL setup path. The audited PostgreSQL schema is an older subset and is not equivalent to the current SQLite runtime model.

Recommendation:

Until parity exists, documentation must say:

`PostgreSQL schema is experimental/incomplete; not production-equivalent to the current SQLite application.`

Do not describe it as a supported backend.

### Drift D — README is better than older overview, but still insufficient as a capability manifest

The root README already reflects many later functions and correctly states Android is now online-only. It is therefore more current than `docs/项目总览与编译说明.md` on that point.

However, the application is evolving too quickly for README bullets to serve as a precise feature truth source.

Recommendation:

README should remain a concise product/start guide and link to a machine-readable/current capability manifest.

### Drift E — even the iteration log trails the pinned commit

The top of `docs/迭代执行记录.md` identifies its latest update as 2026-08-07, while the pinned `main` commit is dated 2026-08-10 and `server.py` identifies release version `2.4.4`. Therefore the iteration log is valuable recent evidence but cannot be treated as complete evidence for the exact pinned commit.

Recommendation:

- release/change logging should be part of the same local release command that updates/version-checks source;
- the release command should fail or warn when version metadata changed but no matching release record exists;
- the check must run locally/server-side and must not depend on GitHub Actions.

## 4. Documentation roles should be separated

Current repository mixes several document types:

- quick start;
- architectural truth;
- agent instructions;
- implementation history;
- design proposals;
- open-source research;
- deployment instructions;
- historical/offline client instructions.

The solution is not simply “update all docs every time.” Assign a role and authority level.

### Proposed structure

```text
docs/
  CURRENT_STATE.md                current supported product state
  CURRENT_ARCHITECTURE.md         current architecture only
  CAPABILITY_MATRIX.md            implemented/partial/experimental/planned
  DATA_MODEL.md                   generated/current domain model
  API_POLICY.md                   auth/scope/idempotency/audit rules
  clients/
    pc.md
    mobile-web.md
    android.md
    ios.md
    offline.md
  operations/
    local-run.md
    linux-deploy.md
    backup-restore.md
    release.md
  design/
    ... future proposals ...
  history/
    iteration-log.md
```

Existing Chinese document names can remain if preferred; the key is role separation and authority labeling.

## 5. Add document status metadata

Every major design/overview document should start with a small header such as:

```text
Status: CURRENT | DESIGN | EXPERIMENTAL | HISTORICAL
AppliesToCommit: <sha or range>
LastVerifiedAt: <date>
Authority: CODE | SCHEMA | OPERATIONS | DESIGN
Supersedes: ...
SupersededBy: ...
```

Do not fabricate verification dates. Update `LastVerifiedAt` only when a human or deterministic audit actually checked the document against current code.

## 6. Preventing future drift without GitHub Actions

This project must not rely on Actions. Documentation consistency checks should live in repository scripts and be directly runnable.

Suggested local check:

```bash
python3 tools/check_project_consistency.py
```

Possible checks:

- Android README mode matches project overview mode;
- documented artifact names exist or are build outputs of scripts;
- documented directories exist;
- release version references are internally consistent;
- API names referenced by current docs exist in route registry;
- permission codes referenced by docs exist in database seed/current permission registry;
- supported PostgreSQL flag cannot be true unless schema parity tests pass;
- client support states match a machine-readable manifest.

A CI service may optionally call the script, but the script is the authority and must run locally/server-side without CI.

## 7. Recommended machine-readable manifest

Add a future file such as:

```yaml
Schema: INVENTORY_PRODUCT_STATE_V1
Version: 2.x
PrimaryDB: sqlite
SupportedDBs:
  sqlite: production
  postgres: experimental
Clients:
  pc_web: supported
  mobile_pwa: supported
  android_webview: supported
  ios_webview: supported_or_experimental
  offline_pwa: maintenance_or_experimental
Capabilities:
  procurement: supported
  pricing: supported
  manufacturing_work_orders: not_implemented
  lot_serial_traceability: not_implemented
```

This should drive human docs and consistency checks where practical.

## 8. Documentation debt priority

### P0

1. correct Android online/offline conflict;
2. label PostgreSQL as incomplete/experimental until parity exists;
3. refresh current architecture domain/schema map;
4. identify the authoritative supported-client list;
5. close the release-version / iteration-log gap.

### P1

1. add current capability matrix;
2. split current-state docs from future design docs;
3. add document status metadata;
4. implement local consistency checker;
5. make release scripts validate documentation-critical artifact paths.

### P2

1. generate API/permission/schema reference pages from code metadata;
2. archive historical instructions;
3. add automatic changelog extraction from structured release records.

## 9. Preliminary truth-alignment score

0–5 static maturity:

- developer navigation discipline: **4/5**
- recent iteration history: **4/5**
- broad overview freshness: **2/5**
- architecture-document freshness: **2/5**
- deployment/client truth consistency: **2.5/5**
- machine-readable current-state manifest: **1/5**
- local automated doc consistency checks: **1/5**

## 10. Core recommendation

Keep `docs/应用开发索引.md` as the human navigation entry, but stop asking narrative overview files to carry product truth by themselves.

The durable solution is:

`source/schema truth -> machine-readable current-state manifest -> local consistency checks -> concise generated/maintained current docs -> historical/design docs clearly labeled`

This reduces both human and AI/Agent misinterpretation while remaining fully independent of GitHub Actions.