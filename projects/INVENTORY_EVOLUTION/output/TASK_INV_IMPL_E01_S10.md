# TASK_INV_IMPL_E01_S10 — Domain Module Extraction

## Status

`DESIGN_READY_BLOCKED_BY_E00_GATE`

## Objective

Begin reducing `server.py` / `services.py` concentration without introducing microservices or a framework rewrite.

## Target structure

```text
inventory_app/domains/
  backup/
  pricing/
  procurement/
  integrations/
```

Each domain should own, as applicable:

```text
service/domain commands
queries
API adapter/route handlers
action-policy declarations
job/outbox handlers
tests
migration registration hooks
```

## Extraction order

1. backup/recovery — E00 already created clean seams;
2. pricing — relatively bounded and needed before later margin-safety work;
3. procurement — real workflows but separable from future manufacturing;
4. integrations — provider adapters + jobs/outbox.

Do **not** start with Inventory/Stock; E02 will define its new semantic kernel and should not be frozen into a premature module boundary.

## Rules

- move behavior with tests, not copy/paste and leave two implementations;
- HTTP layer parses/serializes, domain layer owns business decisions;
- DB access may remain SQLite/shared connection; modular monolith does not require service APIs between domains;
- action policy and job handlers reference domain services, not raw route functions;
- preserve external API behavior while extracting.

## Data migration

None required by module movement itself.

## Tests

For each extracted domain:

- existing regression suite passes unchanged;
- direct domain tests cover representative command/query;
- no duplicate business implementation remains in old giant file;
- import graph has no circular dependency back through `server.py`;
- startup/import smoke test remains clean.

## Acceptance

At least three bounded areas are moved behind domain modules and the central server/service files measurably shrink without behavioral regression.

## Non-goals

- no microservices;
- no network RPC between domains;
- no repository-per-domain split;
- no abstract plugin architecture.

## Dependencies

E01-S01/S02 for common execution contracts; integration extraction benefits from S05–S09.
