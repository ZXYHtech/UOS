# TASK_INV_IMPL_E15_S06 — Representative Data Migration Rehearsal & Reconciliation

## Status
`DESIGN_READY_BLOCKED_BY_E15_S05`

## Objective
Prove that a representative SQLite database can be copied into PostgreSQL without losing business identity, quantity, history, artifact linkage or integrity.

## Rehearsal scope
Use sanitized/authorized representative data or a production-derived staging copy under the same backup/privacy controls.

Migration process records:

- source DB version/hash/backup evidence;
- target migration/schema version;
- table/entity row counts;
- key business aggregates;
- identity mapping if sequence/ID handling changes;
- file/artifact references and hashes;
- start/end/errors/retries;
- reconciliation report.

## Reconciliation
Verify more than row counts. Include business invariants such as:

- stock/balance/reservation totals by material/site/state;
- movement/reversal/reference chains;
- order/shipment/PO/transfer identities;
- serial/lot genealogy where present;
- released BOM/document references;
- job/outbox/idempotency uniqueness;
- economic-event/settlement totals;
- required artifact existence/hash.

## Rules
- source remains untouched/read-only during rehearsal;
- migration never fabricates missing historical semantics;
- unresolved mismatch blocks cutover readiness;
- target performance benchmark occurs only after correctness reconciliation passes;
- every rehearsal is repeatable from a fresh source backup.

## Tests
- intentionally omitted/changed row is detected by reconciliation;
- duplicate uniqueness conflict is surfaced explicitly;
- artifact reference/hash mismatch blocks success;
- rerun from same source produces equivalent reconciled business state.

## Done
A representative full-data migration can be repeated and proves business-level parity, not just successful SQL import.