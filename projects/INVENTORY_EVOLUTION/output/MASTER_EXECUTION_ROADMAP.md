# INVENTORY_EVOLUTION — Master Execution Roadmap

## Status

`MASTER_PLAN_READY_IMPLEMENTATION_BLOCKED_AT_E00_LOCAL_GATE`

This document is the execution index for E00–E15. It does not replace the story files; it tells an implementer which wave may start, what evidence is required, what must remain frozen, and what unlocks the next wave.

## 1. Global hard rules

1. No production change before a fresh current-server code snapshot and current production SQLite backup exist.
2. Database backup is not accepted until isolated restore verification passes.
3. Production cutover is fail-closed after writers are quiesced.
4. No required validation/runtime path depends on GitHub Actions.
5. No big-bang rewrite; every wave uses bounded PR slices with deterministic regression tests.
6. No historical business evidence is invented during migration.
7. Consequential writes use domain validation, permission/state checks, idempotency and audit evidence.
8. Corrections use reversal/adjustment/revision semantics instead of deleting executed history.
9. AI/rules never become alternate sources of truth.
10. PostgreSQL/multi-host is conditional on measured need.

## 2. Current blocking gate

```text
Inventory PR #3
branch impl/e00-release-safety
head 0e0870499f7e8b5e68a308231eae954f106bd5aa
state Draft/Open/Mergeable
```

Required first evidence:

```bash
python3 tools/verify_release.py
python3 tools/verify_release.py --require-bash
```

Required result:

```text
RELEASE VERIFICATION: PASS
```

No later runtime wave may merge before E00 passes and PR #3 has no unresolved blocker.

## 3. Wave dependency graph

```text
E00 Release Safety
  |
  v
E01 Execution Primitives
  |
  +--> E11 early: pricing semantics / floor safety
  |        |
  |        v
  +------> E02 Stock Truth / Reservation / ATP
             |
             v
           E03 Warehouse Execution
             |
             v
           E04 Electronics Part / MPN / AVL
             |
             v
           E05 Revision / EBOM / MBOM / ECN
             |
             v
           E06 Work Order / WIP / Manufacturing
             |
             v
           E07 Lot / Serial / Quality / RF Test
             |
             +--> E08 MRP / Subcontract
             |
             +--> E10 CRM/RMA technical depth

E01 + E02 -----------------> E09 Omnichannel / ATP publication
E04 + E07 + E09 ----------> E10 CRM / Quote / Service / RMA
E05..E10 -----------------> E11 late Cost / Economics / Settlement
E02..E11 -----------------> E12 Metrics / Cockpit / Product Intelligence
E01 + stable domain APIs --> E13 Safe Automation Rules
E12 + governed domain APIs -> E14 Evidence-bound AI Copilot
Measured scale evidence ---> E15 Conditional PostgreSQL / Multi-host
```

## 4. Stage 0 — E00 release safety

### Purpose

Make every later schema/runtime change recoverable and locally verifiable.

### Required outputs

- immutable numbered migration registry;
- historical schema fixtures;
- integrity/orphan checks;
- one repository-local Release Gate;
- WAL-safe database snapshot;
- isolated restore verification;
- exact currently deployed server-code snapshot;
- checksummed manifest/Recovery Bundle;
- off-host target fail-closed behavior;
- independent backup-health record/scheduler.

### Production pre-change gate

```text
confirm current production DB exists
 -> snapshot exact deployed server code
 -> consistent DB snapshot
 -> isolated restore proof
 -> checksums/manifest
 -> off-host bundle if configured
 -> quiesce writers
 -> only then dependency/code/schema change
```

### Exit criteria

- real-checkout Release Gate PASS;
- no unresolved PR blocker;
- production preflight path proven before first real cutover.

## 5. Stage 1 — E01 + E11 early

### E01 purpose

Create reusable execution primitives before multiplying business domains.

Implementation slices:

```text
A shared request/action context
B Action Policy registry
C Business-operation idempotency
D pilot consequential routes
E durable jobs + worker + retry/dead-letter
F transactional outbox + correlation
G bounded module extraction
```

Pilot operations:

```text
transfer.receive
purchase.receive
shipment.complete
```

### E11 early

Immediately after pricing extraction/Action Policy:

- preserve legacy `margin_percent` arithmetic;
- add explicit target-gross-margin semantics;
- implement deterministic floor-price resolution;
- require dedicated authority/reason for below-floor override.

### Exit criteria

- retried consequential command cannot double-apply;
- jobs survive restart without duplicate completion;
- external side effects can be queued atomically after local commit;
- pricing terminology/formula is no longer ambiguous;
- below-floor selling cannot happen silently.

## 6. Stage 2 — E02 stock truth

### Purpose

Create one authoritative answer to `what stock exists, why, what is committed, and what can still be promised?`

Core model:

```text
Movement Ledger = why/how stock changed
Balance Projection = current physical quantity
Reservation = committed promise
ATP = still promiseable quantity
```

Migration style:

```text
identity/UOM
 -> append-only ledger
 -> shadow balance
 -> reconciliation
 -> reservation/ATP
 -> migrate order/shipment/transfer/purchase/manual writes
 -> continuous zero-difference evidence
 -> final cutover
```

### Exit criteria

- no oversubscription under concurrency;
- every authoritative stock change has movement evidence;
- replay is idempotent;
- reservation/ATP is centralized;
- no historical bin/lot/reservation is fabricated;
- legacy direct-balance writes retired only after reconciliation gate.

## 7. Stage 3 — E03 warehouse execution

### Purpose

Turn warehouse location and scan features into stable execution semantics without implementing enterprise WMS complexity.

P0:

- stable location identity;
- receiving staging;
- putaway;
- shared typed scan resolver;
- exact-location pick;
- location-aware count/reconciliation;
- simple cycle-count policy;
- guided mobile scan state machine.

### Exit criteria

- receipt is distinct from putaway;
- scans identify/validate context before mutation;
- pick/count actions operate on authoritative E02 location stock;
- count variance becomes controlled movement, not silent overwrite.

## 8. Stage 4 — E04 electronics component truth

### Purpose

Separate internal part identity from MPN, supplier part and approved alternatives.

Core distinction:

```text
internal part
!= manufacturer + MPN
!= supplier SKU
!= platform SKU
!= approved substitute
```

### Exit criteria

- Manufacturer+MPN unique identity controlled;
- supplier sources retain provenance/MOQ/lead-time;
- typed parametrics distinguish internal requirement vs observed datasheet value;
- AVL/substitute approval is explicit;
- similarity/search/provider confidence cannot create engineering approval.

## 9. Stage 5 — E05 controlled configuration

### Purpose

Create small PLM-style released configuration authority.

Chain:

```text
Part Revision
 -> EBOM + RefDes
 -> MBOM ancestry
 -> EDA staging/diff
 -> Effectivity
 -> ECN/ECO/Deviation
 -> Controlled Docs/Firmware/Test Spec
 -> Release Package
```

### Exit criteria

- Sales BOM remains separate from EBOM/MBOM;
- released revision is immutable;
- MBOM knows exact EBOM/release ancestry;
- where-used/effectivity is queryable;
- engineering change records disposition of affected stock/WIP/documents.

## 10. Stage 6 — E06 manufacturing execution

### Purpose

Create lightweight WO/WIP execution, not full MES.

Core sequence:

```text
released MBOM/config snapshot
 -> WO requirement snapshot
 -> reservation/readiness
 -> kit/pick/issue to WO-owned WIP
 -> return/overissue/scrap
 -> partial accepted output
 -> hold/cancel disposition
 -> close
```

### Exit criteria

- WO configuration does not drift with latest BOM;
- issued material is tied to WO/requirement;
- cancel cannot close with unexplained WIP;
- prototype mode is explicit and non-saleable by default;
- substitutes require approved engineering authority.

## 11. Stage 7 — E07 traceability / quality / RF evidence

### Purpose

Make product release and RF-test evidence trustworthy at the granularity actually captured.

Core chain:

```text
receipt/source lot
 -> quality state
 -> WO issue/genealogy
 -> finished serial/output lot
 -> product/MBOM/firmware revision
 -> released test limits
 -> structured measurements
 -> raw S2P/spectrum artifact hash
 -> equipment + calibration-at-test-time
 -> NCR/rework/retest
 -> final quality release
 -> shipment/customer
```

### Exit criteria

- lot/serial policy is risk-based;
- location, lot and quality state are separate dimensions;
- quarantine/rejected stock is excluded from normal ATP/MRP;
- failed tests remain after passing retest;
- raw artifact/test-limit/equipment/calibration provenance is retained;
- physical completion does not equal saleable release.

## 12. Stage 8 — E08 planning / subcontract

### Purpose

Add explainable time-phased MRP after trustworthy inputs exist.

```text
qualified stock/reservations
+ dated supply
+ released effective MBOM
+ dated demand
+ source lead-time/MOQ
 -> daily PAB/netting
 -> pegging/exceptions
 -> recommendation
 -> human review
 -> idempotent PO/WO/transfer conversion
```

Subcontract:

```text
company material -> external WIP -> returned output -> quality -> reconciliation
```

### Exit criteria

- MRP is advisory, reproducible and source-linked;
- only released manufacturing configuration is exploded;
- company-owned material at supplier remains visible asset/WIP;
- no PO/WO/substitute is silently auto-approved.

## 13. Stage 9 — E09 omnichannel

### Purpose

Turn existing adapters/platform accounts/SKU mappings into durable reconciliation.

```text
remote observation
 -> external object identity
 -> canonical order transition
 -> E02 reservation/ATP
 -> channel publication/local shipment
 -> E01 outbox/worker
 -> remote acknowledgement
 -> reconciliation
```

### Exit criteria

- same remote event replay is harmless;
- account-scoped identity prevents shop collisions;
- mapping changes do not rewrite historical orders;
- channels do not calculate raw stock independently;
- desired remote stock and acknowledged remote stock are separate;
- platform outage never rewrites committed local stock truth.

## 14. Stage 10 — E10 technical sales / service / RMA

### Purpose

Cover the customer lifecycle before and after an order.

```text
customer/contact
 -> inquiry/RF requirements
 -> product/custom candidate
 -> immutable quote revision
 -> sample/evaluation
 -> order
 -> service case
 -> RMA/refund/repair/exchange
 -> engineering/quality feedback
```

### Exit criteria

- receiver text is not silently promoted to durable CRM master;
- sent/accepted quote revisions are immutable;
- accepted order preserves exact quote revision/price evidence;
- returned product enters quarantine;
- refund, physical return, repair and warranty are separate states;
- serialized RMA resolves original shipment/WO/test history.

## 15. Stage 11 — E11 late economics

### Purpose

Close the loop from pricing estimate to actual build/order/channel economics.

```text
Current/reference estimate
!= Released standard cost
!= WO actual cost
!= Order/channel realized contribution
```

Capabilities:

- standard cost version;
- WO actual cost close;
- PPV/usage/labor/scrap/rework/subcontract variance;
- append-only order economic events;
- settlement import/reconciliation;
- realized contribution with evidence quality.

### Exit criteria

- historical cost does not recalc from today's BOM/prices;
- WO cost comes from actual issues/returns/scrap/output evidence;
- settlement re-import is idempotent;
- platform-funded subsidy vs seller discount are distinct;
- profitability displays evidence class, not false precision.

## 16. Stage 12 — E12 governed reporting / product intelligence

### Purpose

One KPI meaning, explainable management decisions.

Layers:

```text
Metric Registry
 -> Read Model/Snapshot
 -> Management Cockpit
 -> Product Scorecard
 -> Decision/Action follow-through
```

### Exit criteria

- every KPI has formula/source/time/scope/evidence version;
- aggregate numbers drill into source records;
- operator action board stays separate from management BI;
- missing evidence is not converted to zero;
- product intelligence exposes dimensions/risk components before any composite score.

## 17. Stage 13 — E13 safe automation

### Purpose

Add versioned event/rule/action automation without bypassing domains.

Risk classes:

```text
A0 insight
A1 notify/draft
A2 reversible mutation
A3 high consequence -> human approval default
```

### Exit criteria

- structured typed predicates only; no arbitrary SQL/Python/shell;
- actions call ordinary domain commands;
- observe-only required before high-impact enablement;
- idempotency/compensation/loop controls/circuit breakers/kill switches exist;
- rule owner and review date are visible.

## 18. Stage 14 — E14 evidence-bound AI

### Purpose

AI helps people understand/work faster without becoming business authority.

```text
AI interpret/extract/rank/summarize/draft
 -> evidence + uncertainty
 -> deterministic validator
 -> explicit human/narrow-rule approval
 -> normal domain command
 -> receipt
```

### Exit criteria

- no direct SQL or secret access;
- context inherits user authorization;
- structured task/schema/provider/prompt provenance retained;
- action preview is distinct from execution;
- prompt injection/untrusted document boundary exists;
- task-specific regression datasets/gates exist;
- long tasks use durable budgeted jobs.

## 19. Stage 15 — E15 conditional scale/PostgreSQL

### Purpose

Scale only from measured evidence.

Decision Gate 1 — should scale work begin?

Evidence may include:

- sustained SQLite write-lock contention;
- material p95/p99 transaction latency;
- unacceptable backup/restore RTO;
- reporting workload harming operations;
- required multi-host writes/HA/PITR.

If not: keep SQLite and finish E15 correctly.

Decision Gate 2 — is PostgreSQL production-ready?

Requires:

- SQLite-specific SQL inventory/adapters;
- same domain contract suite on SQLite/PostgreSQL;
- representative data migration reconciliation;
- backup/restore rehearsal;
- cutover/rollback rehearsal;
- measured benefit.

If not: keep SQLite.

## 20. Production rollout template for every runtime PR

Before each production cutover:

```text
1. exact current server code snapshot
2. consistent current DB snapshot
3. isolated DB restore verification
4. artifact/config Recovery Bundle according to wave scope
5. release gate on target code
6. maintenance/quiescence if schema/runtime changes
7. migration + postflight integrity
8. health/business smoke checks
9. rollback decision window
10. retain evidence/receipts
```

Later waves extending controlled RF artifacts must extend recovery scope so DB and file evidence restore together.

## 21. Immediate next executable work

Current next action is not another design wave.

```text
1. real checkout of Inventory PR #3
2. run repository-local E00 Release Gate
3. resolve failures if any
4. review PR #3 blockers
5. merge E00 only after PASS
6. execute backup-only production preflight against authorized production host/copy
7. only then begin E01 Slice A on a new dedicated branch/PR
```

Until step 5:

```text
E00 = IMPLEMENTED_AWAITING_LOCAL_VERIFICATION
E01..E15 = DESIGN/PREPARATION ONLY
```
