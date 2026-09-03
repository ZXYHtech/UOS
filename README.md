# UOS — Universal Orchestration System

> 从一句目标开始，把项目拆成可发布、可领取、可恢复、可审查的任务，并让多个 Agent 通过 Git 形成可验证的 canonical 协作状态。

## 当前阶段：单仓验证

`ZXYHtech/UOS` 当前仍是 **single-repository validation**。

现阶段只管理本仓库内的项目、任务和产物：

- ✅ standalone UOS 项目 / Task / Claim / Complete / Handoff / Work Session；
- ✅ 同一仓库多个独立 Clone / Agent 的 latest-main Git CAS；
- ✅ Broker V2 Request / Grant / Lock ownership；
- ✅ Completion Outbox / mechanical batch Integration；
- ❌ 不调度 AI_book；
- ❌ 不复制 AI_book runtime state；
- ❌ 不启用跨仓任务路由。

AI_book 只可作为通用 Kernel 经验的只读历史证据。边界和当前验收状态见：

```text
docs/CURRENT_PHASE.md
docs/AI_BOOK_CLAIM_DELTA_SYNC_20260903.md
```

---

# 1. 核心生命周期

当前 canonical 路径：

```text
Boot / ExecutionEpoch
→ Project init
→ Task publish
→ Reconcile READY Work Market
→ optional capability matching
→ Broker V2 Claim
   Request → Grant → active Lock
→ Work
→ Renew / Lease / Fencing
→ Complete
   ├─ direct latest-main CAS
   └─ pure main-ref race exhaustion only
      → Completion Outbox
      → mechanical batch ingest
→ canonical outputs + durability + .done
→ quality / preview / review gate
→ Work Session continuation / handoff / safe stop
```

Git 是 canonical 仲裁者；Python 是执行器；GitHub Actions 是验证/观测适配器，不是第二份 ownership truth。

---

# 2. Boot / ExecutionEpoch

```bash
python tools/uos.py boot
```

当前关键控制面变更需要确认 `.uos/EXECUTION_CONTRACT.yaml` 中的 `ExecutionEpoch`：

```bash
python tools/uos.py \
  --ack-execution-epoch <CURRENT_EPOCH> \
  <command> ...
```

Epoch 不匹配时 fail closed，要求重新 Boot。旧 Agent / 旧聊天上下文不能继续用旧执行语义产生新的 canonical mutation。

---

# 3. Transport

`tools/uos.py`：

```text
auto      默认
git-cas   latest-canonical Git transaction
local     单工作树 / 测试模式
```

`auto`：

```text
无 Git remote       → local
有 canonical remote → git-cas
remote 已配置但不可达 → fail closed
```

不会因网络失败偷偷退回 local ownership。

---

# 4. Project / Task / WorkRoot

创建项目：

```bash
python tools/uos.py \
  --ack-execution-epoch <EPOCH> \
  project init \
  --project-id DEMO \
  --title "Demo project"
```

发布任务：

```bash
python tools/uos.py \
  --ack-execution-epoch <EPOCH> \
  task publish \
  --project DEMO \
  --task-id TASK_DEMO_01 \
  --title "Build demo" \
  --output projects/DEMO/result.md \
  --acceptance "result exists and passes review"
```

Task output 必须位于项目 WorkRoot。发布 Task 只表示工作存在：

```text
Task publication ≠ ownership
```

---

# 5. READY Work Market / Agent Matching

Reconcile 派生：

```text
coordination/runtime/WORK_MARKET.csv
```

它只包含 READY 工作。

可选匹配器：

```text
tools/agent_matching.py
```

匹配维度包括：

- Capability Tier；
- Tools；
- Context Class：`XS < S < M < L < XL`；
- optional Allowed Roles。

匹配只决定“适合领取什么”，不决定 ownership：

```text
Market / match ≠ ownership
```

---

# 6. Broker V2 Claim ownership

直接领取：

```bash
python tools/uos.py \
  --ack-execution-epoch <EPOCH> \
  claim \
  --agent-id AGENT_001 \
  --project DEMO
```

当前 ownership 锚点：

```text
immutable Claim Request
        ↓
immutable Claim Grant
        ↓
active Claim Lock
```

Authority：

```text
UOS_CLAIM_BROKER_V2
```

成功 Claim 返回：

- CanonicalID；
- AgentID；
- LeaseGeneration；
- LeaseToken；
- LeaseExpiresAt；
- FencingToken；
- RequestID / GrantID；
- Inputs / Output / Acceptance。

RECLAIM 使用精确 predecessor provenance，并令：

```text
LeaseGeneration = previous + 1
```

旧 owner、旧 token、过期 Lease、旧 generation candidate 都必须被 fencing。

---

# 7. High-contention exact Claim

通用入口：

```text
tools/high_contention_claim.py
```

它在进入 canonical transaction 之前执行 read-only latest-main preflight、compatibility check、active-lock rejection 和 bounded jitter，减少 burst contention 的无效 main 写入。

5 / 10 / 30 Agent 独立 Clone 的高并发 Claim 回归已覆盖 Request + Grant + Lock + telemetry 四类锚点。

---

# 8. Work Session V2

Tool：

```text
tools/work_session.py
```

Session 是 continuation guard，不是第二个 scheduler。

开始：

```bash
python tools/work_session.py \
  --ack-execution-epoch <EPOCH> \
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

继续：

```bash
python tools/work_session.py \
  --ack-execution-epoch <EPOCH> \
  next \
  --agent-id AGENT_001 \
  --session-id <SESSION_ID>
```

只有当前 Task 已满足：

```text
canonical .done
+ durability = DURABLE_READY
+ quality/review gate released
```

才允许 unrelated next Claim。

关键返回：

```text
CLAIM_GRANTED
WORK_CURRENT_TASK
CURRENT_TASK_RECLAIMED
WAITING_INTEGRATION
OWNERSHIP_LOST
RECOVERY_REQUIRED
STOP_REVIEW_PENDING
REWORK_REQUIRED
STOP_DURABILITY_PENDING
STOP_NO_MATCH
SESSION_STOPPED
```

### stale current Lease

Session 只允许重新 Claim **同一个 current task**。成功后返回新的 Generation/LeaseToken；失败则明确 ownership loss，绝不偷偷切换到别的 Task。

### WAITING_INTEGRATION

如果 current Task 的合法 Completion 已经持久化到 Outbox，Session 会按**当前 canonical GrantID**精确检查对应 ref，并返回：

```text
WAITING_INTEGRATION
```

此时不要重复修改/Complete；先运行机械 ingest。旧 Generation 的保留 Outbox ref 不会阻塞新 Generation owner。

---

# 9. Partial Handoff

```text
tools/partial_handoff.py
tools/handoff_takeover.py
```

核心不变量：

```text
Handoff ≠ Done
Handoff ≠ ownership transfer
Handoff ≠ Acceptance PASS
```

`HANDOFF_READY` 可以持久化恢复证据并让 Lease 进入可 reclaim 状态。后继 Agent 仍必须通过正常 Broker Claim 获得新的 Generation/Token，再读取并重新验证 partial work。

---

# 10. Complete / Durability

```bash
python tools/uos.py \
  --ack-execution-epoch <EPOCH> \
  complete \
  --agent-id AGENT_001 \
  --task TASK_DEMO_01 \
  --lease-token <TOKEN>
```

Direct fast path 重新验证 owner/token/fencing、WorkRoot、声明 outputs 和 preview contract。

canonical 完成事实包括：

```text
业务 outputs / previews
+ coordination/quality/durability/<TASK>.json
+ coordination/completed/<TASK>.done
- coordination/claims/<TASK>.lock
```

因此：

```text
Preview visible
≠ Operator accepted
≠ Artifact durably canonical
≠ Task canonical Done
```

---

# 11. Completion Outbox / Integration Lane

这是 Phase 6 的写竞争治理能力：

```text
tools/completion_outbox.py
python tools/uos.py outbox status
python tools/uos.py outbox ingest
```

它**不改变 Claim ownership**。

只有一个已通过全部本地 Complete 校验的 candidate，在 bounded direct-main 尝试最终失败原因纯粹是 main ref race 时，才允许：

```text
validated completion
→ non-canonical uos-outbox/* ref
→ mechanical ingest
→ latest-main revalidation
→ canonical batch commit
```

核心约束：

```text
Outbox != ownership
Outbox != Done
Claim / Renew never use Outbox
non-race Complete errors never become staged success
old-generation candidate fails after RECLAIM
path/read-set conflict fails closed
```

2 / 5 / 10 / 30 个独立 Completion candidate 的 batch acceptance 均已通过；每批可以用一个 canonical main commit 完成 Integration。

---

# 12. Quality / Preview Gate

当前质量规则由：

```text
.uos/QUALITY_VISIBILITY_POLICY.yaml
tools/quality_gate.py
```

控制。

已知预览伴随交付：

```text
SVG         → SVG + PNG
HTML        → HTML + preview PNG
PDF         → PDF + preview PNG
PPT/DOC/XLS → source + preview PDF
CAD/EDA     → source + preview PNG
```

Pending / Rejected review 会阻止 unrelated next Claim。Agent 应直接在对话中展示结果和预览，而不是让 Operator 日常去 GitHub 自行寻找。

---

# 13. Observability

```text
tools/claim_telemetry.py
tools/claim_observability.py
.github/workflows/uos-claim-observability.yml
```

当前统一 snapshot 包括：

- Request / Grant / active Lock；
- CREATE / RECLAIM / max LeaseGeneration；
- Grant throughput；
- winning CAS attempt / latency / contention；
- Work Session metrics；
- Outbox valid queue depth；
- canonical receipt count；
- retained ingested / invalid-fenced refs；
- batch-size p50/p95/max；
- integration-wait p50/p95/max。

Outbox refs 会保留为 audit/recovery evidence：

```text
remote_refs_total ≠ queue depth
valid_queue_depth = 当前可机械 ingest 的 candidate 数
canonical receipts = 已完成 Integration 的 authoritative count
```

观测 workflow 同时按 relevant main change 和 hourly schedule 运行，因此“只有非-main Outbox ref 新增”的待处理队列也能被定期看到。

---

# 14. Git-CAS 实现原则

`tools/canonical_runner.py`：

```text
fetch latest main
→ detached worktree
→ run whole business command
→ candidate tree
→ non-force push
→ ref race: discard candidate
→ fetch newer main
→ rerun whole command
```

禁止把 stale derived state 只做 re-parent。

`tools/canonical_publish.py` 提供底层 expected-blob / require-absent / no-clobber / non-force CAS primitive；普通 Agent 不应绕过高层 lifecycle 直接构造 ownership state。

---

# 15. 自检

```bash
python tools/selftest.py
```

它自动发现：

```text
tests/test_*.py
```

当前回归覆盖 local + multi-clone lifecycle、Broker V2、Request/Grant integrity、RECLAIM/fencing、high contention、Work Session V2、Partial Handoff、quality visibility、durability、Completion Outbox fallback/batch、`WAITING_INTEGRATION` 和 observability。

永久验收门为：

```text
.github/workflows/uos-selftest.yml
```

2026-09-03，清理完所有临时 candidate harness 后的 Kernel/runtime tree `c009f7d2d92b02f1e3f6bdcd05cec0a09fe405fa` 被 GitHub Actions fresh checkout 精确检出并执行完整 `python tools/selftest.py`。Actions run `33724704449` 最终 **68 / 68 tests PASS**。因此此前“exact-current fresh-checkout 仍缺执行证据”的 blocker 已关闭。

后续仅修改 README / 状态文档的 docs-only commit 不改变上述已验证 Kernel/runtime tree。

---

# 16. AI_book delta closure

2026-09-03 本次声明的 Claim / Concurrency 六项差距均已闭合：

```text
Phase 1  high-contention ingress                    ✅
Phase 2  Request / Grant + Broker V2               ✅
Phase 3  exact reclaim provenance / integrity      ✅
Phase 4  contention + fencing acceptance           ✅
Phase 5  Work Session V2 + telemetry               ✅
Phase 6  Completion Outbox + batch Integration     ✅
Closeout WAITING_INTEGRATION + Outbox observability ✅
```

这只表示 `docs/AI_BOOK_CLAIM_DELTA_SYNC_20260903.md` 中声明的这组六项差距已同步，不表示完整 AI_book parity。

明确没有复制：

- AI_book task/project history；
- AI_book Requests / Grants / Locks / Done runtime；
- AI_book domain data；
- AI_book scheduler authority；
- cross-repository routing。

---

# 17. 当前边界 / 后续仅按需求启用

```text
Single-repository UOS lifecycle             ✅ EXACT-CURRENT SELFTESTED
Broker V2 ownership                         ✅
Work Session V2                             ✅
Completion Outbox / batch Integration       ✅
Provider-neutral observability              ✅
Generic scarce-resource admission           ⏳ NEED-DRIVEN
Adaptive GitHub write/API governor          ⏳ NEED-DRIVEN
Outbox ref archive / GC                     ⏳ NEED-DRIVEN
Multi-repository routing                    ❌ requires operator decision
AI_book dispatch                            ❌ forbidden in current phase
```

---

# 18. 设计原则

1. Durable state lives in files/Git, not chat memory.
2. Git is the canonical arbiter; Python is the executor; CI is optional infrastructure.
3. Publication, Market, matching, Session, Handoff and Outbox are not ownership.
4. Ownership means current canonical Grant + matching active Lock + current Lease/Fencing.
5. Outbox is work-plane persistence; only canonical `.done` is completion.
6. Agents may disappear; Lease/Fencing/recovery must fail closed and recover safely.
7. Ref race means recompute from latest canonical truth, never force stale decisions.
8. Review, preview, durability and completion are distinct facts.
9. Project outputs stay inside WorkRoot authority.
10. Session deadline limits new Claims; it does not abandon current ownership.
11. Kernel stays domain-neutral; production lessons may be backported only as generic mechanisms.
12. Prove one-repository operation before multi-repository orchestration.

## License

Apache-2.0. Do not copy AI_book private project content, credentials, secrets or runtime history into this public repository.
