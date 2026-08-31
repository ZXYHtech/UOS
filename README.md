# UOS — Universal Orchestration System

> 从一句目标开始，把项目拆成可发布、可领取、可恢复、可审查的任务，并让不同数量级的 Agent 在 Git 上协同推进。

## 当前阶段：单仓验证

`ZXYHtech/UOS` 当前只做 **single-repository pilot**。

现阶段 UOS 只管理存放在本仓库内部的项目、任务和产物；**不调度 AI_book，不向 AI_book 写入任务，不做跨仓项目运行态同步，也不启动多仓调度。** 详细边界和 Exit Gate 见 `docs/CURRENT_PHASE.md`。

第一个普通试验项目 `QUICKBOARD` 已经完成：

```text
SPEC ✅
  ├─ UI ✅
  └─ LOGIC ✅
       ↓
DOCS ✅
  ↓
REVIEW ✅
  ↓
PROJECT COMPLETED ✅
```

试跑证据和发现见 `docs/PILOT_RESULT_QUICKBOARD.md`。

## 现在怎么用

最低环境：Python 3 标准库。当前 Pilot 面向**同一个仓库工作树**，不是跨仓/多 clone 调度器。

### 1. 查看 UOS

```bash
python tools/uos.py boot
python tools/uos.py status
```

### 2. 创建一个新项目

```bash
python tools/uos.py project init \
  --project-id DEMO \
  --title "Demo project" \
  --goal "Build a small demo inside this repository"
```

这会创建：

```text
orchestration/projects/DEMO/PROJECT.yaml
orchestration/projects/DEMO/TASK_CATALOG.csv
```

创建项目本身不会制造 Claim 或 Done。

### 3. 发布任务

```bash
python tools/uos.py task publish \
  --project DEMO \
  --task-id TASK_DEMO_SPEC_01 \
  --title "Define the demo" \
  --role ARCHITECT \
  --priority 1 \
  --output projects/DEMO/SPEC.md \
  --acceptance "Define the exact implementation plan"
```

带依赖的任务：

```bash
python tools/uos.py task publish \
  --project DEMO \
  --task-id TASK_DEMO_BUILD_01 \
  --title "Build the demo" \
  --deps TASK_DEMO_SPEC_01 \
  --inputs projects/DEMO/SPEC.md \
  --output projects/DEMO/index.html \
  --acceptance "Working demo exists"
```

`task publish` 只发布任务。**发布 ≠ 领取，Request/Task ≠ Ownership。**

### 4. Agent 领取任务

```bash
python tools/uos.py claim \
  --agent-id AGENT_001 \
  --project DEMO
```

成功后返回 Claim，包括：

- `CanonicalID`
- `AgentID`
- `LeaseGeneration`
- `LeaseToken`
- `LeaseExpiresAt`
- `FencingToken`
- Inputs / Output / Acceptance

只有当前有效 Claim 才代表 ownership。

### 5. 工作时间较长时续租

```bash
python tools/uos.py renew \
  --agent-id AGENT_001 \
  --task TASK_DEMO_SPEC_01 \
  --lease-token <TOKEN>
```

旧 owner、旧 token 或已过期 Lease 会被 fencing 拒绝。

### 6. 完成任务

Agent 先创建任务声明的 output，然后：

```bash
python tools/uos.py complete \
  --agent-id AGENT_001 \
  --task TASK_DEMO_SPEC_01 \
  --lease-token <TOKEN>
```

完成入口会再次验证当前 owner/token 和声明输出；成功后创建 `.done`、释放 Claim，并重新计算依赖状态。

### 7. 查看项目状态

```bash
python tools/uos.py status --project DEMO
```

派生视图：

```text
coordination/runtime/TASK_STATUS.csv
coordination/runtime/STATUS.json
```

## 当前内核能力

当前 `tools/uos.py` 已包含：

- Project Init
- Task Publish
- READY/BLOCKED 依赖推导
- Claim
- Lease / Renew
- LeaseGeneration / LeaseToken / Fencing
- stale reclaim
- Complete
- Status / Reconcile
- 同工作树控制面 mutex
- 原子 runtime/catalog 写入
- 仓库内路径约束，拒绝绝对路径和 `../` 逃逸

回归测试位于：

```text
tests/test_single_repo_pilot.py
```

覆盖生命周期、发布不产生 ownership、并发发布、10 Agent 抢单任务唯一 owner、Lease 过期 reclaim/fencing、仓库路径逃逸拒绝等。

## 定位

`ZXYHtech/UOS` 是 UOS 调度系统的独立开发与验证仓库。

长期目标是让 UOS 成为跨项目、跨仓库的通用 Agent 调度控制面，但该能力**不是当前阶段目标**。只有单仓 Exit Gate 关闭并得到新的 operator 决策后，才进入外部仓库与多仓调度阶段。

## 当前基线来源

独立 UOS 的设计基线来源于 AI_book 中已经验证过的 UOS：

- Protocol baseline: `V2.26`
- UOS baseline: `UOS_V1.11`
- ExecutionEpoch: `UOS_EXEC_20260830_01`
- provider-neutral target: `git + python3`
- lifecycle target: `Boot -> Claim -> Work -> Renew -> Complete -> Reconcile -> Next Task`
- GitHub Actions should remain optional
- canonical ownership semantics: Grant/Claim + Lock + Lease + Fencing
- distributed target: latest-canonical non-force/CAS Git transaction

注意：当前 standalone Pilot 已经能完成同仓项目，但还没有重新集成并验证完整的**多 clone latest-canonical Git CAS**。因此不能把 QUICKBOARD 成功误读成“多仓调度已经完成”。

## 当前项目

```text
UOS_CORE
  └─ 继续加固独立 Kernel、验证、后续提取 Git CAS

QUICKBOARD
  └─ COMPLETED
     ├─ SPEC
     ├─ UI
     ├─ LOGIC
     ├─ DOCS
     └─ REVIEW
```

## 以后再做

单仓闭环稳定之后，并且由 operator 明确开启下一阶段，才考虑：

```text
UOS Control Plane
   ├─ Repository A / Project A
   ├─ Repository B / Project B
   ├─ Repository C / Project C
   └─ ...
```

届时再研究 repository adapter、跨仓任务发现、跨仓 ownership、Git CAS、故障隔离和统一项目视图。

## 设计原则

1. Durable state lives in files/Git, not chat memory.
2. Git is the arbiter; Python is the executor; CI is an optional adapter.
3. Task publication is not ownership; valid Claim is ownership.
4. Agents may disappear; Lease/Fencing/Handoff must recover safely.
5. Project intent can change without silently rewriting history.
6. Kernel is domain-neutral; project quality/content rules are adapters.
7. Weak Agents should be able to work with minimal context.
8. Kernel upgrades are serialized; project work can scale in parallel.
9. Runtime state is repository-local.
10. Prove one-repository operation before introducing multi-repository orchestration.

## License

Apache-2.0. Do not copy AI_book private project content, credentials, secrets, or project-specific runtime history into this public repository.
