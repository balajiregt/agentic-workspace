# Workspace organisation and ownership

The workspace is organised into nine physical category folders, grouped by intent. Open [the folder map](workspace-map.md) for the hierarchy, descriptions and migration table. [workspace.projects.json](../../workspace.projects.json) records both the categories and the individual projects watched by the dashboard.

## Ownership map

| Category | Responsibility |
| --- | --- |
| `products/<domain>/` | Runnable products and agents, grouped by domain: `finance/`, `career/`, `agent-tools/`. |
| `services/` | Backend services with their contracts, deployment assets and API tests. |
| `qa/` | QA frameworks, UI automation and Playwright templates. |
| `labs/` | Experiments and integration labs that are not product code. |
| `evaluation/` | Cross-project controlled trials and shared evidence collection; project-specific checks stay local. |
| `agent-system/` | Canonical skills with their reusable templates, local inference wrappers and the external context-starter symlink. |
| `knowledge/` | Cross-project documentation, reusable prompts, adoption decisions and passive reference snapshots. |
| `tooling/` | Workspace infrastructure scripts, their regression tests and graph-service Docker configuration. |
| `artifacts/` | Ignored generated reports, Graphify output, downloads, environments and migration records. |

Standard agent, Git, CI and editor integration folders remain at the root. Generated reports, dependencies and local process state also remain inside their owning projects where appropriate. Agent dashboard runtime files stay in ignored `products/agent-tools/agent-dashboard/.runtime/`.

## Root files

The root keeps `README.md`, `AGENTS.md`, `CLAUDE.md`, `package.json`, the project registry, the VS Code workspace, one-click launchers and tool configuration. These provide the workspace entrypoints and default configuration locations.

Loop instructions, validation state and budget guidance live under `knowledge/docs/agent-workflow/`. Saved diagram assets live under `knowledge/docs/assets/`. The graph-service Dockerfile and Compose configuration live under `tooling/docker/`; the Compose build context remains the workspace root, using its `.dockerignore`.

```sh
npm run graphs:docker:build
npm run graphs:docker:up
```

## Editor view

Open `agentic-workspace.code-workspace`, `Open-Workspace.command`, or the existing `~/agentic-engineering.code-workspace`. The editor provides Workspace core plus nine named category roots. Workspace core retains the actual folders in Explorer, and opening only the root folder shows the same physical category structure.

Root `.vscode/tasks.json` and npm scripts provide the existing dashboard and validation entrypoints. No new extension is required.

## Project and automation boundaries

Products live under `products/<domain>/`, services under `services/`, QA frameworks under `qa/` and experiments under `labs/`. UI automation belongs under `qa/ui-automation/`; RestAssured automation belongs under `services/microservices/`. The UI resolver still accepts the earlier `projects/ui-automation/` layout for compatibility.

Independent Git repositories retain their own history and working changes.
Playwright Agent is owned by `qa/playwright-agent/`, including
its internal `quality/` evaluator. The sole role-aware mockserver checkout is
`qa/ui-automation/role-aware-mockserver/`; its own Git metadata and GitHub
origin moved into that existing canonical path. There is no second standalone
copy under `qa/`.

RestAssured tests remain under `services/microservices/qa-projects/xyz-service-api-tests/`.
The empty extra API-test placeholder, old decision-bench working checkout and QA
viewer are absent from active roots. Complete recovery copies are ignored under
`artifacts/`; they are not registered projects or supported launch locations.
See [current repository ownership](repository-copies.md). The Kafka lab and
Playwright starter template keep their distinct purposes and Git boundaries.

Canonical shared workflows live in `agent-system/skills/`. Native discovery
remains under `.agents/skills/`, and the Claude alias continues to point there.
Root `AGENTS.md` routes to project-local instructions; it does not select a
global current ticket. See [the project workflow](project-workflow.md).

API and mockserver work items live in their owning project's
`contexts/tasks/<work-item>.yml`; generated exact paths live in ignored
`contexts/.resolved/<work-item>.yml`. Select the actual task explicitly and
regenerate after relevant source or structural changes. Default root resolver
commands use sanitized examples for checks. Use distinct outputs for concurrent
sessions on the same task. Playwright Agent retains its own application maps,
captures and task-input workflow under its existing `contexts/`.

Durable domain explanations and decisions live in each project's `docs/`, with
links to authoritative source, contracts and configuration. Preserve existing
local test, `quality/` and `benchmarks/` ownership; shared comparisons stay under
workspace `evaluation/`. Keep private task inputs and execution evidence ignored,
and promote only verified reusable lessons into docs. Do not create empty
`knowledge/` or `evaluation/` folders in every project.

## Checks

```sh
npm run workspace:check
npm run workspace:test
npm run context:resolve
npm run context:ui:resolve
python3 tooling/scripts/validate_agentic_skills.py
npm --prefix products/agent-tools/agent-dashboard test
```

Agenttrail Kitchen uses port 4780; the optional Map uses port 5330. Both live in products/agent-tools/agent-dashboard and observe existing work. Graph services and local model runtimes retain their existing command aliases and configured ports. The standalone QA viewer is retired; Playwright Agent owns quality reports and the public platform shows project results.

## Registry conventions

Every project entry records `id`, `name`, `path`, `group`, `domain`, `kind`,
`status`, `purpose` and `repository` (`remote`, `visibility`, `nested`). Allowed
kinds and statuses are listed under `conventions`. IDs are stable identifiers;
renaming a folder must not change an ID. `workspace:check` verifies that each
project sits inside its declared group, that nested repositories are ignored by
the workspace repository, and that the retired `projects/` and `qa-projects/`
roots do not return.

Products moved in from elsewhere keep a symlink at their previous path so
existing launchers, Codex skills and editor history keep working. Their own
uncommitted work moves with them and remains theirs to commit.

## Adding another project

Choose the existing category (and, for products, the domain) that owns the new work. Clone or move independent repositories into place and add their path to `.gitignore`. Add runnable project metadata to `workspace.projects.json`; its `groups` define the editor category roots, while `projects` retain individual dashboard IDs. Add an ID to `products/agent-tools/agent-dashboard/dashboard.config.json` only when observation is useful; the pinned Kitchen supports up to twelve watched folders. Run `workspace:check` after changes.
