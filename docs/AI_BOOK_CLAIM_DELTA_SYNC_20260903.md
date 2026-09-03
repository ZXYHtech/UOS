# AI_book → UOS Claim Concurrency Delta Sync Report

Date: 2026-09-03
Status: DECLARED CLAIM / CONCURRENCY DELTA LIST CLOSED THROUGH PHASE 6

## Executive conclusion

The standalone UOS repository remains its own system. AI_book was used only as read-only production evidence for domain-neutral Kernel lessons; AI_book project history, runtime ownership records, task state and domain rules were not copied.

The six Claim/Concurrency mechanisms that this report originally listed as remaining after Phase 1 are now implemented and regression-tested in generic UOS Kernel form:

1. immutable Claim Request + Claim Grant ownership anchors;
2. provider-neutral Claim Broker V2 CREATE / RECLAIM semantics;
3. exact-predecessor reclaim provenance, Claim Integrity and stale-token fencing;
4. Work Session V2 around safe repeated next-task acquisition and ownership recovery;
5. Claim / CAS / Work Session observability;
6. Completion Outbox + mechanical batch Integration for high write contention.

This closes the **declared delta list in this document**. It does **not** mean full AI_book Kernel parity, cross-repository orchestration, or permission to dispatch AI_book work from standalone UOS.

## Synchronization status

| Phase | Generic UOS capability | Status |
|---|---|---|
| Phase 1 | high-contention exact-task ingress and read-only latest-main preflight | PASS |
| Phase 2 | immutable Request → Grant → active Lock, Broker V2 CREATE / RECLAIM | PASS |
| Phase 3 | exact predecessor SHA/provenance, integrity scan, stale writer fencing | PASS |
| Phase 4 | contention/fencing lifecycle acceptance under independent clones | PASS |
| Phase 5 | Work Session V2 + Claim CAS telemetry + provider-neutral observability | PASS |
| Phase 6 | Completion Outbox fallback + latest-main mechanical batch Integration | PASS |
| Phase 6 closeout | `WAITING_INTEGRATION` + Outbox queue/batch/wait observability | PASS |

## What existed before this delta work

Standalone UOS already had important primitives before the incident that triggered this sync:

- latest-canonical detached-worktree Git CAS transactions;
- ref race → discard stale candidate and rerun the command from newer canonical state;
- canonical Claim locks;
- LeaseToken / LeaseGeneration / fencing checks;
- stale lock reclaim primitive;
- deterministic Work Market / Task Status reconcile;
- ExecutionEpoch stale-Agent gate;
- project WorkRoot authority;
- quality visibility / preview gate;
- canonical Complete + durability receipt + `.done`.

Therefore the original problem was never “UOS has no CAS.” The problem was high-contention ingress, stronger ownership anchoring, restart/recovery semantics, observability and write amplification.

## Phase 1 — high-contention ingress

Generic entrypoint:

```text
tools/high_contention_claim.py
```

The project helper under `projects/TRAVEL_GUIDE/tools/claim_depth.py` is only a thin envelope. Generic behavior includes bounded startup jitter, latest-canonical read-only preflight, compatibility filtering, active-owner local `NO_MATCH`, stale-lock pass-through to normal reclaim, and a higher bounded CAS retry budget for bursts.

High-contention acceptance was exercised with independent clones at 5 / 10 / 30 Agents. Later Phase-5 acceptance additionally required Request + Grant + Lock + Claim telemetry for every winning ownership transaction.

## Phase 2–4 — Broker V2 ownership and integrity

Canonical ownership is anchored by:

```text
Claim Request (immutable)
        ↓
Claim Grant (immutable)
        ↓
active Lock
```

The active Lock remains the current ownership pointer; Request/Grant are immutable decision anchors, not a second scheduler.

RECLAIM requires exact predecessor provenance and increments `LeaseGeneration`. A stale Agent, old token or prior-generation candidate is fenced. Claim Integrity checks detect incomplete/mismatched ownership anchors rather than silently guessing ownership.

The ownership authority is:

```text
UOS_CLAIM_BROKER_V2
```

## Phase 5 — Work Session V2 and observability

`tools/work_session.py` is a continuation guard, not a scheduler. It may request the next compatible READY task only after the current task is canonically and durably complete and its quality/review gate is released.

Important recovery semantics:

- stale current Lease → only the exact same current task may be reclaimed;
- successful reclaim returns a new Generation/LeaseToken;
- task reassigned to another Agent → `OWNERSHIP_LOST`;
- ambiguous multiple live Claims → `RECOVERY_REQUIRED`;
- completed current task may close and immediately continue to another compatible task;
- pending/rejected review prevents unrelated next Claims.

Phase-5 Claim telemetry records the winning canonical CAS attempt instead of reconstructing retry counts from Git history. `tools/claim_observability.py` reports Broker authority/mode, throughput, CAS attempts/latency/contention and Work Session metrics.

High-contention acceptance with Phase-5 telemetry passed at 5 / 10 / 30 Agents.

## Phase 6 — Completion Outbox / Integration Lane

The write-contention solution deliberately does **not** put Claim or Renew into an asynchronous queue.

Fast path remains:

```text
legal Complete
→ latest-main canonical CAS
→ canonical Done
```

Only when a fully validated Completion loses its bounded direct-main attempts solely because of unrelated main-ref races may it fall back to:

```text
validated completion candidate
→ non-canonical uos-outbox/* ref
→ mechanical ingest
→ latest-main ownership + fencing + read-set revalidation
→ canonical batch commit
```

Outbox invariants:

- Outbox ref is work-plane persistence only;
- Outbox ref is never ownership;
- staged completion is not canonical Done;
- Claim and Renew never use Outbox;
- ingest rechecks the current Lock/Grant/Generation/LeaseToken/Fencing/Lease expiry/Done state;
- ingest rechecks relevant base objects and refuses conflicting paths;
- prior-generation candidates cannot integrate after RECLAIM;
- accepted batches recompute runtime views from latest main rather than copying stale derived state.

Batch acceptance passed for 2 / 5 / 10 / 30 independent completion candidates. Each accepted batch was integrated with one canonical main commit.

## Phase 6 closeout — no duplicate work while staged

When a Work Session's current task has already persisted a Completion candidate, `next` now checks the **exact current GrantID** and returns:

```text
WAITING_INTEGRATION
```

The Agent must not edit or re-complete that task. It should invoke mechanical Outbox ingest and call Session `next` again only after canonical Done appears.

Using the exact current GrantID prevents a retained older-generation Outbox ref from blocking a Generation+1 owner.

## Current observability

Outbox metrics are part of the same provider-neutral observability snapshot rather than a separate metric authority. Current fields include:

- `remote_refs_total`;
- `valid_queue_depth`;
- `canonical_receipts_total`;
- `retained_ingested_refs`;
- `invalid_or_fenced_uningested_refs`;
- batch count and batch-size p50/p95/max;
- integration-wait p50/p95/max;
- skipped/invalid candidate count.

Canonical receipts, not retained Outbox refs, are the authoritative integrated-completion count.

The closeout production snapshot on 2026-09-03 showed:

```text
ClaimAuthority             UOS_CLAIM_BROKER_V2 for all recorded Grants
Requests / Grants          9 / 9
Reclaims                   1
Max LeaseGeneration        2
Active Locks               0
Valid Outbox queue depth   0
Invalid/fenced outbox refs 0
```

This snapshot is operational evidence, not a permanent performance baseline; future load may produce different latency/contention values.

## What was intentionally NOT copied from AI_book

The following remain outside this synchronization and must not be inferred from the Phase-1–6 closure:

- AI_book task/project history;
- AI_book runtime Claims, Requests, Grants, Locks or `.done` files;
- project-specific AI_book quality rules;
- AI_book path namespaces and domain data;
- fishing/book content or work queues;
- cross-repository task routing;
- AI_book scheduler/dispatch authority.

Standalone UOS remains single-repository unless the operator explicitly approves a later multi-repository phase.

## Remaining need-driven candidates — not declared gaps

These are optional future evolutions only if measurement demonstrates the need:

- adaptive GitHub write-rate / API-budget governor;
- generic scarce-resource admission/backpressure beyond the targeted Completion Outbox lane;
- active-work remote checkpointing beyond completion candidates;
- Outbox audit-ref archival / garbage-collection policy;
- repository sharding or multi-repository routing.

They are not required to declare this report's six-item Claim/Concurrency delta list closed.

## Operational ownership rule

Regardless of helper, session or Outbox state:

```text
ownership = current canonical Grant + matching active Lock + current Lease/Fencing
```

A staged Outbox candidate never changes that rule, and canonical completion exists only after `.done` is present in canonical main.
