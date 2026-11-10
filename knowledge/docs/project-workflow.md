# Working on one project

Choose project → read local instructions → select task context → inspect
authoritative source → make the change → run local checks → retain evidence →
promote reusable lessons into project docs.

## Select the owner

Use [the project registry](../../workspace.projects.json), then read the owning
project's instructions explicitly. Opening the workspace root does not imply
that every nested project's instructions have been loaded.

| Project | Local entrypoint | Context, evaluation and knowledge |
| --- | --- | --- |
| Playwright Agent | [AGENTS.md](../../qa-projects/Playwright%20Agentic%20Framework/AGENTS.md) | Existing `contexts/` maps/captures and ignored `contexts/tasks/` requirements; internal `quality/` evaluators, mutation runner and reports; project `docs/` |
| Role-aware mockserver | [AGENTS.md](../../qa-projects/ui-automation/role-aware-mockserver/AGENTS.md) | `contexts/tasks/`; existing Playwright tests and `benchmarks/`; project `docs/` |
| Microservices | [AGENTS.md](../../projects/microservices/AGENTS.md) | `contexts/tasks/`; existing service and RestAssured Maven modules; module READMEs and aggregate `docs/` |

Root `AGENTS.md` supplies common boundaries. Shared skills describe reusable
procedures; they do not own a project's business rules. Root `knowledge/` holds
workspace operations, shared research and lessons relevant across projects.
Root `evaluation/` retains cross-project trials and collection contracts. Do not
add identical empty `contexts`, `evaluation` and `knowledge` trees to each module.

## Select a task and resolve exact files

Keep one work item per uniquely named file in the owning project's
`contexts/tasks/`. The committed `ABC-123.yml` and `UI-ROLE-001.yml` files are
sanitised examples; they are not instructions to repeat old work. Copy an example
to a new ignored task file and replace only task intent, scope, acceptance
criteria and quality gates. Do not copy source, endpoints, DTOs or full contracts
into it. Keep downloaded private requirements ignored as well.

From the workspace root, select that task explicitly:

```sh
npm run context:resolve -- --context projects/microservices/contexts/tasks/ABC-123.yml
npm run context:ui:resolve -- --context qa-projects/ui-automation/role-aware-mockserver/contexts/tasks/UI-ROLE-001.yml
```

Replace the example filename with the real task. Paths passed to `--context`
and `--output` are workspace-relative unless absolute; `--workspace` selects a
different workspace root. Omitting `--context` resolves the sanitised example.
Output defaults to that project's ignored `contexts/.resolved/<task>.yml`;
`--output` remains available for an explicit session-specific destination. An
ad-hoc input outside a `tasks/` directory writes into an adjacent `.resolved/`.
The resolver rejects output that would overwrite the input.

Read the selected output's `task_context.path` and `sha256`, exact file map,
topology and verification commands. Regenerate after task, source, OpenAPI,
configuration or layout changes. The input hash identifies the task; it does not
prove that source is unchanged or that a runtime check passed. Parallel work on
the same task must choose separate `--output` paths. Distinct task names get
separate outputs automatically.

The graph and local QA dashboard default to these example outputs. To inspect
another task, pass `--api-context` and/or `--ui-context` with its resolved output
path. The context-efficiency report accepts `--context` for a selected API task.
These views are supporting evidence and do not redefine the source contract.
Missing, invalid, wrong-kind or task-stale resolved maps fail explicitly; rerun
the selected resolver instead of substituting another task or an empty ticket.

Playwright Agent keeps its own project skill and existing requirement interfaces;
the mockserver resolver does not resolve that harness. Its curated maps and page
captures must be checked against the target application's current source/runtime.

## Change, verify and retain evidence

Use local commands from the owning project's instructions. OpenAPI/source/config
define implemented behavior; task context describes requested behavior. Report
unsupported expectations as product/contract gaps rather than weakening tests.

Keep executable application tests distinct from evaluating the coding agent.
Agent evaluation uses reviewed acceptance coverage, incorrect changes and mutation
evidence; an application suite passing alone is insufficient. Preserve existing
provider labels, denominators, fixture provenance and historical limitations.
Publishing reviewed aggregates remains the separate `$platform-publish` workflow.

Store reports, captures, traces and private assessment inputs in the existing
ignored project outputs. A handoff should identify task, source revision (and
dirty state), command, environment, result, evidence path and skipped checks.
Never promote secrets, raw requirements, model guesses or one-off logs into docs.

Promote a lesson only after source or execution review shows it is durable. Put
it in the owning project's existing `docs/` or module README and link the source
of truth. Move genuinely shared lessons into root `knowledge/` with links to
owners; do not maintain duplicate descriptions of the same behavior.

## Standalone use and local coding agents

Each core project's local instructions identify its source and runnable checks.
Outside this workspace, use those directly; shared resolvers are optional tools.
When launching a local coding agent from the workspace, `api`, `ui` and
`playwright-agent` slices select the corresponding project by default. Set
`AGENTIC_TASK_CONTEXT` to a workspace-relative task path for an explicit task.
No providers, autonomous hooks or publication are enabled by this organisation.
