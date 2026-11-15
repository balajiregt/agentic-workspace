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

`agent-system/local-agents/run-agent.sh` starts llama.cpp with the selected profile's
context window and:

```text
--parallel 1 --metrics --tools all
```

The Pi output-token budget comes from `agent-system/local-agents/config/model-profiles.json`.
For a one-run override:

```bash
AGENTIC_MAX_TOKENS=2048 npm run agent:tool-agent
```

Pi starts in the selected owning project and receives root routing plus that
project's `AGENTS.md`, the matching skill and shared prompt templates. The API
slice is the default; it starts in `services/microservices`. The UI slice starts
in `qa/ui-automation/role-aware-mockserver`. The separate Playwright
Agent slice starts in `qa/playwright-agent` and uses its
own local workflow.

```bash
npm run agent:tool-agent:api
npm run agent:tool-agent:ui
npm run agent:tool-agent:playwright
npm run agent:tool-agent-long:ui
```

No task is selected automatically. Provide the work item in the request or set
`AGENTIC_TASK_CONTEXT` to an explicit YAML path. Relative paths are interpreted
from the workspace root. For example, to inspect the sanitized API example:

```bash
AGENTIC_TASK_CONTEXT=services/microservices/contexts/tasks/ABC-123.yml npm run agent:tool-agent:api
```

For UI, the sanitized example is
`qa/ui-automation/role-aware-mockserver/contexts/tasks/UI-ROLE-001.yml`.
Replace examples with the actual work item. API/UI launchers resolve an
explicitly supplied task and attach the selected input; the agent reads its
matching project `contexts/.resolved/<work-item>.yml`. The Playwright Agent
slice retains its own context handling rather than using the mockserver
resolver. See [the project workflow](project-workflow.md).

If a service already occupies port `8080`, keep that service running and use an
alternate llama.cpp port:

```bash
AGENTIC_LLAMA_PORT=8088 npm run agent:tool-agent:ui
python3 agent-system/local-agents/check-tool-calls.py --base-url http://localhost:8088/v1 --model local-model
```

Regenerate the matching resolved output after changing the selected task or
relevant source. From the workspace root, these commands resolve the sanitized
examples:

```bash
npm run context:resolve -- --context services/microservices/contexts/tasks/ABC-123.yml
npm run context:ui:resolve -- --context qa/ui-automation/role-aware-mockserver/contexts/tasks/UI-ROLE-001.yml
```

Use the actual task path for active work. Keep task YAML small: stable facts
live in source, OpenAPI, configuration and repository layout. Generated paths
and commands stay in the owning project's ignored `contexts/.resolved/`;
choose a separate `--output` for concurrent sessions on the same task.
Project-local instructions and native check commands remain usable outside the
workspace; shared resolvers and this launcher are optional conveniences.

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
open http://localhost:8764
```

This dashboard uses port `8764`; the QA intelligence dashboard uses port
`8765`.

## Cleanup

If port `8080` is occupied by an old model server:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
kill <PID>
```
