# New Endpoint Change Prompt

Use this prompt to evaluate whether a model can route a new endpoint change
through service code, OpenAPI, tests, shared QA utilities, and deployment impact
without over-editing.

```text
Add a new GET /xyz/status endpoint that returns a simple service status payload:
serviceName, status, and checkedAt.

Use the project instructions and explicitly selected service task before deciding where
code, OpenAPI, tests, shared QA utilities, or deployment changes belong. Keep
shared QA utilities unchanged unless the new endpoint needs reusable helpers.
Report the files you would inspect, the files you would change, and the
verification commands you would run.
```

Expected routing:

- Read root routing and `projects/microservices/AGENTS.md`.
- Select the requested project task under `contexts/tasks/`; `ABC-123.yml` is
  a sanitized example. Read its matching `contexts/.resolved/` output, using an
  explicit `--context` path when resolving missing or stale output.
- Read `agent-system/skills/microservice-change/SKILL.md`.
- Change service repo files for controller/DTO/service behavior.
- Update OpenAPI for the new endpoint.
- Add unit/API tests.
- Avoid `qa-steps` changes unless a reusable helper is genuinely needed.
- Check deployment impact and report no change if ports/probes/runtime are unchanged.

Paths in this template are workspace-relative. From the project root use local
equivalents; outside the workspace follow local instructions and native checks.
