# TRAVEL_GUIDE Agent Claim Guide

## Current warning

Until the dependency/warmup recovery is applied, the Work Market exposes only the intake task as the first canonical READY task. Public research Agents may therefore see `NO_COMPATIBLE_READY_TASK` or a serialized review block.

## Execution epoch

Current required acknowledgement:

```text
UOS_EXEC_20260902_01
```

## Why the default claim command fails

`agent_matching.py` defaults to capability tier 1, no declared tools, and context S. The current intake requires tier 3, web, context M.

Do not launch a research Agent with the default envelope.

## Compatible public research envelope

Use at least:

```bash
python tools/agent_matching.py \
  --ack-execution-epoch UOS_EXEC_20260902_01 \
  claim \
  --agent-id <AGENT_ID> \
  --capability-tier 4 \
  --tools web \
  --context L \
  --project TRAVEL_GUIDE
```

For work requiring local analysis/rendering:

```text
--tools web;python
```

For map rendering:

```text
--tools web;image_gen
```

## Recommended Agent IDs after recovery

- `AG_TRAVEL_TRANSIT_MAP`
- `AG_TRAVEL_CULTURE_REVIEWS`
- `AG_TRAVEL_FOOD_DATA`
- `AG_TRAVEL_FIELD_BOOK`
- `AG_TRAVEL_PRIVATE_PLAN`
- `AG_TRAVEL_REVIEW`

## Private Agent rule

Private Agents must not receive private context through repository plaintext. They require the encryption key out-of-repository and decrypt only transiently.

## Expected healthy behavior

After the recovery patch and 26-task expansion are canonicalized, several public research/book tasks should appear in the READY Work Market at the same time. Public Agents should then claim separate tasks through normal Claim/Lease/Fencing rather than sharing a task or editing the same output.
