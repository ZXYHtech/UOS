# INVENTORY_DEEP_AUDIT — No GitHub Actions Dependency Policy

## Status

This is a hard project constraint requested by the operator.

## Normative rule

No audit conclusion, validation path, implementation recommendation, release gate, backup/recovery mechanism, scheduled job, alerting path, data synchronization path, task execution path, or production correctness property may depend on GitHub Actions.

GitHub Actions may be mentioned only as an optional convenience layer. Removing or disabling Actions must not break the required operating model.

## Required alternatives

Recommendations must prefer mechanisms that can run independently of GitHub Actions, such as:

- local CLI scripts;
- repository-contained test runners;
- server-side systemd services/timers or cron;
- independent worker/queue processes;
- application-internal schedulers where justified;
- external monitoring/alerting that is not tied to GitHub;
- explicit release/deploy scripts runnable from a developer or deployment host;
- database-backed durable job/outbox patterns when business correctness requires them.

## Audit implications

Every task in `INVENTORY_DEEP_AUDIT` must treat the following as separate questions:

1. Does a test/check exist?
2. Can it run from a fresh checkout without GitHub Actions?
3. Is the command documented and reproducible?
4. Does production correctness remain intact if GitHub is unavailable?
5. Are scheduled/background responsibilities owned by the application/server rather than CI?

A proposal fails this project's architecture requirements if its only implementation path is a GitHub Actions workflow.

## Verification principle

Evidence should be based on source inspection, deterministic scripts, executable local/server commands, database/state inspection and reproducible tests. Action run status is not accepted as the sole evidence of correctness.
