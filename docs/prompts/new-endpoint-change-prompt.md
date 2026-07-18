# New Endpoint Change Prompt

Use this prompt to evaluate whether a model can route a new endpoint change
through service code, OpenAPI, tests, shared QA utilities, and deployment impact
without over-editing.

```text
Add a new GET /xyz/status endpoint that returns a simple service status payload:
serviceName, status, and checkedAt.

Use the workspace instructions and current service context before deciding where
code, OpenAPI, tests, shared QA utilities, or deployment changes belong. Keep
shared QA utilities unchanged unless the new endpoint needs reusable helpers.
Report the files you would inspect, the files you would change, and the
verification commands you would run.
```

Expected routing:

- Read `AGENTS.md`.
- Read `contexts/current/service-context.yml`.
- Read `skills/microservice-change/SKILL.md`.
- Change service repo files for controller/DTO/service behavior.
- Update OpenAPI for the new endpoint.
- Add unit/API tests.
- Avoid `qa-steps` changes unless a reusable helper is genuinely needed.
- Check deployment impact and report no change if ports/probes/runtime are unchanged.
