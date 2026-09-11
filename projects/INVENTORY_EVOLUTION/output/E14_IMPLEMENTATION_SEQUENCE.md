# E14 Implementation Sequence — Evidence-bound AI Copilot

## Status
`DESIGN_READY_BLOCKED_BY_GOVERNED_DOMAIN_CONTRACTS`

## Slice A — Authorized context/evidence contract
Implement E14-S01 with read-only facts from one low-risk domain. Prove permission masking/freshness/evidence references before adding broad cross-domain context.

## Slice B — Task/schema registry
Implement E14-S02. Every subsequent AI feature must register purpose, schema, tools, privacy policy and budget.

## Slice C — Constrained read tools / NL lookup
Implement E14-S03 using E12 governed metrics and existing typed entity search. No SQL tool.

## Slice D — Human-reviewed extraction pilot
Implement E14-S04 first for one of the existing OCR-like workflows (supplier quote/inquiry/BOM normalization). Canonical writes remain explicit review actions.

## Slice E — Draft/recommend pilot
Implement C2 tasks such as quote wording, supplier follow-up or MRP explanation. No write authority.

## Slice F — Action Preview bridge
Implement E14-S05 only after E01/E13 Action Policy is proven. Start with low-risk draft/todo actions; explicit approval remains required.

## Slice G — Privacy/prompt-injection hardening
E14-S06 is mandatory before ingesting broad untrusted email/web/customer/supplier content.

## Slice H — Evaluation/provenance gate
Implement E14-S07 before changing production model/provider/prompt widely. Task-specific regression thresholds become part of local release evidence.

## Slice I — Durable long-running AI jobs
Implement E14-S08 through E01 jobs for bulk extraction/analysis after synchronous pilots are stable.

## C4 policy
High-consequence autonomous AI action is explicitly **not** an E14 completion criterion. Stock deduction, quality release, refund approval, BOM release and public-price changes remain deterministic/human-policy controlled.

## Gates
At minimum:

- permission/data-scope tests;
- secret/PII redaction/provider-policy tests;
- prompt-injection fixtures;
- output-schema validation;
- unsupported-claim/evidence-correctness evaluation;
- action-preview/approval/idempotency tests;
- job budget/cancellation/fencing tests;
- E00 Release Gate.

No required AI operation, evaluation or scheduling path depends on GitHub Actions.