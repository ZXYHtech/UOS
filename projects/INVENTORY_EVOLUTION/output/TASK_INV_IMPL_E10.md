# TASK_INV_IMPL_E10 — Technical CRM, Quote, Sample, Service Case & RMA

## Status
`DESIGN_READY_BLOCKED_BY_E04_E07_E09_FOUNDATIONS`

## Objective
Create one lightweight customer lifecycle suitable for RF/electronics sales and after-sales without replacing the existing order, pricing, shipment, quality or internal exception engines.

Target chain:

```text
customer/contact
 -> inquiry/opportunity
 -> structured technical requirement
 -> product/custom candidate
 -> revisioned quotation
 -> sample/evaluation
 -> accepted quote -> order
 -> service case
 -> RMA/refund/repair/exchange when needed
 -> quality/product feedback
```

## Boundaries

```text
Pricing/E11 = commercial formula/floor/economics
E04/E05 = product/engineering identity
E07 = serial/test/quality truth
E09 = marketplace after-sales observations
E10 = customer relationship, quote, service/RMA workflow
ExceptionService = internal operational exception engine, preserved separately
```

## Principles
- marketplace receiver text is not automatically a durable CRM customer;
- sent/accepted quotation revision is immutable;
- quote lines freeze price/technical/cost-basis evidence available at the time;
- samples are explicit gift/paid/loan/evaluation dispositions;
- customer-service case is separate from internal operational exception;
- refund, physical return, technical repair and warranty are distinct states;
- returned goods enter quarantine, never direct ATP;
- serialized RMA preserves original shipment/work-order/test history;
- case/RMA activity history is append-only;
- automation/reminders use E01 durable jobs/systemd, never GitHub Actions.

## Definition of done
E10 is complete when a staff member can trace one customer issue from inquiry/quote/sample/order through support/RMA outcome without reconstructing history from free-text notes.