# Loop Run Log

This log records proof that an agentic workspace change followed the expected
context-routing loop.

## 2026-07-18 API Test Change Validation

Prompt used:

```text
Add RestAssured coverage for the GET /xyz blank customerId validation case.

Use the workspace instructions and current service context to decide where the
test belongs. Do not change service code unless the existing behavior is wrong.
After the change, run the relevant Maven verification command and report the
context files inspected, files changed, and validation result.
```

Expected routing:

- Read `AGENTS.md`.
- Read `contexts/current/service-context.yml`.
- Read `skills/microservice-change/SKILL.md`.
- Use `repository_topology.service_and_tests: split-qa`.
- Keep actual API test changes in
  `projects/microservices/qa-projects/xyz-service-api-tests`.
- Reuse shared RestAssured utilities from `projects/microservices/qa-steps`.

Actual inspected files:

- `AGENTS.md`
- `contexts/current/service-context.yml`
- `skills/microservice-change/SKILL.md`
- `projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/api/CustomerRiskController.java`
- `projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/exception/ApiExceptionHandler.java`
- `projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java`

Framework files added or updated before the prompt test:

- `AGENTS.md`
- `LOOP.md`
- `STATE.md`
- `loop-budget.md`
- `scripts/context_efficiency_report.py`
- `docs/prompts/api-test-change-prompt.md`
- `docs/loop-run-log.md`

Prompt-routed changed files:

- `projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java`

Validation:

- `python3 -m py_compile scripts/context_efficiency_report.py local-agents/render-pi-models.py`
- `python3 scripts/context_efficiency_report.py --task-profile api-test-change`
- `curl http://localhost:8080/actuator/health`
- `cd /Users/balaji/agentic-workspace/projects/microservices && /tmp/agentic-workspace-tools/apache-maven-3.9.9/bin/mvn -pl qa-projects/xyz-service-api-tests -am test`

Validation result:

```text
Actuator health: {"status":"UP","groups":["liveness","readiness"]}
Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
Reactor result: BUILD SUCCESS
Finished at: 2026-07-18T12:01:57+05:30
```

Context-efficiency proof:

```text
Central context tokens: 594
Central context plus skills tokens: 1754
Full microservices corpus tokens: 5077
Task profile tokens (api-test-change): 3001
Task profile compression ratio: 1.69x
Central context compression ratio: 8.55x
```

Conclusion:

The prompt did not name the split-QA test folder directly. The workspace routed
the change through `AGENTS.md`, `service-context.yml`, and
`microservice-change/SKILL.md`, then placed the new RestAssured test in the
actual API test project declared by `repository_topology.service_and_tests:
split-qa`.
