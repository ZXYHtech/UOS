# E10 Implementation Sequence — Technical CRM + After-sales

## Status
`DESIGN_READY_BLOCKED_BY_E04_E07_E09_FOUNDATIONS`

## Slice A — Customer/contact identity + opportunities
Implement E10-S01 additively. Do not auto-merge marketplace receiver text into CRM master.

## Slice B — Technical requirements/candidates
Implement E10-S02 using E04 parametric identity and E05 product revisions. Recommendation only; no engineering promise inferred from similarity.

## Slice C — Revisioned quotation
Implement E10-S03 with immutable sent revisions and E11 pricing/floor controls. Start quote-to-order conversion behind E01 idempotency.

## Slice D — Sample/evaluation lifecycle
Implement E10-S04 with E02 reservation/movement and E07 return-quality rules.

## Slice E — Customer service case/timeline
Implement E10-S05 while preserving `ExceptionService` as separate internal exception domain. Add links, not replacement semantics.

## Slice F — RMA intake/warranty
Implement E10-S06. Returned goods enter quarantine; platform observations reuse E09 external identity.

## Slice G — Repair/retest/exchange/refund
Implement E10-S07 using E07 serial/test history and E09 remote refund sync where relevant.

## Slice H — Reminders/templates/feedback
Implement E10-S08 through E01 durable jobs. Keep automation advisory/notification-only unless a later explicit policy grants a reversible action.

## Gates
Every slice requires relevant deterministic tests plus E00 Release Gate. Critical fixtures must prove:

- quote revision immutability;
- duplicate quote-to-order conversion safety;
- loan/sample ATP exclusion;
- internal note visibility boundary;
- refund does not restock;
- RMA return goes to quarantine;
- failed test persists after retest;
- exchange preserves both serials.

## Authority rule

```text
E10 owns customer workflow/context
E02 owns stock
E07 owns technical/quality evidence
E09 owns remote platform observation/sync
E11 owns pricing/economics
```

Do not duplicate these truths inside CRM/RMA tables.