# TASK_INV_AUDIT_UX_AUTOMATION_BACKLOG_01 — Prioritized UX & Automation Improvement Backlog

## 0. Scope

This backlog converts completed W2–W6 findings into concrete improvements for operators, warehouse, purchasing, engineering, production, sales, aftersales and management.

It consumes especially:

- desktop/mobile UX audits;
- search/scan audit;
- automation-rules audit;
- AI Copilot audit;
- dashboard/executive reporting audits;
- testing/observability audit;
- W6 capability gap matrix.

No item requires GitHub Actions. Scheduled/runtime work must be server/local owned.

## 1. Priority model

- **P0** — foundation/safety or immediate high-value friction removal;
- **P1** — next operational capability;
- **P2** — optimization after core state is trustworthy;
- **P3** — later/volume-dependent.

Complexity: `S / M / L / XL`.

Acceptance signals are intentionally observable and local-testable.

## 2. Backlog — navigation, entity workspace and daily work

| ID | Pri | User | Pain point | Proposed change | Expected benefit | Cplx | Risk | Prerequisite | Acceptance signal |
|---|---|---|---|---|---|---|---|---|---|
| UX-01 | P0 | all PC users | menu breadth keeps growing | introduce task-oriented top-level IA: Today, Orders, Inventory, Purchasing, Products, Production, Quality, Sales/Aftersales, Analysis, Master Data, System | faster navigation, less menu hunting | M | medium | page inventory | common tasks reached in <=2 navigation steps |
| UX-02 | P0 | all | same object data scattered | universal entity workspace/drawer | one-place context, fewer page hops | L | medium | stable entity IDs | material/order/serial opens summary + linked tabs without losing context |
| UX-03 | P0 | all | users must know owning module before search | global cross-entity search | lower lookup time | M | low | shared search service | material/order/PO/transfer/location/logistics/serial searchable from one box |
| UX-04 | P0 | operators | dashboard mixes health and actions | keep home page exception/action-first | immediate next work clearer | S/M | low | todo model | home top section shows owned urgent actions, not KPI wall |
| UX-05 | P1 | managers | repeated filters rebuilt manually | saved views per user/role | faster recurring work | M | low | query/filter contracts | saved filter restored with scope and sort |
| UX-06 | P1 | all | context lost after drill-down | preserve search/filter/page state when opening detail | less repeated navigation | M | low | router refactor | back returns to prior exact view |
| UX-07 | P1 | dense PC workflows | repetitive mouse usage | keyboard shortcuts / command palette for safe navigation actions | faster expert use | M | low | action registry | documented shortcuts cover search, next item, save, cancel |
| UX-08 | P0 | all | generic success messages hide what changed | auditable action receipt component | fewer uncertainty/rechecks | M | low | service result schema | receipt shows object, before→after, actor/time/reference |
| UX-09 | P0 | all | ambiguous destructive confirms | object-specific confirmation wording | prevent accidental stock/status changes | S | low | action inventory | no irreversible dialog uses only generic “确定” |
| UX-10 | P1 | role-specific staff | irrelevant modules create clutter | role-tailored home/navigation defaults | faster onboarding | M | low | permissions | warehouse user starts in tasks/scan, buyer in shortages/PO |

## 3. Backlog — inventory, warehouse and scan execution

| ID | Pri | User | Pain point | Proposed change | Expected benefit | Cplx | Risk | Prerequisite | Acceptance signal |
|---|---|---|---|---|---|---|---|---|---|
| WH-01 | P0 | warehouse | stock shown at warehouse aggregate only | display exact bin/state stock positions | fewer misplaced picks/count errors | XL | high | stock-position model | same material in two bins displayed independently |
| WH-02 | P0 | fulfilment | open orders compete for same stock | order reservation visible in UI | reliable promise quantity | L | high | reservation service | confirmed order shows reserved qty and release/consume state |
| WH-03 | P0 | warehouse mobile | too much typing | scan-first task entry | speed + fewer keying errors | M | medium | scan resolver | task/location/material can be opened by scan |
| WH-04 | P0 | picker | scan proves item, not source bin | require source-location scan for controlled pick | location accuracy | M | medium | bin-level stock | wrong bin scan blocks completion |
| WH-05 | P1 | receiver | permanent bin may be unknown at receipt | receiving/staging bin + putaway queue | faster receiving, cleaner IQC | L | medium | stock positions | receipt can complete to staging then separate putaway |
| WH-06 | P1 | putaway | destination chosen manually each time | preferred-bin deterministic suggestion | lower decision time | M | low | location policy | suggestion explains rule and remains overridable |
| WH-07 | P1 | stock counter | count directly edits balance | count observation → variance → approval/reconcile flow | stronger audit evidence | L | high | ledger/reversal | expected vs observed preserved before adjustment |
| WH-08 | P1 | warehouse lead | no cycle-count cadence | location/material count policy | higher accuracy with less full-count disruption | M | low | count tasks | overdue count tasks generated by policy |
| WH-09 | P1 | picker | large pick list unordered | simple bin-path ordering | less walking | M | low | reliable locations | same task lines sorted by configured physical sequence |
| WH-10 | P2 | warehouse | multiple orders repeat travel | optional batch pick proposal | higher throughput | L | medium | volume + reservation metrics | system groups eligible tasks; operator approves batch |
| WH-11 | P0 | all | barcode aliases can collide | duplicate scan-code validation | prevent wrong-object resolution | M | high | unified identifier registry | duplicate barcode/QR rejected or placed in review |
| WH-12 | P1 | warehouse | labels are ad hoc | shared label service/templates | consistent location/material/serial labels | M | medium | identifier model | labels include canonical IDs and pass scan round-trip test |

## 4. Backlog — engineering, product and manufacturing

| ID | Pri | User | Pain point | Proposed change | Expected benefit | Cplx | Risk | Prerequisite | Acceptance signal |
|---|---|---|---|---|---|---|---|---|---|
| ENG-01 | P0 | engineers/buyers | internal SKU/MPN/supplier SKU conflated | part workspace with explicit identity hierarchy | fewer sourcing/BOM mistakes | L | high | part master | one internal part links multiple MPN/supplier records without ambiguity |
| ENG-02 | P0 | engineers | parameters hard to compare | typed parametric templates/table | faster component search | L | medium | part master | filter/sort numeric params with unit-aware display |
| ENG-03 | P0 | engineers | candidate substitutes are not controlled | AVL/substitute editor with approval state | safe substitutions | L | high | revision/part identity | build can use only approved/effective alternate |
| ENG-04 | P0 | engineers | BOM edits have no released baseline | revisioned EBOM workspace | configuration control | XL | high | revision model | released revision immutable; new draft created for change |
| ENG-05 | P0 | engineering/production | refdes absent | preserve refdes/variant/DNF at line level | EDA-to-build traceability | L | high | EBOM | imported placement refs visible/diffable |
| ENG-06 | P1 | engineering | EDA imports can become generic spreadsheet work | dedicated EDA staging/match/diff flow | safe BOM updates | L | medium | part search + EBOM | unresolved rows block release, not silently mapped |
| ENG-07 | P0 | engineering/quality | files lack effective revision control | controlled-document revision workspace | correct drawing/firmware/test spec use | L | high | document model | WO/test references exact released revision/hash |
| MFG-01 | P1 | production | no executable work order | lightweight WO workspace/state machine | controlled WIP and completion | XL | high | MBOM + reservation | release freezes MBOM revision and requirements |
| MFG-02 | P1 | production | material kitting informal | reservation/allocation/kitting view | fewer shortages at build start | L | medium | WO + stock positions | WO shows required/reserved/issued shortage by line |
| MFG-03 | P1 | production | overissue/return/scrap not structured | dedicated material transaction actions | accurate WIP/cost | L | high | WO ledger | every issue/return/scrap posts reference + reason |
| MFG-04 | P1 | production | partial builds awkward | partial output completion and cancellation disposition | real production state | M/L | medium | WO | partial qty can complete while remaining qty stays open |
| MFG-05 | P2 | planner | shortages planned manually | MRP recommendation workspace | fewer shortages/excess purchases | XL | high | released MBOM + reservations + supply | recommendation includes pegging and does not auto-create PO/WO |

## 5. Backlog — quality, traceability and test

| ID | Pri | User | Pain point | Proposed change | Expected benefit | Cplx | Risk | Prerequisite | Acceptance signal |
|---|---|---|---|---|---|---|---|---|---|
| QA-01 | P1 | receiving/quality | received stock appears usable before inspection | quality stock states | prevent bad material allocation | L | high | stock position | quarantine stock excluded from ATP/MRP/pick |
| QA-02 | P1 | quality | IQC informal | inspection order/result on receipt | supplier quality evidence | L | medium | quality state | partial accept/reject supported per receipt line/lot |
| QA-03 | P1 | quality | nonconformance kept in notes | NCR + disposition workflow | consistent containment/rework/scrap | L | high | quality state | NCR has owner, cause, disposition, closure evidence |
| QA-04 | P2 | quality/supply | recurring supplier issues hard to quantify | supplier-quality score and SCAR follow-up | better sourcing decisions | M | medium | NCR + supplier part | defect/lot/SCAR trend drill-down works |
| TRACE-01 | P1 | production/support | no supplier→finished genealogy | risk-based lot/serial genealogy browser | faster root cause/recall/RMA | XL | high | WO + stock positions | serial traces backward and forward to component lots/orders |
| TEST-01 | P1 | RF test/quality | screenshots/raw files disconnected | structured test-run workspace | searchable evidence | L | high | serial + test spec | DUT serial links measurements + raw artifact + limits |
| TEST-02 | P1 | RF test | pass/fail rules can drift | versioned limit sets/test procedures | reproducible release | L | high | controlled docs | old test run still evaluates against historical limit revision |
| TEST-03 | P1 | quality | equipment validity not visible | equipment/calibration registry | trustworthy measurements | M | high | equipment master | expired calibration blocks/warns by policy and is recorded |
| TEST-04 | P2 | customer service | report generation manual | serial-linked test report generator | faster customer evidence | M | low | structured tests | report regenerated from same source data deterministically |

## 6. Backlog — purchasing, sales, CRM and aftersales

| ID | Pri | User | Pain point | Proposed change | Expected benefit | Cplx | Risk | Prerequisite | Acceptance signal |
|---|---|---|---|---|---|---|---|---|---|
| PUR-01 | P1 | buyer | supplier selection lacks part-level source context | supplier-part comparison view | faster sourcing | M | medium | supplier part | show MOQ, lead time, price history, quality and preferred state |
| PUR-02 | P1 | buyer | overdue PO follow-up manual | due/late receipt action queue | fewer shortages | M | low | lifecycle timestamps | overdue line creates deduped todo, closes on receipt/change |
| PUR-03 | P2 | buyer | repeated price/lead-time changes unnoticed | supplier variance alerts | better negotiation/planning | M | low | supplier history | configurable threshold alert has evidence and owner |
| CRM-01 | P1 | sales | inquiries not first-class | lightweight inquiry/opportunity workspace | better follow-up | L | medium | customer identity | inquiry can link product requirement, owner, next action |
| CRM-02 | P1 | sales | quotations overwrite informal versions | quote revision object | controlled commercial history | L | medium | pricing/customer | accepted order retains exact quote revision |
| CRM-03 | P1 | sales/engineering | technical requirements lost in chat | requirement/spec attachment + structured key fields | fewer quote errors | M | medium | CRM | RF band/gain/interface notes carried into quote/order context |
| CRM-04 | P1 | sales | sample units disappear from saleable inventory | sample/loan/gift lifecycle | accountability | L | high | engineering/sample stock | sample disposition excludes stock from ATP and records recipient |
| RMA-01 | P1 | support | refunds and physical returns conflated | RMA authorization + receipt inspection | correct inventory/financial state | L | high | serial/quality | refund can occur independently from restock eligibility |
| RMA-02 | P1 | support/engineering | diagnosis history fragmented | serial-linked fault/repair/retest timeline | faster recurrence analysis | L | medium | serial/test | same serial shows ship→return→repair→retest→close |
| CS-01 | P1 | customer service | `ExceptionService` is internal operations only | customer case/ticket layer | owned SLA/case history | M | medium | customer/order links | ticket links order/RMA/messages/owner/SLA |
| CS-02 | P2 | support | repeated answers/manual diagnosis | controlled response/KB suggestions | faster support | M | low | ticket taxonomy | suggested article/template always visible as suggestion, editable before send |

## 7. Backlog — commerce, settlement and profitability

| ID | Pri | User | Pain point | Proposed change | Expected benefit | Cplx | Risk | Prerequisite | Acceptance signal |
|---|---|---|---|---|---|---|---|---|---|
| COM-01 | P1 | e-commerce | connector state overloaded into recognition | external-object/import ledger | replay-safe sync | L | high | durable jobs | replay of same external ID creates no second canonical order |
| COM-02 | P1 | e-commerce | sync depends on manual/operator HTTP action | scheduled durable connector jobs | less manual checking | L | medium | job worker | restart resumes/retries without duplicate orders |
| COM-03 | P1 | e-commerce | channel stock may expose raw balance | ATP-based publication policy | lower oversell risk | L | high | reservation/quality state | published qty equals documented policy result |
| COM-04 | P2 | e-commerce | outbound fulfilment errors hard to reconcile | fulfilment outbox + remote ack/reconciliation | more reliable marketplace status | L | medium | connector contract | remote failure never rolls back local shipment; mismatch is visible |
| FIN-01 | P0 | sales/admin | `margin_percent` terminology can mislead | rename/fix margin vs markup formulas + tests | prevent pricing errors | S/M | high | none | test case where 20% markup != 20% gross margin passes |
| FIN-02 | P1 | owner | marketplace costs absent | order economics event model | true contribution profit | L | high | order snapshots | platform/payment/freight/refund costs reconcile per order |
| FIN-03 | P1 | finance/admin | settlement statements not reconciled | statement import/reconciliation workspace | find fee/refund mismatches | L | medium | connector/economics | unmatched/duplicate settlement lines visible and resolvable |
| FIN-04 | P2 | management | product cost changes rewrite historical interpretation | standard/actual cost snapshots | reproducible profitability | XL | high | WO/cost model | historical order keeps original cost basis after master changes |

## 8. Backlog — automation, reporting and AI

| ID | Pri | User | Pain point | Proposed change | Expected benefit | Cplx | Risk | Prerequisite | Acceptance signal |
|---|---|---|---|---|---|---|---|---|---|
| AUTO-01 | P0 | platform | each background task could invent own loop | reusable durable job/outbox framework | reliability + consistency | L | high | migration + worker | job lease/retry/dead-letter survives restart |
| AUTO-02 | P0 | platform | auto-actions can bypass business policy | action registry with permission/scope/idempotency/audit metadata | safer automation | L | high | domain modularization | automation invokes same validated command as UI/API |
| AUTO-03 | P1 | warehouse | low stock only warns | low-stock→replenishment suggestion rule | actionability | M | low | ATP + planning policy | suggestion includes evidence and requires approval to create PO |
| AUTO-04 | P1 | fulfilment | stock shortages routed manually | shortage auto-classification and owner routing | faster resolution | M | low | reservations/todos | duplicate shortage signals produce one owned case |
| AUTO-05 | P1 | purchasing | PO due reminders manual | overdue-PO follow-up rule | fewer late receipts | S/M | low | PO dates | one reminder per configured interval, auto-resolves on receipt |
| AUTO-06 | P1 | quality | quarantine can age unnoticed | quarantine-aging escalation | reduce blocked stock | S/M | low | quality state | threshold crossing creates deduped action with owner |
| AUTO-07 | P1 | integrations | sync retries become noisy | retry automatically, human alert after policy threshold | lower operator noise | M | medium | durable jobs | transient failure recovers silently; persistent failure becomes todo |
| AUTO-08 | P1 | data owner | repeated OCR corrections not fed back | correction-pattern master-data review rule | improve recognition/data quality | M | low | correction metrics | repeated same SKU mismatch creates review, not auto-master change |
| AUTO-09 | P1 | support | RMA recurrence hidden | recurring-fault clustering alert | earlier quality response | M | medium | serial/RMA taxonomy | cluster links underlying cases and confidence evidence |
| AUTO-10 | P2 | management | slow stock reviewed manually | dead/slow stock review queue | release working capital | M | low | aging/demand metrics | rule produces candidate list with reason, no automatic write-off |
| REP-01 | P0 | management | KPI meaning can drift | metric lineage registry | trustworthy dashboards | M | low | event timestamps | every KPI exposes definition/time/scope/freshness |
| REP-02 | P1 | owner | operational and economic views mixed | separate Daily/Weekly/Monthly management views | clearer decisions | M | low | KPI registry | daily exceptions, weekly flow, monthly economics each drill down |
| REP-03 | P1 | product owner | no product portfolio view | product scorecard | prioritize profitable/strategic products | M | medium | economics + CRM + stock | measured vs inferred indicators clearly marked |
| AI-01 | P2 | all | natural-language questions require manual joins | permission-aware NL query over approved read models | faster analysis | L | high | read models + scope | answer cites underlying records/query period and respects permissions |
| AI-02 | P2 | purchasing/engineering | part matching is labor-intensive | AI-assisted candidate part/MPN matching | faster import cleanup | M | medium | deterministic search | AI suggests ranked candidates; human/controlled rule confirms |
| AI-03 | P2 | support | case summaries consume time | evidence-linked ticket/RMA summarization | faster handoff | M | medium | case history | generated summary links source events and can be edited |
| AI-04 | P2 | management | narrative reports manual | draft weekly/monthly narrative from verified KPI read models | save reporting time | M | low | KPI lineage | narrative shows data period and cannot invent unsupported metric |
| AI-05 | P3 | planners | replenishment explanations manual | AI explanation around deterministic forecast/MRP suggestion | easier review | M | medium | deterministic planning | AI cannot alter recommendation quantities without explicit user action |

## 9. Total coverage

This backlog contains **67 concrete improvements**, exceeding the task minimum of 50.

Coverage by focus:

- navigation/entity/daily work: 10;
- warehouse/scan: 12;
- engineering/manufacturing: 12;
- quality/traceability/test: 9;
- purchasing/CRM/aftersales: 11;
- commerce/finance: 8;
- automation/reporting/AI: 17.

(Some items intentionally span multiple operational roles.)

## 10. Highest-value first 15

The first implementation sequence should not simply follow the prettiest UX items. Recommended first 15:

1. `FIN-01` — fix margin/markup semantics;
2. `AUTO-01` — durable job/outbox primitive;
3. `AUTO-02` — action policy registry;
4. `WH-01` — stock position/bin/state model;
5. `WH-02` — reservation visibility/lifecycle;
6. `WH-11` — scan identifier uniqueness;
7. `ENG-01` — electronic part identity workspace;
8. `ENG-03` — controlled AVL/substitutes;
9. `ENG-04` — revisioned EBOM;
10. `ENG-07` — controlled documents/firmware;
11. `UX-03` — global search;
12. `UX-08` — action receipts;
13. `WH-03`/`WH-04` — scan-first task + source-bin validation;
14. `REP-01` — metric lineage registry;
15. `COM-01` — external-object sync ledger after ATP foundation.

## 11. Automation safety classes

Every automation in this backlog should declare one of:

### A — notify only

No business mutation.

Examples: overdue PO, quarantine aging, negative contribution warning.

### B — create suggestion/draft

Creates a reviewable object but not a consequential business effect.

Examples: replenishment recommendation, draft quote narrative, candidate substitute.

### C — reversible low-risk action

May execute automatically only with policy and full audit.

Examples: retry connector job, assign owner, generate report.

### D — consequential approval-required action

Never autonomous by default.

Examples:

- stock movement;
- BOM release;
- supplier substitution;
- refund/write-off;
- quality release;
- WO completion;
- price below floor;
- destructive restore.

## 12. UX acceptance principles

Across all UI items:

1. show the current object and state;
2. show the next valid action;
3. scan/choose rather than retype known identifiers;
4. invalid state/mismatch blocks before mutation;
5. server result is authoritative;
6. every consequential action returns an audit receipt;
7. network failure must not look like success;
8. role/scope limits remain server enforced;
9. status cannot rely on color alone;
10. desktop and mobile share business vocabulary, not necessarily layout.

## 13. AI evidence boundary

AI features may:

- retrieve;
- summarize;
- extract;
- classify;
- rank;
- draft;
- explain;
- detect anomalies;
- propose actions.

AI must not independently establish:

- inventory balance;
- product/BOM revision;
- approved substitute;
- quality release;
- test pass/fail outside deterministic limits;
- legal/financial settlement truth;
- refund/write-off;
- production completion.

Those remain deterministic domain-service decisions with explicit actors/policies.

## 14. Core recommendation

Treat UX and automation as a layer **on top of trustworthy domain state**, not a substitute for it.

The ideal interaction pattern is:

```text
find/scan object
 -> see complete context
 -> system proposes next valid action
 -> deterministic validation
 -> user approves when risk requires
 -> domain service commits once
 -> audit receipt
 -> async side effects through durable worker
```

That pattern improves speed and automation while preserving the control required for an electronics R&D/manufacturing business.