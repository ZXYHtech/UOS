# Partial Handoff — recoverable unfinished work

Protocol: `UOS_PARTIAL_HANDOFF_V1`

Tool:

```text
tools/partial_handoff.py
```

Canonical record:

```text
coordination/handoffs/<TASK_ID>.handoff
```

Checkpoint artifacts:

```text
coordination/handoff_artifacts/<TASK_ID>/<HANDOFF_ID>/<SOURCE_PATH>
```

## Core invariant

```text
Handoff != Done
Handoff != Durability Receipt
Handoff != Ownership transfer
Handoff != Acceptance PASS
```

A handoff preserves enough partial state for recovery. Only a normal canonical
`uos.py claim` creates successor ownership.

## States

```text
PARTIAL
BLOCKED
NEEDS_DIFFERENT_CAPABILITY
INTERRUPTED_SAFE_POINT
HANDOFF_READY
```

### PARTIAL

Checkpoint current progress while the current owner keeps its live Lease.

Useful for long tasks where a recoverable safe point is valuable even though the
Agent intends to continue.

### BLOCKED

The current owner cannot progress because of a known external or technical block.
The Lease remains owned unless the Agent deliberately chooses `HANDOFF_READY`.

### NEEDS_DIFFERENT_CAPABILITY

The current Agent has learned that the task needs a different capability, tool or
context envelope. This records that diagnosis but does not itself transfer work.

### INTERRUPTED_SAFE_POINT

The Agent has stopped at a safe point, but immediate successor takeover is not yet
authorized. The current Lease remains authoritative.

### HANDOFF_READY

The current owner intentionally releases the task for canonical reclaim.

The transaction atomically:

```text
handoff record
+ immutable checkpoint artifacts
+ current Claim LeaseExpiresAt := now
+ HandoffState/HandoffPath on current Lock
+ active Work Session stop state, when present
```

It does **not** create `.done` and does not create a successor Claim.

After the source-of-truth transaction succeeds, the tool requests a normal
`uos.py reconcile` so `WORK_MARKET.csv` reflects the newly reclaimable task. If
that derived-state refresh fails, the handoff remains valid and the response marks
`derived_state_refresh=PENDING`; source-of-truth is not rolled back.

## Why partial artifacts use checkpoint paths

An unfinished draft must not occupy the task's final canonical output path and then
block the successor's no-clobber completion.

Therefore:

```text
caller working file:
projects/DEMO/final.txt

handoff checkpoint:
coordination/handoff_artifacts/TASK_X/HO_.../projects/DEMO/final.txt
```

The handoff record stores both `source_path` and `checkpoint_path`.

Checkpoint paths are unique per HandoffID and append-like. The successor can copy
or inspect the checkpoint after acquiring ownership, then produce the normal final
output in the Project WorkRoot.

Handoff artifact source paths must stay inside the task Project WorkRoot. Directory
artifacts must be packaged explicitly into a file before handoff.

## Create a recoverable checkpoint

```bash
python tools/partial_handoff.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  create \
  --agent-id AGENT_A \
  --task TASK_X \
  --lease-token <CURRENT_TOKEN> \
  --state PARTIAL \
  --completed "parser complete; integration not run" \
  --artifact projects/DEMO/parser.py \
  --validation-run "python -m py_compile parser.py" \
  --known-failures "hardware integration pending" \
  --next-action "run integration fixture" \
  --context-ref projects/DEMO/SPEC.md
```

Every handoff write is conditioned on the exact current Claim blob. If ownership
changes before publication, the old Agent cannot publish stale recovery context.

## Release at a safe point

```bash
python tools/partial_handoff.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  create \
  --agent-id AGENT_A \
  --task TASK_X \
  --lease-token <CURRENT_TOKEN> \
  --state HANDOFF_READY \
  --completed "safe checkpoint reached" \
  --artifact projects/DEMO/draft.py \
  --known-failures "requires HFSS-capable Agent" \
  --next-action "successor claims TASK_X, restores checkpoint, reruns Acceptance"
```

After this succeeds, AGENT_A's Lease is expired. AGENT_A must not renew or complete
using its old token.

## Successor flow

The successor does **not** trust a handoff before ownership.

First obtain the normal Claim:

```bash
python tools/uos.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  claim \
  --agent-id AGENT_B \
  --task TASK_X
```

A normal stale reclaim produces:

```text
LeaseGeneration = previous + 1
LeaseToken = new token
```

Only then read the handoff:

```bash
python tools/partial_handoff.py \
  read \
  --task TASK_X \
  --agent-id AGENT_B \
  --lease-token <NEW_TOKEN>
```

`read` verifies the caller currently owns the canonical Claim and reports whether
LeaseGeneration advanced beyond the handoff owner generation.

The returned warning is deliberate:

```text
UNVERIFIED_PARTIAL_WORK
```

The successor must restore/inspect checkpoint artifacts as needed and rerun the
original task Acceptance before final completion.

## Fencing behavior

After `HANDOFF_READY`:

```text
old owner renew      -> FENCED
old owner complete   -> FENCED
successor normal Claim -> Generation+1 / new token
```

No lock deletion is used to transfer ownership.

## Work Session interaction

If the current task belongs to an active bounded Work Session, `HANDOFF_READY`
updates that session to:

```text
state: STOPPED
stop_reason: HANDOFF_READY
```

The old Session therefore cannot continue by claiming unrelated work after it has
released its current task.

## Quality / preview interaction

A partial handoff is not a completion event, so it does not create a Quality Event,
Preview acceptance, Durability Receipt or `.done`.

If a partial artifact is important for human diagnosis, the Agent may still present
it in conversation, but this must not be described as completed/accepted work.

The normal completion chain remains:

```text
successor Claim
-> restore/rework
-> final outputs + required previews
-> Durability Receipt + .done
-> visible-result review when required
```

## Failure rules

1. Wrong AgentID or LeaseToken -> fail closed.
2. Expired current Lease -> fail closed; stale owner cannot author a handoff.
3. Artifact outside Project WorkRoot -> fail closed.
4. Handoff publication races with a Claim change -> expected-blob mismatch / fail closed.
5. Derived Reconcile failure after a successful HANDOFF_READY does not invalidate the source-of-truth handoff; explicit `uos.py claim --task` can still reclaim from the expired canonical Lock.
6. Handoff content is recovery context, not proof. Final Acceptance must be rerun.
