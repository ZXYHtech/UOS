# TASK_INV_IMPL_E15_S07 — PostgreSQL Production Cutover, Rollback & Recovery Proof

## Status
`DESIGN_READY_CONDITIONAL_BLOCKED_BY_MEASURED_TRIGGER_AND_PARITY`

## Objective
Define a fail-closed production database migration only after E15-S01 triggers justify it and E15-S05/S06 parity/rehearsal are green.

## Preconditions
Production cutover is forbidden unless all are true:

- measured scale/recovery trigger approved;
- E00 pre-change server-code + SQLite backup + isolated restore proof completed immediately before change;
- PostgreSQL canonical migration/domain parity suite passes;
- representative full-data migration reconciles;
- PostgreSQL backup/restore procedure is proven;
- application configuration/secret changes are staged and rollback-ready;
- maintenance window and operator go/no-go checklist approved.

## Cutover concept

```text
quiesce all writers
 -> final consistent SQLite snapshot
 -> migrate final delta/full source according to approved tool
 -> business reconciliation
 -> switch application DB target
 -> migration/integrity/domain smoke
 -> start worker/web
 -> health + critical write/read smoke
 -> enhanced monitoring window
```

Do not run uncontrolled dual-write as a shortcut unless a separately designed/tested replication contract exists.

## Rollback
Rollback decision window and criteria are explicit. If the new backend has correctness/integrity/critical availability issues before irreversible post-cutover business divergence:

```text
stop writers
 -> preserve failed PostgreSQL state/evidence
 -> restore/switch to verified pre-change SQLite snapshot/code/config according to runbook
 -> reconcile any explicitly permitted interim actions
 -> restart/health
```

If production writes have materially diverged on PostgreSQL, rollback is no longer a simple switch; use a separately validated reverse-migration/reconciliation procedure. Do not silently discard committed transactions.

## PostgreSQL recovery
Prove PostgreSQL-native backup/restore (and PITR/replication only if actually adopted) against stated RPO/RTO. Artifact-store consistency remains part of recovery success.

## Tests / Drills
- staging cutover rehearsal from fresh backup;
- injected migration/reconciliation failure stops before switch;
- injected application health failure exercises rollback path;
- post-cutover committed-write scenario proves rollback policy does not discard history;
- PostgreSQL restore drill meets documented integrity checks.

## Done
A production database switch has a rehearsed go/no-go/rollback/recovery procedure at least as strict as the E00 SQLite safety process.