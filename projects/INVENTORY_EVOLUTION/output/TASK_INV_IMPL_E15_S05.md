# TASK_INV_IMPL_E15_S05 — Dual-backend Schema Migration & Domain Contract Parity Suite

## Status
`DESIGN_READY_BLOCKED_BY_E15_S04`

## Objective
Prove PostgreSQL support by running the same logical schema history and domain behavior suite on both backends before it can be called supported.

## Schema parity
Each logical numbered migration must have tested SQLite/PostgreSQL application where backend-specific DDL differs. Fresh DB and representative historical upgrade paths both matter.

The stale standalone `deploy/postgres/schema.sql` is not a production authority and should ultimately be generated/deprecated/replaced by the canonical migration path.

## Domain contract suite
Run the same high-value tests against both backends, including:

- auth/permissions/scope;
- E01 idempotency/jobs/outbox;
- E02 reservation/stock movements/reversals;
- procurement/transfer/shipment;
- released revision/WO/quality flows as implemented;
- connector replay/economic import uniqueness;
- reporting metric/read-model correctness.

## Parity
Compare business results, not raw internal row IDs where backend allocation differs.

Explicitly test concurrency/isolation-sensitive invariants on each backend.

## Rules
- a test skipped on PostgreSQL is not parity evidence unless feature is explicitly unsupported;
- backend conditional code must have focused tests;
- schema versions/checksums/logical migration identity remain traceable;
- PostgreSQL cannot be advertised as supported while core domain suite differs materially.

## Tests / Done
A clean local/staging PostgreSQL instance can be created through canonical migrations and passes the same defined domain-contract suite as SQLite with documented intentional differences only.