# AI_book P1 generic sync evidence — 2026-09-02

Status: **IMPLEMENTED / TESTS PRESENT / EXACT-CURRENT SELFTEST EXECUTION PENDING**

Scope: `ZXYHtech/UOS` single repository only.

## Implemented

```text
tools/agent_matching.py
tools/task_requirements.py
tools/work_session.py
```

### Agent matching

- reads latest canonical READY Work Market;
- filters by capability tier, tool availability, context capacity and optional roles;
- can skip incompatible higher-priority work;
- final ownership still goes through normal `uos.py claim`;
- matching cannot grant ownership.

### Task Agent requirement sidecar

- canonical path `orchestration/projects/<PROJECT>/TASK_AGENT_REQUIREMENTS.csv`;
- only matching hints are mutable;
- Task output/authority/acceptance remain unchanged;
- canonical writes require current ExecutionEpoch acknowledgement.

### Bounded Work Session

- canonical state `coordination/work_sessions/<AGENT>/<SESSION>.json`;
- deadline and max-task bounded;
- project and capability envelope scoped;
- no next unrelated Claim before `.done + DURABLE_READY + Quality Gate released`;
- PENDING review stops continuation;
- REJECTED review requires same-task rework;
- deadline does not abandon an already owned Task;
- failed session bookkeeping after successful Claim is recoverable by adopting one canonical live Claim; ambiguity fails closed.

## Regression files

```text
tests/test_agent_matching.py
tests/test_task_requirements.py
tests/test_work_session_guard.py
tests/test_work_session_git_cas.py
```

The independent-Clone/bare-Git integration scenario is designed to prove:

```text
priority-1 incompatible task
priority-2 compatible task
→ compatible claim only
→ durable completion
→ RuleEpoch warmup PENDING review
→ session stops
→ no incompatible follow-on claim
```

## Non-expansion boundary

Not activated:

```text
AI_book project dispatch
cross-repository scheduling
Role Broker
OUTBOX_INGEST
Resource Admission / Backpressure
multi-repository adapters
```

Recommended next generic candidate: `PARTIAL_HANDOFF_V1-lite`.

Do not mark exact-current P1 regression execution PASS until `python tools/selftest.py` has actually run against the current committed tree in a usable runtime.
