# UOS — Universal Orchestration System

> 从一句目标开始，把项目拆成可发布、可领取、可恢复、可审查的任务，并让多个 Agent 通过 Git 协同推进。

## 当前阶段：单仓验证

`ZXYHtech/UOS` 当前仍是 **single-repository validation**。

现阶段只管理存放在本仓库里的项目、任务和产物；**不调度 AI_book，不向 AI_book 写任务，不做跨仓运行态同步，也不启动多仓调度。** 详细边界见 `docs/CURRENT_PHASE.md`。

第一个普通项目 `QUICKBOARD` 已完成：

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

## 先运行自检

最低环境：`git + Python 3`。

```bash
python tools/selftest.py
```

测试集现在覆盖三层：

1. `tests/test_single_repo_pilot.py` — 同工作树生命周期；
2. `tests/test_canonical_publish.py` — 底层 latest-canonical CAS 原语；
3. `tests/test_git_cas_lifecycle.py` — 完整 `uos.py` 生命周期经过独立 Clone / bare Git remote 的集成回归。

当前执行环境不能解析 `github.com`，所以这里仍不声称“GitHub fresh clone 已实机通过”；仓库内的本地 bare-remote 测试入口已经准备好。

## 默认运行方式

`tools/uos.py` 现在有三种 transport：

```text
auto      默认
git-cas   latest-canonical Git transaction
local     单工作树 / 测试模式
```

### auto 的安全规则

```text
没有 Git remote
    ↓
local

存在 origin / canonical remote
    ↓
git-cas

remote 临时断网
    ↓
FAIL CLOSED
    ↓
绝不偷偷降级为 local Claim
```

这样可以避免网络故障时出现“两套 ownership truth”。

## 创建项目

```bash
python tools/uos.py project init \
  --project-id DEMO \
  --title "Demo project" \
  --goal "Build a small demo inside this repository"
```

正常 Clone 中，该命令会从最新 canonical main 建立隔离 worktree，重新执行 Project Init，再以普通 non-force push 发布。

## 发布任务

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

**Task publication ≠ Ownership。** 发布任务不会自动制造 Claim 或 Done。

## Agent 领取任务

```bash
python tools/uos.py claim \
  --agent-id AGENT_001 \
  --project DEMO
```

成功 Claim 包含：

- `CanonicalID`
- `AgentID`
- `LeaseGeneration`
- `LeaseToken`
- `LeaseExpiresAt`
- `FencingToken`
- Inputs / Output / Acceptance

多个独立 Clone 同抢时，只有最终成功推进 canonical main 的 Claim 才成为事实；main race 后失败者会从新 main 重新执行 Claim，而不是 rebase 旧决定。

## 续租

```bash
python tools/uos.py renew \
  --agent-id AGENT_001 \
  --task TASK_DEMO_SPEC_01 \
  --lease-token <TOKEN>
```

旧 owner、旧 token、过期 Lease 或被新 generation 替换的 owner 都会被 fencing。

## 完成任务

Agent 先在自己的工作区创建任务声明的 output，然后：

```bash
python tools/uos.py complete \
  --agent-id AGENT_001 \
  --task TASK_DEMO_SPEC_01 \
  --lease-token <TOKEN>
```

Git-CAS transport 会把调用者声明的 output 复制到最新 canonical snapshot 中，再执行当前 owner/token 检查、创建 `.done`、释放 Claim、重算依赖状态，并作为一个 canonical tree transaction 发布。

即使 output 命中 `.gitignore`，声明产物也会被纳入该隔离 completion transaction，避免“Done 已提交但产物没进仓库”。

如果 canonical main 上同一路径已经存在不同内容，则 completion 会停止，而不是静默覆盖。

## Reconcile / Status

```bash
python tools/uos.py reconcile
python tools/uos.py status --project DEMO
```

派生视图：

```text
coordination/runtime/TASK_STATUS.csv
coordination/runtime/STATUS.json
```

派生状态现在是确定性的；不再因为单纯的 `generated_at` 时间戳导致每次 `status` 都生成无意义 canonical commit。

最重要的 race 规则：

```text
main@X
  ↓
重算 runtime
  ↓
准备 push
  ↓
main 已推进到 Y
  ↓
丢弃 X 的 candidate
  ↓
从 Y 创建新的隔离 worktree
  ↓
重新运行 reconcile
```

**禁止把基于 X 的旧 runtime 仅仅 re-parent 到 Y。**

## Transport 细节

### `tools/canonical_runner.py`

把完整 `uos.py` 命令运行在最新 canonical snapshot 的临时 detached worktree 中；ref race 后整个命令重新执行。

### `tools/canonical_publish.py`

更底层的显式路径 CAS 原语，提供：

- latest-canonical fetch/build/push；
- non-force push；
- create-if-absent；
- expected-blob replacement；
- fenced delete；
- no-clobber；
- Repository Identity remote / branch gate。

普通 Agent 应优先使用 `tools/uos.py`，不要绕过生命周期直接拼 Claim / Complete。

## 当前能力边界

```text
同工作树生命周期                  ✅
QUICKBOARD 普通项目闭环            ✅
多 Clone CAS primitive             ✅
多 Clone uos.py lifecycle integration  CODE COMPLETE / TEST ADDED
GitHub fresh-clone 实机自检         ⏳
外部项目仓库 adapter               ❌ 当前禁止
AI_book 调度                        ❌ 当前禁止
一个 UOS 调度多个仓库               ❌ 当前禁止
```

## Repository Identity

`.uos/REPOSITORY_IDENTITY.yaml` 把当前 canonical repository 锚定为：

```text
https://github.com/ZXYHtech/UOS
refs/heads/main
```

错误 remote / branch 会 fail closed；fork 或独立复用时必须重新初始化 identity，而不是继承上游 canonical 权限。

## 定位

`ZXYHtech/UOS` 是 UOS 调度内核的独立开发和验证仓库。

长期方向仍然是：

```text
UOS Control Plane
   ├─ Repository A / Project A
   ├─ Repository B / Project B
   ├─ Repository C / Project C
   └─ ...
```

但只有当前单仓 Exit Gate 关闭，并且 operator 明确开启下一阶段后，才会开始 repository adapter、跨仓 ownership、故障隔离和统一项目视图。

## 设计原则

1. Durable state lives in files/Git, not chat memory.
2. Git is the arbiter; Python is the executor; CI is optional.
3. Task publication is not ownership; a valid canonical Claim is ownership.
4. Agents may disappear; Lease/Fencing must recover safely.
5. Ref race means recompute from latest canonical truth, never force/rebase stale decisions.
6. Kernel is domain-neutral; project rules are adapters.
7. Runtime state remains repository-local in the current phase.
8. Prove one-repository operation before introducing multi-repository orchestration.

## License

Apache-2.0. Do not copy AI_book private project content, credentials, secrets or project runtime history into this public repository.
