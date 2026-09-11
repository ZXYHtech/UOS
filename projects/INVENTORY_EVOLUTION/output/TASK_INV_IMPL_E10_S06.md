# TASK_INV_IMPL_E10_S06 — RMA Intake, Return Quarantine & Warranty Decision

## Status
`DESIGN_READY_BLOCKED_BY_E07_E09_FOUNDATIONS`

## Objective
Authorize and receive returns without conflating refund, physical receipt, technical diagnosis and warranty responsibility.

## RMA identity
RMA case/lines preserve customer, original order/shipment, platform after-sales identity, expected material/serial/qty, customer reason and case type (`return | repair | exchange | refund_only | warranty`).

## Physical receipt
Returned product moves into controlled return/quarantine state, never directly to normal ATP. Capture parcel/tracking, actual serial/qty, packaging/accessories, visual condition, photos/evidence, receiver/time.

For serialized RF modules, serial resolves original shipment, product revision, WO and E07 test history.

## Warranty decision
Separate decision object records:

```text
covered | not_covered | partial | goodwill
```

with reason/evidence, actor/time and applicable policy/contract context. Customer-reported reason does not predetermine warranty outcome.

## Rules
- refund-only case may exist without physical return;
- physical return does not automatically imply refund approval;
- unknown/unconfirmed serial is held for review, not guessed;
- return cannot enter saleable stock before required inspection/retest;
- warranty policy is configurable and not hard-coded as one global legal rule.

## Tests
- refund-only creates no stock receipt;
- serialized return resolves original history;
- received return is excluded from ATP;
- warranty decision retains actor/reason;
- duplicate platform return event does not create duplicate RMA.

## Done
The company knows exactly what was authorized, what actually came back and whether warranty responsibility was accepted.