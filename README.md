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

它只包含当前 READY 工作，并给出紧凑的选择信息：

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

## 6. Claim / Lease / Fencing

领取：

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

## 7. Preview / Visible Result Gate

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

预览伴随交付：

```text
SVG        → SVG + PNG
HTML       → HTML + preview PNG
PDF        → PDF + preview PNG
PPT/DOC/XLS→ source + preview PDF
CAD/EDA    → source + preview PNG
```

缺少要求的预览时，Complete 会失败；Preview 不是事后清理任务。

详见 `docs/QUALITY_VISIBILITY_GATE.md`。

## 8. Complete：输出 + Durability Receipt + Done 同一 canonical transaction

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

## 9. Reconcile / Status

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

## 10. Git-CAS 实现

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

普通 Agent 应优先使用 `tools/uos.py`。

## 11. 从 AI_book 回流的通用经验

2026-09-02 已把适合当前单仓阶段的 P0 能力抽成更小的 standalone 等价实现：

```text
ExecutionEpoch stale-Agent gate
Project WorkRoot authority
READY Work Market
Artifact Durability Receipt
```

没有复制 AI_book 项目内容、运行态或大型历史兼容层。

差异与后续候选见：

```text
docs/AI_BOOK_UPSTREAM_DELTA_20260902.md
```

下一批候选但尚未启用：

```text
Bounded Work Session
Capability / Tool / Context matching
Partial Handoff
Resource Admission / Backpressure
```

暂缓：Role Broker、OUTBOX_INGEST、复杂 Kernel self-orchestration。

## 12. 自检

```bash
python tools/selftest.py
```

测试覆盖：

- 同工作树生命周期
- low-level latest-canonical CAS
- 独立 Clone 完整生命周期
- Preview / staged Review Gate
- RuleEpoch warmup 串行 Claim
- ExecutionEpoch
- Project WorkRoot authority
- WORK_MARKET
- Artifact Durability Receipt

当前聊天执行环境仍不能完成“从 GitHub fresh clone 当前提交再运行”的真实网络验收，因此不能把这一项写成 PASS；仓库内本地 bare-Git 回归入口已具备。

## 13. 当前能力边界

```text
QUICKBOARD 普通项目闭环                 ✅
同工作树生命周期                         ✅
多 Clone CAS primitive                  ✅
多 Clone uos.py lifecycle integration   ✅ CODE / TEST PRESENT
Visible Result / Preview Gate           ✅ CODE / TEST PRESENT
ExecutionEpoch                          ✅ CODE / TEST PRESENT
Project WorkRoot authority              ✅ CODE / TEST PRESENT
READY Work Market                       ✅ CODE / TEST PRESENT
Artifact Durability Receipt             ✅ CODE / TEST PRESENT
GitHub fresh-clone 当前提交实跑           ⏳
外部项目仓库 adapter                     ❌ 当前禁止
AI_book 调度                              ❌ 当前禁止
一个 UOS 调度多个仓库                     ❌ 当前禁止
```

## 14. 设计原则

1. Durable state lives in files/Git, not chat memory.
2. Git is the arbiter; Python is the executor; CI is optional.
3. Task publication / Market listing are not ownership; canonical Claim is ownership.
4. Agents may disappear; Lease/Fencing must recover safely.
5. Ref race means recompute from latest canonical truth, never force/rebase stale decisions.
6. Rule changes require visible early samples before broad parallelization.
7. Review, preview, durability and completion are distinct facts.
8. Project outputs stay inside explicit WorkRoot authority.
9. Kernel stays domain-neutral and small; do not import historical complexity without a current need.
10. Prove one-repository operation before multi-repository orchestration.

## License

Apache-2.0. Do not copy AI_book private project content, credentials, secrets or project runtime history into this public repository.
