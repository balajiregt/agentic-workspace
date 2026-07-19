# Loop Run Log

This log records proof that an agentic workspace change followed the expected
context-routing loop.

## 2026-07-19 QA Gap Guardrail Validation

Prompt scenario:

```text
I added a test expecting GET /xyz?customerId=INVALID_ID_FORMAT to return 400.
Run/analyze it and tell me whether this is supported behavior or a
product/contract gap.
```

Expected routing:

- Read `AGENTS.md`.
- Read `contexts/current/service-context.yml`.
- Read `skills/microservice-change/SKILL.md`.
- Inspect the controller, service, OpenAPI, shared QA utilities, and API test
  files only.
- Do not delete or rewrite a test only to make the suite pass.

Actual evidence:

- `CustomerRiskController` validates `customerId` with `@NotBlank`.
- `CustomerRiskService` trims and uppercases the value, then evaluates risk.
- OpenAPI declares `customerId` as a required string with `minLength: 1`.
- There is no `@Pattern`, regex check, allowlist, or OpenAPI `pattern`.

Expected agent conclusion:

```text
INVALID_ID_FORMAT is a nonblank customerId, so the current service evaluates it.
A test expecting 400 is a product/contract gap unless service validation and
OpenAPI are updated. Do not silently remove or rewrite the test.
```

Framework updates:

- `AGENTS.md` now treats unsupported test expectations as QA/product gaps.
- `skills/microservice-change/SKILL.md` now requires reporting the gap instead
  of hiding it by deleting the test.
- `docs/prompts/qa-gap-analysis.md` adds a reusable Pi prompt for this scenario.

Validation:

- `cd /Users/balaji/agentic-workspace/projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test-compile`
- `cd /Users/balaji/agentic-workspace/projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test -Dapi.port=8081`

Validation result:

```text
Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

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
