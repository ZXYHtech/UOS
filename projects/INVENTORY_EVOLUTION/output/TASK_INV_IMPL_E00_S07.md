# TASK_INV_IMPL_E00_S07 — Off-host Backup Copy + Health + Scheduler Path

## Status

`IMPLEMENTED_AWAITING_LOCAL_VERIFICATION`

External implementation: `ZXYHtech/inventory#3`, branch `impl/e00-release-safety`, reviewed head `7a8e0adcc0bf4f8fddba4688802ef2486f18f56c`.

## Operational flow

```text
consistent DB snapshot
 -> isolated recovery verification
 -> manifest DB/artifacts/config + release provenance
 -> verify off-host target exists + mount sentinel
 -> copy + destination hash verification
 -> atomic bundle publish
 -> health JSON
 -> prune old local verified snapshots only after success
```

Runtime ownership is local/server-side:

- direct CLI;
- cron if chosen by operator;
- installed systemd oneshot + timer;
- no GitHub Actions scheduler dependency.

## Fail-closed off-host target

Production/scheduled copy requires `.inventory-backup-target` on the verified mounted NAS/NFS/SMB/sshfs/off-disk filesystem.

Rules:

- destination root is never auto-created;
- missing destination fails;
- existing-but-unmarked destination fails;
- copy verifies source checksums before transfer;
- destination files and Manifest are re-hashed before atomic publish;
- backup health records failure/success;
- existing published bundle is never overwritten.

This prevents a disappeared mount from turning into a same-named local directory that falsely appears to be an off-host backup.

## Scheduler hardening

`setup_server.sh` installs but does not automatically enable the timer unless explicitly requested.

When enablement is requested:

```text
Web/OCR health PASS
 -> release identity published
 -> run one verified backup iteration
 -> only then enable timer
```

Invalid off-host target/config therefore blocks timer enablement.

The installed backup service declares the baseline recovery config set; missing declared config fails the job rather than silently publishing an incomplete bundle.

## Deployment/upgrade hardening relevant to S07

- setup/repair excludes the entire runtime `data/` tree from `rsync --delete`;
- update remembers whether the backup timer was active;
- timer/service are stopped before code/schema cutover;
- previously-active timer is restarted only after application health succeeds;
- failed cutover after writer quiescence leaves services stopped for explicit recovery;
- pre-upgrade off-host bundle is completed before production writers are stopped/code is replaced.

## Tests

Repository-local tests cover:

- missing target rejection;
- unmarked target rejection;
- marked target success;
- same-second snapshot naming safety;
- declared config missing → failed backup health;
- successful Manifest + off-host bundle contains declared config;
- source/destination checksum verification;
- deployment ordering and runtime-data preservation through `test_deployment_safety.py`.

## Acceptance mapping

- direct operator/systemd/cron execution: implemented;
- off-host copy hook: implemented;
- destination pre-existence/sentinel: implemented;
- destination checksum verification: implemented;
- health success/failure record: implemented;
- retention only after successful pipeline: implemented;
- first-run verification before timer enablement: implemented;
- recovery config capture: implemented;
- no hosted scheduler dependency: implemented.

## Operator decisions still required

Before production enablement define:

- RPO/RTO;
- retention;
- actual second failure domain;
- mount mechanism/permissions;
- monitoring/alert owner for failed backup-health state.

After verifying the mounted target, create the sentinel on that filesystem, e.g.:

```bash
sudo -u inventory touch /mnt/inventory-backup/.inventory-backup-target
```

Then execute the authoritative release gate and a controlled backup smoke.

E00-S07 remains open until `python3 tools/verify_release.py` passes from a real checkout.
