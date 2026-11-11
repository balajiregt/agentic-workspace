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
  knowledge/docs/agent-workflow/LOOP.md             -> human-started agent workflow loop
  knowledge/docs/agent-workflow/STATE.md            -> current validation-slice state
  knowledge/docs/agent-workflow/loop-budget.md      -> RAM/context/output token budgets
  agent-system/local-agents/       -> lightweight setup/run wrappers for local models
  knowledge/docs/               -> cross-project guides, research and workflow diagrams
  agent-system/skills/             -> reusable agent instructions and owned templates
    microservice-change/examples/ -> service topology context examples
  products/
    finance/finfolio-app/, finance/finfolio-agent/ -> FinFolio tracker and alerting agent
    career/career-agent/ -> career scouting agent
    agent-tools/agent-dashboard/ -> agent activity observer
    portfolio/portfolio-web/ -> public portfolio site
    portfolio/portfolio-template/ -> public MIT portfolio template (fictional content)
  services/
    microservices/    -> Spring Boot, RestAssured, local AGENTS/docs/contexts
  qa/
    playwright-agent/ -> local context/docs and internal quality/
    ui-automation/role-aware-mockserver/ -> local context/docs and app/backend/UI tests
    playwright-template/ -> Playwright starter
  labs/
    kafka-test-project/ -> Kafka and event-quality lab
  evaluation/         -> shared controlled trials and evidence collection
  tooling/scripts/            -> context efficiency utilities
```

See [the folder map](workspace-map.md) for the complete current category hierarchy and the 10 November 2026 migration table.
Use [the project workflow](project-workflow.md) to select the owning project,
task context, checks and evidence before making a change.

## Local Agent Setup

This repo includes a lightweight `agent-system/local-agents/` folder. For an 8 GB MacBook
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

The launcher starts Pi in the selected owning project: API defaults to
`services/microservices`, UI to the role-aware mockserver, and
`npm run agent:tool-agent:playwright` to Playwright Agent. It supplies root
routing plus local `AGENTS.md`. Select the task explicitly through
`AGENTIC_TASK_CONTEXT` or the request; it does not assume an example task.
Shared skills route changes across owners without a workspace-wide current
work item.

To intentionally run against another repo:

```bash
bash agent-system/local-agents/run-agent.sh /path/to/your/service-repo
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

Prompt the agent with the selected project's task context. This is a sanitized
API example; replace it with the actual work item:

```text
Use the Jira context in services/microservices/contexts/tasks/ABC-123.yml.
Follow repository_topology before deciding where tests or deployment changes belong.
Update service code, OpenAPI, tests, and deployment impact only as required by the context.
```

For existing-test edits, use a direct prompt like:

```text
For the existing API test that covers the affected endpoint, add one assertion for <field>.
Use services/microservices/AGENTS.md and the selected project task context before editing.
Do not create, rename, or append to unrelated test files.
```

More detail lives at:

```text
knowledge/docs/local-agent-runtime.md
agent-system/local-agents/README.md
agent-system/local-agents/config/model-profiles.json
agent-system/local-agents/setup.sh
agent-system/local-agents/run-agent.sh
```

## Project-owned context

Root `AGENTS.md` routes work to a project. Read that project's `AGENTS.md` and
select its task before resolving context. The API and mockserver tasks below
are sanitized examples, not a shared current ticket:

```bash
npm run context:resolve -- --context services/microservices/contexts/tasks/ABC-123.yml
npm run context:ui:resolve -- --context qa/ui-automation/role-aware-mockserver/contexts/tasks/UI-ROLE-001.yml
```

The no-argument root commands resolve those examples for smoke checks. For real
work, provide the selected work item's path. Each resolver writes the matching
project-local `contexts/.resolved/<work-item>.yml`; read that output and use its
exact files and commands. Regenerate after task or relevant source changes.
Keep tasks and outputs distinct across concurrent work; do not reuse another
task's resolved file. `--output` can select a separate output when two sessions
work on the same task.

Task inputs contain scope, acceptance criteria, affected behaviour, topology
and gates. Stable paths, runtime commands and behaviour come from current
source, OpenAPI, configuration and repository layout. Do not maintain a second
contract or set of response examples in task YAML. New private requirements
and generated outputs remain ignored; the committed examples are sanitized.

Follow `repository_topology` before placing service, API test and deployment
changes. The local [microservices instructions](../../services/microservices/AGENTS.md)
and [mockserver instructions](../../qa/ui-automation/role-aware-mockserver/AGENTS.md)
also provide commands and source maps usable without workspace resolvers.

Playwright Agent uses its own [local instructions](<../../qa/playwright-agent/AGENTS.md>)
and existing `contexts/` maps, captures and selected requirements. Its
`quality/` evaluator and mutation runner belong to that product; do not route
Playwright Agent tasks through the mockserver's sample context.

Durable project explanations belong in each project's existing `docs/`.
Workspace `knowledge/` holds cross-project guidance, research, adoption records
and shared lessons. Local tests, `quality/` and `benchmarks/` retain their
existing owners; shared controlled comparisons remain under `evaluation/`.

Examples live at:

```text
agent-system/skills/microservice-change/examples/service-context.microservice.yml
agent-system/skills/microservice-change/examples/service-context.service-owned-tests.yml
agent-system/skills/microservice-change/examples/service-context.monolithic.yml
```

## Microservice Validation Slice

The workspace includes a concrete dummy service setup represented by the
sanitized split-QA microservice task example:

```text
services/microservices/
  xyz-service/                         -> Spring Boot dummy API
  xyz-deployments/                     -> deployment companion assets
  qa-steps/                            -> shared RestAssured utilities
  qa-projects/xyz-service-api-tests/   -> actual API tests
```

The same context format also supports the more common service-owned topology,
where endpoint code, OpenAPI, and API tests live in the service repo. See:

```text
agent-system/skills/microservice-change/examples/service-context.service-owned-tests.yml
```

Run the service:

```bash
cd services/microservices/xyz-service
mvn spring-boot:run
```

Run the RestAssured API tests:

```bash
cd services/microservices
mvn -pl qa-projects/xyz-service-api-tests -am test
```

## Loop Validation

The repo includes a small loop-engineering layer for proof-oriented local agent
runs:

```text
AGENTS.md
knowledge/docs/agent-workflow/LOOP.md
knowledge/docs/agent-workflow/STATE.md
knowledge/docs/agent-workflow/loop-budget.md
knowledge/docs/prompts/api-test-change-prompt.md
knowledge/docs/loop-run-log.md
```

Run a focused token report for an API test change:

```bash
npm run context:resolve
python3 tooling/scripts/context_efficiency_report.py --task-profile api-test-change
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
qa/ui-automation/
  role-aware-mockserver/               -> Playwright tests, demo app, and Koa mockserver
```

Install and run it without adding Node dependencies to the workspace root:

```bash
npm --prefix qa/ui-automation/role-aware-mockserver install
npx --prefix qa/ui-automation/role-aware-mockserver playwright install chromium
npm run ui:test
```

Focused UI runs:

```bash
npm run ui:test:roles
npm run ui:test:legacy-interception
```

Read the mockserver's local `AGENTS.md`, select its task, then follow:

```text
agent-system/skills/playwright-ui-change/SKILL.md
```

for mockserver-backed Playwright and browser-flow changes. The separate
Playwright Agent product follows its own local workflow and quality module.

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
  -> built-in graph for impacted tooling/tests/commands
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

### Inspect QA evidence

The standalone QA dashboard viewer was retired on 31 October 2026. Review
Playwright Agent reports from its internal quality tools, and use the Build with
Balaji project pages for published aggregate results. The old viewer's source and
local edits are retained in ignored `artifacts/product-retirement-20261031/qa-dashboard-viewer/`.
Its root launch aliases and active project registration have been removed.

## Agent Skills

Workspace-local skills use a compact Karpathy-style Markdown format:
frontmatter for routing, then short sections for goal, inputs, procedure,
quality gates, examples, and stop condition.

```text
agent-system/skills/microservice-change/SKILL.md
agent-system/skills/context-efficiency-audit/SKILL.md
knowledge/docs/karpathy-style-skill-format.md
knowledge/docs/agentic-workflow-diagrams.md
knowledge/docs/local-agent-runtime.md
```

## Controlled benchmark instrumentation

See [benchmark protocol and validation](../../evaluation/benchmarks/README.md) for reproducible synthetic tasks, measured evidence, missing metrics and claim limitations.

## Instagram engineering resource integration

The workspace now includes focused engineering skills and source references drawn from the reviewed saved posts. Existing API/UI routing, context resolvers, local runtimes, and Graphify setup remain the starting point.

Read [the adoption guide](instagram/README.md) for available skills and example prompts, [the resource catalogue](instagram/catalog.md) for every named topic from the initial screening, and [the source library](instagram/source-library.md) for pinned upstream references. Native skill entrypoints live in .agents/skills with canonical content under agent-system/skills/. Copilot, Claude Code, and Kilo receive workspace-level entry instructions.

Validate the integration with `python3 tooling/scripts/validate_agentic_skills.py`. This checks file integrity, discovery entrypoints, licenses, and local references; it does not claim that every editor agent has executed a skill successfully.
