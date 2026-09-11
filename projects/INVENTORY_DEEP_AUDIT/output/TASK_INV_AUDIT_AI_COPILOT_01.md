# TASK_INV_AUDIT_AI_COPILOT_01 — AI Copilot and Agent Automation Opportunities Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed OCR/recognition architecture, correction/revision records, business services, planned rules/jobs, product/engineering data, CRM/support/reporting target domains and security/privacy constraints.

This report designs assistive AI opportunities. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite is a good candidate for an AI copilot **after** deterministic business contracts are strengthened, because it contains rich linked operational data and already demonstrates the correct human-in-the-loop pattern in OCR.

The design principle should be:

```text
AI interprets, extracts, ranks, summarizes and drafts
Deterministic services validate identities, permissions, states, quantities and money
Human or explicit rule policy authorizes consequential actions
```

AI must never become an invisible second source of truth for stock, price, BOM, quality, settlement or product revision.

The existing OCR subsystem is the strongest precedent: machine candidate -> validation -> human confirmation -> canonical service. Reuse that pattern.

Preliminary maturity:

- OCR human-in-loop architecture: 4/5
- AI provider production readiness: 1–2/5
- correction/evaluation data: 3/5
- business knowledge graph readiness: 2/5 today, improving strongly after W3/W4
- AI tool/action governance: 0.5/5
- evidence/citation layer: 0.5/5

## 2. AI capability classes

### C0 — explain/summarize

No business mutation. Example: summarize a product's stock/sales/RMA situation.

Low risk if data access is authorized and claims cite source records.

### C1 — extract/classify/rank

Produces structured candidate data. Example: extract supplier quote or classify support case.

Must expose confidence/evidence and allow correction.

### C2 — draft/recommend

Produces a proposed PO, quote, response, substitution or replenishment plan.

Deterministic validation before user approval.

### C3 — bounded action assistant

Calls approved domain commands only after explicit user approval or narrowly configured automation policy.

Examples: create draft PO, add approved alias, schedule follow-up.

### C4 — high-consequence autonomous action

Examples: deduct stock, release quality, approve refund, release BOM, change public price.

**Not recommended by default.** Require explicit deterministic workflow/approval; AI may prepare evidence but should not be sole authority.

## 3. AI architecture

Recommended flow:

```text
User/Business event
 -> context builder (authorized records only)
 -> AI task with declared purpose/schema
 -> structured candidate + evidence refs + uncertainty
 -> deterministic validators
 -> human/rule approval
 -> normal domain service command
 -> audit record
```

Never allow the model direct SQL access in production.

AI tools should expose constrained business functions, such as:

```text
search_materials(query)
get_material(id)
get_stock(material, scope)
get_supplier_history(material)
create_po_draft(validated_lines)
create_case_note(...)
```

not `execute_sql()`.

## 4. Evidence-first answer contract

For factual operational answers, the copilot should return:

```text
Answer / recommendation
Supporting records
Data timestamp/freshness
Known limitations / missing data
Proposed action (if any)
```

Examples:

`Why can't order O-123 ship?`

should cite:

- order lines;
- current reservation/ATP;
- shipment state;
- shortage component;
- expected PO/transfer supply.

It must not guess `supplier will arrive tomorrow` without a recorded expected date/source.

## 5. Use-case catalogue — document/data extraction

### 1. Supplier quotation extraction

Input: PDF/image/email attachment.

Extract candidate:

- supplier;
- manufacturer/MPN;
- supplier SKU;
- MOQ;
- unit-price breaks;
- currency;
- lead time;
- validity;
- remarks.

Human validates before updating supplier/source data or PO.

### 2. Datasheet metadata extraction

Extract manufacturer, MPN, package, core parameters, lifecycle/compliance claims and source-page references.

Do not overwrite approved engineering attributes automatically. Show exact document/revision/source.

### 3. BOM/EDA normalization

From KiCad/Altium/exported BOM:

- normalize value/package/MPN/refdes;
- match internal parts;
- rank candidates;
- flag unresolved/ambiguous lines.

Never silently substitute a base model or alternate.

### 4. Purchase/packing-list OCR

Extract receipt candidate data, then validate against open PO before human receipt confirmation.

### 5. Marketplace/order screenshot recognition

Continue existing mature OCR pattern and improve evaluation rather than replacing it.

## 6. Use-case catalogue — part and engineering copilot

### 6. Part matching assistant

Given arbitrary customer/supplier/EDA part text, explain ranked internal candidates based on exact code/MPN/alias/spec.

No auto-selection on ambiguity.

### 7. Alternate-part discovery

Generate **candidate** alternates using parametric similarity, AVL history and datasheets.

Output must separate:

- approved alternate;
- known conditional alternate;
- AI-proposed unapproved candidate.

Only engineering workflow can approve substitution.

### 8. Where-used impact summary

Given EOL/ECN component, summarize affected released BOMs, products, open WOs, stock and demand.

This is largely deterministic retrieval plus natural-language explanation.

### 9. ECO drafting

Draft change reason, affected objects, old/new BOM/document revisions and verification checklist from structured change input.

Release remains controlled/human-approved.

### 10. Engineering requirement matching

Compare CRM technical requirements against product parametric data and identify fit/gaps.

Explicitly label missing/estimated product data.

## 7. Use-case catalogue — procurement and MRP

### 11. Purchase recommendation explanation

Convert deterministic MRP/replenishment result into readable rationale:

```text
why buy
which demand
which open supply
lead time
MOQ
alternate risk
```

AI must not recalculate hidden demand independently of MRP.

### 12. Supplier selection assistant

Rank candidate approved sources using deterministic facts:

- price;
- lead time;
- quality;
- delivery performance;
- MOQ;
- availability;
- currency.

AI can explain tradeoffs; procurement approves.

### 13. PO draft assistant

Group accepted replenishment recommendations and prepare a draft PO with assumptions/warnings.

No automatic approval/submission.

### 14. Supplier-risk digest

Summarize EOL, sole-source, late-delivery, NCR and price-trend signals by critical component/product.

### 15. Supplier communication draft

Draft inquiry/follow-up for late PO, technical clarification or corrective action based on case facts. Human reviews before send.

## 8. Use-case catalogue — warehouse / operations

### 16. Natural-language object lookup

Examples:

- `找一下 PE43711 现在在哪些仓位还有货`
- `哪个订单因为这个料缺货？`

System converts intent to constrained search/query APIs and cites returned objects.

### 17. Exception explanation

Summarize why a shipment/transfer/receipt is blocked and suggest valid next actions from state machine.

### 18. Count-variance triage

Rank possible explanations from movement history, open tasks and scan logs. Do not auto-adjust inventory.

### 19. Putaway/pick suggestion

Suggest locations based on deterministic capacity/location policy and active tasks. Warehouse confirms.

### 20. Operation-log summarization

Turn long before/after event history into concise timeline while retaining links to original records.

## 9. Use-case catalogue — quality and test

### 21. RF test-report summary

Read structured measurement/test data and summarize:

- passed/failed items;
- worst margin to limit;
- relevant trace trends;
- test setup/equipment;
- comparison to prior run.

Pass/fail must come from deterministic released limit-set evaluation, not model judgment.

### 22. S-parameter/test anomaly assistance

AI can identify unusual curve patterns or compare traces to known historical failure groups, but result is diagnostic hypothesis, not quality disposition.

### 23. NCR drafting/classification

From failed inspection/test evidence, draft defect description/category and impacted records.

Quality confirms disposition/root cause.

### 24. Failure-cluster analysis

Group RMA/test/NCR cases by symptoms, revision, component lot and conditions, then surface statistically meaningful clusters with sample size.

Do not claim causal root cause from correlation alone.

### 25. Troubleshooting assistant

For support/engineering, propose a stepwise diagnostic checklist using controlled product documentation and known test history.

Safety-critical/high-power instructions must come from approved content, not unrestricted generation.

## 10. Use-case catalogue — sales / CRM

### 26. Inquiry extraction

From email/chat/note, extract customer, requested RF specs, quantity, target price/date and unanswered questions into an opportunity draft.

Human confirms before CRM record/update.

### 27. Product recommendation

Match requirement against product specs/stock/lead time and return ranked products with explicit fit/gap evidence.

### 28. Quote drafting

Create quotation draft using approved pricing service, customer agreement and product data.

AI writes wording/structure; deterministic pricing/cost/margin calculations remain authoritative.

### 29. Follow-up draft

Summarize conversation and draft next customer message. Human reviews/send policy applies.

### 30. Win/loss summarization

Aggregate structured loss reasons + case notes and identify recurring product/price/lead-time gaps.

## 11. Use-case catalogue — customer service/RMA

### 31. Case summarization

Produce current status, customer ask, actions already taken, linked order/serial/RMA and next action from long timeline.

### 32. Case classification/routing

Suggest category/severity/domain owner. High severity remains human-reviewable.

### 33. Similar-case retrieval

Find previously resolved cases for same product/revision/symptom and link their verified resolution.

### 34. RMA pre-triage

Given serial and customer symptoms, retrieve test/manufacturing history and propose diagnostic plan.

Do not deny warranty or blame customer automatically.

### 35. Knowledge-article drafting

Draft article from repeated resolved cases and controlled documents. Technical owner reviews/version-controls before publication.

## 12. Use-case catalogue — finance and management

### 36. Margin anomaly explanation

Given a negative-contribution order, explain which economic events caused it: discount, COGS, freight, platform fee, refund/RMA.

Do not invent missing settlement data.

### 37. Settlement mismatch assistance

Rank likely matches for unmatched settlement rows and explain amount/date/order similarity. Finance confirms.

### 38. Daily owner brief

Summarize governed KPI/exception records:

- critical shortages;
- late PO/orders;
- quality/RMA issues;
- cash/inventory anomalies;
- negative margin;
- actions due.

Every statement links to metric/object evidence.

### 39. Product portfolio narrative

Explain why a product is categorized as invest/reprice/redesign/MTO/EOL from explicit scorecard dimensions.

### 40. Natural-language governed analytics

User asks:

`过去三个月哪个产品卖得多但售后成本也高？`

Copilot maps to governed metric definitions, executes constrained analytical query and reports calculation scope.

This catalogue includes **40 bounded AI opportunities**.

## 13. Tool permission model

AI inherits the user’s effective authorization; it never receives broader data simply because the model can reason across domains.

Tool call checks must include:

- user/session;
- permission;
- warehouse/account/customer scope;
- business object state;
- action risk/approval.

For read tools, avoid exposing hidden credentials/PII beyond the user's role.

For write tools, use the exact same service commands as normal UI.

## 14. Read versus write modes

Default chat/copilot mode should be read-only unless user explicitly initiates action.

For proposed writes:

```text
AI proposes
 -> UI shows structured diff/action preview
 -> deterministic validation
 -> explicit approve
 -> service command
 -> operation receipt
```

Do not hide tool actions inside conversational prose.

## 15. Structured output schemas

Every extraction/recommendation task should have a versioned JSON schema.

Example quote/inquiry extraction:

```text
customer_candidate
requirements[]
quantity
requested_date
target_price
source_spans/evidence
confidence_by_field
unknown_fields[]
```

Reject malformed model output rather than best-effort writing it to canonical records.

## 16. Confidence is not authority

A high model confidence does not override business rules.

Examples:

- 99% confident material match but exact MPN differs -> cannot auto-substitute;
- 99% confident test trace looks good but released limit fails -> FAIL remains;
- 99% confident warranty likely invalid -> human/policy decision still required;
- 99% confident stock count -> scan/ledger truth still authoritative.

Use confidence to prioritize review, not bypass deterministic controls.

## 17. Retrieval and evidence boundaries

AI context should retrieve only necessary records.

Preferred source order:

1. canonical transactional data;
2. released controlled documents;
3. structured test/product/spec data;
4. approved knowledge articles;
5. historical cases/notes;
6. external web/vendor data only when task explicitly requires current outside information.

For external datasheets/vendor content, preserve URL/document revision/date and distinguish external claim from internally approved spec.

## 18. PII and external provider policy

Before using online models, define which data may leave the deployment boundary.

Data classes:

- public product data;
- internal engineering data;
- supplier commercial data;
- customer PII;
- credentials/secrets;
- raw order screenshots;
- controlled/NDA documents.

Secrets must never be included in model prompt/context.

For customer/order PII, minimize/redact fields unless necessary and provider/data-retention policy is approved.

Local models/OCR may be preferable for sensitive extraction if quality is sufficient.

## 19. Model/provider provenance

Every consequential AI result should record:

- task type/schema version;
- provider/model;
- model version/identifier when available;
- prompt/template version;
- source object IDs/hashes;
- created time/user;
- structured output;
- validation result;
- human corrections;
- final accepted/rejected state.

This extends the existing recognition revision/correction pattern.

## 20. Evaluation framework

Each AI feature needs a task-specific regression dataset.

Metrics vary by use case:

- extraction exact-field accuracy;
- material-match top-1/top-k and false-auto-match;
- classification precision/recall;
- recommendation acceptance rate;
- hallucinated/unsupported factual claim rate;
- citation/evidence correctness;
- time saved;
- human correction frequency;
- cost/latency;
- privacy boundary violations = zero tolerance.

Compare against deterministic/no-AI baseline where possible.

## 21. Human correction as learning signal

Preserve:

```text
AI candidate
human accepted/corrected/rejected
changed fields
reason where useful
```

Aggregate correction patterns to improve prompts/rules/models.

Do not automatically train external models on customer/business data without explicit governance/consent policy.

## 22. Prompt-injection and untrusted documents

Supplier/customer documents and web pages are untrusted content. Treat instructions inside them as data, not system commands.

Controls:

- task-specific model prompt with strict schema;
- no arbitrary tool permissions during extraction;
- tool calls only from trusted orchestration layer;
- source document cannot request credential access or writes;
- sanitize/limit retrieved content;
- explicit approval for write actions.

## 23. Natural-language query safety

Do not convert user text into unrestricted SQL.

Preferred architecture:

```text
NL question
 -> intent/metric/entity plan
 -> approved query functions / semantic layer
 -> deterministic DB query
 -> AI explains result
```

For governed analytics, map terms such as `利润`, `库存周转`, `RMA率` to metric registry definitions.

## 24. Agent loops and budgets

For multi-step AI tasks:

- max tool calls;
- time/cost budget;
- allowed tools/domain scope;
- max rows/artifacts;
- explicit stop conditions;
- approval checkpoints;
- cancellation;
- durable job state for long work.

Avoid an unconstrained autonomous loop against business APIs.

## 25. Durable AI jobs

Reuse OCR worker concepts for:

- long document extraction;
- product analysis;
- report drafting;
- anomaly clustering;
- bulk classification.

Job record:

```text
queued -> running -> succeeded / review_required / failed
```

Include retry policy and model/provider error class. Required workers run under systemd/server infrastructure, not GitHub Actions.

## 26. AI UX

Avoid a generic floating chat as the only interface.

Embed copilot where context is strongest:

- material workspace: `find alternates / summarize supply risk`;
- PO: `explain recommendation`;
- product: `portfolio summary`;
- quote: `draft from requirements`;
- RMA: `summarize history / propose test checklist`;
- dashboard: `explain today's critical items`.

Also provide global chat for cross-entity questions, but always show data sources/actions.

## 27. Action preview

Before AI-assisted write:

```text
Proposed action
Objects affected
Before -> after
Reason/evidence
Validation warnings
Approval required
```

The confirmation button executes a deterministic service command, not “trust model output”.

## 28. Cost control

Track per AI task:

- provider/model;
- tokens/request or provider billing unit;
- latency;
- success/failure;
- user/domain;
- value proxy (accepted output/time saved).

Use cheaper deterministic/local methods for tasks that do not need generative reasoning.

Do not send every search/autocomplete through an LLM when existing matching logic is faster and safer.

## 29. Phased rollout

### Phase A — C0/C1, read/extract

1. case/order/product summaries;
2. supplier quote/datasheet extraction;
3. inquiry requirement extraction;
4. material candidate explanation;
5. daily management brief from governed data.

### Phase B — C2 drafts/recommendations

1. quote draft;
2. PO draft;
3. alternate candidate review;
4. support reply/troubleshooting draft;
5. NCR/ECO draft;
6. settlement match suggestion.

### Phase C — bounded C3 actions

Only after rules/idempotency/permissions mature:

- create follow-up;
- assign case;
- create draft document/order;
- add reviewed classification/alias;
- submit explicitly approved domain command.

### Phase D

Do not pursue broad C4 autonomy unless individual use cases demonstrate safety/business value and deterministic policy can constrain them.

## 30. Priority roadmap

### P0

1. AI task/result/evidence schema;
2. provider/data privacy classification;
3. constrained read tool layer respecting user scope;
4. structured outputs + validators;
5. source/evidence display;
6. model/prompt provenance;
7. correction/rejection history;
8. evaluation datasets;
9. no direct SQL or secret access.

### P1

1. embedded product/support/procurement copilot experiences;
2. controlled write tools with preview/approval;
3. durable AI job worker generalized from OCR;
4. governed natural-language analytics;
5. prompt-injection defenses;
6. cost/latency dashboards.

### P2

1. advanced failure/product-demand clustering;
2. scenario planning;
3. semi-autonomous bounded workflows under rules engine;
4. local/domain models where economics/privacy justify them.

## 31. Acceptance signals

- factual AI answers link to supporting authorized records and data freshness;
- AI cannot access data/actions beyond the current user’s effective scope;
- extraction output must pass a versioned schema before use;
- ambiguous material/substitute results never silently become canonical selection;
- quality/test pass-fail remains deterministic from released limits;
- price/MRP/profit calculations remain governed services, not free-form model math;
- consequential writes show preview and require applicable approval;
- every accepted AI result retains provider/model/prompt/source/correction provenance;
- untrusted documents cannot instruct the agent to access secrets or perform writes;
- evaluation tracks unsupported claims and human correction, not just subjective usefulness;
- no required AI job, test or scheduling path depends on GitHub Actions.

## 32. Core recommendation

Use AI as a **contextual reasoning and drafting layer over deterministic business services**, following the OCR subsystem's existing candidate-validation-confirmation pattern. The most valuable future copilot is not one that “runs the inventory system itself”; it is one that can connect part, stock, supplier, BOM, order, test, customer and profit evidence quickly while making uncertainty and proposed actions explicit.