# TASK_INV_AUDIT_RELIABILITY_DR_01 — Reliability, Backup, Restore and Business Continuity Audit

## 0. Scope

Pinned source: `ZXYHtech/inventory@78d5cda2527cf24836cd5b82a41f02ca8efdd02c`.

Reviewed BackupService findings, SQLite lifecycle/WAL settings, deployment/systemd scripts, OCR/image durable queues, operation patterns and W2/W3 requirements for idempotent business transitions.

This is an analysis-only report. It does not modify the external inventory repository.

## 1. Executive conclusion

Inventory Lite already contains several sound reliability primitives:

- SQLite WAL mode and busy timeout;
- SQLite online backup API rather than unsafe live file copying;
- explicit restore confirmation;
- durable OCR/image task/job records with retry/error state;
- systemd restart policies and explicit memory ceilings for web/OCR processes;
- inventory and transfer history/reversal patterns that can reconstruct business actions.

The principal gap is that these are **good local mechanisms, not yet a complete continuity contract**. There is no evidence that production RPO/RTO, off-host redundancy, automatic restore drills, broad idempotency, degraded mode, service-health metrics and cross-store recovery are all owned as one operational system.

Preliminary maturity:

- service restart/process containment: 3.5/5
- DB backup implementation: 4/5
- restore guardrails: 3/5
- durable OCR jobs: 3.5/5
- general job replay/idempotency: 2/5
- full-system backup scope: 2/5
- off-host redundancy: unverified
- automated recovery drill: 1/5
- explicit RPO/RTO/continuity runbook: 1/5

## 2. Failure-domain inventory

Reliability planning should explicitly cover:

### Application/process

- web server crash/OOM;
- OCR worker crash/OOM;
- job stuck/hung;
- bad deployment;
- partial config update.

### Database

- process interruption during transaction;
- lock contention;
- disk full;
- SQLite corruption;
- accidental destructive admin action;
- incompatible schema migration.

### File/artifact store

- original image loss;
- controlled document/test artifact loss;
- path/disk corruption;
- DB references file that no longer exists.

### Integration

- Taobao/platform outage;
- timeout after remote commit;
- credentials expire;
- rate limiting;
- duplicate/reordered callbacks/polls.

### Infrastructure

- host failure;
- disk failure;
- network outage;
- certificate expiration;
- power loss;
- DNS/reverse-proxy failure.

### Human/operational

- wrong stock adjustment;
- incorrect restore;
- accidental deletion;
- stale backup assumption;
- lost admin credential;
- silent failed scheduled task.

## 3. RPO and RTO

Define operator-owned targets by data class rather than inventing one number.

Example policy structure:

```text
Data class                 RPO target   RTO target
Orders/stock ledger        configured   configured
Platform sync cursor       configured   configured
Attachments/test records   configured   configured
Reports/cache derivatives  rebuildable  lower priority
```

The system should record measured recovery results against these targets.

RPO/RTO are business decisions; source code should enforce configured policy/monitoring, not silently choose acceptable data loss.

## 4. Backup scope

A DB backup alone is not a full recovery point once the system stores files and secrets.

Define a manifest covering:

- SQLite DB;
- uploaded originals;
- released controlled documents;
- RF test raw artifacts;
- generated artifacts that are not cheaply reproducible;
- application release/schema version;
- server configuration needed for recovery;
- secret metadata while keeping master key separate;
- backup manifest/checksums.

Derivative images/caches can be omitted only if a deterministic rebuild path is proven.

## 5. Backup scheduling

Existing configuration does not itself prove backups execute.

Canonical server-owned design:

```text
inventory-backup.timer
 -> inventory-backup.service
 -> create DB/file recovery point
 -> verify manifest/hash
 -> copy off-host
 -> record result
```

An application worker or cron is also acceptable. GitHub Actions must not own required backup cadence.

The dashboard should display:

- last successful backup;
- last verified backup;
- off-host copy status;
- age vs RPO policy;
- last restore drill.

## 6. Restore verification

Before destructive restore:

1. identify application/schema version;
2. verify backup manifest/checksums;
3. run SQLite `integrity_check`;
4. verify required file artifacts exist;
5. restore into isolated temporary path first;
6. apply compatible migrations if policy permits;
7. run smoke/invariant checks;
8. enter maintenance mode;
9. preserve a pre-restore recovery point;
10. switch restored state atomically/safely;
11. start services and re-run smoke checks;
12. record actor/time/source backup/result.

A `RESTORE` confirmation string is a useful UX guard but is not enough for production recovery safety.

## 7. Recovery drill

Automated or operator-triggered drill should periodically:

```text
latest backup
 -> isolated temporary restore
 -> DB integrity
 -> schema version
 -> row/invariant checks
 -> attachment sample/hash checks
 -> app startup/login/read/write smoke
 -> cleanup
 -> record duration/result
```

Never perform verification by restoring over production.

The important KPI is **last known restorable backup**, not latest file creation time.

## 8. Off-host redundancy

Retention on the same disk does not protect against host/disk loss.

Provide at least one independent failure domain, such as:

- NAS;
- another server via rsync/SFTP;
- encrypted object storage.

Use immutable/versioned storage where practical for critical backups.

Master secret-encryption keys should not live only inside the same backup set as encrypted secrets.

## 9. Database corruption and integrity

Operational checks:

- scheduled/maintenance `PRAGMA quick_check` or `integrity_check` according to acceptable load;
- disk-free-space threshold;
- WAL/checkpoint health;
- backup verification;
- schema migration checksum/version;
- orphan/invariant checks after migrations.

Do not automatically “repair” corrupt operational data without preserving original evidence and explicit operator decision.

## 10. Disk-full handling

Disk exhaustion can break DB writes, image processing, uploads and backups simultaneously.

Monitor separately:

- DB filesystem free bytes/%;
- artifact filesystem;
- backup destination;
- temp/OCR workspace.

Set warning/critical thresholds operationally.

When below critical threshold:

- reject nonessential large uploads/jobs;
- retain core order/stock integrity where possible;
- alert operator;
- never delete authoritative artifacts automatically simply to free space.

## 11. Service process resilience

Current deployment uses systemd restart behavior and explicit memory constraints/OOM policy. Preserve this, but tune through measured workload rather than arbitrary tightening.

Web and OCR should remain independently restartable so an OCR memory spike does not take down order/inventory APIs.

Future worker classes should similarly isolate:

- connector jobs;
- report/analytics jobs;
- AI/OCR;
- backups;
- core web API.

## 12. Durable jobs and leases

Generalize the OCR durable pattern.

A reliable job needs:

```text
queued
claimed/leased
running
succeeded
retry_wait
failed/dead_letter
cancelled
```

Record:

- attempt count;
- lease expiry/worker ID;
- heartbeat for long jobs where needed;
- next retry;
- structured error;
- idempotency key;
- result reference.

After worker crash, expired leases must become safely retryable.

## 13. Timeout-after-commit problem

A central reliability scenario:

```text
client sends shipment completion
server commits stock deduction
network breaks before client sees response
client retries
```

Without business idempotency, retry can double-post.

Required pattern:

- client/business operation key;
- UNIQUE server constraint;
- durable result record;
- retry returns original result.

Apply to every irreversible stock/financial/integration command.

## 14. External integration reliability

Use transactional outbox pattern:

```text
local business transaction
 -> commit local object + outbox event
 -> independent worker calls platform
 -> remote acknowledgement recorded
 -> retry/reconcile
```

Never couple local stock correctness to availability of the remote platform API.

Checkpoint/cursor advances only after durable processing.

## 15. Degraded operation

Define what remains available during partial outages.

Examples:

### Platform API unavailable

- local inventory/order operations continue;
- outbound events queue;
- UI clearly shows sync stale/pending;
- no claim that remote stock/order state is current.

### OCR/AI unavailable

- manual order entry/confirmation remains available;
- recognition jobs queue/retry;
- no core stock path depends on AI.

### Reporting worker unavailable

- core transactions continue;
- reports marked stale.

### Internet unavailable on server

- local LAN inventory workflows may continue if deployment permits;
- cloud/platform operations visibly degraded.

## 16. Offline/mobile continuity

A local mobile offline app must not be mistaken for disaster recovery. Offline writes create their own consistency/conflict problem.

Choose explicitly whether offline mode is:

- read-only/emergency lookup;
- queued operational writes with conflict protocol;
- legacy tool to retire.

W5 mobile/offline audit covers details.

## 17. Deployment rollback

A bad release is a reliability incident.

Recommended deployment contract:

- release version recorded;
- DB migration preflight;
- backup/recovery point before destructive migration;
- local smoke test before traffic;
- one-command/server-local rollback where schema allows;
- migration compatibility documented;
- no dependency on GitHub Actions.

Never deploy an application rollback that cannot read a forward-migrated DB unless that incompatibility is explicitly handled.

## 18. Monitoring and alerting

Minimum platform health signals:

- web health/readiness;
- worker heartbeat/backlog;
- DB writable/latency;
- SQLite lock errors;
- disk space;
- backup age/verification;
- job retry/dead-letter count;
- platform sync lag/error;
- OCR queue age;
- application unhandled error count.

Business health signals belong alongside technical health:

- unprocessed orders;
- stuck shipment tasks;
- unreconciled platform events;
- stale MRP/settlement/report jobs.

## 19. Incident/runbook records

Create concise operational runbooks for:

- web service down;
- DB locked/corrupt;
- disk full;
- restore latest backup;
- platform integration outage;
- OCR worker unhealthy;
- failed migration;
- leaked/expired platform credentials.

Each runbook should state safe diagnostic commands, what not to delete, escalation and recovery verification.

## 20. Priority roadmap

### P0

1. define RPO/RTO by critical data class;
2. server-owned scheduled backup independent of GitHub;
3. full backup manifest including file artifacts;
4. off-host copy;
5. isolated automatic restore verification;
6. business idempotency for irreversible commands;
7. durable worker lease/retry standard;
8. health/disk/backup/job monitoring;
9. deployment/migration rollback runbook.

### P1

1. regular recovery drills with measured duration;
2. degraded-mode UX;
3. platform outbox/reconciliation;
4. artifact-store consistency verifier;
5. incident history/operational SLO reporting;
6. migration fixtures from real prior schema versions.

### P2

1. PostgreSQL PITR only after migration is justified;
2. warm standby/multi-host topology if business RTO requires it;
3. geographically independent backup if risk profile justifies it.

## 21. Acceptance signals

- killing a worker mid-job does not lose or double-apply the job;
- timeout/retry after committed shipment/receipt posts once;
- core local transactions continue while marketplace API is unavailable;
- latest successful backup can be restored in isolation and passes integrity/smoke checks;
- backup status shows both creation and verification age;
- complete restore includes referenced authoritative files, not DB alone;
- host-disk loss has an off-host recovery copy according to configured policy;
- failed migration/deployment has a tested recovery path;
- required recovery/backup/monitoring execution does not rely on GitHub Actions.

## 22. Core recommendation

Treat reliability as **business-event durability + independently verified recovery**, not merely service auto-restart. The current SQLite backup and OCR job patterns are strong seeds; generalize them into idempotent commands, durable workers, off-host verified backups, explicit RPO/RTO and degraded-operation rules.