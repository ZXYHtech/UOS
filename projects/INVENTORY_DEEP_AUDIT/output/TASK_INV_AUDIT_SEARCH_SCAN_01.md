# TASK_INV_AUDIT_SEARCH_SCAN_01 — Global Search, Barcode/QR and Fast Warehouse Interaction Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed material code/name/model/barcode/QR/alias search behavior, OpenPnP migration notes, warehouse/mobile UX, shipment scan logs and future MPN/lot/serial requirements.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite already has a surprisingly capable **material matching engine**. Existing documentation describes real-time candidate search across code, name, model/MPN-like field, package/category, barcode/QR and aliases, with code-priority ranking, variant protection, current-stock context and explicit user choice for ambiguous candidates. OCR/BOM matching also includes normalization and low-risk correction rules.

The gap is that search remains mostly **material-selection functionality inside individual workflows**, rather than a unified cross-entity navigation and scan-command layer.

The next step should therefore preserve the existing matching logic and elevate it into two shared services:

```text
Global Search Service
Scan Resolution Service
```

Preliminary maturity:

- material candidate matching: 4/5
- alias/code normalization: 4/5
- ambiguity safety: 4/5
- global cross-entity search: 1.5/5
- barcode/QR identity governance: 2.5/5
- scan-first warehouse workflows: 2.5/5
- future lot/serial scanning: 0.5/5

## 2. Existing search behavior worth preserving

The documented material matcher already follows strong rules:

- material code has highest priority;
- exact/normalized code matches outrank fuzzy text;
- code separators/case can be normalized;
- aliases participate in candidate retrieval;
- barcode and QR can match;
- multiple candidates require explicit user selection;
- a requested detailed/variant code must not silently fall back to a parent/base model;
- candidate result can show inventory context;
- selected value resolves back to canonical material code.

These are excellent master-data safety principles and should become shared contracts, not be reimplemented separately in PC/mobile/OpenPnP/AI flows.

## 3. Separate retrieval, ranking and action

Design search in layers:

```text
Normalize input
 -> retrieve candidates
 -> rank/explain matches
 -> user/system selects canonical object
 -> workflow performs separately authorized action
```

Search itself must never mutate stock/master data because a candidate scored highly.

This is especially important for OCR, AI and scan flows.

## 4. Global cross-entity search

Target one command/search surface across:

- internal material/SKU;
- manufacturer/MPN;
- supplier part number;
- aliases/legacy/customer code;
- barcode/QR;
- order number;
- logistics/tracking number;
- purchase order;
- transfer;
- future work order;
- supplier/customer;
- warehouse/location;
- lot/date code;
- serial number;
- RMA/service case;
- controlled document number.

Each result should show:

```text
object type
primary identity
secondary context
current status
important warning
matched field
```

and open the entity workspace/deep link directly.

## 5. Search result safety

A result should explain why it matched:

```text
Exact material code
Alias: legacy code ZYX...
MPN exact match
Tracking number
Serial number
```

Do not merge objects merely because display text is similar.

For ambiguous matches, never auto-open/auto-act on first result.

## 6. Electronics part search model

After W3 parametric master implementation, index:

- internal part code;
- manufacturer;
- MPN;
- package/footprint;
- value/tolerance;
- aliases;
- supplier SKU;
- lifecycle;
- parametric attributes;
- datasheet/document identifiers.

Use structured filters alongside text search:

```text
category=amplifier IC
frequency range
package
manufacturer
lifecycle=active
approved/preferred
stock > 0
```

Do not substitute full-text fuzzy search for exact MPN identity.

## 7. Search index architecture

For current scale, a dedicated Elasticsearch/OpenSearch cluster is likely unnecessary.

Recommended progression:

### Stage 1

Database queries + normalized search columns + targeted indexes.

### Stage 2

SQLite FTS5 or PostgreSQL full-text/trigram after backend evolution if measured need exists.

### Stage 3

External search engine only if data volume/relevance/analytics justify operational overhead.

Search index is a projection. Canonical business object remains database source of truth.

## 8. Normalization contract

Centralize functions for:

- Unicode width/dash normalization;
- trim/case normalization;
- code compacting while preserving canonical display;
- natural numeric sorting;
- manufacturer/MPN punctuation normalization where safe;
- phone/tracking normalization in their own domains.

Do not use one destructive normalization for every identifier.

For example `ABC-10` and `ABC10` may be searchable as equivalents, while canonical code must stay unchanged.

## 9. Barcode/QR identity types

Do not treat every scan as a material code string.

Define scan payload types:

```text
MATERIAL
LOCATION
LOT
SERIAL
ORDER
SHIPMENT
TRANSFER
PO
WORK_ORDER
RMA
PACKAGE
UNKNOWN_EXTERNAL
```

A barcode registry can map opaque code to canonical object:

```text
scan_identifiers
  code_type
  code_value
  entity_type
  entity_id
  active
  source
  created_at

UNIQUE(code_type/code_namespace, code_value)
```

Manufacturer/supplier barcodes may require parsing standards or scoped namespaces rather than global uniqueness assumptions.

## 10. QR content policy

Prefer QR codes containing a stable internal identifier/URL/token such as:

```text
zxyh://serial/<id>
```

or a short signed/opaque reference.

Do not encode mutable stock quantity/status in permanent labels.

Printed labels should remain useful even after location/status changes.

## 11. Scan resolution

A central resolver takes raw scanned text and context:

```text
resolve_scan(raw, user, current_task)
 -> exact typed candidates
 -> permitted contextual actions
```

Example:

```text
scan location A-03
 -> show contents
 -> count / move / putaway tasks

scan material PE43711
 -> show stock by location
 -> tasks requiring it

scan serial RF-2026-...
 -> product/test/shipment/RMA history
```

The resolver identifies objects; domain services authorize actions.

## 12. Task-context validation

Inside a pick/receive/WO task, scanning should be stricter than global lookup.

Example:

```text
Expected: MPN/internal part A, lot-controlled
Scanned: alternate B
```

System should:

- identify B;
- check AVL/substitution policy;
- show why it differs;
- block or route approval;
- never treat “similar name” as acceptable.

## 13. Receive-by-scan

PO receipt flow:

```text
scan PO / supplier label
 -> resolve open line
 -> scan material/MPN
 -> lot/date code if required
 -> quantity
 -> location
 -> IQC state
 -> receipt confirmation
```

Reduce typing but preserve explicit quantity and inspection semantics.

## 14. Pick/ship-by-scan

Recommended sequence:

```text
scan shipment/task
 -> show source location
 -> scan location
 -> scan material/lot/serial
 -> validate reservation
 -> quantity
 -> pack/package
 -> complete
```

Every mismatch should stop or explicitly branch to exception handling.

## 15. Transfer-by-scan

Outbound:

```text
transfer -> source location -> material/lot -> qty -> dispatch
```

Inbound:

```text
transfer/package -> destination -> material/lot -> received qty
 -> normal or discrepancy
```

Reuse current partial-receipt/exception logic rather than bypassing it with scan shortcuts.

## 16. Count-by-scan

Stock count should record **observation**, not directly overwrite balance.

```text
scan location
 -> scan item/lot
 -> count observed qty
 -> compare expected later according to blind-count policy
 -> variance approval
 -> controlled adjustment
```

Allow blind counting to reduce confirmation bias if business chooses it.

## 17. Manufacturing scan flow

Future WO:

- scan WO;
- scan kit location;
- scan component lot/serial;
- issue;
- scan finished serial label;
- record test/release.

This makes genealogy a natural by-product of execution instead of manual paperwork.

## 18. Duplicate/incorrect label handling

Detect:

- same barcode assigned to two active internal materials;
- serial duplicate;
- retired/obsolete label;
- unknown supplier code;
- damaged/unreadable code;
- lot code format ambiguity.

Never “fix” duplicate identities by auto-selecting the newest row.

Provide merge/remap master-data workflow with audit.

## 19. Label printing

Support templates by object type:

- material/bin label;
- incoming lot;
- finished serial;
- work-order traveler;
- shipment/package;
- RMA.

Template should define:

- human-readable identity;
- barcode/QR;
- optional revision/lot;
- label size/printer;
- template revision.

For controlled serial labels, prevent accidental reissue/duplicate printing or at least record reprint history.

## 20. Scanner hardware modes

Support progressively:

- keyboard-wedge USB/Bluetooth scanner;
- phone camera;
- native Android scanner intent/API if useful;
- industrial handheld later.

Core scan resolver should not depend on hardware type.

## 21. Speed target

Warehouse scan UX should minimize round trips without sacrificing authority.

Useful techniques:

- prefetch expected task lines/locations;
- local lookup cache for identifiers;
- server validates final command;
- immediate audio/haptic success/error feedback;
- retain task context between scans;
- focus scan field automatically.

Do not cache authoritative stock writes locally merely to make scans feel fast.

## 22. Search analytics

Track privacy-safe operational metrics:

- zero-result queries;
- ambiguous-result rate;
- manual candidate override;
- scan unknown-code rate;
- common aliases used;
- time-to-selection;
- master-data defects discovered.

This helps improve naming/aliases/indexes.

Do not log sensitive arbitrary query text forever without retention policy.

## 23. Priority roadmap

### P0

1. extract existing material matching into shared/searchable contract;
2. global cross-entity search surface;
3. centralized scan resolver and typed code namespaces;
4. entity deep links;
5. consistent exact/alias/MPN ranking and match explanation;
6. scan-to-pick/receive/transfer/count prototypes;
7. duplicate label/identity validation.

### P1

1. parametric part filters;
2. location/lot/serial scanning;
3. label-template system and reprint audit;
4. mobile camera optimization;
5. saved/recent searches;
6. FTS/index projection if measured query scale requires it.

### P2

1. GS1/manufacturer barcode parsing where business value exists;
2. industrial handheld integration;
3. search recommendations/semantic assistance with exact-identity guardrails.

## 24. Acceptance signals

- existing exact/variant/alias material matching behavior is preserved during extraction;
- a global query can find an order, MPN, supplier, location or future serial without knowing its module;
- ambiguous candidates are never silently auto-selected;
- scanning a code resolves a typed canonical object before an action occurs;
- wrong location/material/lot in a task is blocked or explicitly routed to exception;
- duplicate active barcode/serial identities are detected;
- stock count scan records observation then controlled variance, not direct unlogged overwrite;
- scan actions still pass normal permission/state/idempotency checks;
- no required search indexing/scan sync/test process depends on GitHub Actions.

## 25. Core recommendation

Do not rebuild material search; it is already one of the stronger UX primitives. **Extract and generalize it** into global search plus typed scan resolution, then make warehouse/mobile workflows scan-first. This improves speed while preserving exact part identity, ambiguity safety and future lot/serial genealogy.