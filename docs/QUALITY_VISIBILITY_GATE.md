# Quality Visibility Gate — 成果可见性、预览与分阶段确认

Status: `ACTIVE`  
Policy anchor: `.uos/QUALITY_VISIBILITY_POLICY.yaml`  
Runtime helper: `tools/quality_gate.py`

## 1. 目的

UOS 不应出现这种工作方式：

```text
Agent 连续完成很多任务
        ↓
只写 GitHub / Done
        ↓
用户没有直接看到成果
        ↓
项目后期才发现方向或格式错误
        ↓
大批返工
```

正确方式是：

```text
任务完成
  ↓
生成源成果 + 快速预览
  ↓
Agent 在对话里直接呈现摘要和预览
  ↓
规则刚变更时前三项强制确认
  ↓
确认正确后继续
  ↓
稳定阶段按确定性比例抽检
```

用户不应为了日常验收被要求自己进入 GitHub 仓库逐个寻找成果。

## 2. RuleEpoch

`.uos/QUALITY_VISIBILITY_POLICY.yaml` 中的 `RuleEpoch` 表示当前质量/预览规则代次。

当以下内容发生实质变化时，必须 `RuleEpoch + 1`：

- 任务完成定义；
- 成果预览要求；
- 用户确认方式；
- 抽检比例；
- 关键质量规则；
- 会明显改变 Agent 工作方式的新约束。

每个新 RuleEpoch 都重新进入“前三项强制确认”阶段，避免新规则刚上线就让几十个任务一起跑偏。

## 3. Review Gate

当前默认：

```text
第 1 个完成任务  → 强制用户确认
第 2 个完成任务  → 强制用户确认
第 3 个完成任务  → 强制用户确认
第 4 个完成任务  → 正常放行
第 5 个完成任务  → 抽检
第 10 个          → 抽检
第 15 个          → 抽检
...
```

即：

- `WarmupRequired = 3`
- `SampleEvery = 5`
- 默认抽检约 20%
- `risk_tier=HIGH` 可始终强制确认

抽检不是 Agent 自己随机决定，而是按 canonical completion sequence 确定，确保多个 Agent 得到同一个判断。

## 4. 待确认时必须暂停后续 Claim

当一个质量事件进入 `PENDING`：

```text
当前任务成果 canonical 完成
        ↓
生成 quality event
        ↓
REVIEW_PENDING
        ↓
新的 Claim 被暂停
        ↓
Agent 把成果直接展示给用户
        ↓
用户 Accept / Reject
```

这一步的目的就是防止“用户还没看到第 1 个新规则成果，Agent 已经照同一错误模式完成了后面 20 个任务”。

查看当前待确认：

```bash
python tools/quality_gate.py status
```

## 5. Agent 的对话呈现义务

任务完成后，Agent 不能只回复：

```text
已完成，文件在 GitHub xxx/path
```

而应直接在对话里提供：

1. 一句话成果结论；
2. 2–5 条关键变化；
3. 主要输出文件；
4. 可视成果的直接预览/附件/截图；
5. 如果进入 Review Gate，明确告诉用户“这是本轮第 N 个强制确认/抽检成果”；
6. 等用户确认后再继续领取后续任务。

Routine inspection 不应要求用户自己进入仓库寻找文件。

## 6. Preview Gate

编辑源文件和用户方便查看的预览文件是两个不同目的。UOS 要求重要的非直接可视源文件同时产生快速预览。

### 当前默认映射

| 源成果 | 必需预览 |
|---|---|
| `figure.svg` | `figure.png` |
| `page.html` | `page.preview.png` |
| `report.pdf` | `report.preview.png` |
| `deck.pptx` / `.ppt` | `deck.preview.pdf` |
| `doc.docx` / `.doc` | `doc.preview.pdf` |
| `table.xlsx` / `.xls` | `table.preview.pdf` |
| STEP / IGES / DXF / DWG / AEDT / KiCad / PCB / CAD | `*.preview.png` |

PNG/JPG 等本身已经是快速可视成果时不强制重复生成另一份图片。

纯 Markdown、TXT、JSON、CSV、源代码等文本型成果通常用“对话摘要 + 关键片段/表格”即可，不机械生成无价值截图。

## 7. Task Publish 自动补齐预览输出

质量策略启用时：

```bash
python tools/uos.py task publish \
  --output projects/DEMO/figure.svg
```

canonical Task Catalog 会保存为：

```text
projects/DEMO/figure.svg;projects/DEMO/figure.png
```

因此 Claim 到任务的 Agent 会从一开始就知道自己必须同时交付源 SVG 与 PNG，而不是完成后才临时追加一个“生成预览”的补丁任务。

## 8. Complete 时机械检查

如果任务需要预览但 Agent 没有生成：

```text
PREVIEW_OR_OUTPUT_MISSING
```

Completion transaction 不会进入 canonical main。

例如只生成：

```text
figure.svg
```

但没有：

```text
figure.png
```

则任务不能 Complete。

## 9. Accept

用户确认成果没问题后：

```bash
python tools/quality_gate.py review accept \
  --task TASK_X \
  --by OPERATOR
```

质量事件转为 `ACCEPTED`，后续 Claim 恢复。

在聊天 Agent 工作流中，这条命令应由 Agent 在得到用户明确/无歧义确认后执行，不要求用户自己进终端或 GitHub 操作。

## 10. Reject / 原任务返工

用户发现方向、效果、版式或内容不对时：

```bash
python tools/quality_gate.py review reject \
  --task TASK_X \
  --by OPERATOR \
  --feedback "具体问题"
```

UOS 会：

1. 保留质量事件与用户反馈；
2. 将事件标记为 `REJECTED`；
3. 撤销该任务的 canonical `.done`；
4. 暂停无关后续 Claim；
5. 只允许显式重新 Claim 原任务进行修正；
6. 修正完成后再次进入 `PENDING`，必须重新确认。

因此不需要等整个项目做完后才另外创建大量返工任务。

## 11. 规则变更后的预期节奏

推荐节奏：

```text
规则 V1 生效
  ↓
任务 1 → 展示 → 用户确认
  ↓
任务 2 → 展示 → 用户确认
  ↓
任务 3 → 展示 → 用户确认
  ↓
证明 Agent 理解新规则
  ↓
任务 4 正常
  ↓
任务 5 抽检
  ↓
继续运行 + 周期抽检
```

如果前三项中的任何一项被 Reject，应先完成返工并重新确认，再继续推进。

## 12. 与 Git-CAS 的关系

Review/Preview Gate 不创建第二套调度真相。

质量事件位于：

```text
coordination/quality/events/
```

它们与 Project/Task/Claim/Done 一样通过 latest-canonical Git transaction 发布。

ref race 时整个 UOS command 会基于新 main 重跑，因此“这是第几个完成任务、是否应该抽检”也会从最新 canonical events 重新计算。

## 13. 当前边界

这仍然是 `ZXYHtech/UOS` 的单仓质量机制：

- 不调度 AI_book；
- 不启用跨仓项目；
- 不依赖 GitHub Actions；
- 不把 UI 展示责任推给用户；
- 不把生成预览文件等价成“已通过人工质量判断”。

Preview 解决“方便看”，Review 解决“看了以后确认方向对”。两者不能互相替代。
