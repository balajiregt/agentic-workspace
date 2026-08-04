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
