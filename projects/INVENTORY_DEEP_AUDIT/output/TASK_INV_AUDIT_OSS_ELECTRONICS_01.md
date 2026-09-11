# TASK_INV_AUDIT_OSS_ELECTRONICS_01 — Electronics Inventory / BOM / Build Deep Benchmark

## 0. Scope and freshness

Research date: **2026-09-11**.

Inventory Lite evidence remains pinned to `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Benchmark systems:

- InvenTree;
- Part-DB;
- OpenPnP.

These products solve overlapping but different problems. InvenTree is the most relevant reference for electronics-oriented inventory + build management; Part-DB is particularly strong for electronic component cataloguing/data enrichment; OpenPnP is a machine/job execution application and should be treated as an integration boundary rather than an ERP replacement.

## 1. Current maintenance and license snapshot

| System | Current evidence as of 2026-09-11 | License | Best-fit reference role |
|---|---|---|---|
| InvenTree | Stable release `1.5.4`, dated 2026-09-08 | MIT | Electronics parts, supplier parts, stock items/locations, BOM, build orders, traceability, plugins/API |
| Part-DB | Latest release `2.14.1`, dated 2026-08-02 | AGPL-3.0-or-later | Electronic component catalog, attachments, providers, project BOMs, EDA/KiCad integration, labels/search |
| OpenPnP | Stable release `2.6`, dated 2026-03-01 | GPL-3.0 | SMT machine configuration, board/placement job execution, feeders, packages, scripting/events |

### License boundary

The recommendation is to reuse **design ideas and interoperability concepts**, not copy code without legal review. InvenTree's MIT license is permissive; Part-DB's AGPL and OpenPnP's GPL have materially different obligations.

## 2. InvenTree — strongest direct benchmark

### 2.1 Why it is highly relevant

InvenTree explicitly models an electronics-friendly distinction between:

```text
Part = logical/catalog item
Stock Item = physical quantity/instance of that Part in a location
```

A Stock Item can hold:

- location;
- quantity;
- supplier/supplier part;
- serial number;
- batch code;
- status;
- purchase-order relationship;
- build/consumption relationships;
- test results and other tracking metadata.

This directly validates a core W2/W3 conclusion: Inventory Lite needs to separate **part identity** from **stock position/instance/state**, instead of making one `(material, warehouse, platform)` balance row carry every physical meaning.

## 3. InvenTree parametric part model

InvenTree's parameter system provides:

- reusable parameter templates;
- parameter values attached to parts/objects;
- parametric tables;
- sorting/filtering by parameter values.

Critically, official docs state parameters are metadata and **are not used directly for core business logic**.

This is an excellent design boundary for Inventory Lite:

```text
Parametric attributes
 -> search/filter/comparison/documentation

Approved engineering identity / lifecycle / AVL
 -> deterministic business rules
```

Do not let an arbitrary string parameter such as `voltage=5V` silently become a production substitution rule.

## 4. InvenTree manufacturer / supplier separation

InvenTree provides separate company/manufacturer/supplier-part concepts and supplier plugin integrations. The supplier plugin flow can:

```text
search supplier
 -> select category
 -> map parameters
 -> create/import part data
 -> optionally create initial stock
```

This is more mature than Inventory Lite's current supplier + material relationship and supports the W3 target identity stack:

```text
Internal Part
 -> Manufacturer Part (MPN)
 -> Approved supplier/source
 -> Supplier SKU / pricing / lead time
```

Borrow this separation.

## 5. InvenTree stock-item pattern

A particularly portable pattern is the physical `StockItem` entity.

Instead of one balance row attempting to represent:

- bin;
- lot;
- serial;
- supplier receipt;
- quality status;
- owner;
- build provenance;

create a stock-position/item model with those dimensions, then aggregate availability.

For Inventory Lite this could become:

```text
stock_positions
  material_id
  warehouse/location
  lot_id/serial_id
  quality_state
  owner/reservation class
  supplier receipt source
  quantity
```

Not every position needs a serial, but every physical distinction that affects usability should have a structured dimension.

## 6. InvenTree build orders

Official documentation states a Build Order:

- creates stock by assembling a part according to a BOM;
- allocates stock items to required build lines;
- subtracts allocated stock as the build completes;
- supports scheduling/target dates;
- exposes availability/substitute information through API structures.

This is highly aligned with W3's lightweight WO model.

### Portable lesson

Use the BOM to create a **build-specific material requirement/allocation snapshot**, rather than deducting arbitrary components only at completion.

```text
released BOM
 -> build requirement lines
 -> allocate concrete qualified stock
 -> consume
 -> create output stock
```

## 7. InvenTree substitutes / variants

The API schema exposes build-line concepts such as:

- `available_substitute_stock`;
- `allow_variants`;
- BOM item substitutes;
- optional/consumable items.

This validates keeping:

```text
engineering-approved alternate relationship
```

separate from pure parametric similarity.

Inventory Lite should allow an AI/search engine to discover candidates, but only the controlled AVL/substitute domain determines whether a build can use them.

## 8. InvenTree status and traceability

InvenTree stock status includes explicit states such as OK, Attention Needed, Damaged, Destroyed, Rejected, Lost, Quarantined and Returned. Stock items can carry serial/batch and be associated with purchase/build relationships.

This reinforces the target invariant:

```text
physical on hand != available/nettable supply
```

Quality/condition state must be first-class and feed allocation/MRP.

## 9. InvenTree API/plugin architecture

The documented API schema covers:

- authentication;
- background tasks;
- barcode scanning;
- BOM;
- build orders;
- company management;
- label printing;
- external machine management;
- external orders;
- parts/categories;
- plugins;
- reporting;
- stock/locations;
- users.

The API schema itself is versioned, which is a useful pattern for Inventory Lite as integrations expand.

### Portable lessons

1. publish a stable OpenAPI-like contract;
2. separate plugin provider interfaces from core business objects;
3. make labels/barcode/reporting reusable services;
4. keep external-machine integration as a bounded adapter.

## 10. InvenTree ideas to borrow first

### P0

- Part vs Stock Item separation;
- structured manufacturer/supplier part identity;
- parametric templates/filtering;
- build allocation to concrete stock positions;
- lot/serial/batch/status on stock instances;
- controlled substitute relations;
- API schema/versioning.

### P1

- plugin mixins/provider architecture;
- label printing service;
- external stock/location semantics;
- stock-item test-result links;
- external machine integration contract.

### Do not copy blindly

- every InvenTree field/status;
- its entire Django/React architecture;
- offset pagination patterns for large future event tables;
- inventory-specific semantics where Inventory Lite needs e-commerce/settlement/CRM behavior beyond InvenTree's scope.

## 11. Part-DB — strongest reference for component knowledge and engineering catalogue UX

### 11.1 Current evidence

Part-DB 2.14.1 was released 2026-08-02. Release notes around 2.13–2.14 show active work on:

- electronic distributor/provider integration;
- multi-field search;
- project BOM export;
- EDA/KiCad information;
- labels;
- barcode handling;
- AI/MCP read tools;
- permissions/security;
- migrations.

The server is licensed AGPL-3.0-or-later and supports SQLite/MySQL/MariaDB/PostgreSQL through its framework stack.

## 12. Part-DB product lesson: component record as a knowledge hub

Part-DB's primary strength is not general ERP workflow. It treats the electronic component record as the center for:

- classification/category;
- manufacturer/supplier information;
- parameters;
- attachments/datasheets;
- pricing/provider data;
- storage/location;
- labels/barcodes;
- EDA/project BOM relationships.

This closely matches the target Inventory Lite **Part Workspace** from W3/W5.

Recommended Inventory Lite material workspace:

```text
Identity
Parametrics
Manufacturer/MPN
Supplier sources/prices
Stock/locations
Where-used/BOM
Documents/datasheets
Lifecycle/AVL
Quality history
```

## 13. Part-DB provider model

Recent release notes show provider integrations remain a core focus (for example TME provider/API support and other distributor search fixes).

Portable design:

```text
PartDataProvider
  search(query)
  fetch_part(external_id)
  fetch_pricing(...)
  fetch_documents(...)
  provenance
```

Every imported attribute should retain source/provenance and require policy before overwriting approved internal engineering data.

This is preferable to hard-coding LCSC/TME/DigiKey/etc. directly into the material service.

## 14. Part-DB EDA / project BOM lessons

Part-DB 2.14 release work includes project BOM CSV export and EDA/KiCad metadata handling. This confirms the value of a dedicated engineering import/export boundary.

Inventory Lite should not treat an EDA BOM spreadsheet as an ordinary bulk material import.

Use:

```text
EDA BOM
 -> normalize
 -> match internal/manufacturer parts
 -> unresolved/ambiguous review
 -> draft EBOM revision
 -> diff
 -> release
```

The EDA boundary should preserve refdes/package/value/MPN and never silently rewrite production MBOM.

## 15. Part-DB search/security lessons

Recent 2026 releases include fixes for:

- multi-field matching;
- permission checks in MCP/search tools;
- barcode imports;
- label permissions;
- XSS/SVG sanitization;
- spreadsheet formula injection;
- trusted-host configuration.

This is useful evidence for W5's conclusions: flexible electronic-component data/search and uploaded technical files create a real attack surface. Inventory Lite should include:

- output escaping;
- SVG/file sanitization or safe download policy;
- formula-injection-safe exports;
- permission-aware AI/search tools;
- trusted host/origin configuration.

## 16. Part-DB ideas to borrow first

### P0

- component-centric workspace;
- generic information-provider interface;
- source/provenance on imported part data;
- EDA/KiCad import/export mapping;
- strong multi-field electronic part search;
- reusable labels/barcodes.

### P1

- local AI/provider support behind explicit tools;
- electronic part visualization/EDA metadata;
- richer project BOM comparison/export.

### Do not copy blindly

- general component-library UI without production/commerce state;
- AGPL code without license review;
- AI tool availability as authority to modify parts;
- data-provider values as implicitly approved engineering truth.

## 17. OpenPnP — correct role is machine execution boundary

### 17.1 Current evidence

OpenPnP stable 2.6 was released 2026-03-01 and remains an actively developed open-source SMT pick-and-place application under GPL-3.0.

Its core concepts include:

- jobs;
- boards/panels;
- placements;
- parts;
- packages;
- feeders;
- machine/nozzle/camera configuration;
- job planner;
- machine scripting/events.

OpenPnP's job workflow configures boards, placements, parts/packages/feeders and then executes physical placement on a machine.

## 18. Do not make OpenPnP the inventory authority

OpenPnP is designed to drive pick-and-place execution, not to own enterprise inventory, purchasing, sales, lot genealogy or cost truth.

Correct boundary:

```text
Inventory Lite released WO / assembly job
 -> exact product/BOM/placement package
 -> feeder/material allocation
 -> OpenPnP executes machine job
 -> execution events/results return
 -> Inventory Lite records authoritative material/work-order state
```

Do not synchronize by letting both systems independently edit the same inventory balance.

## 19. Part/package/placement mapping

OpenPnP distinguishes:

- Part — logical component used by placement;
- Package — physical footprint/package characteristics;
- Placement — particular board coordinate/refdes using a part;
- Feeder — machine source of the part.

This is a very useful manufacturing mapping:

```text
Internal Part / approved manufacturer part
 -> EDA reference designator / placement
 -> package/footprint
 -> production feeder/reel/lot
```

Inventory Lite's EBOM should preserve refdes; production execution can resolve each build to the actual approved lot/reel allocated to a feeder.

## 20. OpenPnP scripting/events lesson

OpenPnP supports scripting without source modification and exposes job/machine events such as feeder and placement/job events.

Portable integration lesson:

- consume stable execution events;
- do not expose unrestricted scripts inside Inventory Lite core;
- machine adapters must be isolated and permission-scoped;
- make execution callbacks idempotent.

For example:

```text
Job.Started
Placement.Complete
Feeder.Fault
Job.Finished
Job.Error
```

can map to manufacturing telemetry, but stock consumption policy should remain controlled in Inventory Lite.

## 21. OpenPnP integration target for Inventory Lite

A future adapter could export:

```text
production_job_package
  work_order
  product/PCB revision
  placements (refdes, internal part, package)
  approved manufacturer/supplier part
  feeder assignment candidate
```

and import:

```text
machine_job_id
start/end
placement counts
skip/error events
feeder fault
actual part/feed mapping where available
```

Do not claim lot genealogy unless the physical reel/feeder loading process captures lot identity.

## 22. Cross-system capability comparison

| Capability | InvenTree | Part-DB | OpenPnP | Inventory Lite target |
|---|---|---|---|---|
| Electronic part catalogue | Strong | Strong | Basic machine part identity | Strong internal + MPN/provider model |
| Parametric attributes | Strong | Strong focus | Limited relevance | Searchable typed parameters |
| Manufacturer/supplier relation | Strong | Strong provider focus | Not business focus | AVL/source model |
| Stock locations | Strong | Strong component inventory | Feeder/machine source, not warehouse | Bin/stock-position model |
| Lot/serial traceability | Strong | Component inventory features; less manufacturing-centric | Not ERP authority | Risk-based lot/serial genealogy |
| BOM | Strong | Project BOM focus | Placements/jobs rather than ERP BOM | EBOM + MBOM + sales BOM |
| Build/work order | Strong | Project-focused | Physical machine job | Lightweight WO with machine adapter |
| Substitutes | Strong BOM substitute concepts | Candidate/provider data | Feeder/job choices, not engineering AVL | Explicit approved/conditional alternate |
| Labels/barcodes | Strong | Strong | Machine-specific identifiers | Shared label/scan service |
| API/plugins | Strong documented schema/plugins | Modern web API/provider/MCP work | Java scripting/events | Versioned API + constrained providers |
| Machine execution | External-machine support only | No | Core strength | Integrate, do not rebuild |

## 23. Most important portable patterns

### Pattern A — logical part vs physical stock instance

From InvenTree. Highest-value W3 data-model change.

### Pattern B — parameter metadata is not business authority

From InvenTree. Use parameters for discovery; released AVL/revision rules for manufacturing.

### Pattern C — provider/provenance layer

From InvenTree + Part-DB. External distributor/manufacturer data should enter through adapters and retain source.

### Pattern D — build allocation to concrete stock

From InvenTree. Reservation/WO material line needs actual stock-position allocation before consumption.

### Pattern E — component workspace

From Part-DB. Make the part page a knowledge + supply + stock + engineering hub.

### Pattern F — explicit EDA boundary

From Part-DB + OpenPnP. Normalize EDA parts/refdes/package separately from inventory/import semantics.

### Pattern G — machine system is an adapter

From OpenPnP. Inventory Lite owns business/work-order truth; machine software owns physical placement execution.

## 24. Recommended implementation sequence influenced by this benchmark

### Phase 1

1. internal part / manufacturer part / supplier part separation;
2. parametric templates;
3. stock-position / stock-item model;
4. bin/location/quality/lot dimensions;
5. global exact/parametric part search.

### Phase 2

1. revisioned EBOM with refdes;
2. provider interfaces;
3. EDA staging/matching/diff;
4. build/work-order allocation;
5. labels/barcodes.

### Phase 3

1. lot/serial genealogy;
2. test results on serialized stock;
3. external machine adapter contract;
4. OpenPnP job export/result import;
5. supplier/distributor data refresh.

## 25. Sources

Current public evidence consulted on 2026-09-11:

### InvenTree

- Stable release notes: https://docs.inventree.org/en/stable/releases/release_notes/
- GitHub/license: https://github.com/inventree/InvenTree
- Stock items/locations/traceability: https://docs.inventree.org/en/stable/stock/
- Parameters: https://docs.inventree.org/en/stable/concepts/parameters/
- Build orders: https://docs.inventree.org/en/stable/manufacturing/build/
- API schema: https://docs.inventree.org/en/stable/api/schema/
- BOM API/schema: https://docs.inventree.org/en/stable/api/schema/bom/
- Supplier plugin mixin: https://docs.inventree.org/en/stable/plugins/mixins/supplier/

### Part-DB

- Releases: https://github.com/Part-DB/Part-DB-server/releases
- Repository: https://github.com/Part-DB/Part-DB-server
- License metadata: https://github.com/Part-DB/Part-DB-server/blob/master/composer.json

### OpenPnP

- Releases: https://github.com/openpnp/openpnp/releases
- Repository/license: https://github.com/openpnp/openpnp
- User manual: https://github.com/openpnp/openpnp/wiki/User-Manual
- Scripting/events: https://github.com/openpnp/openpnp/wiki/Scripting
- Version 2.6 changes: https://github.com/openpnp/openpnp/blob/main/CHANGES.md

## 26. Acceptance signals

- exact current release evidence is dated;
- InvenTree, Part-DB and OpenPnP are compared according to their actual product boundaries;
- electronics-specific MPN/supplier/parameter/BOM/refdes/build/traceability concepts are analyzed;
- the benchmark identifies integration patterns rather than recommending one system wholesale;
- OpenPnP is explicitly treated as machine execution, not stock authority;
- code-license differences are explicit;
- recommendations map directly onto W3/W5 target models;
- no required integration or validation path depends on GitHub Actions.

## 27. Core recommendation

The most valuable external pattern is InvenTree's **Part -> physical Stock Item -> Build Allocation** chain, combined with Part-DB's component knowledge/provider/EDA focus and OpenPnP's explicit machine-job boundary. Inventory Lite should become the authoritative business spine connecting these concepts, not attempt to make one mutable `materials + inventory` pair or the pick-and-place software own every layer.