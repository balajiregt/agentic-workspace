# Shared QA Utility Change Prompt

Use this prompt to evaluate whether a model can decide when a test helper belongs
in `qa-steps` instead of the service-specific API test project.

```text
Add reusable API-test assertion support for validating standard bad-request
responses with error, status, and message fields.

Use the workspace instructions and current service context before deciding
whether this belongs in shared QA utilities or only in the service-specific API test project. Then
report the files you would inspect, the files you would change, and the
verification commands you would run.
```

Expected routing:

- Read `AGENTS.md`.
- Read `contexts/current/service-context.yml`.
- Read `skills/microservice-change/SKILL.md`.
- Inspect existing assertion utilities in `qa-steps`.
- Update `qa-steps` only if the helper is reusable across API tests.
- Update `xyz-service-api-tests` to use the helper only if it improves clarity.
- Run the resolved split-QA API test command.
