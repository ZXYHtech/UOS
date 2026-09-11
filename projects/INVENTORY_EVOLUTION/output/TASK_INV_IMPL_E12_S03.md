# TASK_INV_IMPL_E12_S03 — Exception-first Management Cockpit & Action Loop

## Status
`DESIGN_READY_BLOCKED_BY_E12_S01_S02`

## Objective
Keep the existing operator home screen action-focused while adding a separate owner/management cockpit that turns cross-domain evidence into owned decisions.

## Cockpit sections

```text
ATTENTION NOW
FLOW HEALTH
ECONOMICS / CAPITAL
PRODUCT / STRATEGY
```

Examples: critical shortages, overdue PO/WO, quarantine/NCR/RMA aging, sync/settlement failures, negative contribution, inventory cash concentration, product risk.

## Management action log
A review can create an action with source metric/report, target object/domain, action text, owner, due date, status, expected outcome and completion evidence.

Next review shows outstanding prior actions and the relevant metric trend.

## Rules
- KPI movement alone is not automatically an alert;
- action-required exceptions are deduplicated/owned/resolvable;
- average metrics should expose tail risk (e.g. P90/overdue list) where useful;
- low-volume RF data shows counts/context to avoid misleading percentages.

## Tests
- cockpit item drills to evidence;
- management action retains source metric snapshot;
- closed action history is immutable/auditable;
- operator dashboard remains independent and unaffected by management query load/permissions.

## Done
Management review becomes a closed operating loop rather than a passive chart page.