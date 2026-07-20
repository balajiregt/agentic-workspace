# Local Agent Runtime

This workspace keeps one validated local Pi editing model with three budget
profiles.

## Working Model

```text
unsloth/gemma-4-E2B-it-qat-GGUF:UD-Q4_K_XL
```

Default profile:

```text
contextWindow: 4096
maxTokens: 1536
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

If Pi reaches the output-token limit during edit loops, use the long profile:

```bash
npm run setup:tool-agent-long
npm run agent:tool-agent-long
```

Long profile:

```text
contextWindow: 8192
maxTokens: 4096
```

If `25000/25000` works on your machine, keep it explicit:

```bash
npm run setup:tool-agent-25k
npm run agent:tool-agent-25k
```

Treat the 25k profile as experimental. It is useful when the model keeps
running on your machine, but it is not the default because it can create high
memory pressure and very long turns.

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

`local-agents/run-agent.sh` starts llama.cpp with the selected profile's
context window and:

```text
--parallel 1 --metrics --tools all
```

The Pi output-token budget comes from `local-agents/config/model-profiles.json`.
For a one-run override:

```bash
AGENTIC_MAX_TOKENS=2048 npm run agent:tool-agent
```

It starts Pi from the workspace root and loads:

```text
AGENTS.md
contexts/current/service-context.yml
contexts/current/resolved-context.yml
skills/microservice-change/SKILL.md
docs/prompts/
```

Regenerate the resolved context after changing the current task YAML:

```bash
npm run context:resolve
```

The current task YAML should stay small. Stable service facts live in
the repo layout, OpenAPI, and service code; exact paths and commands are
generated into `contexts/current/resolved-context.yml`.

The prompt templates include a QA gap analysis flow. Use it when a test expects
behavior that may not exist yet, such as a new negative test expecting `4xx`
for an input that still satisfies the current OpenAPI schema. The agent should
report whether this is supported by service code and OpenAPI, a test bug, or a
product/contract gap. It should not delete the test just to make the suite pass.

## Prompt

Use the project prompt template inside Pi:

```text
/existing-test-assertion <field or response assertion for the affected endpoint>
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
