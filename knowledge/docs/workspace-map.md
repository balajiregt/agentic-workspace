# Agentic workspace folder map

The workspace has seven category folders on disk. Applications and QA frameworks keep their existing paths; evaluation, agent support, knowledge and tooling live together in their own categories. This map describes the layout after the 31 October 2026 reorganisation.

## High level folder map

Every arrow below represents actual folder containment. These category names are real directories.

```mermaid
flowchart LR
  W["agentic-workspace/"] --> P["projects/<br/>Applications, services and labs"]
  W --> Q["qa-projects/<br/>QA frameworks and templates"]
  W --> E["evaluation/<br/>Cross-project trials and shared measurement"]
  W --> A["agent-system/<br/>Shared skills, context examples and local agents"]
  W --> K["knowledge/<br/>Cross-project guides and reference sources"]
  W --> T["tooling/<br/>Workspace scripts and their tests"]
  W --> O["artifacts/<br/>Generated reports, graphs and local tools"]
```

## Folder tree and responsibilities

```text
agentic-workspace/
├── projects/                              — applications, services and labs
│   ├── agent-dashboard/                   — Agenttrail Kitchen activity observer
│   ├── framework-benchmark-dashboard/     — Build with Balaji project showcase
│   ├── kafka-test-project/                — independent Kafka/event quality lab
│   ├── microservices/                     — Maven service and API automation
│   │   ├── AGENTS.md                      — local workflow and verification entrypoint
│   │   ├── contexts/                      — selected tasks and ignored .resolved/ outputs
│   │   ├── docs/                          — durable aggregate knowledge
│   │   ├── xyz-service/                   — Spring Boot source and OpenAPI
│   │   ├── qa-steps/                      — shared RestAssured helpers
│   │   ├── qa-projects/
│   │   │   └── xyz-service-api-tests/      — context-selected API tests
│   │   └── xyz-deployments/               — Compose and Kubernetes assets
├── qa-projects/                           — QA frameworks and templates
│   ├── Playwright Agentic Framework/      — Playwright Agent and internal quality/ tools
│   │   ├── contexts/                      — application maps, captures and private task inputs
│   │   └── docs/                          — durable project guidance
│   ├── playwright_pom_fixtures_modular_framework_template/
│   ├── ui-automation/
│   │   └── role-aware-mockserver/         — sole Git-backed UI app, mockserver and tests
│   │       ├── contexts/                  — selected tasks and ignored .resolved/ outputs
│   │       ├── docs/                      — architecture and security guidance
│   │       └── benchmarks/                — project-owned execution comparison
├── evaluation/
│   ├── benchmarks/                        — controlled trials and evidence collection
│   │   └── dashboard/                     — execution benchmark tooling
├── agent-system/
│   ├── contexts/                          — reusable examples and migration guidance
│   │   ├── current/                       — guidance; no active global task
│   │   ├── examples/                      — sample task contexts
│   │   └── services/                      — currently empty
│   ├── skills/                            — canonical task workflows
│   ├── local-agents/                      — Pi and llama.cpp setup and launchers
│   │   └── config/                        — local model profiles
│   └── context-starter/                   — symlink to an external directory
├── knowledge/
│   ├── docs/                              — cross-project guides, research and recorded evidence
│   │   ├── agent-workflow/                — loop instructions, state and budget
│   │   ├── assets/                        — saved diagram assets
│   │   ├── instagram/                     — resource adoption catalogue and provenance
│   │   └── prompts/                       — reusable task prompts
│   └── resources/
│       └── instagram-sources/             — passive upstream reference snapshots
├── tooling/
│   ├── docker/                            — graph-service Dockerfile and Compose
│   ├── scripts/                           — resolvers, graph builders and validation
│   └── tests/                             — checks for shared workspace tooling
└── artifacts/                             — ignored generated and local output
    ├── graphify-out/                      — graph output and cache
    ├── qa-dashboard/                      — generated QA dashboard
    ├── qa-dashboard-negative/             — synthetic negative dashboard examples
    ├── test-graph/                        — generated test relationships
    ├── tools/                             — downloaded tools and local environments
    └── workspace-reorganisation-2026-10-31/ — private migration records
```

This tree expands the category folders and principal project boundaries. Project-local dependencies, Java packages, browser reports and caches remain inside their owning projects.

## Root integration folders

Tools expect these dot-prefixed folders at the root. They sit alongside the seven categories and may be hidden by a file browser.

| Folder | Responsibility |
| --- | --- |
| `.agents/skills/` | Native discovery entrypoints pointing to canonical workflows in `agent-system/skills/`. |
| `.claude/` | Claude bridge; `skills` links to `.agents/skills/`. |
| `.kilo/rules/` | Kilo workspace instruction bridge. |
| `.github/` | Copilot instructions, dependency maintenance and CI workflows. |
| `.githooks/` | Local Git hook scripts; presence does not imply installation. |
| `.vscode/` | Editor tasks and settings. |
| `.idea/` | IDE metadata. |
| `.netlify/` | Local hosting metadata. |
| `.git/` | Root workspace version history. |

Root files include [AGENTS.md](../../AGENTS.md), [package.json](../../package.json), [workspace.projects.json](../../workspace.projects.json), the [VS Code workspace](../../agentic-workspace.code-workspace) and the one-click launchers.

Root instructions, npm/version settings, Git/security rules and launchers remain directly discoverable by their tools. Workflow documents are under [agent-workflow](agent-workflow/LOOP.md), graph-service Docker configuration is under `tooling/docker/`, and the saved [SVG](assets/workspace-diagram.svg) is a historical snapshot; the ownership map above reflects current active projects.

## How context connects to project code

```mermaid
flowchart TD
  U["User request"] --> R["AGENTS.md<br/>Routing and workspace rules"]
  R --> P["Choose project<br/>Read local AGENTS.md"]
  P --> C["Project contexts/tasks/<br/>Select one work item"]
  R --> S["agent-system/skills/<br/>Task workflow"]
  C --> X["tooling/scripts/<br/>Resolve exact project paths"]
  X --> D["Project contexts/.resolved/<br/>Task-specific generated file map"]
  D --> API["projects/microservices/<br/>Service, contract and RestAssured"]
  D --> UI["Role-aware mockserver<br/>App, backend and Playwright"]
  P --> PA["Playwright Agent local contexts<br/>Maps, captures and requirements"]
  S --> W["Inspect relevant files and make the change"]
  API --> W
  UI --> W
  PA --> W
  W --> V["Run applicable project checks"]
  V --> E["Ignored project reports and artifacts<br/>Retain verification evidence"]
  E --> K["Project docs/<br/>Promote reusable verified lessons"]
  K -.-> SH["Workspace knowledge/<br/>Cross-project lessons only"]
```

Resolved context identifies files and verification commands; it does not itself
run tests. Select the task explicitly; default root resolver commands use
sanitized examples. UI and API automation remain isolated. The API example
selects `projects/microservices/qa-projects/xyz-service-api-tests/`, with no
additional API-test copy under the outer QA category. See the
[project workflow](project-workflow.md) for task, evidence and knowledge ownership.

## Project entrypoints

| Area | Start here |
| --- | --- |
| Agent activity observer | [Agent dashboard](../../projects/agent-dashboard/README.md) |
| Choose project and task | [Project workflow](project-workflow.md) |
| API services and tests | [Microservices instructions](../../projects/microservices/AGENTS.md) |
| Event quality lab | [Kafka project](../../projects/kafka-test-project/README.md) |
| Playwright Agent | [Project instructions](<../../qa-projects/Playwright Agentic Framework/AGENTS.md>) |
| Role-aware UI automation | [Mockserver instructions](../../qa-projects/ui-automation/role-aware-mockserver/AGENTS.md) |
| Acceptance and mutation evidence | [Playwright Agent quality tools](<../../qa-projects/Playwright Agentic Framework/quality/README.md>) |
| Controlled trials | [Shared benchmarks](../../evaluation/benchmarks/README.md) |
| Local inference | [Local agents](../../agent-system/local-agents/README.md) |
| Resource adoption | [Catalogue README](instagram/README.md) |
| Existing runtime and QA commands | [Workspace manual](workspace-guide.md) |

Agenttrail observes available activity; Playwright Agent owns test authoring and quality assessment. The standalone QA viewer is retired. Folder existence and dashboard activity do not establish passing tests or completed work.

## What moved

| Previous root folder | Current location |
| --- | --- |
| `benchmarks/` | `evaluation/benchmarks/` |
| Retired decision-bench checkout | Ignored recovery artifacts; active quality tools live inside Playwright Agent |
| `contexts/` | Project-owned `contexts/`; reusable service templates in `agent-system/skills/microservice-change/examples/` |
| `skills/` | `agent-system/skills/` |
| `local-agents/` | `agent-system/local-agents/` |
| `context-starter/` | `agent-system/context-starter/` |
| `docs/` | `knowledge/docs/` |
| `resources/` | `knowledge/resources/` |
| `scripts/` | `tooling/scripts/` |
| `tests/` | `tooling/tests/` |
| `graphify-out/` | `artifacts/graphify-out/` |
| `LOOP.md` | `knowledge/docs/agent-workflow/LOOP.md` |
| `STATE.md` | `knowledge/docs/agent-workflow/STATE.md` |
| `loop-budget.md` | `knowledge/docs/agent-workflow/loop-budget.md` |
| `Dockerfile.graphs` | `tooling/docker/Dockerfile.graphs` |
| `docker-compose.graphs.yml` | `tooling/docker/docker-compose.graphs.yml` |
| `Untitled-1.svg` | `knowledge/docs/assets/workspace-diagram.svg` |

Active nested repositories are Playwright Agent, the role-aware mockserver, the public platform, the Kafka lab and the starter template. Each keeps its Git boundary. The retired decision checkout, with its Git directory and local environment, is recovery data under artifacts. Reference snapshots remain passive and unchanged.

Update this map and the registry when category ownership changes. This is a dated navigation guide, not an automatically generated live inventory.

## Active versus recovery storage

Each product has one working root. The former standalone mockserver path and
legacy decision-bench path are retired. Their preserved originals live under
ignored `artifacts/focused-restructure-20261031/recovery/`; they are not active
projects. Viewer recovery snapshots remain under ignored artifacts. The two task-created
temporary release worktrees were removed with normal Git cleanup after verifying
that their source was committed, no unique/private files remained, and all refs
were preserved. Recovery data has no registry entries or launch aliases.
