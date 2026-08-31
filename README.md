# UOS — Universal Orchestration System

> 从一句目标开始，把项目拆成可发布、可领取、可恢复、可审查的任务，并让不同数量级的 Agent 在 Git 上协同推进。

## 当前阶段：先跑通单仓项目

`ZXYHtech/UOS` 当前只做 **single-repository pilot**。

现阶段 UOS 只管理存放在本仓库内部的项目、任务和产物；**不调度 AI_book，不向 AI_book 写入任务，不做跨仓项目运行态同步，也不启动多仓调度。** 详细边界见 `docs/CURRENT_PHASE.md`。

第一项普通试验项目是 `QUICKBOARD`：一个零依赖浏览器任务看板。它用于验证 UOS 是否能在自己的仓库里完成“创建项目 -> 发布任务 -> Agent 领取 -> 执行 -> Review -> 完成”的完整闭环。

## 定位

`ZXYHtech/UOS` 是 UOS 调度系统的独立开发与验证仓库。

长期目标是让 UOS 成为跨项目、跨仓库的通用 Agent 调度控制面，但该能力**不是当前阶段目标**。只有单仓项目闭环通过并得到新的 operator 决策后，才进入外部仓库与多仓调度阶段。

## 当前基线来源

独立 UOS 的内核基线来源于 AI_book 中已经验证的 UOS：

- Protocol baseline: `V2.26`
- UOS baseline: `UOS_V1.11`
- ExecutionEpoch: `UOS_EXEC_20260830_01`
- Provider-neutral target: `YES`
- Minimum runtime target: `git + python3`
- Normal lifecycle: `Boot -> Claim -> Work -> Renew -> Complete -> Reconcile -> Next Task`
- GitHub Actions: optional adapter, not a required runtime
- Bare Git / Local Git: supported target
- Canonical ownership: Grant + Lock + Lease + Fencing
- Canonical writes: latest-state non-force/CAS transaction

这些能力仍需要从 AI_book 中抽取成真正可在本仓库独立运行的 Kernel；在 standalone acceptance 通过前，不宣称 UOS 仓库已经完全具备生产调度能力。

## 当前目标形态

```text
一句目标 / 新需求
      ↓
UOS 仓库内 Project Init / Intent
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
继续下一个任务
```

当前所有 project runtime 和 project output 都留在 `ZXYHtech/UOS` 内。

## 当前项目

```text
UOS_CORE
  └─ 抽取独立 Kernel、项目发布能力、单仓验收

QUICKBOARD
  └─ 第一个普通业务试验项目
     ├─ SPEC
     ├─ UI
     ├─ LOGIC
     ├─ DOCS
     └─ REVIEW
```

## 以后再做

单仓闭环稳定之后，再单独开启下一阶段：

```text
UOS Control Plane
   ├─ Repository A / Project A
   ├─ Repository B / Project B
   ├─ Repository C / Project C
   └─ ...
```

到那时才研究 repository adapter、跨仓任务发现、跨仓 ownership 边界、故障隔离、统一项目视图等能力。

## 设计原则

1. Durable state lives in files/Git, not chat memory.
2. Git is the arbiter; Python is the executor; CI is an optional adapter.
3. Request/Assignment is not ownership; canonical Claim is ownership.
4. Agents may disappear; Lease/Fencing/Handoff must recover safely.
5. Project intent can change without silently rewriting history.
6. Kernel is domain-neutral; project quality/content rules are adapters.
7. Weak Agents should be able to work with minimal context.
8. Kernel upgrades are serialized; project work can scale in parallel.
9. Runtime state is repository-local.
10. Prove one-repository operation before introducing multi-repository orchestration.

## License

Apache-2.0. Do not copy AI_book private project content, credentials, secrets, or project-specific runtime history into this public repository.
