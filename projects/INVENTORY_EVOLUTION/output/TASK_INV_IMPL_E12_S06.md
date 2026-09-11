# TASK_INV_IMPL_E12_S06 — Scheduled Reports, Role Scope & Reporting Operations

## Status
`DESIGN_READY_BLOCKED_BY_E12_S01_S02`

## Objective
Deliver governed daily/weekly/monthly reporting through production-owned scheduling while preserving server-side data scope and freshness evidence.

## Scheduled outputs
Examples:

- daily exception digest;
- weekly operating review;
- monthly management pack;
- product/supplier risk review.

Use E01 durable jobs plus systemd timer/cron as appropriate. No required report generation/delivery depends on GitHub Actions.

## Role views
Examples:

- owner: cross-domain exceptions/cash/profit/product actions;
- warehouse: fulfilment/inventory/transfer;
- procurement: shortage/PO/supplier;
- production/quality: WO/yield/NCR/test;
- sales/support: opportunity/quote/case/RMA;
- finance/admin: settlements/cost/reconciliation.

Scope is enforced in reporting API/query layer, not frontend hiding.

## Operational controls
- report run has durable identity/status/version/freshness;
- delivery retries are idempotent;
- failed snapshot/report does not publish partial misleading output;
- generated report references metric definition versions and data-as-of time;
- sensitive financial/customer data obeys least-privilege export policy.

## Tests
- unauthorized role cannot retrieve hidden metric drill-down through API;
- duplicate scheduled run does not duplicate delivery;
- stale/failed source snapshot is labeled or blocks report per policy;
- generated historical report remains tied to the metrics/data-as-of used.

## Done
Management reporting is repeatable, role-safe and production-owned instead of depending on manual screenshots or hosted CI schedules.