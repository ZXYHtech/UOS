# UOS — Universal Orchestration System

> 从一句目标开始，把项目拆成可发布、可领取、可恢复、可审查的任务，并让多个 Agent 通过 Git 协同推进。

## 当前阶段：单仓验证

`ZXYHtech/UOS` 当前仍是 **single-repository validation**。

现阶段只管理存放在本仓库里的项目、任务和产物；**不调度 AI_book，不向 AI_book 写任务，不做跨仓运行态同步，也不启动多仓调度。** 详细边界见 `docs/CURRENT_PHASE.md`。

第一个普通项目 `QUICKBOARD` 已完成；当前继续验证 standalone Kernel 本身。

## 1. Boot：先取得当前 ExecutionEpoch

最低环境：`git + Python 3`。

```bash
python tools/uos.py boot
```

Boot 会返回当前：

```text
execution_epoch: UOS_EXEC_20260902_01
```

发生执行语义变更后，旧 Agent / 旧聊天上下文不能继续用旧规则产生新的 canonical 控制面写入。

以下关键动作必须显式确认当前 Epoch：

```text
project init
task publish
claim
renew
complete
reconcile
```

统一写法：

```bash
python tools/uos.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  <command> ...
```

`boot` 与 `status` 是发现/检查入口，不要求 Epoch Ack。

Epoch 不匹配会返回 `REBOOT_REQUIRED`，要求重新 Boot，而不是让旧 Agent 静默继续。

## 2. Transport

`tools/uos.py` 有三种 transport：

```text
auto      默认
git-cas   latest-canonical Git transaction
local     单工作树 / 测试模式
```

`auto`：

```text
没有 Git remote → local
存在 canonical remote → git-cas
remote 已配置但暂时不可达 → FAIL CLOSED
```

绝不因为网络失败偷偷退回 local Claim，避免产生两套 ownership truth。

## 3. 创建项目

```bash
python tools/uos.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  project init \
  --project-id DEMO \
  --title "Demo project" \
  --goal "Build a small demo inside this repository"
```

默认项目工作根：

```text
projects/DEMO/
```

这个 `WorkRoot` 同时是任务输出权限边界。

## 4. 发布任务：输出不能跨 Project WorkRoot

```bash
python tools/uos.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  task publish \
  --project DEMO \
  --task-id TASK_DEMO_SPEC_01 \
  --title "Define the demo" \
  --role ARCHITECT \
  --priority 1 \
  --output projects/DEMO/SPEC.md \
  --acceptance "Define the exact implementation plan"
```

例如 `DEMO` 项目：

```text
✅ projects/DEMO/result.md
❌ projects/OTHER/result.md
```

跨项目输出会被 `PATH_AUTHORITY_DENIED` 拒绝。

**Task publication ≠ Ownership。** 发布任务不会制造 Claim 或 Done。

## 5. Work Market：不用扫描整个任务池找工作

每次 Reconcile 都会生成：

```text
coordination/runtime/WORK_MARKET.csv
```

它只包含当前 READY 工作，并给出紧凑选择信息：

- Project / TaskID
- Priority / Role / Workstream
- Size
- Min Capability Tier
- Context Class
- Tool Requirements
- Output

Market 只用于发现：

```text
Market listing ≠ Ownership
```

真正 ownership 仍必须通过 canonical Claim。

## 6. Capability / Tool / Context Matching

P1 已加入一个轻量匹配器：

```text
tools/agent_matching.py
```

它从**最新 canonical Work Market**选择与 Agent 能力匹配的 READY Task，然后仍然调用正常 `uos.py claim`。

匹配条件：

```text
Agent CapabilityTier >= Task MinCapabilityTier
Agent Tools ⊇ Task ToolRequirements
Agent ContextCapacity >= Task ContextClass
Agent Role ∩ Task AllowedRoles ≠ ∅   （配置时）
```

Context 顺序：

```text
XS < S < M < L < XL
```

示例：

```bash
python tools/agent_matching.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  claim \
  --agent-id AGENT_001 \
  --project DEMO \
  --capability-tier 3 \
  --tools "git;python" \
  --context M \
  --roles WORKER
```

高优先级任务如果要求 Tier 4 + HFSS + L context，而当前 Agent 只有 Tier 3 / git+python / M，则不会硬抢；匹配器可以选择更低优先级但兼容的 READY Task。

匹配结果仍然：

```text
Task match ≠ ownership
```

只有后续 canonical Claim 成功才有 ownership。

### 可选 Task 匹配要求

```text
tools/task_requirements.py
```

写入：

```text
orchestration/projects/<PROJECT>/TASK_AGENT_REQUIREMENTS.csv
```

例如：

```bash
python tools/task_requirements.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  set \
  --project DEMO \
  --task TASK_HFSS_01 \
  --min-capability 4 \
  --context L \
  --tools "python;hfss" \
  --allowed-roles ENGINEER
```

Sidecar 只影响**任务匹配提示**，不能改变 Output、WriteScope、依赖、Claim、Lease 或 Acceptance。

## 7. Claim / Lease / Fencing

直接领取仍然可用：

```bash
python tools/uos.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  claim \
  --agent-id AGENT_001 \
  --project DEMO
```

成功 Claim 返回：

- CanonicalID
- AgentID
- LeaseGeneration
- LeaseToken
- LeaseExpiresAt
- FencingToken
- Inputs / Output / Acceptance

多个独立 Clone 同抢时，只有成功推进 canonical main 的 Claim 成为事实；失败者必须从最新 main 重算。

续租：

```bash
python tools/uos.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  renew \
  --agent-id AGENT_001 \
  --task TASK_DEMO_SPEC_01 \
  --lease-token <TOKEN>
```

旧 owner、旧 token、过期 Lease 或旧 generation 会被 fencing。

## 8. Bounded Work Session：例如“继续工作 30 分钟”

P1 的 Work Session 是**持续工作约束**，不是第二个 scheduler：

```text
tools/work_session.py
```

Canonical Session State：

```text
coordination/work_sessions/<AGENT>/<SESSION>.json
```

开始 30 分钟：

```bash
python tools/work_session.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  start \
  --agent-id AGENT_001 \
  --minutes 30 \
  --project DEMO \
  --max-tasks 10 \
  --capability-tier 3 \
  --tools "git;python" \
  --context M \
  --roles WORKER
```

每次准备继续时：

```bash
python tools/work_session.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  next \
  --agent-id AGENT_001 \
  --session-id <SESSION_ID>
```

Session 只有在以下事实全部成立后才会允许下一次 Claim：

```text
上一 Task canonical .done
+ Durability Receipt = DURABLE_READY
+ Review/Preview Gate 已放行
+ deadline 未结束
+ max_tasks 未用完
+ 存在能力兼容 READY Task
```

常见返回：

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

### Deadline 不会粗暴丢弃当前任务

```text
时间到 + 当前没有 Claim
→ 不再领取

时间到 + 已经拥有 Task
→ WORK_CURRENT_TASK
→ stop_after_current=true
```

也就是说，30 分钟是**新 Claim 边界**，不是“到点直接遗弃当前 ownership”。

详见 `docs/WORK_SESSION_AND_AGENT_MATCHING.md`。

## 9. Preview / Visible Result Gate

当前质量规则：

```text
RuleEpoch = 1
WarmupRequired = 3
WarmupMaxConcurrentClaims = 1
SampleEvery = 5
```

规则改变后的前三个真实成果：

```text
Task 1 → 完成 → 展示成果/预览 → Operator 确认
Task 2 → 完成 → 展示成果/预览 → Operator 确认
Task 3 → 完成 → 展示成果/预览 → Operator 确认
```

前三项通过后才恢复正常并行；之后第 5、10、15…个 completion 抽检，高风险任务始终可以强制 Review。

待确认成果存在时，新 Claim 暂停。Agent 必须直接在对话中呈现结果，不能把常规验收推给用户去 GitHub 自己找。

Work Session **必须服从这个 Gate**：即使 session 还有时间，只要当前成果 `review_status=PENDING`，就返回 `STOP_REVIEW_PENDING`，不得继续领取。

预览伴随交付：

```text
SVG         → SVG + PNG
HTML        → HTML + preview PNG
PDF         → PDF + preview PNG
PPT/DOC/XLS → source + preview PDF
CAD/EDA     → source + preview PNG
```

缺少要求的预览时，Complete 会失败；Preview 不是事后清理任务。

详见 `docs/QUALITY_VISIBILITY_GATE.md`。

## 10. Complete：输出 + Durability Receipt + Done 同一 canonical transaction

Agent 先在自己的工作区生成声明的全部 output / preview，然后：

```bash
python tools/uos.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  complete \
  --agent-id AGENT_001 \
  --task TASK_DEMO_SPEC_01 \
  --lease-token <TOKEN>
```

Complete 会重新验证：

```text
当前 Claim owner/token/fencing
+ Project WorkRoot
+ 声明 output 是否存在
+ Preview contract
```

成功时在同一个 canonical tree transaction 中发布：

```text
业务 output / preview
+ coordination/quality/durability/<TASK>.json
+ coordination/completed/<TASK>.done
- coordination/claims/<TASK>.lock
```

Durability Receipt 使用 `UOS_ARTIFACT_DURABILITY_V1`，为每个声明产物记录路径、类型与 SHA-256。

因此明确区分：

```text
Preview visible
≠ Operator accepted
≠ Artifact durably canonical
≠ Task .done
```

即使 output 命中 `.gitignore`，声明产物仍会被纳入隔离 canonical completion transaction。

## 11. Reconcile / Status

```bash
python tools/uos.py status --project DEMO

python tools/uos.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  reconcile
```

派生视图：

```text
coordination/runtime/TASK_STATUS.csv
coordination/runtime/WORK_MARKET.csv
coordination/runtime/STATUS.json
```

Reconcile 是确定性的。main race 时：

```text
main@X
→ 计算 runtime
→ main 已到 Y
→ 丢弃 X candidate
→ 从 Y 建新 worktree
→ 完整重跑 reconcile
```

禁止把旧 runtime 仅仅 re-parent 到新 main。

## 12. Git-CAS 实现

### `tools/canonical_runner.py`

把完整业务命令运行在最新 canonical snapshot 的临时 detached worktree 中；ref race 后整个命令重跑。

ExecutionEpoch Ack 会在外层解析，但质量/预览逻辑看到的业务 argv 仍从 `task / claim / complete` 开始，防止全局参数意外绕过 Preview Gate。

### `tools/canonical_publish.py`

底层显式路径 CAS 原语：

- latest-canonical fetch/build/push
- non-force push
- create-if-absent
- expected-blob replacement
- fenced delete
- no-clobber
- Repository Identity remote / branch gate

普通 Agent 应优先使用 `tools/uos.py`；Work Session / Agent Matching 只是它前后的薄控制层。

## 13. 从 AI_book 回流的通用经验

2026-09-02 当前已同步：

```text
P0
  ExecutionEpoch stale-Agent gate          ✅
  Project WorkRoot authority                ✅
  READY Work Market                         ✅
  Artifact Durability Receipt               ✅

P1A
  Capability / Tool / Context Matching      ✅ CODE / TEST PRESENT
  Bounded Work Session                      ✅ CODE / TEST PRESENT
```

仍未同步：

```text
P1B
  Partial Handoff                           ⏳ 下一候选
  Resource Admission / Backpressure         ⏳ 真实需求驱动

P2
  Role Broker / role leases                 ⏸
  OUTBOX_INGEST                             ⏸
  complex Kernel self-orchestration         ⏸
  multi-repository adapters                 ❌ 当前禁止
```

差异记录：

```text
docs/AI_BOOK_UPSTREAM_DELTA_20260902.md
docs/AI_BOOK_P1_SYNC_20260902.md
```

## 14. 自检

```bash
python tools/selftest.py
```

测试自动发现 `tests/test_*.py`，当前覆盖：

- 同工作树生命周期
- low-level latest-canonical CAS
- 独立 Clone 完整生命周期
- Preview / staged Review Gate
- RuleEpoch warmup 串行 Claim
- ExecutionEpoch
- Project WorkRoot authority
- WORK_MARKET
- Artifact Durability Receipt
- capability / tool / context matching
- Task Agent requirement sidecar
- Work Session deadline / max-task / review / durability guard
- Work Session + capability matching Git-CAS 集成场景

当前聊天执行环境仍不能完成“从 GitHub fresh clone 当前提交再运行”的真实网络验收，因此不能把 exact-current full suite 写成 PASS；仓库内本地 bare-Git 回归入口已经具备。

## 15. 当前能力边界

```text
QUICKBOARD 普通项目闭环                   ✅
同工作树生命周期                           ✅
多 Clone CAS primitive                    ✅
多 Clone uos.py lifecycle integration     ✅ CODE / TEST PRESENT
Visible Result / Preview Gate             ✅ CODE / TEST PRESENT
ExecutionEpoch                            ✅ CODE / TEST PRESENT
Project WorkRoot authority                ✅ CODE / TEST PRESENT
READY Work Market                         ✅ CODE / TEST PRESENT
Artifact Durability Receipt               ✅ CODE / TEST PRESENT
Capability-aware matching                 ✅ CODE / TEST PRESENT
Bounded Work Session                      ✅ CODE / TEST PRESENT
Partial Handoff                           ⏳
Resource Admission / Backpressure         ⏳
GitHub fresh-clone 当前提交实跑             ⏳
外部项目仓库 adapter                       ❌ 当前禁止
AI_book 调度                                ❌ 当前禁止
一个 UOS 调度多个仓库                       ❌ 当前禁止
```

## 16. 设计原则

1. Durable state lives in files/Git, not chat memory.
2. Git is the arbiter; Python is the executor; CI is optional.
3. Task publication / Market listing / capability match / Work Session are not ownership; canonical Claim is ownership.
4. Agents may disappear; Lease/Fencing must recover safely.
5. Ref race means recompute from latest canonical truth, never force/rebase stale decisions.
6. Rule changes require visible early samples before broad parallelization.
7. Review, preview, durability and completion are distinct facts.
8. Project outputs stay inside explicit WorkRoot authority.
9. Session deadline controls new Claims; it does not abandon an existing Claim.
10. Kernel stays domain-neutral and small; do not import historical complexity without a current need.
11. Prove one-repository operation before multi-repository orchestration.

## License

Apache-2.0. Do not copy AI_book private project content, credentials, secrets or project runtime history into this public repository.
