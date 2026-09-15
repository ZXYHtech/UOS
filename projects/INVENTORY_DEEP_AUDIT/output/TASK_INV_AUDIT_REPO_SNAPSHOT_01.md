# TASK_INV_AUDIT_REPO_SNAPSHOT_01 — Inventory Lite repository snapshot and audit entry map

## 1. Snapshot identity

- Repository: `ZXYHtech/inventory`
- Default branch: `main`
- Pinned commit: `78d5cda2527cf24836cd5b82a41f02ca8efdd02c`
- Commit timestamp: `2026-08-10T04:47:40Z`
- Commit message: `限制库存服务内存并保护代理进程`
- Pinned tree: `8f504df62c5678e23ce81d8a30f92d252f277cb6`
- Audit mode: read-only external repository evidence. Do not modify Inventory Lite from this project.

All follow-up findings in this audit should be tied either to the pinned commit above or explicitly marked as a later refresh.

## 2. Canonical source-of-truth hierarchy

The repository itself already defines a useful precedence rule. For implementation truth, use the following order:

1. `docs/应用开发索引.md` — navigation map and handoff entry point.
2. `docs/迭代执行记录.md` — recent change/deployment history and regression evidence.
3. Current source code — implementation truth.
   - `inventory_app/database.py`: SQLite schema, migrations, seed and DB helpers.
   - `inventory_app/services.py`: core domain/business write rules.
   - `inventory_app/server.py`: HTTP routing, authentication, permission enforcement and warehouse data scope.
   - `inventory_app/recognition.py`: OCR / recognition logic and provider behavior.
   - `inventory_app/static/app.js`: PC web application behavior and page routing.
   - `mobile/app.js`: online mobile application behavior.
4. `docs/逐步迭代提示词库.md` — intended staged requirements and acceptance intent.
5. `docs/Agent接手工作流.md` — operational/testing/release process.

When documentation and implementation disagree, the audit must treat current schema + services + server-side permission checks as authoritative and mark the document as drift, not silently reconcile it.

## 3. Repository map

### 3.1 Backend / domain core

`inventory_app/`

- `database.py` — 78,232 bytes. Schema, compatibility migration, seed, database helpers.
- `services.py` — 418,714 bytes. Core business services and integrations. This is already a major concentration hotspot.
- `server.py` — 277,525 bytes. REST-style HTTP endpoints, auth, permission checks, warehouse scope and static serving. Second major concentration hotspot.
- `recognition.py` — 112,600 bytes. OCR / screenshot-order recognition logic.
- `ocr_queue.py` — 11,472 bytes. Isolated OCR queue / process behavior.
- `image_assets.py` — 23,971 bytes. Image asset handling.
- `digit_classifier.py` + `models/digit_35_templates.json` — specialized OCR digit correction model assets.

### 3.2 PC client

`inventory_app/static/`

- `app.js` — 664,489 bytes. The single largest source file in the system and the dominant PC UI/router/state concentration point.
- `styles.css` — 54,086 bytes.
- `index.html` — 306 bytes; effectively a shell around the JavaScript application.

### 3.3 Online mobile client

`mobile/`

- `app.js` — 305,031 bytes.
- `styles.css` — 19,562 bytes.
- PWA manifest + service worker.

The online mobile client is a second independently evolved front-end rather than a thin responsive view over the PC client, so feature parity and duplicated business presentation rules must be audited explicitly.

### 3.4 Offline mobile client

`mobile-offline/`

- `app.js` — 20,029 bytes.
- PWA shell, local/offline data and service worker.

The root README still describes this as an independent offline mobile capability, but Android is no longer supposed to ship this offline bundle.

### 3.5 Android wrapper

`android-offline-app/`

Despite the directory name, its README explicitly states that it is now an **online WebView APK** only. It points to `/mobile/`, stores business data on the server and does not provide offline stock modification.

Important duplication evidence:

`android-offline-app/app/src/main/assets/offline/` has the exact same tree SHA as `mobile-offline/` (`18e3ad66a19e5604a6885cd0aa15075680aa6a1e`). The embedded offline files also have identical blob SHAs. The Android README simultaneously says that the APK no longer packages offline web resources. This is a strong cleanup / stale-artifact candidate and should be verified against `build.gradle`, packaging rules and release scripts before deletion.

### 3.6 iOS wrapper

`ios-app/`

- Native `WKWebView` app.
- Includes an iOS share extension.
- Default target is the same online `/mobile/` surface.
- Build path is separate from Android and web release paths.

This is another client surface requiring parity/version/release ownership review.

### 3.7 Deployment and databases

`deploy/`

- `linux/`: server setup, HTTPS configuration, release, update and restart scripts.
- `sqlite/`: database construction and one-off repair utilities.
- `postgres/`: `schema.sql`, `seed.sql`, initialization shell.

Important architectural boundary: `inventory_app/database.py` is described by the project as the SQLite schema and migration source of truth. PostgreSQL is a reserved migration target. The audit must therefore treat `deploy/postgres/schema.sql` as a separate implementation that can drift, not as automatically equivalent.

### 3.8 Tests and operational tools

There is no dedicated `tests/` tree in the pinned snapshot. Tests live under `tools/`:

- `test_core_workflows.py` — 72,734 bytes.
- `test_client_routing.js` — 45,842 bytes.
- `test_auth_security.py`.
- OCR workflow/sample/stress tests.
- image derivative stress test.
- warehouse efficiency test.

The pinned tree contains no `.github/` directory, so there is no repository-local GitHub Actions CI definition at this commit. The audit must distinguish “tests exist and were run manually/by scripts” from “tests are automatically enforced for each change”.

### 3.9 Documentation and business references

`docs/` contains both living engineering documentation and bulky business/reference artifacts:

- Architecture, handoff, requirements, OCR, procurement/cost, pricing, order/fulfilment rules, security and server/mobile docs.
- `docs/迭代执行记录.md` is unusually large (213,197 bytes) and has become a long-lived change journal.
- `docs/企业主数据管理体系_V1.0_完整包_3.zip` is ~5.5 MB binary content stored in Git.
- `docs/商品型号_库存_淘宝SKU_统一管理表_含分类.xlsx` is also a binary business-reference artifact.

These files are legitimate evidence but should not be confused with executable source-of-truth. Binary reference artifacts also increase repository weight and need ownership/version rules.

## 4. Current documented product scope

The pinned documentation indicates that Inventory Lite now covers substantially more than basic stock counts:

- identity / role / permission model;
- multi-warehouse access scope;
- product/material master data, aliases, categories and BOM/package relations;
- inventory balances, safety-stock warnings and movement ledger;
- screenshot/OCR order intake with mandatory human confirmation;
- order, shipment and warehouse task flow;
- transfer-out / receive / discrepancy lifecycle;
- purchasing, suppliers and cost functions;
- product pricing and commercial material/profile data;
- warehouse locations/layout;
- platform accounts and Taobao integration boundaries;
- import/export, backups and operation audit logs;
- PC, online mobile, offline PWA, Android and iOS surfaces.

This scope means that future evaluation must use an ERP/WMS/manufacturing/commerce frame, not a simple inventory-app checklist.

## 5. Immediate structural observations

### 5.1 Monolithic concentration is now material

Four files dominate major layers:

- PC `app.js`: 664 KB
- `services.py`: 419 KB
- mobile `app.js`: 305 KB
- `server.py`: 278 KB

This does not prove defects by itself, but it predicts higher change coupling, weak module ownership, difficult selective testing, merge conflicts, duplicated state logic and higher Agent context cost. The architecture audit should quantify classes/functions/routes/page modules inside these files before recommending any split.

### 5.2 Documentation has already outgrown the original MVP architecture note

`docs/architecture.md` still describes an MVP-style entity and API set, while `docs/应用开发索引.md` and the iteration journal describe many later domains such as procurement/cost, pricing/material profiles, category audit, backup/restore, richer transfer states and mobile workflows.

Therefore `architecture.md` must be treated as **historical baseline / partial architecture documentation**, not as a complete current-system specification.

### 5.3 Naming drift exists in mobile packaging

The directory `android-offline-app` now documents an online-only APK. Meanwhile a full duplicate offline asset bundle remains in the Android project tree. This is a concrete example of naming/artifact drift that can mislead future maintainers and Agents.

### 5.4 Multiple data models must be compared, not assumed equal

There are at least three persistent-data representations to inspect:

1. SQLite live schema and migrations in `database.py`.
2. PostgreSQL migration-target schema under `deploy/postgres/`.
3. Browser-local/offline data model in `mobile-offline/`.

Any future claim that the system is “PostgreSQL ready” or “offline sync ready” must be proven with field/state/constraint parity rather than inferred from the presence of scripts.

### 5.5 Test assets exist, but automated enforcement is not visible in the pinned tree

The repository has substantial test scripts, including core workflow and client routing tests, but no `.github` CI configuration in this snapshot. Reliability assessment must separately score test coverage, repeatability, fixture isolation and automatic enforcement.

### 5.6 Existing open-source absorption document is useful but too narrow for the new goal

`docs/开源系统功能吸收与移植方案.md` already references InvenTree, Dolibarr, ERPNext, Tryton and Odoo Community and deliberately keeps Inventory Lite lightweight. That earlier conclusion is now an input, not a final constraint: the new audit explicitly evaluates suitability for electronics R&D, manufacturing, sales and after-sales, so previously deferred MRP/manufacturing functions must be reassessed against the expanded business goal.

## 6. Reproducible audit entry sequence

Every follow-up source audit should begin with this sequence:

```text
1. Confirm target repository = ZXYHtech/inventory
2. Confirm pinned commit = 78d5cda2527cf24836cd5b82a41f02ca8efdd02c
3. Read AGENTS.md
4. Read docs/应用开发索引.md
5. Read the latest relevant section of docs/迭代执行记录.md
6. Open only the source-of-truth files for the target domain
7. Compare docs against code; code wins when they conflict
8. Record exact file/function/API/table evidence in the task output
9. Mark finding type: FACT / INFERENCE / PROPOSAL
10. Do not write to ZXYHtech/inventory from this UOS audit project
```

Domain routing:

| Audit question | Primary source |
| --- | --- |
| DB entities / migrations / permissions seed | `inventory_app/database.py` |
| Inventory / orders / shipments / transfers / purchasing / costing | `inventory_app/services.py` |
| API enforcement / auth / warehouse scope | `inventory_app/server.py` |
| OCR and recognition | `inventory_app/recognition.py`, `ocr_queue.py` |
| PC pages and UX | `inventory_app/static/app.js`, `styles.css` |
| Online mobile | `mobile/app.js`, `mobile/styles.css` |
| Offline behavior | `mobile-offline/` |
| Android wrapper | `android-offline-app/` |
| iOS wrapper | `ios-app/` |
| Release/deployment/DB target | `deploy/` |
| Regression evidence | `tools/test_*`, `docs/迭代执行记录.md` |

## 7. Baseline risk / opportunity hypotheses for follow-up tasks

These are hypotheses, not final findings:

1. **Architecture modularity risk — HIGH**: core server, services and PC/mobile UIs have become very large single files.
2. **Schema parity risk — HIGH**: SQLite, PostgreSQL and offline data models may not evolve in lockstep.
3. **Client parity risk — HIGH**: PC, mobile, Android and iOS are separate release surfaces with duplicated UX/business presentation logic.
4. **Manufacturing completeness gap — likely HIGH**: current BOM/procurement/cost features do not by themselves prove revision-controlled EBOM/MBOM, ECO, MRP, work orders, WIP, quality or genealogy.
5. **Commerce integration opportunity — HIGH**: current platform account / Taobao adapters provide a foundation for a broader channel integration layer.
6. **Automation opportunity — HIGH**: OCR queue, adapter abstractions, operation logs and service-layer writes provide good anchor points for rules/agents/background jobs.
7. **Governance/CI opportunity — MEDIUM-HIGH**: substantial tests exist but pinned repository has no visible CI definition.
8. **Repository hygiene opportunity — MEDIUM**: duplicate offline assets and binary reference packs make source ownership/versioning harder.

Each hypothesis must be confirmed or rejected by later tasks.

## 8. Next unlocked audit work

This snapshot is sufficient to begin the following current-state tasks once the UOS lifecycle permits them:

- capability/workflow matrix;
- data-model and lifecycle audit;
- API and permission audit;
- architecture/modularity audit;
- PC/mobile/offline UX parity audit;
- testing/observability and deployment audit.

The parallel open-source landscape task can proceed independently using current public evidence.
