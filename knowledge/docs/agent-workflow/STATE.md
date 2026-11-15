# Workspace Validation Owners

No task is selected by this document. Choose the project, read its local
`AGENTS.md`, and select the requested work item. Native commands, source maps,
contract boundaries and project-specific knowledge belong to their owner:

| Owner | Instructions |
| --- | --- |
| Playwright Agent, acceptance and mutation evidence | [Project instructions](../../../qa/playwright-agent/AGENTS.md) |
| Role-aware mockserver and browser tests | [Project instructions](../../../qa/ui-automation/role-aware-mockserver/AGENTS.md) |
| API service, contract, deployment and RestAssured | [Aggregate instructions](../../../services/microservices/AGENTS.md) |

The committed `ABC-123.yml` and `UI-ROLE-001.yml` project tasks are sanitised
examples for resolver smoke checks. They are not globally active tickets.
Select a task explicitly, regenerate its matching ignored
`contexts/.resolved/<work-item>.yml` after relevant changes, and use separate
outputs for concurrent sessions on the same task. See
[the project workflow](../project-workflow.md) for commands and ownership.

Keep raw evidence in ignored project outputs and durable explanations in the
owning project's docs. Shared comparisons remain in workspace `evidence/`.

Graph-based engineering stance:

- Built-in graph: `tooling/scripts/build_test_graph.py` generates the deterministic
  API/UI test-impact graph from resolved contexts.
- Local viewer:

```bash
npm run graph:build
npm run dashboard:build
npm run dashboard:serve -- --port 8765
npm run graph:serve -- --port 8766
npm run graphify:build
npm run graphify:serve -- --port 8767
npm run graphs:serve
npm run graphs:docker:build
npm run graphs:docker:up
```

- Output is local and ignored under `artifacts/test-graph/`.
- Dashboard output is local and ignored under `artifacts/qa-dashboard/`.
- Graphify output is local and ignored under `artifacts/graphify-out/`.
- Duplicate prevention is instruction-first in the API and Playwright skills.
- Graphify can be used later as an optional broad workspace knowledge graph,
  but it is not the primary duplicate-detection or test-routing mechanism.
- The current dashboard is a static stakeholder and agent slice. It includes
  CSS-only visual bars for quality and test mix, release confidence,
  changed-file impact recommendations, coverage/gap signals, duplicate/overlap
  candidates, pass/fail health, graph freshness, and runtime usage readiness.
  High-volume tables are searchable and capped to the top 10 rows by default,
  with a Show all toggle for larger suites.
  Real usage metrics can be loaded later from
  `artifacts/usage-metrics/usage.json`.
