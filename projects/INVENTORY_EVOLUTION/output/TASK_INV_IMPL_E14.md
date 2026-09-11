# TASK_INV_IMPL_E14 — Evidence-bound AI Copilot

## Status
`DESIGN_READY_BLOCKED_BY_GOVERNED_DOMAIN_CONTRACTS`

## Objective
Add an assistive AI layer only after deterministic business contracts exist, using the existing OCR human-in-loop pattern as the precedent.

Core principle:

```text
AI interprets / extracts / ranks / summarizes / drafts
Deterministic services validate identity / permission / state / quantity / money
Human or explicit safe rule policy authorizes consequential action
```

AI is never a second source of truth for stock, price, BOM, quality, settlement, product revision or released test result.

## Capability classes

```text
C0 explain / summarize
C1 extract / classify / rank
C2 draft / recommend
C3 bounded action assistant after explicit approval or narrowly scoped E13 policy
C4 high-consequence autonomous action: not a default supported mode
```

Examples of C4 include stock deduction, quality release, refund approval, BOM release and public-price change. AI may prepare evidence but is not sole authority.

## Architecture

```text
user / business event
 -> authorized context builder
 -> declared AI task + schema
 -> structured candidate + evidence refs + uncertainty
 -> deterministic validators
 -> human / E13 approval when needed
 -> normal domain command
 -> durable receipt + AI provenance
```

## Hard boundaries
- no direct SQL tool;
- no direct database credentials/secrets in model context;
- AI inherits the user's effective permissions/scope and never broadens them;
- read mode is default;
- writes require explicit structured action preview and deterministic revalidation;
- untrusted supplier/customer/web documents are data, never trusted instructions;
- confidence is never authority;
- pass/fail remains deterministic from released limit sets;
- natural-language analytics maps to E12 governed metrics/query functions, not unrestricted NL-to-SQL;
- long AI work uses E01 durable jobs with budgets/stop conditions;
- provider/model/prompt/source/version/correction provenance is retained;
- no required AI runtime/evaluation/scheduling path depends on GitHub Actions.

## Definition of done
A factual AI answer identifies its supporting records, freshness and limitations; any proposed action is visibly separate from execution; and every accepted AI-assisted write is performed through the same deterministic domain command and approval path as normal UI.