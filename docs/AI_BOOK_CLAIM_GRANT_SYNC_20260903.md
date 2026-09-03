# AI Book → standalone UOS Claim/Grant sync status — 2026-09-03

## Scope

This document records the generic orchestration capabilities backported from the mature AI_book multi-Agent control plane into standalone `ZXYHtech/UOS`. It does **not** copy AI_BOOK project tasks, runtime locks, grants, done receipts, book-specific prompts, or project-private state.

## Phase 1 — high-contention exact-task ingress — SYNCED

Standalone UOS now provides a generic high-contention exact-task entry path in `tools/high_contention_claim.py`:

- bounded randomized launch jitter;
- read-only latest-canonical preflight before creating a Claim transaction;
- zero-write `NO_MATCH` when an exact task is already actively owned;
- latest-canonical Git CAS still remains the ownership authority;
- transient ref races are retried without rebasing stale ownership decisions;
- project wrappers such as `projects/TRAVEL_GUIDE/tools/claim_depth.py` are thin parameter wrappers, not alternate ownership systems.

Validation: real Git tests with 5 / 10 / 30 independent clones claiming distinct exact tasks all succeeded.

## Phase 2 — immutable Grant dual-anchor + integrity — SYNCED

New Claims created by standalone UOS now publish two ownership anchors in the **same canonical Claim transaction**:

1. active `coordination/claims/<TASK>.lock`;
2. immutable `coordination/claim_grants/<AGENT>/<REQUEST>.grant`.

The Lock records `GrantID`, `GrantPath`, ClaimAuthority and fencing metadata. The Grant records CanonicalID, AgentID, LeaseGeneration, LeaseToken, expiry, fencing token, project/output context and an ownership checkpoint.

For new Grant-backed ownership, renew/complete fails closed when Lock, Grant, AgentID, generation or LeaseToken disagree. A Grant remains after successful completion as immutable ownership history while the active Lock is removed.

### Migration compatibility

Claims created before Phase 2 do not have `GrantPath`. They are intentionally treated as `LEGACY_LOCK_ONLY` / `LEGACY_ACTIVE` until they naturally complete or are reclaimed. The Phase 2 deployment does not invalidate or rewrite their current LeaseToken.

This compatibility rule is required so a kernel upgrade does not fence Agents already doing legitimate work.

## Claim Integrity Scan

`tools/claim_integrity_scan.py` derives `coordination/runtime/CLAIM_INTEGRITY.csv` and classifies ownership as:

- `PASS` — Grant-backed active ownership matches;
- `RECLAIMABLE` — Grant-backed lease is stale and may be fenced by an explicit higher generation;
- `LEGACY_ACTIVE` / `LEGACY_STALE` — pre-Phase-2 ownership accepted during migration;
- `DONE` — completion exists and immutable Grant remains as history;
- `SUPERSEDED` — older Grant has a newer generation successor;
- `VIOLATION` — orphan/mismatched ownership state;
- `REPAIRED` — only when an explicitly requested bounded safe repair was applied.

`.github/workflows/uos-claim-integrity.yml` continuously audits Claim/Grant/Done changes. Normal CI is read-only: it does not auto-repair ownership.

## Validation evidence

Phase 2 regression coverage verifies:

- Lock and immutable Grant are committed together;
- Grant remains after Complete while active Lock is removed;
- tampering with immutable Grant blocks Complete;
- legacy pre-Phase-2 Lock remains usable;
- existing Git-CAS lifecycle and project warmup tests still pass;
- 5 / 10 / 30 concurrent independent clones all obtain distinct Claims with exactly one matching Grant per Lock;
- every concurrent Lock/Grant pair has the same CanonicalID, AgentID, LeaseGeneration, LeaseToken and GrantID.

## Not yet declared fully synced

Phase 2 does **not** claim full AI_book Broker V2 parity. Remaining generic kernel work includes:

1. persistent Claim Request as a first-class ingress object;
2. formal Broker V2 CREATE and exact-SHA STALE/COOPERATIVE RECLAIM transaction path;
3. explicit reclaim provenance and successor Grant semantics across higher LeaseGeneration;
4. integration of the integrity scan into canonical reconcile/status rather than CI-only auditing;
5. Work Session / bounded automatic continuation;
6. Claim latency, contention and broker-throughput observability;
7. higher-volume publish/integration queue design where Git branch write serialization becomes the bottleneck.

These capabilities should be backported only as generic KERNEL_SYNC logic. AI_BOOK runtime state and project-specific policies remain isolated.
