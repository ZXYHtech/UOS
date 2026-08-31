# Project & Task Publishing Target

## Goal

UOS must not only dispatch pre-existing tasks. A standalone installation should be able to create a project, publish tasks, change intent, and let Agents immediately discover and claim the new work.

Target operator flow:

```bash
python tools/uos.py project init --project-id DEMO --title "Demo project"
python tools/uos.py task publish --project DEMO --title "First task" --role WORKER --priority 1
python tools/uos.py reconcile
```

The exact CLI may evolve, but the behavior must remain deterministic and file/Git-backed.

## Required objects

A project should minimally provide:

- ProjectID
- current IntentVersion
- title / goal
- lifecycle state
- task catalog
- project events / links when needed
- quality/compliance adapter references
- resource requirements when needed

A published task should minimally provide:

- Canonical Task ID
- ProjectID
- title / role
- priority
- dependencies
- status (`READY`, `BLOCKED`, etc.)
- inputs/context references
- output target
- write scope / exclusive keys when needed
- capability/context/tool requirements
- acceptance criteria
- compliance/quality profile

## Publishing invariant

Creating a task is not the same as assigning ownership.

```text
Task publish -> READY/BLOCKED catalog state
Agent request -> broker decision
Grant + Lock -> canonical ownership
```

A task publisher must never manufacture a Claim, LeaseToken, Grant or `.done` record.

## Self-hosting

`UOS_CORE` is the first standalone project. Its migration/evolution tasks are stored under `orchestration/projects/UOS_CORE/` so UOS can eventually schedule its own development exactly as it schedules an external project.
