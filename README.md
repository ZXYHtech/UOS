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

## 先运行自检

最低环境：`git + Python 3`。

```bash
python tools/selftest.py
```

这会执行：

- 同一工作树的 Project / Task / Claim / Lease / Fencing / Complete 生命周期回归；
- 临时 bare Git + 多个独立 clone 的 latest-canonical CAS 回归。

CAS 设计与边界见 `docs/CANONICAL_GIT_CAS.md`。

## 现在怎么用

### 模式 A：当前普通项目入口（同一个仓库工作树）

当前 `tools/uos.py` 是已经跑通 QUICKBOARD 的主入口。它现在仍以**同一个仓库工作树**为默认拓扑。

#### 1. 查看 UOS

```bash
python tools/uos.py boot
python tools/uos.py status
```

#### 2. 创建一个新项目

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

#### 3. 发布任务

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

#### 4. Agent 领取任务

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

#### 5. 工作时间较长时续租

```bash
python tools/uos.py renew \
  --agent-id AGENT_001 \
  --task TASK_DEMO_SPEC_01 \
  --lease-token <TOKEN>
```

旧 owner、旧 token 或已过期 Lease 会被 fencing 拒绝。

#### 6. 完成任务

Agent 先创建任务声明的 output，然后：

```bash
python tools/uos.py complete \
  --agent-id AGENT_001 \
  --task TASK_DEMO_SPEC_01 \
  --lease-token <TOKEN>
```

完成入口会再次验证当前 owner/token 和声明输出；成功后创建 `.done`、释放 Claim，并重新计算依赖状态。

#### 7. 查看项目状态

```bash
python tools/uos.py status --project DEMO
```

派生视图：

```text
coordination/runtime/TASK_STATUS.csv
coordination/runtime/STATUS.json
```

### 模式 B：多 clone canonical Git CAS（底层事务原语）

UOS 现在新增：

```text
tools/canonical_publish.py
```

它已经在临时 bare Git remote + 独立 clones 上验证：

- latest-main non-force publish；
- ref race 后从最新 main 重建；
- create-if-absent Claim 唯一赢家；
- expected-blob fencing；
- output + `.done` + Claim 删除原子 completion；
- same-path no-clobber；
- 删除必须带 expected blob；
- `.uos/REPOSITORY_IDENTITY.yaml` 存在时验证 canonical remote / branch。

**注意：它现在是底层 transport primitive，不是一个新的“多仓调度入口”。** 普通 Agent 暂时不要绕过 `tools/uos.py` 自己拼 Claim / Complete。下一步工作是把这层 CAS transport 正式集成到 `uos project/task/claim/renew/complete/reconcile`。

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

当前 `tools/canonical_publish.py` 已包含：

- latest-canonical Git transaction
- explicit canonical main target
- non-force push only
- ref-race retry from latest main
- require-absent CAS
- expected-blob CAS
- atomic multi-path publish + fenced delete
- Repository Identity target verification

回归入口：

```bash
python tools/selftest.py
```

对应测试：

```text
tests/test_single_repo_pilot.py
tests/test_canonical_publish.py
```

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
- canonical ownership semantics: Claim + Lock + Lease + Fencing
- distributed target: latest-canonical non-force/CAS Git transaction

当前 standalone Pilot 已经重新建立并验证了**独立的多 clone Git CAS 事务原语**，但该事务层尚未完全并入默认 `tools/uos.py` 生命周期。因此不能把 CAS primitive 的成功误读成“多仓调度已经完成”。

## 当前项目

```text
UOS_CORE
  └─ 单仓 Kernel
     ├─ QUICKBOARD 闭环 ✅
     ├─ same-working-tree lifecycle ✅
     ├─ multi-clone CAS primitive ✅
     └─ CAS lifecycle integration ⏳

QUICKBOARD
  └─ COMPLETED ✅
```

## 以后再做

只有单仓闭环稳定，并且由 operator 明确开启下一阶段，才考虑：

```text
UOS Control Plane
   ├─ Repository A / Project A
   ├─ Repository B / Project B
   ├─ Repository C / Project C
   └─ ...
```

届时再引入 repository adapter、跨仓任务发现、跨仓 ownership、故障隔离和统一项目视图；不会把当前 CAS primitive 直接当作多仓调度器。

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
