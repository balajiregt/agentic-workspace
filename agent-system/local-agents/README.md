# Local Agents

This folder contains the local Pi + llama.cpp wrapper for the validated editing
model:

```text
unsloth/gemma-4-E2B-it-qat-GGUF:UD-Q4_K_XL
```

Run:

```bash
npm run setup:tool-agent
npm run agent:tool-agent
```

The default local-agent slice is API/RestAssured. To route the same local model
to UI automation/Playwright context instead:

```bash
npm run agent:tool-agent:ui
```

Explicit slice commands:

```bash
npm run agent:tool-agent:api
npm run agent:tool-agent:ui
```

For longer edit loops:

```bash
npm run setup:tool-agent-long
npm run agent:tool-agent-long
```

For explicit high-budget experiments:

```bash
npm run setup:tool-agent-25k
npm run agent:tool-agent-25k
```

The legacy 8 GB aliases point to the same profile:

```bash
npm run setup:8gb
npm run agent:8gb
```

Before trusting Pi edits:

```bash
npm run agent:doctor
```

Expected:

```text
TOOL_CALL_CHECK=PASS
```

If a local service already uses port `8080`, run the model and agent on another
port:

```bash
AGENTIC_LLAMA_PORT=8088 npm run agent:tool-agent:ui
python3 agent-system/local-agents/check-tool-calls.py --base-url http://localhost:8088/v1 --model local-model
```

Model files stay in the Hugging Face/llama.cpp cache, not in this repository.

## Project and task selection

API and UI slices now start in their owning microservices/mockserver projects by
default. `npm run agent:tool-agent:playwright` selects Playwright Agent and its
project skill. An explicit positional target directory still overrides the
default. Only root and selected project instructions are added.

No example work item is silently selected. For an API/mockserver task, set
`AGENTIC_TASK_CONTEXT` to its workspace-relative YAML path; the launcher resolves
it into that project's per-task ignored output before starting the agent. For
Playwright Agent, select requirements through its existing skill/CLI; an explicit
context path can be supplied as a reference without the mockserver resolver.
Read [the workflow](../../knowledge/docs/project-workflow.md) before launching.
