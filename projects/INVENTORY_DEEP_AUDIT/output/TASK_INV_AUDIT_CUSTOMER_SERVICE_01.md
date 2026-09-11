# TASK_INV_AUDIT_CUSTOMER_SERVICE_01 — Customer-service Case and Operational Collaboration Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed `ExceptionService`, orders, shipment tasks, platform accounts, operation logs and W4 RMA/CRM requirements.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite already has a useful internal operational exception surface. `ExceptionService` can aggregate recognition failures, order exceptions, platform-sync exceptions, stock shortages, shipment exceptions, missing logistics data and transfer exceptions; it also supports assignment, notes, resolve/close actions and operation logging.

That capability should be preserved, but it is **not yet a customer-service ticket/case system**. The inspected core schema does not show a first-class customer-service ticket entity, persistent SLA fields, customer conversation thread, category/root-cause taxonomy or linkage to RMA/refund outcomes.

The right design is not to replace `ExceptionService`. It is to separate:

```text
Operational Exception = internal process problem requiring action
Customer Service Case = customer-facing issue/request requiring ownership and resolution
```

One may create or link to the other.

Preliminary maturity:

- internal exception aggregation: 3.5/5
- exception assignment/action logging: 3/5
- customer-service case lifecycle: 0.5/5
- SLA/escalation: 0.5/5
- conversation/context timeline: 1/5
- knowledge/root-cause analytics: 0.5/5

## 2. Preserve the current ExceptionService role

Current behavior is valuable because it derives an action queue from real business objects rather than requiring duplicate issue entry.

Examples already surfaced include:

- AI/OCR failure or unresolved recognition;
- duplicate/order confirmation issues;
- order status exception;
- marketplace synchronization failure;
- shipment stock shortage;
- shipment/logistics issue;
- transfer exception.

This should evolve into a generic **operational exception registry** with stable exception identity, owner, timestamps and resolution metadata.

Do not turn every internal exception into a customer ticket automatically. Many warehouse/system exceptions never need customer communication.

## 3. Customer-service case identity

Introduce a durable case object:

```text
service_cases
  id
  case_no
  customer_id
  contact_id
  channel/source
  platform_account_id
  external_case_id
  order_id
  shipment_id
  rma_id
  case_type
  severity/priority
  status
  owner_user_id
  opened_at
  first_response_at
  resolved_at
  closed_at
  next_action_at
  subject
  summary
```

A case must exist independently from an order because customers can ask pre-sale, product-use, technical and warranty questions without a formal order.

## 4. Case taxonomy

Suggested top-level categories:

- pre-sales specification question;
- quotation/order question;
- payment/invoice;
- order modification;
- shipping/logistics;
- wrong/missing item;
- product setup/use;
- technical performance issue;
- suspected defect;
- return/refund/exchange;
- warranty/repair;
- documentation/test-report request;
- complaint;
- other.

Keep customer-reported category separate from final root cause.

A customer reporting “gain too low” might ultimately be:

- wrong test setup;
- connector/cable loss;
- incorrect supply;
- damaged product;
- firmware/configuration issue;
- real manufacturing defect.

## 5. Status model

A small, clear lifecycle is preferable:

```text
OPEN
IN_PROGRESS
WAITING_CUSTOMER
WAITING_INTERNAL
WAITING_LOGISTICS
WAITING_RMA
RESOLVED
CLOSED
```

Use linked object states for detail rather than creating dozens of ticket statuses.

Reopening a case should retain prior resolution history.

## 6. SLA and aging

A useful SLA model should measure at least:

- first-response due/actual;
- next-action due;
- resolution target;
- total case age;
- time waiting on customer separately from internal active time if needed.

Policy may vary by:

- customer class;
- sales channel;
- severity;
- warranty/technical case;
- working calendar.

Do not hard-code one universal SLA into the schema.

For a small team, the first implementation can be simple: first-response target + next-action overdue + case-age alert.

## 7. Unified context panel

The greatest UX win is not a separate ticket page full of duplicated data. A support agent should open one case and see relevant context:

```text
Customer/contact
 -> inquiry/quote history
 -> order and price snapshot
 -> shipment/tracking
 -> exact serial/product revision
 -> test report/history
 -> prior service cases
 -> RMA/repair/refund
 -> operational exceptions
```

The system should resolve these through references instead of copying fields into the case.

## 8. Conversation and activity timeline

Use an append-only activity model:

```text
service_case_events
  case_id
  event_type: note | inbound_message | outbound_message | call | status_change | assignment | escalation | linked_exception | linked_rma
  occurred_at
  actor/user
  external_message_id
  channel
  visibility: internal | customer_visible
  body/summary
  attachment/reference
```

Do not make mutable `remark` text the permanent conversation history.

The existing exception-note pattern is useful for short-lived operational annotations but insufficient for customer correspondence and auditability.

## 9. External channel message identity

If future Taobao/email/chat connectors ingest customer messages, use durable external identity:

```text
platform_account_id
external_thread_id
external_message_id
message_timestamp
payload_hash
```

Replay must not duplicate case events.

Message ingestion should be connector/worker based and independent of GitHub Actions.

## 10. Internal exception linkage

A service case can link one or more operational exceptions:

```text
Customer asks: “Why has order not shipped?”
 -> service case CS-001
 -> linked shipment stock-shortage exception
 -> warehouse action
 -> customer update
```

Resolution should not automatically close both objects unless their business states justify it.

Conversely, a high-severity operational exception may create a proactive customer-service case when customer impact is known.

## 11. RMA and technical support handoff

For suspected hardware failure:

```text
service case
 -> troubleshooting checklist
 -> if unresolved: RMA request
 -> RMA diagnosis/repair/retest
 -> case receives outcome
 -> customer communication
 -> close
```

Keep customer communication and technical RMA execution separate but cross-linked.

For serialized RF modules, support should be able to retrieve exact test and revision history before authorizing return where appropriate.

## 12. Troubleshooting templates

High-value reusable playbooks for RF products may include:

- verify supply voltage/current;
- verify 50-ohm source/load;
- verify cable/adapter loss;
- check frequency range;
- confirm control-state/attenuation settings;
- collect S-parameter/spectrum screenshot or Touchstone file;
- identify serial/firmware version;
- compare against product test report.

These should be structured templates/checklists, not hard-coded logic. They reduce repeated questions and improve diagnosis quality.

## 13. Macro/reply templates

Support response templates can cover:

- shipping delay;
- tracking information;
- test setup instructions;
- RMA instructions;
- sample return reminder;
- quote follow-up;
- documentation request.

Templates should allow human review before send unless a low-risk automation policy explicitly permits automatic messages.

## 14. Escalation

Escalation targets should be domain-specific:

- warehouse/logistics;
- sales;
- engineering;
- quality;
- procurement;
- finance;
- management.

Escalation should create ownership and next action, not merely mention another person in a note.

High-value escalation rules:

- repeated same-serial failure;
- safety/high-power concern;
- multiple customer reports on same product revision;
- overdue RMA diagnosis;
- platform dispute deadline;
- high-value refund;
- suspected systemic product defect.

## 15. Root cause and resolution taxonomy

At resolution capture:

- final problem category;
- root cause when known;
- resolution type;
- responsible domain;
- product/revision/lot/serial links;
- customer impact;
- whether quality/NCR/ECO/KB update is required.

Do not force a root cause when evidence is insufficient; allow `unknown/not confirmed` explicitly.

## 16. Recurring-issue analytics

Useful analyses:

- cases per 100 orders/shipments;
- first response/resolution time;
- reopen rate;
- top issue categories;
- product/revision failure concentration;
- shipping-carrier issues;
- repeated setup misunderstandings;
- warranty/RMA conversion rate;
- refund rate by cause;
- cases linked to same component lot;
- knowledge article deflection/usefulness later.

Volume alone should not be interpreted as product defect without normalizing by sales/installed base.

## 17. Knowledge-base loop

A support case should be able to suggest a reusable knowledge article candidate when:

- the same question repeats;
- troubleshooting steps are stable;
- engineering confirms the answer;
- documentation is missing or confusing.

Knowledge records should carry product/revision applicability and review date for technical content.

Do not allow AI-generated support answers to become authoritative without source/review controls for technical claims.

## 18. AI assistance opportunities

After structured cases exist, AI can assist with:

- summarize long case timeline;
- classify intent/category;
- suggest relevant product docs/test setup;
- draft reply;
- extract serial/order/tracking IDs;
- suggest duplicate/related cases;
- surface likely root-cause clusters.

AI should not autonomously approve warranty, refund or technical safety conclusions without policy and deterministic checks.

## 19. Notifications and reminders

Server-local scheduler/worker can generate:

- overdue next-action reminder;
- SLA breach warning;
- waiting-customer follow-up;
- RMA diagnosis overdue;
- platform dispute deadline;
- stale unresolved case.

Notifications should deduplicate and record acknowledgement where meaningful. GitHub Actions is forbidden as a required scheduler.

## 20. Permissions

Suggested split:

- support: create/update cases and customer-visible communication;
- warehouse: view linked fulfilment context, act on warehouse exceptions;
- engineering/quality: technical diagnosis and escalation notes;
- finance: refund/payment context;
- managers: SLA/reporting and high-value approval;
- admin: templates/policies.

Internal-only notes must never leak through customer-facing APIs.

## 21. Priority roadmap

### P0

1. first-class service case;
2. owner/status/next action/SLA timestamps;
3. order/shipment/customer/RMA links;
4. append-only activity timeline;
5. structured category/resolution codes;
6. operational exception linkage;
7. overdue work queue.

### P1

1. channel/email/message connector ingestion;
2. RF troubleshooting templates;
3. reply macros;
4. escalation rules;
5. recurring-issue analytics;
6. KB candidate workflow.

### P2

1. AI summarization/classification/draft replies;
2. proactive customer notifications from critical operational exceptions;
3. richer self-service portal;
4. knowledge retrieval assistant with controlled sources.

## 22. Acceptance signals

- a customer case can exist without an order;
- one case can link order, shipment, serial, RMA and operational exceptions without copying their mutable state;
- assignment/status/response history is append-only and auditable;
- waiting-customer and internal-active time can be distinguished;
- internal notes are not exposed as customer-visible messages;
- RMA handoff preserves one end-to-end case context;
- recurring issues can be grouped by product/revision/root cause;
- operational exception resolution does not silently close a customer case;
- no required notification/message-sync/test path depends on GitHub Actions.

## 23. Core recommendation

Keep `ExceptionService` as the internal operational-exception engine and add a separate **customer-service case layer** with SLA, conversation timeline, business-object context and escalation. Linking these two domains will deliver much more value than trying to turn free-form order/shipment remarks into a support system.