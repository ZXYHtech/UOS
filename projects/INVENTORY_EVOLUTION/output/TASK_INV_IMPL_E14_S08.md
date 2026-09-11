# TASK_INV_IMPL_E14_S08 — Durable AI Jobs, Budgets, Cancellation & Operations

## Status
`DESIGN_READY_BLOCKED_BY_E01_JOBS_E14_S02`

## Objective
Run long extraction/analysis/bulk AI work restart-safely with bounded tools, cost/time and explicit stop/review states.

## Job lifecycle

```text
queued -> running -> succeeded | review_required | failed | cancelled
```

Reuse E01 durable job lease/fencing/attempt infrastructure rather than adding an AI-specific background scheduler.

## Budget contract
Each task execution has limits for:

- maximum tool calls;
- maximum rows/artifacts/context size;
- wall-clock timeout;
- model/token/cost budget;
- allowed tool/domain scope;
- retry count/provider fallback policy;
- stop conditions / approval checkpoints.

## Runtime rules
- worker lease generation/fencing prevents stale worker result publication;
- cancellation is durable and checked between tool/model steps;
- provider rate-limit/network errors use classified bounded retry;
- malformed output/insufficient evidence can terminate as `review_required`, not fake success;
- partial intermediate output is not published as canonical business result;
- high-cost/repeated-error circuit breaker can pause a task/provider class;
- required runtime is server-owned; no GitHub Actions scheduler.

## Operations view
Expose queue age, running tasks, review-required, failures, provider/model latency/cost, retry/dead-letter, cancellation and evaluation health by task type.

## Tests
- worker crash resumes without publishing duplicate result;
- stale lease cannot overwrite new attempt;
- max tool/cost/time budget stops loop;
- cancellation prevents later result publication;
- provider failure routes through declared retry/fallback/review policy;
- succeeded job preserves exact task/schema/model/source provenance.

## Done
Long AI work behaves like an owned production worker subsystem rather than an unconstrained autonomous agent loop.