# Inventory Pro repository isolation — operator decision 2026-09-14

ImplementationRepository: https://github.com/ZXYHtech/inventory-Pro
ImplementationBranch: main (integration); codex/* or impl/* (reviewed changes)
LegacyProductionRepository: https://github.com/ZXYHtech/inventory
LegacyRepositoryAccess: READ_ONLY_HISTORICAL_EVIDENCE
UOSPlanningBranch: impl/inventory-evolution-v1
IntentVersion: INVENTORY_PRO_ISOLATED_V2_20260914

The operator explicitly moved new-architecture work to Inventory Pro on 2026-09-14.
This rule supersedes older inventory repository / PR #3 / production preflight instructions
in historical packets. Never merge the old inventory PR #3 or push evolution code to inventory.
Old audit commit IDs remain historical evidence; they are not the current implementation target.

Before every implementation action:
1. Re-read this policy and the current project definition. Work only in a separate inventory-Pro checkout.
2. Verify origin resolves to ZXYHtech/inventory-Pro and record the exact current Pro commit.
3. Use a dedicated Pro branch and local/server-local tests; no required GitHub Actions dependency.
4. Do not reuse the running Inventory Lite directory, database, port, service, deployment host defaults,
   credentials or agent pairing. No production database access/copy is authorized by this migration.
5. E00 is implemented but NOT accepted. Run the real Pro checkout gate; fix reproduced failures first.
6. E01–E15 documents are designs, not runtime completion. Preserve normal UOS claim/lease/quality rules.
7. Existing old-context agents must stop old-repository writes and reload this intent before continuing.
8. Initial deployment is a separately configured isolated test environment only. Production replacement
   requires a new explicit operator decision after test evidence and migration reconciliation.

UOS remains the orchestration/evidence repository. Do not copy UOS locks, grants, .done receipts or
other projects into Inventory Pro. Audit outputs describing the old system remain historical.
No kernel-wide multi-repository scheduler or ownership transfer is introduced.

Migration provenance:
- old inventory E00 source: 0e0870499f7e8b5e68a308231eae954f106bd5aa
- old audited baseline: 78d5cda2527cf24836cd5b82a41f02ca8efdd02c
- UOS design snapshot before redirect: b7557ab
- old inventory PR #3 is superseded as an implementation destination, not a new-repository merge gate.
