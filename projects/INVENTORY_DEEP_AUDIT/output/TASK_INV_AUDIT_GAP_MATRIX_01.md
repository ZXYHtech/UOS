# TASK_INV_AUDIT_GAP_MATRIX_01 — Weighted Current-System vs Target-Needs Gap Matrix

## 0. Purpose and evidence discipline

This matrix synthesizes all completed audit outputs through W6 and the pinned Inventory Lite source:

`ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`

It compares:

1. what the current system demonstrably supports;
2. what an e-commerce electronics R&D / production / sales company needs next;
3. the operational/business risk of the gap;
4. implementation difficulty and prerequisites;
5. patterns observed in maintained open-source peers.

### Important scoring boundary

The 0–5 maturity values are **ordinal audit bands**, not mathematically precise measurements and not production certifications.

- `0` — absent as a first-class capability;
- `1` — fragments/fields/manual workaround;
- `2` — partial workflow, important missing invariants;
- `3` — usable for current small-team operation with meaningful limitations;
- `4` — strong, auditable operational capability;
- `5` — highly controlled, mature and scale-proven for the target business.

Difficulty is also relative:

- `S` — small/local improvement;
- `M` — multi-file/domain change;
- `L` — new aggregate/state model or migration;
- `XL` — cross-domain foundational migration.

## 1. Executive conclusion

Inventory Lite is **not an early prototype**. It already has strong day-to-day order/fulfilment, transfer, OCR confirmation, pricing, procurement primitives, permissions, audit logs and useful operator workflows.

The system's main gap is not feature count. It is the absence of several **business-truth kernels** needed before safely automating and scaling an electronics company:

```text
Stock truth
  -> location/state/lot/serial + reservation + idempotent ledger

Engineering truth
  -> internal part/MPN/supplier identity + revisioned EBOM/MBOM + ECN/doc control

Manufacturing truth
  -> WO + issue/return/scrap/output + quality/test genealogy

Commerce truth
  -> canonical external objects + ATP publication + RMA + settlement economics

Operational truth
  -> migrations + security hardening + recovery drill + observability/release gate
```

The correct strategy is therefore **foundation first, domain expansion second, optimization/AI third**.

## 2. Weighted gap matrix

| # | Capability dimension | Current maturity | Target need | Business impact if missing | Difficulty | Priority | Main prerequisite(s) | Peer pattern/reference |
|---:|---|---:|---|---|---|---|---|---|
| 1 | Stock identity / quantity semantics | 2.0 | physical, qualified, reserved, incoming, engineering, quarantine, external-WIP separated | **Critical**: oversell, wrong ATP/MRP, hidden non-saleable stock | XL | **Must** | canonical stock model | Medusa reservation; InvenTree StockItem; ERP/WMS ledger |
| 2 | Reservation / allocation | 1.5 | first-class reservation linked to order/WO/project and consumed/released explicitly | **Critical**: concurrent orders can promise same stock | L | **Must** | stock identity + idempotent movement | Medusa ReservationItem; WMS allocation |
| 3 | Bin/location-level stock | 2.0 | one material may exist in multiple bins/lot/state positions | **High**: scan/pick/count accuracy and WMS growth blocked | XL | **Must** | stock-position redesign | OpenBoxes receiving/bin; Odoo locations |
| 4 | Stock ledger idempotency / reversals | 2.5 | unique business-operation identity; compensating reversals | **Critical**: retry/double-click/concurrency can duplicate effects | L | **Must** | ledger contract | ERPNext ledger; OpenBoxes rollback; Medusa workflow compensation |
| 5 | Electronics part master | 2.0 | internal part + manufacturer + MPN + supplier part + lifecycle + typed parameters | **High**: BOM sourcing/substitution/search remain ambiguous | L | **Must** | master-data migration | InvenTree / Part-DB |
| 6 | AVL / controlled substitutes | 1.0 | approved/conditional alternate relationships with effectivity/reason | **High**: wrong substitute can affect product performance/reliability | L | **Must** | part identity + revision model | InvenTree substitutes |
| 7 | Revisioned EBOM / MBOM / ECN | 0.5–1.0 | immutable released revisions, refdes, EBOM→MBOM baseline, ECO/ECN | **Critical**: cannot prove what product revision should be built | XL | **Must** | part master + document state model | ERPNext submitted BOM; Odoo/TC-style controlled flow |
| 8 | Document / firmware control | 1.0 | immutable released revisions/checksum/applicability/supersession | **High**: wrong drawing/firmware/test file may be used | L | **Must** | revision/effectivity concepts | controlled ERP docs + Part-DB resource hub |
| 9 | Work order / production execution | 0.5 | released WO, reservation, kitting, issue/return/scrap, partial completion/output | **Critical** for production: no controlled WIP/material genealogy | XL | **Should (early)** | released MBOM + stock/reservation | InvenTree Build; ERPNext/Odoo WO |
| 10 | MRP / material planning | 1.0 | time-phased netting across released demand and qualified supply | **High**: shortages/excess procurement and manual planning | XL | **Should (early)** | reservation + MBOM + WO/open supply | ERPNext/Odoo planning |
| 11 | Lot/serial genealogy | 0.5 | risk-based lot/serial policy and supplier→build→shipment→RMA chain | **Critical for traceable RF products** | XL | **Should (early)** | stock position + WO | InvenTree; ERPNext; Odoo; Tryton stock-lot |
| 12 | Quality / IQC / NCR / MRB | 0.5–1.0 | stock quality states, inspection, disposition, rework/scrap/SCAR | **Critical**: rejected/quarantine material can otherwise appear usable | L/XL | **Should (early)** | stock state + receipt/WO transitions | Tryton quality; ERPNext/Odoo QC |
| 13 | RF/electrical test records | 0.5 | serial/lot-linked structured results + raw files + limits + equipment/calibration | **High**: cannot prove released unit performance or debug RMA efficiently | L | **Should** | serial genealogy + document/equipment masters | InvenTree test links; manufacturing evidence pattern |
| 14 | Procurement maturity | 3.0 | supplier-part, lead time/MOQ, quality, MRP pegging, supplier performance | **High** but current workflow is already usable | M/L | **Should** | part master + quality + MRP | ERPNext/Odoo procurement |
| 15 | Omnichannel durable synchronization | 2.0 | external-object ledger, cursor/retry, fulfilment/inventory/refund reconciliation | **High**: manual sync burden and channel divergence | L | **Should** | reservation/ATP + durable jobs | Saleor apps; Medusa modules/workflows |
| 16 | Order fulfilment execution | 4.0 core / 1.5 reservation | preserve mature shipment task, add reservation/bin/parcel/serial semantics | **High**: current strength should not be rewritten | M/L | **Must to evolve, not replace** | reservation + stock position | OpenBoxes/Odoo picking |
| 17 | CRM / quotation / sample lifecycle | 1.0–1.5 | lightweight technical lead→quote revision→sample→order follow-up | **Medium/High**: inquiries and technical sales knowledge stay fragmented | M/L | **Should** | customer identity + pricing | Tryton opportunities; ERP CRM patterns |
| 18 | Returns / RMA / warranty | 0.5–1.0 | authorization, receipt inspection, serial diagnosis, repair, replacement/refund | **High** for electronics support and traceability | L | **Should** | serial + quality + order/shipment | Medusa returns + RF-specific extension |
| 19 | Customer-service case management | 1.5 | customer case/ticket, ownership, SLA, conversation/order/RMA context | **Medium**: internal exceptions exist but customer support history is weak | M | **Should** | customer/RMA linkage | CRM/helpdesk patterns |
| 20 | Pricing | 3.5–4.0 | preserve lists/rules/revisions; fix margin-vs-markup semantics | **High** due terminology risk, but foundation strong | S/M | **Must quick fix** | canonical formula tests | Medusa pricing; ERP pricing |
| 21 | Channel economics / contribution margin | 1.0 | platform/payment/freight/tax/refund/settlement events + reconciliation | **High**: revenue can look healthy while channel loses money | L | **Should** | order snapshots + cost basis + connector | commerce settlement/economic event patterns |
| 22 | Manufacturing cost accounting | 1.0 actual / 3.0 estimated | standard cost version + actual WO issue/labor/overhead/scrap/subcontract variance | **High** for profitability and product decisions | XL | **Should after WO** | WO + genealogy + economics | ERP standard/actual costing patterns |
| 23 | Product intelligence | 1.0–1.5 | measured scorecard: sales, contribution, turns, stockout, support, supplier/lifecycle risk | **Medium/High** strategic value | M | **Could** | economics + CRM + stock metrics | BI/read-model patterns |
| 24 | Executive reporting / KPI lineage | 1.5–2.0 | exception-first daily view + weekly/monthly flow/economics with metric definitions | **Medium/High**: management decisions otherwise require manual joining | M | **Should** | lifecycle timestamps + economics | reporting/read-model pattern |
| 25 | Desktop UX / entity workspaces | 3.0 | task-oriented IA + material/product/order/customer/serial workspaces | **Medium** productivity issue, growing with feature count | M | **Should** | domain model cleanup | Part-DB component hub; mature ERP entity pages |
| 26 | Global search / barcode / scan | 3.0 search / 2.5 guided scan | shared resolver across part/MPN/alias/order/location/serial; scan-to-action | **High** warehouse/R&D speed and error prevention | M | **Should** | stock location/serial semantics | Part-DB/InvenTree/Odoo Barcode |
| 27 | Mobile online execution | 3.5–4.0 | scan-first guided physical tasks, explicit network write status | **Medium/High** current asset worth refining | M | **Should** | shared state/action contract | Odoo Barcode/WMS mobile |
| 28 | Offline business mutation | 1.5–2.0 authority clarity | choose read-cache, emergency package or true conflict-aware offline; no ambiguous multi-master | **High risk if misunderstood** | XL for true offline | **Later / decision gate** | offline systems require conflict semantics |
| 29 | Security / secrets | 2.5–3.0 | CSP/XSS hardening, secret vault/encryption, upload rules, route policy tests | **Critical** due bearer tokens, customer data and platform credentials | L | **Must** | action registry + deployment hardening | recent OSS security fixes across peers |
| 30 | Permissions/object scope | 4.0 concept / 2.5 maintainability | declarative action policy + generated actor/object tests | **Critical**: one missed scope check can expose data/action | M | **Must** | route modularization | framework permission metadata |
| 31 | Backup / restore / DR | 2.0 operational maturity | independent schedule, off-host copy, restore-to-temp verification, RPO/RTO | **Critical** business continuity | M/L | **Must** | schema/version + service scripts | standard recovery discipline |
| 32 | Testing / release gates | 3.0 | preserve broad local tests; add state/concurrency/migration/security/recovery contract suite | **Critical** as domains expand | M | **Must** | deterministic fixtures | peer upgrade discipline |
| 33 | Observability | 1.5–2.0 | structured logs, request/job correlation, metrics/health/alerts | **High**: failures become hard to diagnose at automation scale | M | **Should** | worker/action IDs | operational platform patterns |
| 34 | Schema migration / PostgreSQL parity | 1.5 | numbered migrations and one supported schema truth; PG only after parity proof | **Critical for safe evolution**, not immediate PG need | L | **Must migrations / Later PG** | migration fixtures | all maintained peers |
| 35 | Source modularity / maintainability | 2.0 | domain packages; smaller router/services/client modules; explicit ownership | **High**: new manufacturing features otherwise amplify regression risk | L | **Must** | regression suite | Tryton/Medusa/Dolibarr modules |
| 36 | Durable job/outbox platform | 2.5 OCR precedent / 1.0 general | one reusable DB-backed worker contract with retry/lease/idempotency/dead-letter | **High** for sync, reports, MRP, AI, backup verification | L | **Must** | job schema + worker supervisor | Inventory OCR + Medusa workflows |
| 37 | Safe deterministic automation rules | 1.5 | event→condition→action policy, approval class, idempotency, audit | **Medium/High** productivity leverage | L | **Should** | domain events + action registry | Dolibarr triggers; Medusa events |
| 38 | AI Copilot | 1.0 general / OCR 4.0 | assistive evidence-bound tools; no direct SQL/business truth | **Medium** leverage, **high risk** if premature autonomy | M/L | **Could** | search, read models, action approval | Part-DB AI tools + Inventory OCR precedent |
| 39 | Accounting/general ledger | out of target scope | integrate/export settlement/cost evidence to accounting system | **Medium**; rebuilding GL creates huge distraction | XL | **Later / integrate** | economics ledger | ERP peers demonstrate scope cost |
| 40 | Advanced WMS wave/cluster/MFC | 0–0.5 | only if order volume/travel/hardware prove need | **Low now** | XL | **Later** | reliable bin/reservation/scan metrics | Odoo wave; OpenWMS complexity ceiling |

## 3. Must / Should / Could / Later classification

### MUST — business-truth and safety foundations

These should be treated as architecture gates rather than optional features:

1. canonical stock identity with location/state dimensions;
2. first-class reservation/allocation;
3. idempotent stock-changing operations and compensating reversals;
4. electronics internal-part/MPN/supplier-part identity;
5. controlled AVL/substitute semantics;
6. released EBOM/MBOM revision + ECN/effectivity baseline;
7. document/firmware released-version control;
8. pricing margin/markup terminology correction;
9. declarative permission/object-scope coverage;
10. secret/CSP/upload/deployment security hardening;
11. numbered schema migrations + integrity checks;
12. independently scheduled/verified backup and recovery;
13. domain modularization before adding another generation of giant-file features;
14. reusable durable job/outbox primitive;
15. repository-local state/concurrency/migration/recovery/security release gate.

### SHOULD — next business capability layer

1. work order execution spine;
2. quality stock state + IQC/NCR/MRB;
3. lot/serial genealogy;
4. MRP after released MBOM/stock semantics exist;
5. RF/electrical test evidence;
6. supplier-part/lead-time/MOQ/performance enhancements;
7. durable omnichannel synchronization/reconciliation;
8. lightweight technical CRM/quote/sample workflow;
9. RMA/repair/warranty;
10. customer-service case layer;
11. channel settlement/economics;
12. actual work-order cost after production transactions;
13. global search/scan-to-action;
14. executive KPI lineage/read models;
15. structured observability;
16. safe deterministic rules automation.

### COULD — leverage once data truth exists

1. product portfolio intelligence;
2. advanced forecasting/safety-stock tuning;
3. AI Copilot for retrieval, drafting, matching and anomaly explanation;
4. richer automated report generation;
5. plugin/provider packaging beyond internal interfaces;
6. advanced supplier/part-data enrichment.

### LATER — require measured scale or explicit strategic decision

1. PostgreSQL migration solely for scale;
2. Redis/general event bus;
3. microservices;
4. wave/cluster picking;
5. automated warehouse MFC;
6. true offline multi-master inventory mutation;
7. full accounting/general ledger;
8. generic low-code workflow designer;
9. third-party plugin marketplace;
10. autonomous AI agents executing high-risk actions without approval.

## 4. Highest business-risk gaps

### Risk A — saleable/available stock is not authoritative enough

Current strength in shipment execution can create false confidence because the system protects final quantity better than business commitment quantity.

Until reservation/quality/location semantics are authoritative:

- omnichannel publication can oversell;
- MRP can net the wrong supply;
- engineering/project stock can look commercially usable;
- quality-held stock can contaminate ATP;
- concurrent open orders can compete for the same quantity.

**Gate:** fix stock semantics before aggressive channel or replenishment automation.

## 5. Highest electronics/manufacturing gap

The biggest gap is not “add a production menu.” It is configuration control:

```text
Which exact part revision?
Which BOM revision?
Which approved alternate?
Which document/firmware/test revision?
Which stock lot/serial?
Which work order consumed it?
Which finished serial received it?
```

Without those keys, adding work-order screens would create process appearance without traceability.

**Gate:** part/revision/stock identity first, WO second, MRP/actual cost third.

## 6. Highest commerce gap

The current order/fulfilment foundation is relatively strong. The missing layer is durable multi-channel state and economics:

```text
external order observation
 -> canonical order
 -> reservation/ATP
 -> fulfilment
 -> external acknowledgement
 -> refund/RMA
 -> settlement economics
 -> reconciliation
```

**Gate:** do not publish raw `quantity_available` as channel sellable stock.

## 7. Highest platform/operational gap

The application already has substantial local tests and good OCR-worker engineering, but cross-domain growth needs a more explicit release contract:

```text
fresh checkout
 -> migrate fixture DBs
 -> deterministic domain tests
 -> concurrency/idempotency tests
 -> permission/security tests
 -> backup/restore drill
 -> client syntax/workflow tests
 -> deploy
```

GitHub Actions may optionally call these commands, but is not a required executor or production dependency.

## 8. Dependency graph

```text
                     ┌─ Security / migrations / tests / recovery ─┐
                     │                                           │
Part identity ─> Revision/ECN ─> Released EBOM ─> MBOM ─> WO ─> Actual cost
     │                                      │         │       │
     └─ AVL/substitute                     └─> MRP    │       └─ profitability
                                                        │
Stock position ─> quality state ─> reservation ─> allocation/issue/ship
      │             │                 │          │
      │             └─ IQC/NCR        │          └─ omnichannel ATP
      └─ lot/serial ──────────────────┴─> genealogy ─> test ─> RMA

Durable job/outbox ─> marketplace sync / reports / MRP / AI / backup verify

CRM/quote ─> order ─> fulfilment ─> RMA/support
     │                               │
     └──────── channel economics <───┘
```

## 9. Suggested implementation gates

### Gate 0 — protect what already works

Before structural changes:

- freeze deterministic fixtures;
- run current core/security/client/recognition tests locally;
- establish schema version and backup/restore verification;
- inventory all stock-changing commands.

### Gate 1 — stock kernel

Exit criteria:

- same material can exist in multiple bins/states;
- reservations have business references;
- ATP is derivable and reconciled;
- all consequential stock operations are idempotent;
- ledger reversal is explicit.

### Gate 2 — engineering configuration kernel

Exit criteria:

- internal part / MPN / supplier part are distinct;
- AVL/substitute decisions are controlled;
- released EBOM/MBOM revision exists;
- refdes/effectivity are preserved;
- controlled docs/firmware can be tied to product revision.

### Gate 3 — manufacturing/quality kernel

Exit criteria:

- WO freezes MBOM revision;
- reservation/issue/return/scrap/output are auditable;
- lot/serial genealogy works for configured products;
- quality state controls nettable/ship-able stock;
- RF test evidence links to serial/lot and spec revision.

### Gate 4 — commerce/economics automation

Exit criteria:

- external-object ledger supports replay-safe channel sync;
- published stock uses ATP policy;
- RMA/refund physical and financial states are distinct;
- settlement costs reconcile to orders;
- contribution margin is reproducible historically.

### Gate 5 — optimization/AI

Only after earlier gates:

- MRP/forecast recommendations;
- product intelligence;
- anomaly detection;
- AI search/case/report assistance;
- safe low-risk auto-actions.

## 10. What should explicitly NOT block progress

The following are **not prerequisites** for the recommended next-stage system:

- PostgreSQL;
- microservices;
- Redis;
- Kubernetes;
- GraphQL;
- a general accounting suite;
- a generic BPM engine;
- GitHub Actions;
- autonomous AI.

Keeping these optional materially reduces execution risk.

## 11. Reference-system mapping

| Target area | Best peer concepts to borrow |
|---|---|
| electronic part/stock distinction | InvenTree, Part-DB |
| EDA/provider catalog | Part-DB |
| machine execution adapter | OpenPnP |
| receiving/putaway/bin WMS | OpenBoxes |
| reservations/channel inventory | Medusa |
| commerce connector boundary | Saleor/Medusa |
| business document immutability | ERPNext |
| configurable warehouse/manufacturing depth | Odoo |
| modular business domains | Tryton/Medusa |
| extension seams/triggers | Dolibarr |
| compensation/workflow jobs | Medusa + Inventory Lite OCR worker |
| ledger/reconciliation | ERPNext/OpenBoxes |

## 12. Strategic fit verdict

### E-commerce

**Current fit: good for operator-controlled low/moderate volume; incomplete for highly automated omnichannel.**

Keep order/shipment flows, add reservation/ATP and durable connector reconciliation.

### Electronics R&D

**Current fit: partial.**

The material/spec/resource/project-BOM foundation is useful, but manufacturer/MPN/AVL/revision/refdes/ECN/document-control semantics need first-class treatment.

### Manufacturing

**Current fit: insufficient as controlled production system.**

Work order, released MBOM, material issue/WIP/output, lot/serial, quality and test genealogy must be introduced.

### Sales / aftersales

**Current fit: order-centric, not customer-lifecycle-centric.**

Add lightweight technical CRM/quote/sample and serial-aware RMA/support rather than implementing a massive general CRM.

### Management / profitability

**Current fit: operationally useful, strategically incomplete.**

Pricing is strong, but realized channel contribution and product portfolio metrics require economics and lifecycle event data.

## 13. Top 20 recommendation ranking

Ordered by dependency and risk, not by UI visibility:

1. redesign canonical stock identity around bin/state/lot/owner dimensions;
2. implement first-class reservations;
3. standardize idempotent stock operation keys + reversals;
4. introduce numbered DB migrations and schema-version contract;
5. establish local release gate including concurrency and recovery tests;
6. harden secrets/XSS/upload/object-scope security;
7. split `services.py`/`server.py`/clients toward domain modules;
8. extract durable DB-backed job/outbox primitive from OCR precedent;
9. add internal part → manufacturer part → supplier part identity;
10. add controlled AVL/substitute model;
11. implement released revisioned EBOM/MBOM + ECN/effectivity/refdes;
12. implement controlled docs/firmware revision layer;
13. add lightweight WO reservation/issue/return/scrap/output state machine;
14. add quality stock state + IQC/NCR/MRB;
15. add risk-based lot/serial genealogy;
16. link structured RF/electrical test evidence to serial/lot/spec/equipment;
17. implement time-phased MRP over released MBOM and qualified supply;
18. evolve platform connectors into external-object + outbox/reconciliation architecture;
19. add RMA/repair + channel settlement/economics;
20. layer technical CRM, executive product intelligence, rules and AI on top of reliable source data.

## 14. Acceptance against task requirement

This matrix:

- scores more than 12 dimensions using evidence from prior audits;
- explicitly distinguishes ordinal maturity from false numeric precision;
- classifies Must/Should/Could/Later;
- includes business impact, implementation difficulty, dependencies and peer references;
- ties roadmap order to foundational invariants rather than feature popularity;
- maintains the project-wide prohibition on GitHub Actions as a required runtime, test or scheduling dependency.

## 15. Core judgment

Inventory Lite should not be replaced. Its operational strengths are worth preserving.

But the next stage must stop measuring progress by number of pages/features. The decisive upgrade is to establish **business truth and controlled state** underneath the UI:

`stock + reservation + revision + WO + genealogy + quality + economics + durable execution`.

Once those kernels are correct, the existing fast operator workflows can be extended into a highly capable electronics R&D/manufacturing/e-commerce operating system without inheriting the unnecessary weight of a full ERP suite.