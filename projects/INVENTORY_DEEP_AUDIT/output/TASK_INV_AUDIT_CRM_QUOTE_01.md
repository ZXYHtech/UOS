# TASK_INV_AUDIT_CRM_QUOTE_01 — Inquiry, Quotation, Sample and Customer-specific Sales Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed order/customer-adjacent fields, pricing engine, price lists/customer groups, order price snapshots, prototype/sample requirements and platform/order ingestion architecture.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite has strong downstream sales execution primitives—orders, pricing rules, channel conditions and shipment workflows—but little evidence of a first-class **pre-order commercial pipeline**.

The target company does not need a heavyweight generic CRM first. It needs a small RF/electronics sales workflow that connects:

```text
inquiry
 -> technical requirement
 -> product/solution candidate
 -> quotation revision
 -> sample/evaluation
 -> follow-up
 -> order conversion
```

The important design goal is continuity of evidence: when a customer asks for a 1.6 GHz LNA, custom filter or attenuator module, the quote should retain the technical requirements, chosen product/revision, price/cost basis, validity, sample history and later order conversion.

Preliminary maturity: **1.5/5** for CRM/quotation lifecycle.

## 2. Existing strengths to reuse

Useful foundations:

- price lists by channel/customer group;
- material price validity and minimum quantity;
- pricing rules;
- price revision history;
- order-item price snapshots;
- material specifications/resources;
- platform/order source identity;
- sample/engineering-stock target model from W3;
- operation logging.

Avoid building quotation pricing separately from `PricingService`; quotation should call the pricing domain and then freeze its own commercial snapshot.

## 3. Customer/account master

Introduce a minimal customer identity independent of shipping receiver text.

```text
customers
  id
  customer_code
  customer_name
  customer_type: company | individual | distributor | platform_buyer
  region/country
  sales_owner_user_id
  customer_group
  status
  tax/billing attributes where needed
  created_at
```

Contacts should be separate:

```text
customer_contacts
  customer_id
  name
  role
  phone/email/im identifiers
  primary flag
```

Do not equate marketplace receiver information with a durable B2B customer account automatically. Matching platform buyers to CRM accounts should be explicit or confidence-based with human confirmation.

## 4. Inquiry/opportunity object

For the small-company context, one lightweight object can serve inquiry/opportunity needs.

```text
sales_opportunities
  id
  opportunity_no
  customer_id
  contact_id
  source
  sales_owner
  stage
  expected_value
  expected_close_date
  probability optional
  technical_summary
  status
```

Suggested stages:

```text
new_inquiry
qualification
technical_review
quoted
sample_evaluation
negotiation
won
lost
on_hold
```

Do not force probability-based enterprise forecasting initially; stage, owner, next action and age are more operationally useful.

## 5. RF/electronics requirement capture

A quote workflow must handle technical requirements much better than ordinary retail CRM.

Use structured + free-form requirements:

- frequency range;
- gain/insertion loss;
- noise figure;
- output power/linearity;
- impedance/interface;
- connector type;
- supply voltage/current;
- dimensions/enclosure;
- control interface;
- quantity;
- environmental/test requirements;
- target price;
- requested delivery date;
- custom vs existing SKU.

Do not hard-code all RF parameters into the opportunity table. Use typed requirement attributes/spec groups so different product families remain extensible.

## 6. Product/solution candidates

An inquiry may evaluate several candidates:

```text
opportunity_candidates
  opportunity_id
  material/product_id
  product_revision
  fit_status
  gap_summary
  engineering_required
  preferred
```

For custom development, allow candidate type `new/custom product` that links later to an R&D project/product-creation workflow.

This creates a useful bridge from sales demand to engineering roadmap.

## 7. Quotation header and revision

Quotation must be revisioned, not edited in place after it is sent.

```text
quotations
  id
  quote_no
  opportunity_id
  customer_id
  currency
  status
  current_revision_id

quotation_revisions
  quotation_id
  revision_no
  valid_until
  payment_terms
  delivery_terms
  lead_time_text/snapshot
  commercial_notes
  status: draft | approved | sent | superseded | accepted | rejected
  created_by
  approved_by
  sent_at
```

When price/terms change after customer negotiation, create Rev B rather than overwriting Rev A.

## 8. Quote lines

Each line should preserve:

- product/material;
- product revision/configuration;
- quantity break;
- list/base price;
- discount/rule;
- quoted unit price;
- cost basis type/version;
- gross/contribution margin estimate;
- lead-time promise basis;
- technical description snapshot;
- optional/custom flag.

This snapshot prevents master-price changes from altering old quotations.

## 9. Margin approval

The W2 pricing audit identified terminology and profitability gaps. Quote approval should eventually support:

- floor-price warning;
- target gross-margin threshold;
- contribution-margin estimate;
- override reason;
- approval by threshold.

Do not approve based only on sales price if estimated manufacturing/purchase cost is missing or stale. Instead show evidence quality:

```text
cost basis: current estimate / released standard / unknown
as-of date
confidence/warning
```

## 10. Quote validity and lead time

Quotation validity needs explicit expiry.

Lead-time promise should be treated as a commercial snapshot, not a perpetual property of the SKU. It may depend on:

- current stock;
- supplier lead time;
- manufacturing load;
- MOQ;
- custom development;
- customer quantity.

Initially allow manually approved lead time; later integrate MRP/ATP for computed promise dates.

## 11. Samples/evaluation units

Connect the W3 sample model directly to opportunity/customer.

Sample request states:

```text
requested
approved
prepared
shipped
customer_evaluating
return_due
returned
converted_to_sale
closed
lost/damaged
```

Distinguish:

- free gift sample;
- paid sample;
- refundable sample;
- evaluation loan.

Capture exact serial for high-value RF modules once serial tracking exists.

## 12. Follow-up and next action

The highest-value CRM feature for a two-person/small sales operation is often simply preventing forgotten inquiries.

Each open opportunity should have:

- owner;
- next action;
- next-action due date;
- last meaningful contact date;
- stage age;
- reason lost/on-hold.

The dashboard should prioritize overdue follow-ups and quotes nearing expiry rather than require users to search conversation history.

## 13. Conversation/activity history

Use a generic activity feed:

```text
sales_activities
  opportunity/customer id
  activity_type: call | email | chat | meeting | note | sample | quote | status_change
  occurred_at
  actor
  summary
  attachment/reference
```

Do not attempt to clone a messaging app. Start with structured notes and references. External app connectors can later ingest selected messages/email metadata if business value justifies it.

## 14. Quote-to-order conversion

When a quote is accepted:

```text
accepted quotation revision
 -> create sales order draft
 -> preserve quote revision reference
 -> carry price snapshots/terms
 -> reserve ATP after order commitment policy
```

The resulting order must remain linked to exactly the quote revision accepted by the customer.

Do not rebuild the order manually and lose commercial provenance.

## 15. Customer-specific pricing

Current customer-group pricing is useful. Add customer-specific contracts only when needed:

- price agreement;
- validity window;
- MOQ/quantity breaks;
- product scope;
- currency;
- approval owner.

Avoid duplicating customer-specific rules inside quotations; master agreements should feed quotation pricing and the quote freezes the result.

## 16. Lost reasons and product intelligence

Capture structured lost reasons:

- price too high;
- lead time;
- spec mismatch;
- certification/document gap;
- competitor selected;
- no response;
- project cancelled;
- MOQ issue;
- product unavailable/EOL.

This turns CRM data into product-roadmap evidence rather than only sales administration.

For an RF module shop, aggregate unmet parameter requests can identify high-value future products.

## 17. Automation opportunities

Without GitHub Actions dependency:

- overdue follow-up reminders;
- quotation expiry alerts;
- sample return reminders;
- stale opportunity detection;
- auto-create follow-up after quote sent;
- auto-suggest price based on customer group/quantity;
- warn when quote uses obsolete product/BOM revision;
- suggest existing similar product from parametric search;
- flag repeated lost reason/product gap.

Writes/notifications should run from application/server schedulers/workers.

## 18. UX priority

Recommended screens:

1. inquiry/opportunity inbox;
2. opportunity detail with technical requirements + activity timeline;
3. quote builder with quantity tiers and margin evidence;
4. quote revision comparison;
5. sample/evaluation register;
6. follow-up queue;
7. lost-reason/product-demand analytics.

Keep the workflow lightweight enough that staff actually uses it.

## 19. Priority roadmap

### P0

1. customer/contact master;
2. inquiry/opportunity with owner/stage/next action;
3. technical requirement attributes;
4. revisioned quotation + frozen line snapshots;
5. quote-to-order link;
6. sample link to opportunity/customer;
7. lost reason.

### P1

1. approval thresholds based on floor/margin;
2. customer-specific price agreements;
3. parametric product-match suggestions;
4. quote PDF generation from controlled template;
5. reminders/activity feed.

### P2

1. email/chat connector ingestion;
2. AI-assisted requirement extraction and quote drafting;
3. opportunity probability/forecast analytics;
4. custom-product request -> R&D project automation.

## 20. Acceptance signals

- a customer inquiry has an owner and cannot become invisible merely because no order exists yet;
- quote Rev A remains unchanged after Rev B is created;
- accepted order resolves exactly the accepted quote revision and price snapshot;
- technical RF requirements are searchable and comparable to product specs;
- sample/evaluation stock is linked to customer/opportunity and correct disposition;
- overdue follow-up/return/quote-expiry exceptions are visible;
- lost reasons can be aggregated into product-demand insights;
- no required reminder/quote generation/test path depends on GitHub Actions.

## 21. Core recommendation

Build a **small technical-sales CRM**, not a generic enterprise CRM: inquiry + RF requirements + revisioned quote + sample + next action + order conversion. Reuse the existing pricing engine and make every commercial decision traceable to the technical and cost evidence available at the time.