# TASK_INV_IMPL_E15_S03 — Query / Index / Pagination & Artifact-storage Scale Hygiene

## Status
`DESIGN_READY`

## Objective
Remove avoidable query/file bottlenecks before blaming the relational backend.

## Query conventions
For large/event tables require:

- bounded/cursor pagination with stable indexed ordering;
- no unbounded list endpoints;
- query-plan review (`EXPLAIN QUERY PLAN` / backend equivalent) for important slow paths;
- indexes derived from real filters/joins/orderings;
- totals only when affordable/explicit;
- large export/report generation through durable jobs;
- reporting snapshots/read models before external cache infrastructure.

Likely high-growth data includes movements, operation logs, external objects, economic events, test measurements/artifacts metadata, genealogy, case events, rule/job attempts.

## Cache policy
Use progression:

```text
correct query/index
 -> read model/snapshot
 -> bounded process cache for stable reference data
 -> external cache only after measured need
```

Cache never becomes stock/reservation/finance truth.

## Artifact storage
Keep large S2P/spectrum/images/controlled documents outside ordinary relational BLOB rows:

```text
DB metadata + immutable object/file key + size/hash/MIME/retention/reference
```

Start local filesystem if adequate, but business identity must survive future NAS/object-storage migration.

Backup/recovery includes DB + required artifact store with checksum/reference verification.

## Tests
- large lists remain bounded and stable across pagination;
- key query fixtures use intended indexes/query shape;
- read model rebuild parity is proven;
- moving an artifact storage backend does not change domain artifact identity/hash/reference;
- DB-only restore with missing required controlled/test artifacts is considered incomplete.

## Done
Known query/file growth paths have explicit scaling contracts before new database/cache infrastructure is introduced.