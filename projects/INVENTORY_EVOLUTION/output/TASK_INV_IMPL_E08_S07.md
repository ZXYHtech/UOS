# TASK_INV_IMPL_E08_S07 — Subcontract Return, Reconciliation, Quality & Cost Evidence

## Status
`DESIGN_READY_BLOCKED_BY_E07_GATE`

## Objective
Close outside-processing material and output honestly: partial returns, accepted output, scrap/process loss, unresolved variance and linked processing cost must remain separately visible.

## Return/output lifecycle

```text
sent
 -> partially_returned
 -> returned
 -> quality_closed
 -> operationally_closed
```

Financial settlement remains a separate procurement/E11 concern.

## Reconciliation invariant
For each company-owned input line:

```text
sent
= consumed
+ returned_unused
+ approved_process_loss
+ scrap
+ approved_variance
+ unresolved_variance
```

Normal operational close requires `unresolved_variance = 0`.

## Output receipt
Returned processed output may be same material, subassembly or finished product. Receipt must:

- reference subcontract order and released package;
- preserve actual captured lot/serial genealogy;
- enter E07 quality state according to policy, normally `PENDING_INSPECTION` before acceptance;
- support partial output return and rejected/rework quantity.

## Cost evidence
Record operational cost evidence separately:

- processing/unit fee;
- setup/NRE/tooling;
- supplier-provided materials;
- test service;
- freight/expedite;
- approved scrap/rework charge.

Do not double-count company-owned material already issued to external WIP. E11 later calculates realized economics.

## Tests
- partial return keeps order open;
- close fails with unexplained company-owned quantity;
- approved variance requires authority/reason;
- returned output enters correct quality state;
- rejected output is not ATP;
- processing fee remains distinct from company material cost;
- genealogy reflects only actually captured lot/serial granularity.

## Done
Every unit of company-supplied material sent outside is reconciled or explicitly dispositioned, and every returned output follows the normal quality/traceability path.