# Current Workspace State

Active validation slice:

```text
contexts/current/service-context.yml
contexts/current/ui-context.yml
```

Current service:

```text
projects/microservices/xyz-service
```

Current topology:

```text
service_and_tests: split-qa
deployment: separate-repo
```

Implication:

- Service code and OpenAPI live in `xyz-service`.
- Shared RestAssured support lives in `qa-steps`.
- Actual service API tests live in `qa-projects/xyz-service-api-tests`.
- Deployment impact is checked in `xyz-deployments`.

Current validation command:

```bash
cd projects/microservices
mvn -pl qa-projects/xyz-service-api-tests -am test
```

Current UI validation slice:

```text
projects/ui-automation/role-aware-mockserver
```

Implication:

- Playwright UI tests, Koa mockserver, and the demo app live under
  `projects/ui-automation`.
- UI automation uses `contexts/current/ui-context.yml`,
  `contexts/current/resolved-ui-context.yml`, and
  `skills/playwright-ui-change/SKILL.md`.
- UI dependencies are installed in the UI project, not the workspace root.

Current UI validation commands:

```bash
npm run context:ui:resolve
npm run ui:test
npm run ui:test:roles
npm run ui:test:legacy-interception
```

Current graph-based engineering stance:

- Built-in graph: `scripts/build_test_graph.py` generates the deterministic
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
- Graphify output is local and ignored under `graphify-out/`.
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
