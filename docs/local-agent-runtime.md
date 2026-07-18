# Local Agent Runtime

This workspace keeps one validated local Pi editing profile.

## Working Model

```text
unsloth/gemma-4-E2B-it-qat-GGUF:UD-Q4_K_XL
```

Profile:

```text
contextWindow: 4096
maxTokens: 1024
parallel slots: 1
llama.cpp tools: all
```

This model passed the tool-call gate:

```text
TOOL_CALL_CHECK=PASS structured tool_calls returned: read
```

## Setup

```bash
npm run setup:tool-agent
npm run agent:tool-agent
```

For convenience, the 8 GB aliases point to the same working profile:

```bash
npm run setup:8gb
npm run agent:8gb
```

## Validation Gate

Run this only after the agent terminal shows llama.cpp is listening on port
`8080`:

```bash
npm run agent:doctor
```

Proceed with Pi edits only when it prints:

```text
TOOL_CALL_CHECK=PASS
```

## Runtime Behavior

`local-agents/run-agent.sh` starts llama.cpp with:

```text
--ctx-size 4096 --parallel 1 --metrics --tools all
```

It starts Pi from the workspace root and loads:

```text
AGENTS.md
contexts/current/service-context.yml
skills/microservice-change/SKILL.md
docs/prompts/
```

## Prompt

Use the project prompt template inside Pi:

```text
/existing-test-assertion riskCategory is not empty for the customer risk response
```

## Metrics

Optional dashboard:

```bash
npm run metrics:8gb
open http://localhost:8765
```

## Cleanup

If port `8080` is occupied by an old model server:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
kill <PID>
```
