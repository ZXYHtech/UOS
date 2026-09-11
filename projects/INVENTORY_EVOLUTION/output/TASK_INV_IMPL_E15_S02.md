# TASK_INV_IMPL_E15_S02 — Concurrency & Production-like Load Regression Suite

## Status
`DESIGN_READY_BLOCKED_BY_CORE_DOMAIN_IMPLEMENTATION`

## Objective
Prove business correctness under contention and establish repeatable scale baselines before changing database technology.

## Scenarios
Use synthetic but realistic fixtures for:

- concurrent shipment/reservation consumption of the same stock;
- shipment vs transfer vs WO issue contention;
- duplicate purchase/transfer receive submission;
- count close vs adjustment;
- platform event replay bursts;
- worker claim/retry/crash/restart;
- high-volume movement/audit/external-object/test metadata histories;
- reporting/search during normal writes;
- large imports/exports as durable jobs.

## Scale bands
Keep parameterized fixture sizes rather than one magical production size, e.g. small/medium/stress row counts appropriate to current hardware.

## Measures
Capture latency distribution, lock waits/timeouts, business invariant violations, duplicate effects, memory/CPU, DB growth and recovery behavior.

## Correctness first
A fast test with oversubscribed stock or duplicate movement is a failure. Business invariants are asserted before performance thresholds.

## Runtime
Load/concurrency suite is repository-local/server-local tooling and may be run on representative staging hardware. GitHub Actions is not required.

## Tests / Acceptance
- concurrent stock-consuming commands cannot oversubscribe;
- duplicate retries produce one effect;
- worker crash cannot double-apply;
- test reports p50/p95/p99 and lock metrics consistently;
- same scenario can be executed later against PostgreSQL for parity/performance comparison.

## Done
There is a repeatable baseline showing whether SQLite is actually the bottleneck and whether a backend change preserves business correctness.