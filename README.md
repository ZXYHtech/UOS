# UOS — Universal Orchestration System

> 从一句目标开始，把项目拆成可发布、可领取、可恢复、可审查的任务，并让不同数量级的 Agent 在 Git 上协同推进。

## 定位

`ZXYHtech/UOS` 是 UOS 调度系统的 **canonical 上游仓库**。

AI_book 不再作为 UOS 的永久宿主，而作为 UOS 的一个 reference workload / consumer。后续 UOS Kernel 的通用改进优先在本仓库完成、验证、版本化，再同步到 AI_book；AI_book 中发现的通用修复先回灌 UOS，再由固定版本同步回 AI_book。

## 当前基线

从 AI_book 中独立出来的基线以以下已验证能力为准：

- Protocol baseline: `V2.26`
- UOS baseline: `UOS_V1.11`
- ExecutionEpoch: `UOS_EXEC_20260830_01`
- Provider-neutral: `YES`
- Minimum runtime: `git + python3`
- Normal lifecycle: `Boot -> Claim -> Work -> Renew -> Complete -> Reconcile -> Next Task`
- GitHub Actions: optional adapter, not a required runtime
- Bare Git / Local Git: supported target
- Canonical ownership: Grant + Lock + Lease + Fencing
- Canonical writes: latest-state non-force/CAS transaction

## 目标形态

```text
一句目标 / 新需求
      ↓
Project Init / Intent
      ↓
Task Plan + Task Catalog
      ↓
Publish READY tasks
      ↓
Agent Boot / Claim
      ↓
Work / Review / Revision
      ↓
Complete / Reconcile
      ↓
New task / Pivot / Spawn / Reopen
```

UOS 本身也作为 `UOS_CORE` 项目运行：它可以在自己的仓库中发布 UOS 优化任务，让 Agent 领取并持续改进 UOS。

## 仓库关系

```text
ZXYHtech/UOS                 <- UOS Kernel canonical upstream
  ├─ kernel / orchestration
  ├─ generic tools
  ├─ project templates
  ├─ UOS_CORE self-hosted tasks
  └─ version + sync manifest

ZXYHtech/AI_book             <- reference workload / consumer
  ├─ AI_BOOK project data
  ├─ book/game/research outputs
  └─ pinned UOS snapshot
```

**只同步通用 Kernel，不同步项目运行态。** Claims、Grants、Done、Runtime、AI_book 任务和内容属于各仓库自己的 canonical state，禁止跨仓复制。

## 独立化状态

当前仓库已经完成“独立上游仓库初始化”，接下来按 `docs/EXTRACTION_AND_SYNC.md` 逐步搬迁通用 Kernel 和工具。在完整 standalone acceptance 通过前，本 README 不宣称本仓库已经取代 AI_book 中正在运行的 UOS 实例。

## 设计原则

1. Durable state lives in files/Git, not chat memory.
2. Git is the arbiter; Python is the executor; CI is an optional adapter.
3. Request/Assignment is not ownership; canonical Claim is ownership.
4. Agents may disappear; Lease/Fencing/Handoff must recover safely.
5. Project intent can change without silently rewriting history.
6. Kernel is domain-neutral; project quality/content rules are adapters.
7. Weak Agents should be able to work with minimal context.
8. Kernel upgrades are serialized; project work can scale in parallel.
9. Runtime state is repository-local; only versioned Kernel artifacts synchronize.
10. UOS must be able to schedule and improve UOS itself.

## License

Apache-2.0. Do not copy AI_book private project content, credentials, secrets, or project-specific runtime history into this public repository.
