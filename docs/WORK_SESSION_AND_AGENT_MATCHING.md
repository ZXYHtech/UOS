# Bounded Work Session + Agent Matching

Status: `P1 PILOT / SINGLE-REPOSITORY ONLY`

This is a small standalone implementation of two useful AI_book UOS lessons:

1. bounded continuation for requests such as “continue working for 30 minutes”;
2. capability/tool/context-aware READY task selection.

Neither feature grants ownership. Canonical `uos.py claim` remains the only task ownership transition.

## 1. Safety order

A Work Session may continue only through this order:

```text
current Claim
→ Agent work
→ Complete
→ declared outputs + required previews
→ UOS_ARTIFACT_DURABILITY_V1 = DURABLE_READY
→ Quality Event
→ PENDING? stop for operator review
→ REJECTED? rework same task
→ ACCEPTED / AUTO_ACCEPTED
→ session deadline / max-task check
→ capability-aware selection
→ canonical Claim
```

Therefore `AUTO` continuation cannot bypass:

- ExecutionEpoch;
- Lease/Fencing;
- Preview Gate;
- Artifact Durability;
- RuleEpoch first-three confirmation;
- later deterministic samples;
- rejected-task rework.

## 2. Capability-aware task discovery

Tool:

```text
tools/agent_matching.py
```

It reads the latest canonical `coordination/runtime/WORK_MARKET.csv`, applies the Agent envelope, then delegates the selected task to `tools/uos.py claim`.

Matching dimensions:

```text
Agent CapabilityTier >= Task MinCapabilityTier
Agent tools ⊇ Task ToolRequirements
Agent ContextCapacity >= Task ContextClass
Agent Role intersects Task AllowedRoles   (when configured)
```

Context order:

```text
XS < S < M < L < XL
```

Example:

```bash
python tools/agent_matching.py \
  --ack-execution-epoch <CURRENT_EPOCH> \
  claim \
  --agent-id AGENT_01 \
  --project DEMO \
  --capability-tier 3 \
  --tools "git;python" \
  --context M \
  --roles WORKER
```

If a higher-priority task requires Tier 4 + HFSS + L context, this Agent skips it and may claim a lower-priority compatible READY task instead.

An exact incompatible Task returns `NO_COMPATIBLE_READY_TASK` plus mismatch reasons rather than silently claiming it.

## 3. Optional per-task matching sidecar

Tool:

```text
tools/task_requirements.py
```

Sidecar:

```text
orchestration/projects/<PROJECT>/TASK_AGENT_REQUIREMENTS.csv
```

This lets a project add matching requirements without changing ownership or path authority.

Example:

```bash
python tools/task_requirements.py \
  --ack-execution-epoch <CURRENT_EPOCH> \
  set \
  --project DEMO \
  --task TASK_HFSS_01 \
  --min-capability 4 \
  --context L \
  --tools "python;hfss" \
  --allowed-roles ENGINEER
```

The sidecar overrides only these matching hints:

- `min_capability_tier`;
- `context_class`;
- `tool_requirements`;
- `allowed_roles`.

It does **not** alter Task Output, WriteScope, dependencies, Claim, Lease or acceptance criteria.

## 4. Bounded Work Session

Tool:

```text
tools/work_session.py
```

Canonical state:

```text
coordination/work_sessions/<AGENT_ID>/<SESSION_ID>.json
```

Start a 30-minute session:

```bash
python tools/work_session.py \
  --ack-execution-epoch <CURRENT_EPOCH> \
  start \
  --agent-id AGENT_01 \
  --minutes 30 \
  --project DEMO \
  --max-tasks 10 \
  --capability-tier 3 \
  --tools "git;python" \
  --context M \
  --roles WORKER
```

Then the Agent repeatedly asks the guard for the next safe action:

```bash
python tools/work_session.py \
  --ack-execution-epoch <CURRENT_EPOCH> \
  next \
  --agent-id AGENT_01 \
  --session-id <SESSION_ID>
```

Possible results include:

```text
CLAIM_GRANTED
WORK_CURRENT_TASK
STOP_REVIEW_PENDING
REWORK_REQUIRED
STOP_DURABILITY_PENDING
STOP_NO_MATCH
SESSION_STOPPED
RECOVERY_REQUIRED
```

## 5. Deadline semantics

Deadline is a **new-claim boundary**, not permission to abandon owned work.

If the deadline expires while no task is owned:

```text
no new Claim
→ SESSION_STOPPED / DEADLINE_REACHED
```

If the deadline expires while the Agent already owns a Task:

```text
WORK_CURRENT_TASK
stop_after_current = true
```

The current task should reach a safe completion/handoff state; the Session simply refuses another unrelated Claim afterward.

## 6. Review semantics

If the current task has:

```text
.done
+ DURABLE_READY receipt
+ review_status=PENDING
```

then `session next` returns:

```text
STOP_REVIEW_PENDING
```

The Agent must show the result/previews to the operator in conversation. It may not claim the next task.

If the operator rejects the result, the session returns:

```text
REWORK_REQUIRED
```

and keeps the session focused on the same Task.

## 7. Recovery

A Claim can succeed before the session-state update succeeds because task ownership and session bookkeeping are deliberately separate facts.

If that happens the result is:

```text
CLAIM_GRANTED_SESSION_RECORD_PENDING
```

The Agent must not claim another Task. Re-running `session next` scans canonical live Claims for the same Agent and adopts the single recoverable Claim into the session.

If more than one active Claim is found for that Agent, the session fails closed with `RECOVERY_REQUIRED` instead of guessing.

## 8. What this does not add

This P1 pilot does not add:

- Role Broker / role leases;
- Resource pool scheduling;
- OUTBOX ingestion;
- daemon workers;
- databases;
- multi-repository routing.

Those remain separate future decisions.

## 9. Regression surface

Tests:

```text
tests/test_agent_matching.py
tests/test_task_requirements.py
tests/test_work_session_guard.py
```

They cover incompatible high-priority skipping, hard tool mismatch, context ordering, sidecar overrides, stale Epoch rejection, PENDING review stop, REJECTED rework, durability fail-closed, max-task stop and deadline-with-current-task behavior.
