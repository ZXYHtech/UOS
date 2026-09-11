# Inventory Evolution — No GitHub Actions Runtime Dependency

## Rule

`GitHubActionsDependency: FORBIDDEN` remains a hard implementation constraint inherited from the audit.

GitHub may host source, branches, reviews and optional convenience CI. However, no required correctness property or production operation may depend on GitHub Actions being available.

## Required local/server-owned paths

The following must have direct repository/server execution paths:

- schema migration and migration verification;
- release verification and regression tests;
- permission/state/idempotency checks;
- background workers and durable job execution;
- marketplace synchronization and reconciliation;
- MRP and scheduled planning;
- backup, off-host copy and restore verification;
- monitoring/health checks;
- report generation;
- production/quality/test processing.

Preferred mechanisms:

- Python/Node CLI commands in the repository;
- systemd services and timers;
- cron where appropriate;
- durable database-backed jobs/outbox;
- independent worker processes.

## Release principle

A developer on a fresh checkout, or an operator on the deployment server, must be able to execute the authoritative validation path without access to GitHub Actions.

If CI is added later, it should call the same repository-local verification command rather than owning unique hidden validation logic.
