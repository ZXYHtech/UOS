# TASK_INV_AUDIT_AUTOMATION_RULES_01 — Rules Engine and Event-driven Automation Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed business services, operation logs, notification/todo concepts, order/fulfilment, purchasing/inventory, W3 manufacturing and W4 sales/aftersales/finance target models.

This report defines safe automation opportunities and execution guardrails. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite should add a **small event + rules + durable action framework**, not a general-purpose BPM engine and not a set of scattered `if` statements/timers.

The system already has useful ingredients:

- operation logs;
- domain statuses;
- notifications/todos;
- durable OCR jobs;
- platform sync states;
- business service boundaries.

The missing platform primitive is a controlled way to say:

```text
Business event occurs
 -> evaluate versioned rules
 -> produce deterministic actions
 -> require approval when risk is high
 -> execute through normal domain service
 -> record result / retry / reversal
```

Most automation should begin as **suggest / create draft / notify / route exception**, not silent irreversible mutation.

Preliminary maturity:

- notifications/todos: 3/5
- domain event evidence: 2.5/5
- durable background-job precedent: 3/5
- generic rules engine: 0.5/5
- automation approval/rollback governance: 0.5/5

## 2. Risk classes

Classify every automated action.

### A0 — read-only insight

Examples: calculate warning, suggest supplier, summarize anomaly.

Can run automatically.

### A1 — notification/todo/draft

Examples: create reminder, assign exception, draft PO.

Usually automatic; user confirms consequential follow-up.

### A2 — reversible business mutation

Examples: create reservation, update non-financial classification.

Requires explicit rule authority and compensating reversal.

### A3 — high-consequence mutation

Examples: ship/deduct stock, release quality, approve refund, publish price, pay/settle, release BOM.

Default policy: human approval required. Automation may prepare/validate but not silently commit unless a narrowly scoped operator-approved policy exists.

## 3. Required rule model

```text
rules
  id
  rule_code
  name
  event_type
  condition_expression / structured_json
  action_type
  action_params
  risk_class
  approval_policy
  enabled
  version
  effective_from/to
  created_by
  approved_by

rule_executions
  rule_id/version
  event_id
  evaluated_at
  condition_result
  action_id/job_id
  status
  actor_mode: automatic | approved
  result/error
```

A rule version used historically must remain explainable after rule edits.

## 4. Event contract

Business events should have stable type and identity, for example:

```text
inventory.balance_changed
inventory.reservation_shortage
purchase.po_approved
purchase.receipt_posted
order.confirmed
shipment.completed
transfer.exception
work_order.released
quality.inspection_failed
rma.opened
quote.sent
platform.sync_failed
settlement.mismatch
```

Event payload should contain IDs and minimal facts, not copy entire mutable objects unnecessarily.

## 5. Automation catalogue — inventory and replenishment

| # | Trigger / condition | Automated action | Approval / rollback / audit |
|---|---|---|---|
| 1 | Nettable stock drops below safety/reorder threshold | Create replenishment suggestion | A1; no PO creation; dedupe by material/site/planning snapshot |
| 2 | Days of cover below supplier lead time | Raise shortage-risk todo | A1; auto-close when risk clears; retain detection history |
| 3 | Stockout occurs on active sellable SKU | Create product/replenishment review | A1; link affected orders and duration |
| 4 | Same SKU has repeated stockouts in rolling period | Suggest safety-stock policy review | A0/A1; never edit safety stock silently |
| 5 | Inventory exceeds configured cover/value threshold | Create excess-stock review | A1; include value/demand evidence |
| 6 | No movement for configured period and no open demand | Flag slow/dead-stock candidate | A1; human confirms lifecycle/disposal action |
| 7 | Stock reservation expires | Release reservation if policy explicitly permits and object still valid | A2; idempotent reversal event; notify owner |
| 8 | Transfer receipt leaves unresolved variance | Create high-priority transfer exception | A1; cannot auto-write off quantity |

## 6. Automation catalogue — procurement and supplier

| # | Trigger / condition | Automated action | Approval / rollback / audit |
|---|---|---|---|
| 9 | Approved replenishment suggestions grouped by supplier | Generate draft PO | A1; buyer reviews quantities/prices/terms before submit |
| 10 | PO promised date approaches with no receipt/confirmation | Supplier follow-up todo | A1; dedupe; owner = buyer |
| 11 | PO becomes overdue | Escalate priority and update purchasing dashboard | A1; no automatic cancellation |
| 12 | New receipt price deviates beyond configured threshold | Price-variance exception | A1; compare same currency/UOM/source basis |
| 13 | Supplier lead time repeatedly exceeds policy | Suggest lead-time master update | A1; planner approves master-data change |
| 14 | Supplier IQC rejection rate breaches configured threshold | Supplier quality review / SCAR candidate | A1; no supplier disable without approval |
| 15 | Critical component has only one approved source | Supply-risk todo | A1; route to engineering + procurement |
| 16 | Component lifecycle becomes NRND/EOL through confirmed master-data update | Create where-used impact review | A1; suggest last-time-buy/redesign analysis; no auto-buy |

## 7. Automation catalogue — orders, allocation and fulfilment

| # | Trigger / condition | Automated action | Approval / rollback / audit |
|---|---|---|---|
| 17 | Canonical paid/confirmed order arrives and ATP policy satisfied | Create reservation and suggested warehouse allocation | A2; reservation reversible; policy/version recorded |
| 18 | Order cannot fully reserve | Mark backorder/shortage exception and notify sales | A1; do not promise guessed date |
| 19 | Order reserved but not picked within SLA | Warehouse todo/escalation | A1; dedupe by order/shipment |
| 20 | Shipment completed locally | Queue platform fulfilment outbox event | A1/A2 integration event; idempotent remote key |
| 21 | Platform fulfilment push fails retryably | Retry with backoff | A1; bounded attempts then manual review |
| 22 | Platform/local shipment status mismatch during reconciliation | Create reconciliation exception | A1; never overwrite local ledger automatically |
| 23 | Tracking number missing after shipped state | Create logistics-data correction todo | A1 |
| 24 | Remote cancellation arrives before shipment | Release reservation / cancel pending fulfilment according to explicit state policy | A2; compensating events + audit; post-ship becomes RMA exception instead |

## 8. Automation catalogue — manufacturing / MRP

| # | Trigger / condition | Automated action | Approval / rollback / audit |
|---|---|---|---|
| 25 | MRP run detects net requirement | Create planned buy/make/transfer recommendations | A1; planner firms them |
| 26 | Released WO has sufficient qualified stock | Auto-create material reservation | A2; reversible until issue; exact MBOM revision recorded |
| 27 | WO material shortage appears | Create shortage exception pegged to component/demand | A1 |
| 28 | Approved alternate can cover shortage | Suggest substitute | A1; engineering approval required when conditional |
| 29 | WO due date at risk from late component | Escalate planner/procurement todo | A1; include pegging and expected receipt |
| 30 | WO completed but unresolved issued material remains | Block cost-close and create reconciliation task | A1 gate; no silent consumption/write-off |
| 31 | Actual consumption deviates from standard beyond threshold | Create usage-variance review | A1; never rewrite BOM automatically |
| 32 | Repeated high setup/rework on product | Create manufacturability improvement candidate | A0/A1 |

## 9. Automation catalogue — quality, test and traceability

| # | Trigger / condition | Automated action | Approval / rollback / audit |
|---|---|---|---|
| 33 | Purchase receipt for IQC-controlled material | Create inspection order and keep stock pending inspection | A2 workflow creation; quality release remains human/controlled |
| 34 | Inspection result fails | Open NCR + quarantine affected quantity | A2; quality-state movement auditable/reversible only by disposition |
| 35 | Finished serialized unit missing mandatory valid test | Block saleable quality release | Deterministic gate; no override without authorized reason |
| 36 | Test equipment calibration expired at execution | Mark test invalid/review-required | A1/A2 evidence status; do not silently pass |
| 37 | Same product revision failure rate rises above threshold | Quality/engineering review | A1; require sufficient sample-size warning |
| 38 | Suspect component lot linked to multiple failures | Generate impact list of affected serials | A0/A1; human decides recall/hold |
| 39 | NCR disposition = rework | Create rework/retest task | A1; linked original NCR/serial |
| 40 | Controlled document revision superseded | Warn open unreleased WOs/tests still referencing stale draft/current selection | A1; never switch released historical work automatically |

## 10. Automation catalogue — sales, CRM and after-sales

| # | Trigger / condition | Automated action | Approval / rollback / audit |
|---|---|---|---|
| 41 | New inquiry created | Assign owner by configured territory/product/account rule | A1; manual reassignment allowed and audited |
| 42 | Quote sent | Create follow-up next action | A1; dedupe per quote revision |
| 43 | Quote nearing expiry and opportunity still active | Reminder | A1 |
| 44 | Opportunity remains stale beyond stage threshold | Escalate/close-review todo | A1; never auto-mark lost without policy/human decision |
| 45 | Evaluation sample return due | Sales/customer-service reminder | A1 |
| 46 | Customer case exceeds first-response/next-action SLA | Escalation todo | A1 |
| 47 | RMA received | Create inspection/diagnostic task | A1 |
| 48 | RMA test identifies confirmed repeat defect | Link/create quality review candidate | A1; root cause remains evidence-based |
| 49 | Advance replacement shipped and original return overdue | Asset/return escalation | A1 |
| 50 | Same support question/category repeats | Suggest knowledge-base article candidate | A0/A1; human authors/approves content |

## 11. Automation catalogue — channel finance / management

| # | Trigger / condition | Automated action | Approval / rollback / audit |
|---|---|---|---|
| 51 | Settlement batch imported | Normalize/match rows idempotently | A1 processing; unmatched rows remain exceptions |
| 52 | Expected vs actual platform fee exceeds threshold | Finance reconciliation exception | A1 |
| 53 | Order estimated/actual contribution profit < 0 | Pricing/owner review | A1; never auto-change public price |
| 54 | Refund occurs on already low-margin order | Surface realized-loss warning | A0/A1 |
| 55 | Weekly product metric snapshot identifies quality burden + strong sales | Product redesign review | A1 |
| 56 | Product has high inventory cash + low movement | Owner inventory-action todo | A1 |
| 57 | Backup age exceeds RPO policy | Operations alert | A1; high urgency; independent of GitHub |
| 58 | Worker dead-letter/backlog exceeds threshold | Operations alert | A1 |

## 12. Automation catalogue — data quality and governance

| # | Trigger / condition | Automated action | Approval / rollback / audit |
|---|---|---|---|
| 59 | New/imported material resembles existing code/MPN/alias | Duplicate-master review | A1; never auto-merge |
| 60 | BOM import contains unresolved/ambiguous parts | Engineering data-quality queue | A1; release blocked until resolved |
| 61 | Active material missing manufacturer/MPN required by category | Master-data completion todo | A1 |
| 62 | Same barcode maps to more than one active object | Block scan action + master-data exception | Deterministic gate |
| 63 | Released product references obsolete/unreleased mandatory controlled document | Configuration exception | A1/gate depending use |
| 64 | Metric/report source freshness exceeds policy | Mark report stale and schedule recalculation | A1; never display stale as current |

This catalogue contains **64 concrete automation opportunities**, exceeding the task's minimum of 30.

## 13. Condition language

Do not expose arbitrary Python/SQL execution as user-defined rules.

Use structured predicates:

```text
all:
  - field: event.material_id
    op: exists
  - metric: stock.days_cover
    op: <
    value_from: supplier.lead_time_days
```

Supported operations should be whitelisted and type checked.

Advanced expressions can be added later, but arbitrary code in DB is a security/upgrade hazard.

## 14. Action execution

Rules must call ordinary domain commands, not direct SQL.

Correct:

```text
rule -> command: create_reservation(...)
```

Wrong:

```text
rule -> UPDATE inventory SET ...
```

This preserves authorization, validation, ledger and idempotency invariants.

## 15. Approval policies

Possible policy types:

- `NONE` — read-only/draft/notification;
- `ROLE_APPROVAL`;
- `THRESHOLD_APPROVAL` — amount/quantity/risk;
- `TWO_PERSON` for selected high-risk releases;
- `DOMAIN_POLICY` — e.g. approved substitute only.

Rule evaluation may prepare an action request without executing it.

## 16. Dry-run and simulation

Before enabling a rule, run it in `observe_only` mode over historical/recent events:

```text
would have fired N times
objects affected
estimated action/result
false-positive review
```

For purchasing/replenishment rules, simulate quantities/cash impact.

Never enable a broad high-impact rule without observing its trigger frequency.

## 17. Idempotency and deduplication

Every action needs a deterministic key such as:

```text
rule_version + source_event_id + action_type + target_id
```

Repeated event delivery or worker retry should return the original execution.

Notifications also need dedupe to prevent repeated spam from a condition that remains true.

## 18. Condition-state automations

Some rules are not event-only, e.g. `PO overdue`.

Use scheduled evaluation that creates a synthetic observation/event:

```text
schedule -> evaluate due objects -> condition became true/continues/cleared
```

Record first detected, last detected and cleared time.

Server-local timer/worker owns execution; GitHub Actions is forbidden as required scheduler.

## 19. Rollback semantics

Rollback depends on action class.

- notification/todo: close/cancel record;
- draft PO: delete draft if policy permits;
- reservation: release with compensating event;
- classification: revision history/revert command;
- stock/financial event: **never delete**; post reversal/correction;
- external API: often cannot rollback reliably; use reconciliation/compensating command.

Each rule action definition must state its reversal capability before enablement.

## 20. Audit and explainability

For every execution answer:

- which event triggered it;
- rule/version;
- condition values;
- whether it ran automatically or after approval;
- which user approved;
- domain command/idempotency key;
- result/reversal;
- error/retry.

A user should be able to click `Why was this PO draft created?` and see the shortage/lead-time/MOQ evidence.

## 21. Prevent automation loops

Example loop:

```text
rule changes status -> emits status event -> same rule fires again
```

Controls:

- event/action idempotency;
- rule execution context/cause;
- max chain depth;
- ignore self-caused events where appropriate;
- cycle detection across rules;
- rate limits.

## 22. Kill switch and scopes

Support:

- global automation pause;
- per-rule disable;
- per-domain pause;
- account/warehouse scope;
- effective time;
- max executions per time window;
- high-impact circuit breaker.

Pausing automation must not disable core manual business commands.

## 23. Rule ownership and review

Every enabled rule has:

- business owner;
- technical owner;
- last reviewed date;
- evidence/intent;
- metrics showing executions/overrides/errors.

Review rules after process changes so stale automation does not preserve obsolete policy.

## 24. Observability

Dashboard:

- enabled rules;
- executions today/week;
- pending approvals;
- failed/retrying;
- dead-letter;
- top firing rules;
- user overrides/reversals;
- estimated time/actions saved;
- rules with no recent trigger;
- circuit-breaker state.

## 25. Implementation style

Start inside modular monolith:

```text
automation/
  events.py
  rule_registry.py
  evaluator.py
  actions.py
  approvals.py
  worker.py
```

Use DB-backed event/outbox/job tables. Do not introduce Kafka or a distributed workflow engine at current scale.

## 26. Priority roadmap

### P0

1. stable domain event envelope;
2. durable outbox/job execution;
3. versioned structured rules;
4. A0/A1 notification/draft automations first;
5. idempotency/deduplication;
6. approvals for A2/A3;
7. execution audit/explanation;
8. server-local scheduler and kill switch.

### P1

1. reservation/replenishment automations;
2. CRM/service reminders;
3. quality/traceability gates;
4. settlement/reconciliation rules;
5. dry-run historical simulation;
6. rule health/override analytics.

### P2

1. user-configurable safe rule builder;
2. optimization/recommendation policies;
3. AI-assisted rule drafting only with human review;
4. more complex event correlation if real use requires it.

## 27. Acceptance signals

- at least the 64 catalogue rules are classified by risk/action semantics;
- a rule never writes stock/master/financial data through direct SQL;
- retries cannot double-execute the same action;
- high-consequence actions default to approval;
- stock/financial corrections use compensating events rather than deletion;
- users can inspect why a rule fired and which version ran;
- rules can run in observe-only mode before enablement;
- automation loops are bounded/detected;
- global/per-rule kill switches work without disabling manual operations;
- scheduled rules run from server-owned worker/timer independent of GitHub Actions.

## 28. Core recommendation

Build automation as **versioned policy over durable business events**, starting with alerts, routing and drafts. Only automate reversible/irreversible mutations after reservation, idempotency, approval and audit contracts are solid. This gives the company broad automation safely without turning Inventory Lite into an opaque workflow engine.