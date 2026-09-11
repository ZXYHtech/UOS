# TASK_INV_IMPL_E14_S07 — AI Provenance, Evaluation Dataset & Regression Gate

## Status
`DESIGN_READY_BLOCKED_BY_E14_S02`

## Objective
Make AI behavior measurable and historically explainable so model/provider/prompt changes cannot silently degrade operational quality.

## Provenance
Each consequential AI execution records:

- task/schema version;
- provider/model identifier/version when available;
- prompt/template version;
- source object IDs/hashes and freshness;
- user/task purpose;
- structured candidate/output;
- deterministic validation result;
- human accept/correct/reject result;
- correction diff/reason where useful;
- latency/cost/token/tool-call metadata as policy permits.

## Evaluation datasets
Maintain task-specific regression fixtures derived from approved synthetic/historical examples with privacy controls.

Metrics by task may include:

- exact-field extraction accuracy;
- material-match top-1/top-k and dangerous false-match rate;
- classification precision/recall;
- unsupported factual claim rate;
- evidence/citation correctness;
- human correction frequency;
- recommendation acceptance rate;
- latency/cost;
- privacy-policy violation count (zero tolerance).

Compare to deterministic/no-AI baseline where meaningful.

## Release gate
Provider/model/prompt/schema changes run the relevant local/server evaluation suite before production enablement. Define minimum task-specific thresholds, especially false auto-match / unsupported-claim safety metrics.

No GitHub Actions dependency is required; evaluation runs via repository-local CLI and/or server-owned durable jobs.

## Rules
- a newer/larger model is not automatically better;
- evaluation failures block rollout or force observe-only/review-required mode;
- human correction history is evidence, not automatic external training authorization;
- historical AI outputs preserve the provenance needed to reproduce/explain them as far as provider metadata permits.

## Tests
- prompt/model version change creates distinct provenance;
- evaluation threshold failure blocks production activation;
- source/evidence mismatch is detected;
- privacy violation fixture is a hard fail;
- human correction is retained without overwriting original candidate.

## Done
AI features have regression gates and measurable quality rather than relying on anecdotal “looks good” testing.