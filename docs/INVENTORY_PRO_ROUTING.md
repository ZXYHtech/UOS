# Inventory project routing — 2026-09-14

Operator decision: new inventory architecture is isolated in `ZXYHtech/inventory-Pro`.
Implementation planning/tasks remain in UOS branch `impl/inventory-evolution-v1`:
- `orchestration/projects/INVENTORY_EVOLUTION/PROJECT.yaml`
- `orchestration/projects/INVENTORY_EVOLUTION/TASK_CATALOG.csv`
- `projects/INVENTORY_EVOLUTION/REPOSITORY_ISOLATION.md`
- `projects/INVENTORY_EVOLUTION/output/PRO_IMPROVEMENT_TEST_RELEASE_PLAN.md`

That project uses IntentVersion `INVENTORY_PRO_ISOLATED_V2_20260914`.
New agents must reload the target and verify the Pro origin before code changes.
Old `inventory` branches/PR #3 remain historical; no new architecture writes or deployment there.
The historical INVENTORY_DEEP_AUDIT can still read pinned old inventory evidence, but does not
have write authority. Other UOS projects and the kernel execution epoch are unchanged.
Task/lock/done ownership stays in UOS; no automatic cross-repository ownership is introduced.
No production deployment or production-data access is authorized by this migration.
