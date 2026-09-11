# TASK_INV_IMPL_E15_S08 — Conditional Multi-host Web / Worker & Shared Artifact Storage

## Status
`DESIGN_READY_CONDITIONAL_NOT_REQUIRED`

## Objective
Describe the next topology only if measured availability/concurrency needs require more than one application host after PostgreSQL adoption.

## Target when justified

```text
PostgreSQL primary database
+ stateless/modular-monolith web processes
+ durable workers claiming DB jobs
+ shared artifact storage if more than one host needs file access
```

This remains one application architecture; microservices are not required.

## Preconditions
- PostgreSQL production support and recovery are already proven;
- application session/auth/config behavior supports multiple processes/hosts safely;
- local-only file paths have been removed from shared business identity through artifact-storage abstraction;
- durable job lease/fencing works across hosts;
- duplicate scheduler ownership is prevented;
- load/availability evidence shows actual business value.

## Scheduler / workers
Only one logical scheduled job is created for each cadence/scope. Multiple worker processes may compete safely through DB claim/lease semantics. systemd/orchestrator ownership replaces hosted CI scheduling.

## Artifact storage
When local filesystem no longer suffices, migrate payloads to NAS/object storage through the existing immutable artifact key/hash abstraction. Business records keep stable artifact identity throughout the storage move.

## Non-goals
Do not add by default:

- Kafka/general event bus;
- Redis as business-state source;
- microservice decomposition;
- read replicas;
- Kubernetes;
- separate analytics cluster.

Each requires its own measured need.

## Tests
- two web/worker hosts cannot duplicate one idempotent business action/job;
- worker fencing protects stale lease across hosts;
- scheduled work is not created twice;
- artifact read/write/hash identity works from either host;
- losing one worker/web host does not corrupt business state.

## Done
If multi-host operation is ever needed, the system has a small proven topology that scales the modular monolith rather than replacing it with distributed complexity.