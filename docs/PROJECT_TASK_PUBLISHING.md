# Project & Task Publishing Target

## Goal

UOS must not only dispatch pre-existing tasks. A standalone installation should be able to create a project, publish tasks, change intent, and let Agents immediately discover and claim the new work.

Target operator flow:

```bash
python tools/uos.py project init --project-id DEMO --title "Demo project"
python tools/uos.py task publish --project DEMO --task-id TASK_DEMO_01 --title "First task" --role WORKER --priority 1 --output projects/DEMO/result.md --acceptance "result exists"
python tools/uos.py reconcile
```

The exact CLI may evolve, but the behavior must remain deterministic and file/Git-backed.

## Required objects

A project should minimally provide:

- ProjectID
- current IntentVersion
- title / goal
- lifecycle state
- task catalog
- project events / links when needed
- quality/compliance adapter references
- resource requirements when needed

A published task should minimally provide:

- Canonical Task ID
- ProjectID
- title / role
- priority
- dependencies
- status (`READY`, `BLOCKED`, etc.)
- inputs/context references
- output target
- write scope / exclusive keys when needed
- capability/context/tool requirements
- acceptance criteria
- compliance/quality profile

## Publishing invariant

Creating a task is not the same as assigning ownership.

```text
Task publish -> READY/BLOCKED catalog state
Agent request -> broker decision
Claim + Lock -> canonical ownership
```

A task publisher must never manufacture a Claim, LeaseToken or `.done` record.

## Visible-result / preview invariant

Task planning must include **how the operator will inspect the result**, not only the editable/source artifact.

When `.uos/QUALITY_VISIBILITY_POLICY.yaml` is enabled, canonical task publication automatically expands known source outputs into source + preview pairs.

Examples:

```text
figure.svg  -> figure.svg + figure.png
page.html   -> page.html + page.preview.png
deck.pptx   -> deck.pptx + deck.preview.pdf
doc.docx    -> doc.docx + doc.preview.pdf
model.step  -> model.step + model.preview.png
```

Therefore preview generation is part of the original task acceptance boundary. It must not normally become a separate cleanup task after the user discovers that the result is difficult to inspect.

`complete` will be rejected if a required preview companion is missing.

Full mapping and review behavior are defined in `docs/QUALITY_VISIBILITY_GATE.md`.

## Rule-change confirmation invariant

After a material quality/rule change, `RuleEpoch` must increment. The current default policy requires:

```text
completion 1 -> operator review
completion 2 -> operator review
completion 3 -> operator review
completion 4 -> normal
completion 5 -> sampled review
completion 10 -> sampled review
...
```

A pending review pauses new Claims. The Agent must show the result summary and previews directly in the conversation instead of instructing the user to browse GitHub.

If the operator rejects the result, UOS reopens the same task by removing its `.done`, keeps the feedback, blocks unrelated progress, and requires another review after correction.

## Self-hosting

`UOS_CORE` is the first standalone project. Its migration/evolution tasks are stored under `orchestration/projects/UOS_CORE/` so UOS can schedule its own development exactly as it schedules a normal same-repository project.
