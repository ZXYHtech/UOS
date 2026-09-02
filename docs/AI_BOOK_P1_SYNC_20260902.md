# AI_book → standalone UOS P1 sync — 2026-09-02

## Result

Two P1 capabilities identified in `docs/AI_BOOK_UPSTREAM_DELTA_20260902.md` are now implemented as small standalone adapters:

```text
Bounded Work Session                 → tools/work_session.py
Capability / Tool / Context Matching → tools/agent_matching.py
Task matching sidecar                → tools/task_requirements.py
```

This remains **single-repository only**. It does not activate AI_book dispatch or multi-repository routing.

## Why the standalone implementation is smaller

AI_book historically accumulated Broker, Role, Resource, Session and compatibility surfaces because it was both a live project and the UOS incubation host.

Standalone UOS keeps ownership centered on one invariant:

```text
discovery / matching / session decision
            ≠ ownership

only canonical uos.py Claim
            = ownership
```

The new adapters therefore do not create their own Claim schema, scheduler, database, daemon or worker service.

## Capability matching

`agent_matching.py` consumes latest canonical READY work and filters it by:

```text
capability tier
tool availability
context capacity
optional role compatibility
```

A compatible lower-priority task may be selected instead of an incompatible higher-priority task.

The selected task is then passed to normal `uos.py claim`, preserving:

- latest-canonical Git CAS;
- unique ownership;
- LeaseGeneration / LeaseToken / Fencing;
- ExecutionEpoch;
- pending-review Claim pause.

## Matching sidecar

`task_requirements.py` adds optional project-local matching hints at:

```text
orchestration/projects/<PROJECT>/TASK_AGENT_REQUIREMENTS.csv
```

The sidecar cannot grant authority and cannot change task outputs or completion rules.

It is useful because the current Task Catalog already carries capability/context columns but the minimal `task publish` CLI does not yet expose all tool/role matching fields.

## Bounded Work Session

A session stores:

```text
agent
project scope
deadline
max task count
capability envelope
claimed task history
completed task history
current task
stop state/reason
```

Canonical path:

```text
coordination/work_sessions/<AGENT>/<SESSION>.json
```

A session is intentionally a continuation guard rather than a scheduler.

### Hard continuation invariant

No unrelated next Claim is allowed until the previous task satisfies:

```text
canonical .done
+ UOS_ARTIFACT_DURABILITY_V1 = DURABLE_READY
+ Quality Event gate released
```

`PENDING` review stops the session for user-visible inspection.

`REJECTED` review returns `REWORK_REQUIRED` for the same task.

A missing durability receipt or missing quality event under an enabled quality policy fails closed.

## Deadline behavior

Deadline/max-tasks control **new claims**.

They do not revoke an existing Claim:

```text
deadline reached + current Claim
→ WORK_CURRENT_TASK
→ stop_after_current=true
```

This avoids creating abandoned ownership merely because a 30-minute session timer elapsed.

## Recovery behavior

Task ownership and session bookkeeping are separate canonical facts.

If Claim succeeds but the session file update loses a race or transport fails, the session does not claim again. A subsequent `session next` searches live canonical Claims for that Agent:

```text
exactly one → adopt it
more than one → RECOVERY_REQUIRED / fail closed
```

## Regression additions

```text
tests/test_agent_matching.py
tests/test_task_requirements.py
tests/test_work_session_guard.py
tests/test_work_session_git_cas.py
```

The Git-CAS integration test covers:

```text
incompatible priority-1 task
+ compatible priority-2 task
+ bounded session
→ compatible Claim only
→ durable Complete
→ RuleEpoch warmup review PENDING
→ Session STOP_REVIEW_PENDING
→ no incompatible next Claim
```

## Remaining P1

Still not synchronized:

```text
Partial Handoff
Resource Admission / Backpressure
```

Recommended order:

1. Partial Handoff next, because it improves crash/tool-limit recovery without adding scheduling complexity.
2. Resource Admission only when a real standalone project needs scarce shared capacity or explicit concurrency caps.

## P2 remains deferred

```text
Role Broker / role leases
OUTBOX_INGEST
complex Kernel self-orchestration planner
multi-repository adapters
```

These remain intentionally absent rather than accidentally missing.
