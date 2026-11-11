# Agentic Workspace

Use this workspace for agent and harness engineering, API/UI automation, and measured experiments. Nine category folders organise the work by intent; root instructions and launchers connect them. Projects keep their own frameworks and repository boundaries.

## Start here

1. Open `agentic-workspace.code-workspace` in VS Code, or double-click `Open-Workspace.command` in Finder. The existing `~/agentic-engineering.code-workspace` opens the same organised project set.
2. Double-click **Open-Agent-Dashboard.command** to start or reuse the chef dashboard and open live observations at http://127.0.0.1:4780/.
3. For a scripted visual walkthrough, double-click **Open-Agent-Example.command**. Example activity is labelled; it is not evidence that real agents are running.

In VS Code, use the NPM Scripts play button for `agents:dashboard`, or run the task **Agent flows: Open**. The dashboard keeps running when its launch terminal closes. Stop it with **Stop-Agent-Dashboard.command** or `npm run agents:stop`.

The dashboard package is installed once in its own project. A fresh checkout's first launch may download the pinned package. Later launches reuse it and verify readiness before opening the browser.

## Workspace map

See the [actual folder hierarchy and Mermaid maps](knowledge/docs/workspace-map.md) for the layout on disk, folder responsibilities, repository boundaries, and the flow from task context to project code.

| Folder | Responsibility |
| --- | --- |
| `products/` | Runnable products by domain: `finance/` (FinFolio app and agent), `career/` (career agent), `portfolio/` (public portfolio site and its template), `agent-tools/` (Agenttrail dashboard) |
| `services/` | Backend services with contracts, deployment assets and RestAssured API tests |
| `qa/` | Playwright Agent, role-aware UI automation and the Playwright starter template |
| `labs/` | Experiments such as the Kafka testing lab |
| `evaluation/` | [Shared controlled trials and evidence collection](evaluation/benchmarks/README.md) |
| `agent-system/` | Task context, canonical skills, [local inference](agent-system/local-agents/README.md) and context starter |
| `knowledge/` | [Guides](knowledge/docs/workspace-guide.md), prompts, [adoption catalogue](knowledge/docs/instagram/README.md) and reference snapshots |
| `tooling/` | Workspace scripts, their regression tests and Docker configuration |
| `artifacts/` | Ignored generated reports, Graphify output, local tools and migration records |

The grouped VS Code view mirrors these nine categories, and `workspace.projects.json` records each project's group, domain, kind, status and repository. Each active product has one working location. Playwright Agent owns its internal quality tools; the role-aware mockserver Git checkout lives only under `qa/ui-automation/role-aware-mockserver/`. Retired source and private recovery data stay under ignored `artifacts/`. Agent and editor integration folders remain at the root. See the map for the complete migration table.

Workflow notes live in [knowledge/docs/agent-workflow](knowledge/docs/agent-workflow/LOOP.md). Graph-service Docker files live in `tooling/docker/`; the existing `graphs:docker:build` and `graphs:docker:up` npm commands use that location.

## Agenttrail views

- `npm run agents:map` or **Open-Agent-Map.command**: project/component map at http://127.0.0.1:5330/.
- `npm run agents:dashboard`: Kitchen activity view at http://127.0.0.1:4780/.
- Map controls: `agents:map:status` and `agents:map:stop`.

Both views use the same dashboard project and pinned local packages. The Map
reads `PLAN.md`; its checkboxes describe declared tasks, while file activity is
observed separately. Neither view launches coding agents.

## Useful checks

```sh
npm run workspace:check
python3 tooling/scripts/validate_agentic_skills.py
npm run context:ui:resolve
```

Read [the organisation guide](knowledge/docs/workspace-organisation.md) for project ownership, [the detailed workspace manual](knowledge/docs/workspace-guide.md) for existing runtime/QA commands, and [AGENTS.md](AGENTS.md) before agent work.

## Platform and showcased repositories

See the [repository copies map](knowledge/docs/repository-copies.md) for the platform, standalone
showcase checkouts and preserved local project boundaries.

## Focused project ownership

- Playwright test authoring, acceptance assessment and mutation evidence: `qa/playwright-agent/` (`quality/` is internal).
- Role-aware demo, mockserver and UI tests: `qa/ui-automation/role-aware-mockserver/`, the sole Git-backed checkout.
- API source, contracts and RestAssured tests: `services/microservices/`, including its existing `qa-projects/xyz-service-api-tests/`.
- Public portfolio site (balaji-kumarasamy.netlify.app): `products/portfolio/portfolio-web/`.
- Agent activity observation: `products/agent-tools/agent-dashboard/`; shared trial tooling: `evaluation/benchmarks/`.

The Playwright starter template is reference scaffolding, not another active agent
or application. The old decision-bench and standalone QA viewer have no active
project paths or launch aliases. Recovery data is excluded from active project
registration, agent watches and Git source publication.

## Project-owned work

Follow [the project workflow](knowledge/docs/project-workflow.md): choose a project,
read its local instructions, select task context, inspect authoritative source,
make the change, run local checks, retain evidence, and promote verified lessons
into project docs. Shared skills, research and cross-project trials stay central.
Run `npm run context:test` to verify task isolation and resolver routing.
