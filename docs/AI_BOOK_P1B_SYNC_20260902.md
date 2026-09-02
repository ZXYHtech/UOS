# AI_book → standalone UOS P1B sync — 2026-09-02

## Result

The next useful generic AI_book capability has been rebuilt in standalone UOS:

```text
Partial Handoff ✅ CODE / TEST PRESENT
```

Implementation:

```text
tools/partial_handoff.py
tools/handoff_takeover.py
docs/PARTIAL_HANDOFF.md
```

Regression additions:

```text
tests/test_partial_handoff.py
tests/test_partial_handoff_git_cas.py
```

This remains single-repository only. No AI_book runtime, Claims, Grants, Done
records, project content or cross-repository routing were copied or activated.

## Preserved AI_book invariant

The historical AI_book rule worth keeping is:

```text
Handoff != Done
Handoff != ownership transfer
successor must acquire canonical Claim
successor must revalidate Acceptance
```

Standalone UOS keeps this invariant while using a smaller mechanism.

## Standalone release mechanism

Instead of introducing a new Broker/reclaim ticket protocol, `HANDOFF_READY`
atomically changes only the current owner's state:

```text
handoff record
+ immutable partial checkpoints
+ current Lock LeaseExpiresAt := now
+ HandoffState / HandoffPath
+ current bounded Work Session stop, when present
```

The Lock is not deleted.

The successor then uses the existing stale-reclaim path:

```text
normal uos.py claim
→ LeaseGeneration + 1
→ new LeaseToken
```

Therefore canonical Claim remains the only ownership fact.

## Claim CAS protection for every handoff write

Even a non-releasing `PARTIAL` checkpoint is conditioned on the exact current
canonical Claim blob.

If another Agent has already reclaimed the task, the old Agent cannot publish a
late handoff record merely because its local workspace still contains old state.

## Immutable checkpoint artifacts

A first implementation concern was discovered during design: storing unfinished
artifacts directly at final task output paths could later conflict with UOS
no-clobber completion.

The final design stores partial files under:

```text
coordination/handoff_artifacts/<TASK>/<HANDOFF_ID>/<SOURCE_PATH>
```

The handoff payload records:

```text
source_path
checkpoint_path
```

This preserves recoverable work without occupying or mutating final canonical
output paths.

Source artifact paths are still constrained to the task Project WorkRoot.
Directories must be packaged explicitly before checkpointing.

## Derived-state refresh

After `HANDOFF_READY`, the canonical source-of-truth Lock is already reclaimable.
The tool then requests a normal UOS Reconcile so:

```text
TASK_STATUS / WORK_MARKET
```

reflect the new state for capability-aware discovery.

If Reconcile fails after the handoff transaction succeeds, the handoff remains
valid and the response records `derived_state_refresh=PENDING`; source-of-truth is
not rolled back.

## Work Session integration

If a bounded Work Session owns the current task, `HANDOFF_READY` changes the
session to:

```text
state = STOPPED
stop_reason = HANDOFF_READY
```

This prevents the releasing Agent from continuing to unrelated work through the
old session.

## Successor takeover helper

`tools/handoff_takeover.py` is a convenience adapter:

```text
uos.py claim
→ successful canonical ownership
→ partial_handoff.py read
```

It does not implement Claim itself.

If Claim succeeds but handoff reading fails, it returns:

```text
CLAIM_GRANTED_HANDOFF_READ_PENDING
```

and explicitly instructs the Agent not to Claim again. This avoids duplicate
ownership attempts after a partial transport/read failure.

## Successor trust boundary

`partial_handoff.py read` requires the successor's current AgentID + LeaseToken.
The result reports whether LeaseGeneration advanced beyond the handoff owner's
generation and always carries:

```text
UNVERIFIED_PARTIAL_WORK
```

The successor must restore/inspect checkpoint artifacts and rerun the original
Task Acceptance before final completion.

## Regression intent

The local suite covers:

- PARTIAL does not release ownership;
- HANDOFF_READY expires the Lease but creates no Done;
- wrong owner/token is rejected;
- cross-project artifact paths are rejected;
- non-owner cannot read handoff.

The independent-clone/bare-Git integration suite covers:

```text
owner Work Session
→ normal Claim generation 1
→ partial checkpoint
→ HANDOFF_READY
→ immutable canonical checkpoint
→ old Session STOPPED
→ old owner Renew fenced
→ derived Work Market refreshed
→ successor takeover through normal Claim generation 2
→ verified handoff read
→ old owner Complete fenced
→ successor final completion
→ handoff/checkpoint retained for audit
```

## Remaining generic AI_book candidate

The remaining P1 candidate is:

```text
Resource Admission / Backpressure
```

It is intentionally still **NEED-DRIVEN**, not automatically enabled. The current
single-repository kernel does not yet have a demonstrated scarce shared resource
that justifies adding reservation/admission complexity.

P2 remains deferred:

```text
Role Broker / role leases
OUTBOX_INGEST
complex Kernel self-orchestration
multi-repository adapters/routing
```
