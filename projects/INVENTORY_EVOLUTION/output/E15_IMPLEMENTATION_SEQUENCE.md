# E15 Implementation Sequence — Conditional Scale / PostgreSQL Evolution

## Status
`DESIGN_READY_CONDITIONAL_NOT_SCHEDULED`

E15 is a readiness/evidence program. It does **not** require moving production off SQLite.

## Slice A — Scale SLOs / trigger evidence
Implement E15-S01 metrics and review thresholds while SQLite remains production backend.

## Slice B — Concurrency/load regression
Implement E15-S02 against SQLite first. Fix business transaction/idempotency/query defects before attributing failures to backend limits.

## Slice C — Query/index/pagination/artifact hygiene
Implement E15-S03 continuously as data grows. Re-measure after each meaningful optimization.

## Decision Gate 1 — Is PostgreSQL work justified?
Only continue toward production migration if sustained measured evidence shows SQLite/backend topology is the limiting factor or required recovery/multi-host capability has material business value.

If not, stop here and keep SQLite.

## Slice D — Backend compatibility inventory/adapter
Implement E15-S04 without production database change.

## Slice E — Dual-backend canonical migrations + domain parity
Implement E15-S05 in development/staging PostgreSQL. PostgreSQL remains unsupported until parity suite is green.

## Slice F — Representative data migration rehearsal
Implement E15-S06 repeatedly from fresh verified SQLite backups until business reconciliation is deterministic.

## Decision Gate 2 — Production migration approval
Require:

```text
measured trigger still valid
+ PostgreSQL parity green
+ migration reconciliation green
+ PostgreSQL backup/restore proof
+ performance/recovery benefit demonstrated
+ operational ownership accepted
```

Otherwise retain SQLite.

## Slice G — Production cutover/rollback drill
Implement/rehearse E15-S07 on staging before any production change. Production run follows the full pre-change backup policy.

## Slice H — Production PostgreSQL cutover (conditional)
Only after explicit go/no-go approval. Preserve final SQLite snapshot and all cutover/reconciliation evidence.

## Slice I — Multi-host/shared storage (separate conditional gate)
E15-S08 is considered only if PostgreSQL is proven and measured availability/concurrency need justifies multiple hosts.

## Continuous invariants
- modular monolith remains default;
- no automatic microservices/Kafka/Redis/Kubernetes migration;
- domain behavior matters more than backend-specific row IDs;
- data migration correctness precedes performance benchmarking;
- rollback may never discard already committed divergent business writes;
- all migration/load/recovery tooling is repository/server local and does not require GitHub Actions.

## Completion interpretation
E15 may legitimately be marked complete with production still on SQLite when:

- operating thresholds are governed;
- load/concurrency suites exist;
- backend portability/parity readiness is proven to the intended level;
- migration/cutover path is documented/rehearsed as required;
- no measured trigger justifies the operational cost of PostgreSQL.

“Did not migrate because evidence did not justify it” is a successful outcome, not an unfinished project.