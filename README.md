# Agentic Workspace

This repository is a portable workspace pattern for local coding-agent work. It
does not vendor model binaries or llama.cpp builds. Instead, it keeps the
runtime wrappers, context files, skills, validation projects, and docs that a
local agent should use.

```text
agentic-workspace/
  AGENTS.md           -> default repo instructions for coding agents
  LOOP.md             -> human-started agent workflow loop
  STATE.md            -> current validation-slice state
  loop-budget.md      -> RAM/context/output token budgets
  local-agents/       -> lightweight setup/run wrappers for local models
  contexts/
    current/          -> current Jira/service context used by the agent
    examples/         -> microservice and monolith context examples
  docs/               -> validation docs and workflow diagrams
  skills/             -> compact reusable agent instructions
  projects/
    microservices/    -> Spring Boot service/deployment repos
    monolithic/       -> monolithic application repos
  scripts/            -> context efficiency utilities
```

## Local Agent Setup

This repo includes a lightweight `local-agents/` folder. For an 8 GB MacBook
Air, it sets up `llama.cpp`, configures Pi, starts the model, and launches the
agent. It does not commit model files, llama.cpp builds, or `node_modules`.

The only validated local editing model is:

```text
unsloth/gemma-4-E2B-it-qat-GGUF:UD-Q4_K_XL
```

Run:

```bash
npm run setup:tool-agent
npm run agent:tool-agent
```

The 8 GB aliases point to the same working profile:

```bash
npm run setup:8gb
npm run agent:8gb
```

The first run downloads the GGUF model through `llama.cpp` and stores it in the
user-level Hugging Face/llama.cpp cache, not inside this repository.

The profile uses `contextWindow=4096`, `maxTokens=1536`, `--parallel 1`, and
`--tools all`.

If Pi reaches the output-token limit during edit loops, use the long profile:

```bash
npm run setup:tool-agent-long
npm run agent:tool-agent-long
```

That uses `contextWindow=8192` and `maxTokens=4096`. The repo also has an
explicit experimental 25k profile for machines that can tolerate it:

```bash
npm run setup:tool-agent-25k
npm run agent:tool-agent-25k
```

The launcher starts Pi from `/Users/balaji/agentic-workspace` by default so it
can discover `AGENTS.md`, `contexts/current/service-context.yml`, `skills/`,
and sibling service/QA/deployment folders before editing.

To intentionally run against another repo:

```bash
bash local-agents/run-agent.sh /path/to/your/service-repo
```

To watch token usage while llama.cpp and Pi are running, start the dashboard in
another terminal:

```bash
npm run metrics:8gb
open http://localhost:8765
```

It shows prompt tokens, output tokens, total tokens, configured context window,
configured max output tokens, active slot usage, model name, and raw token
metrics from llama.cpp.

Before trusting a local model for file edits, check whether the server returns
structured tool calls:

```bash
npm run agent:doctor
```

If this prints `TOOL_CALL_CHECK=FAIL`, the model may answer with JSON such as
`{"name":"edit",...}` instead of letting Pi execute the edit. The context setup
is still useful for token/routing experiments, but the selected model/server is
not yet a validated editing-agent profile.

If it prints `Connection refused`, wait for the agent terminal to show
`listening on http://127.0.0.1:8080`, then run the doctor again.

Prompt the agent with the central context file:

```text
Use the Jira context in /Users/balaji/agentic-workspace/contexts/current/service-context.yml.
Follow repository_topology before deciding where tests or deployment changes belong.
Update service code, OpenAPI, tests, and deployment impact only as required by the context.
```

For existing-test edits, use a direct prompt like:

```text
For the existing API test that covers the affected endpoint, add one assertion for <field>.
Use AGENTS.md and contexts/current/service-context.yml before editing.
Do not create, rename, or append to unrelated test files.
```

More detail lives at:

```text
docs/local-agent-runtime.md
local-agents/README.md
local-agents/config/model-profiles.json
local-agents/setup.sh
local-agents/run-agent.sh
```

## Central Context

`AGENTS.md` is the repo-level fallback. If a user forgets to say "read the
service YAML," the agent should still read the small current task context:

```text
contexts/current/service-context.yml
```

Then generate or read the resolved context:

```bash
npm run context:resolve
```

```text
contexts/current/resolved-context.yml
```

The split is intentional:

```text
service-context.yml          -> small ticket/task facts
OpenAPI + repo layout        -> stable service and contract facts
resolved-context.yml         -> generated exact paths and commands
```

Agents should follow `repository_topology` before deciding whether tests live
inside the service repo or in the split QA project.

Current ticket context lives at:

```text
/Users/balaji/agentic-workspace/contexts/current/service-context.yml
```

Put only the current Jira ticket summary, scope, affected endpoints, and quality
gates there. Do not hand-maintain exact file paths, Maven commands, fixtures, or
response examples in the current task YAML. The resolver derives paths from the
repo layout and treats OpenAPI/service code as the behavior source. Repos under
`projects/` do not need to be modified just to use the local agent framework.

Examples live at:

```text
/Users/balaji/agentic-workspace/contexts/examples/service-context.microservice.yml
/Users/balaji/agentic-workspace/contexts/examples/service-context.service-owned-tests.yml
/Users/balaji/agentic-workspace/contexts/examples/service-context.monolithic.yml
```

## Microservice Validation Slice

The workspace includes a concrete dummy service setup that mirrors the current
split-QA microservice context file:

```text
projects/microservices/
  xyz-service/                         -> Spring Boot dummy API
  xyz-deployments/                     -> deployment companion assets
  qa-steps/                            -> shared RestAssured utilities
  qa-projects/xyz-service-api-tests/   -> actual API tests
```

The same context format also supports the more common service-owned topology,
where endpoint code, OpenAPI, and API tests live in the service repo. See:

```text
contexts/examples/service-context.service-owned-tests.yml
```

Run the service:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices/xyz-service
mvn spring-boot:run
```

Run the RestAssured API tests:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices
mvn -pl qa-projects/xyz-service-api-tests -am test
```

## Loop Validation

The repo includes a small loop-engineering layer for proof-oriented local agent
runs:

```text
AGENTS.md
LOOP.md
STATE.md
loop-budget.md
docs/prompts/api-test-change-prompt.md
docs/loop-run-log.md
```

Run a focused token report for an API test change:

```bash
npm run context:resolve
python3 scripts/context_efficiency_report.py --task-profile api-test-change
```

Other task profiles:

```bash
npm run context:new-endpoint
npm run context:shared-qa
npm run context:walkthrough
```

The validation prompts exercise common API automation failures: finding the
right service-specific API test project, avoiding invented endpoints or files,
and reporting product/contract gaps when a negative test expects behavior not
implemented by source code or documented in OpenAPI.

## Agent Skills

Workspace-local skills use a compact Karpathy-style Markdown format:
frontmatter for routing, then short sections for goal, inputs, procedure,
quality gates, examples, and stop condition.

```text
skills/microservice-change/SKILL.md
skills/context-efficiency-audit/SKILL.md
docs/karpathy-style-skill-format.md
docs/agentic-workflow-diagrams.md
docs/local-agent-runtime.md
```
