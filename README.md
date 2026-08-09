# Agentic Workspace

This repository is a portable agentic workspace pattern for QA/API and UI
automation. It helps coding agents add or modify API tests, inspect OpenAPI and
service behavior, reuse shared test utilities, route Playwright UI work, and
report product/contract gaps instead of blindly forcing tests to pass.

The included runtime validates the workflow with local agents on a small
machine, but the same context, skill, and verification pattern can be adopted by
cloud coding agents too. The repo does not vendor model binaries or llama.cpp
builds; it keeps the wrappers, context files, skills, validation projects, and
docs that an agent should use.

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
    ui-automation/    -> isolated Playwright UI automation projects
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

The launcher starts Pi from this workspace root by default so it can discover
`AGENTS.md`, `contexts/current/service-context.yml`, `skills/`, and sibling
service/QA/deployment folders before editing.

To intentionally run against another repo:

```bash
bash local-agents/run-agent.sh /path/to/your/service-repo
```

To watch token usage while llama.cpp and Pi are running, start the dashboard in
another terminal:

```bash
npm run metrics:8gb
open http://localhost:8764
```

It shows prompt tokens, output tokens, total tokens, configured context window,
configured max output tokens, active slot usage, model name, and raw token
metrics from llama.cpp.

The token metrics dashboard uses port `8764` so the QA intelligence dashboard
can own port `8765`.

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
Use the Jira context in contexts/current/service-context.yml.
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

For Playwright/UI automation tasks, agents should use the separate UI context:

```text
contexts/current/ui-context.yml
```

Then generate or read:

```bash
npm run context:ui:resolve
```

```text
contexts/current/resolved-ui-context.yml
```

This keeps RestAssured API automation and Playwright UI automation in one
workspace while preserving separate frameworks, dependencies, and verification
commands.

Current ticket context lives at:

```text
contexts/current/service-context.yml
```

Put only the current Jira ticket summary, scope, affected endpoints, and quality
gates there. Do not hand-maintain exact file paths, Maven commands, fixtures, or
response examples in the current task YAML. The resolver derives paths from the
repo layout and treats OpenAPI/service code as the behavior source. Repos under
`projects/` do not need to be modified just to use the local agent framework.

Examples live at:

```text
contexts/examples/service-context.microservice.yml
contexts/examples/service-context.service-owned-tests.yml
contexts/examples/service-context.monolithic.yml
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
cd projects/microservices/xyz-service
mvn spring-boot:run
```

Run the RestAssured API tests:

```bash
cd projects/microservices
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

## Playwright UI Automation Slice

The workspace also includes an isolated role-aware Playwright validation slice:

```text
projects/ui-automation/
  role-aware-mockserver/               -> Playwright tests, demo app, and Koa mockserver
```

Install and run it without adding Node dependencies to the workspace root:

```bash
npm --prefix projects/ui-automation/role-aware-mockserver install
npx --prefix projects/ui-automation/role-aware-mockserver playwright install chromium
npm run ui:test
```

Focused UI runs:

```bash
npm run ui:test:roles
npm run ui:test:legacy-interception
```

Agents should follow:

```text
skills/playwright-ui-change/SKILL.md
```

for Playwright, browser-flow, role-aware mockserver, or UI automation changes.

## Graph-Based Test Intelligence

The workspace uses a lightweight built-in graph for deterministic API/UI test
routing:

```bash
npm run graph:build
npm run graph:serve -- --port 8766
```

This generates an ignored local viewer under:

```text
artifacts/test-graph/
```

The built-in graph is intentionally small. It reads the resolved API and UI
contexts and shows relationships such as:

```text
endpoint -> controller -> service -> OpenAPI -> RestAssured test
UI flow -> Playwright spec -> helper -> mockserver route -> role
```

Use it for impact analysis and verification planning: "which tests and commands
are related to this ticket?"

Duplicate prevention remains instruction-first. Agents must inspect resolved
tests and classify coverage as already covered, missing assertion, new
scenario, or product/mockserver gap before creating another test. Similarity
tools can provide signals later, but they should not replace that decision
rule.

Graphify is a good optional exploration layer for a broader workspace knowledge
graph across code, docs, configs, OpenAPI, and skills. Treat Graphify output as
supporting context for broad questions, not as the source of truth for test
routing. If used locally, keep its generated output ignored and separate from
the built-in test graph.

Run Graphify locally without a global install:

```bash
npm run graphify:build
npm run graphify:serve -- --port 8767
```

Launch both graph views together:

```bash
npm run graphs:serve
```

Build or serve only the dashboard:

```bash
npm run dashboard:build
npm run dashboard:negative
npm run dashboard:serve -- --port 8765
```

`dashboard:negative` creates a separate synthetic artifact under
`artifacts/qa-dashboard-negative/` for validating how failure, gap, duplicate,
and stale-graph states are displayed before merging dashboard changes.

Run the graph views in a container for non-IDE stakeholders:

```bash
npm run graphs:docker:build
npm run graphs:docker:up
```

Docker Desktop or another Docker daemon must be running before using the
container commands.

Default URLs:

```text
QA dashboard:      http://127.0.0.1:8765/
Test-impact graph: http://127.0.0.1:8766/
Graphify graph:    http://127.0.0.1:8767/graph.html
```

In real ticket work, the agent should use the graph layer as supporting
evidence, not as a replacement for resolved context:

```text
ticket/context -> resolved API/UI context -> duplicate coverage check
  -> built-in graph for impacted tests/commands
  -> optional Graphify for broad repo exploration
  -> edit only the needed test/assertion/gap report
  -> run focused verification
```

The QA dashboard is a lightweight static view for non-IDE stakeholders and
agents. It uses CSS-only bars and stacked strips, with no charting dependency.
It summarizes impacted API/UI tests, pass/fail status from available test
reports, graph node counts, stale graph status, release confidence,
changed-file based test recommendations, deterministic coverage gaps,
duplicate/overlap candidates, duplicate-prevention evidence from the loop log,
test mix, quality signals, and runtime usage readiness.

For larger suites, the dashboard keeps high-volume sections bounded by default.
Tables render the top 10 rows first, include a local search box, show current
match counts, and provide a lightweight Show all toggle. This keeps the first
screen readable even when the workspace grows to hundreds of API and
Playwright tests.

Runtime usage metrics are optional. If an export is present at
`artifacts/usage-metrics/usage.json`, the dashboard can correlate the active
endpoint and UI flow with real-world usage. Without that export, it shows the
inputs still needed: API gateway/service counts by endpoint, UI analytics by
flow and role, and production-like error counts.

### Static QA Metrics Viewer

The workspace also includes a lightweight browser-only artifact viewer:

```bash
npm run viewer:dev
```

Open:

```text
http://127.0.0.1:8790
```

The viewer is designed for a free/static Netlify deployment. Business users can
open the URL and upload generated artifacts such as:

```text
artifacts/qa-dashboard/dashboard.json
artifacts/qa-dashboard-negative/dashboard.json
artifacts/test-graph/test-graph.json
graphify-out/graph.json
```

Files are parsed locally in the browser. There is no backend upload, no
database, and no artifact storage. The viewer also supports sandboxed preview
of generated HTML files such as dashboard `index.html` and Graphify
`graph.html`.

Netlify settings for a new project:

```text
Base directory: projects/qa-dashboard-viewer
Build command: npm run build
Publish directory: .
```

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
