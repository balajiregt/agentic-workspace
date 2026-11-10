# Workspace organisation and ownership

The workspace is organised into seven physical category folders. Open [the folder map](workspace-map.md) for the hierarchy, descriptions and migration table. [workspace.projects.json](../../workspace.projects.json) records both the categories and the individual projects watched by the dashboard.

## Ownership map

| Category | Responsibility |
| --- | --- |
| `projects/` | Runnable applications, services and integration labs. |
| `qa-projects/` | QA frameworks, Playwright templates and additional API tests. |
| `evaluation/` | Cross-project controlled trials and shared evidence collection; project-specific checks stay local. |
| `agent-system/` | Canonical skills with their reusable templates, local inference wrappers and the external context-starter symlink. |
| `knowledge/` | Cross-project documentation, reusable prompts, adoption decisions and passive reference snapshots. |
| `tooling/` | Workspace infrastructure scripts, their regression tests and graph-service Docker configuration. |
| `artifacts/` | Ignored generated reports, Graphify output, downloads, environments and migration records. |

Standard agent, Git, CI and editor integration folders remain at the root. Generated reports, dependencies and local process state also remain inside their owning projects where appropriate. Agent dashboard runtime files stay in ignored `projects/agent-dashboard/.runtime/`.

## Root files

The root keeps `README.md`, `AGENTS.md`, `CLAUDE.md`, `package.json`, the project registry, the VS Code workspace, one-click launchers and tool configuration. These provide the workspace entrypoints and default configuration locations.

Loop instructions, validation state and budget guidance live under `knowledge/docs/agent-workflow/`. Saved diagram assets live under `knowledge/docs/assets/`. The graph-service Dockerfile and Compose configuration live under `tooling/docker/`; the Compose build context remains the workspace root, using its `.dockerignore`.

```sh
npm run graphs:docker:build
npm run graphs:docker:up
```

## Editor view

Open `agentic-workspace.code-workspace`, `Open-Workspace.command`, or the existing `~/agentic-engineering.code-workspace`. The editor provides Workspace core plus seven named category roots. Workspace core retains the actual folders in Explorer, and opening only the root folder shows the same physical category structure.

Root `.vscode/tasks.json` and npm scripts provide the existing dashboard and validation entrypoints. No new extension is required.

## Project and automation boundaries

Applications and QA projects retain their existing paths under `projects/` and `qa-projects/`. UI automation belongs under `qa-projects/ui-automation/`; RestAssured automation belongs under `projects/microservices/`. The UI resolver still accepts the earlier `projects/ui-automation/` layout for compatibility.

Independent Git repositories retain their own history and working changes.
Playwright Agent is owned by `qa-projects/Playwright Agentic Framework/`, including
its internal `quality/` evaluator. The sole role-aware mockserver checkout is
`qa-projects/ui-automation/role-aware-mockserver/`; its own Git metadata and GitHub
origin moved into that existing canonical path. There is no second standalone
copy under `qa-projects/`.

RestAssured tests remain under `projects/microservices/qa-projects/xyz-service-api-tests/`.
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
npm --prefix projects/agent-dashboard test
```

Agenttrail Kitchen uses port 4780; the optional Map uses port 5330. Both live in projects/agent-dashboard and observe existing work. Graph services and local model runtimes retain their existing command aliases and configured ports. The standalone QA viewer is retired; Playwright Agent owns quality reports and the public platform shows project results.

## Adding another project

Choose the existing category that owns the new work. Add runnable project metadata to `workspace.projects.json`; its `groups` define the editor category roots, while `projects` retain individual dashboard IDs. Add an ID to `projects/agent-dashboard/dashboard.config.json` only when observation is useful; the pinned Kitchen supports up to twelve watched folders. Run `workspace:check` after changes.
