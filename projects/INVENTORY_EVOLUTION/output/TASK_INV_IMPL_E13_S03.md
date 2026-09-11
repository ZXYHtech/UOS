# TASK_INV_IMPL_E13_S03 — Action Registry, Risk Class & Approval Policy

## Status
`DESIGN_READY_BLOCKED_BY_E01_ACTION_POLICY`

## Objective
Register exactly which domain commands automation may request and which approval policy applies.

## Action registry
Each action definition declares:

- domain command;
- allowed input schema;
- risk class A0–A3;
- required permission/scope;
- approval policy;
- idempotency strategy;
- reversal/compensation capability;
- maximum quantity/value/scope where applicable.

## Approval policies
Support bounded policies such as:

```text
NONE
ROLE_APPROVAL
THRESHOLD_APPROVAL
TWO_PERSON
DOMAIN_POLICY
```

Examples:
- create reminder/draft PO: A1, automatic;
- reservation: A2, allowed only under explicit policy and reversible;
- ship/release quality/refund/publish price/release BOM: A3, human approval by default.

## Rules
- rule author cannot grant itself permissions;
- action executes through the same domain service used manually;
- approval captures approver, time, object/current state and rule-version evidence;
- stale approval is revalidated if target state materially changed.

## Tests
- A3 cannot execute without required approval;
- ordinary rule editor cannot escalate authority;
- approved action still fails if domain state became invalid;
- reversal capability is declared before rule can be enabled.

## Done
Automation can only ask for a known safe command under an explicit risk/approval contract.