# TASK_INV_IMPL_E15_S04 — SQLite-specific Assumption Inventory & Database Adapter Boundary

## Status
`DESIGN_READY_BLOCKED_BY_MODULAR_DOMAIN_IMPLEMENTATION`

## Objective
Identify and contain backend-specific SQL/transaction behavior so domain services can be tested against SQLite and PostgreSQL without a big-bang rewrite.

## Compatibility inventory
Audit and classify usages of:

- `INSERT OR IGNORE` / SQLite upsert syntax;
- `lastrowid` / rowid assumptions;
- `PRAGMA` behavior;
- text/date/time coercion;
- booleans/numeric affinity;
- NULL uniqueness semantics;
- partial/functional indexes where used;
- DDL/autoincrement differences;
- schema introspection;
- transaction begin/isolation/locking semantics;
- JSON/string operators where introduced.

## Adapter boundary
Prefer narrow database primitives/helpers where backend syntax materially differs, while keeping domain transaction ownership explicit.

Do **not** create a generic ORM rewrite merely for portability if it obscures business SQL/invariants.

## Rules
- SQLite remains first-class, not a throwaway dev backend;
- backend-specific behavior must be explicit/tested;
- migration DDL can have backend-specific implementation behind one logical migration version where required;
- domain service semantics/results stay backend-neutral.

## Tests
- compatibility inventory has an owner/disposition for every known SQLite-specific construct;
- adapter helper emits equivalent semantics on both backends for supported primitives;
- NULL/unique/idempotency behavior is tested explicitly rather than assumed;
- transaction contract documents differences that require guarded implementation.

## Done
PostgreSQL support work has a bounded compatibility surface instead of discovering SQLite assumptions during production cutover.