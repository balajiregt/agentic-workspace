# Loop Run Log

This log records proof that an agentic workspace change followed the expected
context-routing loop.

## 2026-07-20 Generic API Automation Refactor

Reason:

- The framework should not be shaped around one demo service, field, or negative
  test value.
- It should work for API automation teams using different APIs and different
  API test frameworks.

Refactor:

- Core rules now say "existing API test framework" instead of assuming
  RestAssured/Java/JUnit.
- Skill point 11 now describes unsupported behavior generically: if a test
  expects a response not implemented by source or documented in OpenAPI, report
  a product/contract gap.
- Resolver-derived validation hints are generic contract/source signals, not
  hardcoded `customerId` or `INVALID_ID_FORMAT` rules.
- Demo-specific details remain only in the sample project and historical proof
  log entries.

Validation:

- `npm run context:resolve`
- `python3 -m py_compile scripts/resolve_context.py scripts/context_efficiency_report.py`
- `cd /Users/balaji/agentic-workspace/projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test-compile`

Validation result:

```text
BUILD SUCCESS
```

## 2026-07-20 Point 11 Read-Only Gap Test Failure

Prompt scenario:

```text
I added a test expectation:
GET /xyz?customerId=INVALID_ID_FORMAT should return 400 Bad Request.

Tell me whether this expectation is supported behavior, a test bug, or a
product/contract gap.
```

Observed local-model failure:

- The model correctly generated/read `contexts/current/resolved-context.yml`.
- It found `resolved_files.api_test`.
- It incorrectly edited the API test and replaced the blank-customerId test
  with an invalid-format test.
- It did not stop at skill point 11.

Framework update:

- Gap-analysis prompts are now explicitly read-only unless the user asks to
  implement the service/contract change.
- `scripts/resolve_context.py` now derives validation hints from OpenAPI and
  source code:
  - OpenAPI `customerId` has `minLength: 1` and no `pattern`.
  - Controller has `@NotBlank` and no `@Pattern`.
  - Service trims/uppercases customerId and has no invalid-format check.
- Skill point 11 now tells the agent to use `derived_validation` when present.

Expected agent conclusion:

```text
This is a product/contract gap. INVALID_ID_FORMAT is nonblank, so current
service behavior evaluates it. To return 400, add explicit service validation
and document it in OpenAPI.
```

Validation:

- `npm run context:resolve`
- `cd /Users/balaji/agentic-workspace/projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test-compile`

Validation result:

```text
BUILD SUCCESS
```

## 2026-07-20 Lean Context Resolver Refactor

Problem:

- `contexts/current/service-context.yml` was becoming too large and hard to
  maintain.
- Exact paths, commands, fixtures, and response examples were being added to the
  task YAML to compensate for local-model mistakes.
- That made the framework less dynamic and less practical.

Refactor:

- `contexts/current/service-context.yml` now contains only the current task.
- `scripts/resolve_context.py` generates `contexts/current/resolved-context.yml`
  with exact paths and verification commands.
- The resolver derives from the current task, repo layout, and OpenAPI instead
  of requiring one metadata YAML per service.
- Agents read the small task context first, then the generated resolved context.

Context-size proof:

```text
Current task context: 28 lines
Estimated current task tokens: 179
```

Model-behavior lesson:

- The local model found `resolved_files.api_test`, so generated path context
  solved the file-discovery problem.
- It then duplicated an already-covered medium scenario and guessed
  `decisionReason contains "review"`.
- The framework now says to check existing endpoint/input/expected-behavior
  coverage before adding another API test.
- Exact response values come from service code or OpenAPI; guessed substrings
  are not acceptable.

Validation:

- `npm run context:resolve`
- `python3 scripts/context_efficiency_report.py --task-profile api-test-change`
- `cd /Users/balaji/agentic-workspace/projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test-compile`
- `cd /Users/balaji/agentic-workspace/projects/microservices/xyz-service && mvn spring-boot:run -Dspring-boot.run.arguments=--server.port=8081`
- `cd /Users/balaji/agentic-workspace/projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test -Dapi.port=8081`

Validation result:

```text
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-07-20 Target File Breadcrumb Validation

Prompt scenario:

```text
add one more api test in CustomerRiskAPitest.java for 'riskCategory' when it is
'medium'
```

Observed failure mode after the first routing guardrail:

- The model searched for `CustomerRiskAPitest.java` under the QA project.
- It did not map the near-match name to `CustomerRiskApiTest.java`.
- It then created a placeholder file under `src/test/java/CustomerRiskAPitest.java`
  with an invented package, base URL, request body, and endpoint.

Framework update:

- `contexts/current/service-context.yml` now includes `target_files`.
- `target_files.api_test` points directly to the real RestAssured test class.
- `AGENTS.md`, `skills/microservice-change/SKILL.md`, and
  `docs/prompts/existing-test-assertion.md` now require target files to be used
  before fuzzy search.

Expected agent conclusion:

```text
Use target_files.api_test:
/Users/balaji/agentic-workspace/projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java

Do not create CustomerRiskAPitest.java or any new QA project.
```

Validation:

- `cd /Users/balaji/agentic-workspace/projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test-compile`

Validation result:

```text
BUILD SUCCESS
```

## 2026-07-20 Existing Test File Routing Validation

Prompt scenario:

```text
add one more api test in CustomerRiskAPitest.java for 'riskCategory' when it is
'medium'
```

Observed failure mode:

- A local model created `qa-projects/CustomerRiskAPI-api-tests/CustomerRiskAPitest.java`.
- That path is outside the YAML-declared QA project.
- The generated test invented `http://api.example.com` and
  `/riskCategory/{riskCategory}` instead of using `GET /xyz`.

Expected routing:

- Read `AGENTS.md`.
- Read `contexts/current/service-context.yml`.
- Search the YAML-declared QA test root.
- Map the prompt's near-match class name `CustomerRiskAPitest.java` to the real
  existing file `CustomerRiskApiTest.java`.
- Add the medium-risk case to the existing RestAssured test file.
- Use existing fixtures and service rules instead of invented endpoints.

Actual changed file:

- `projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java`

Expected agent conclusion:

```text
MEDIUM risk is supported behavior. Use MEDIUM_RISK_CUSTOMER / CUST-5000, call
GET /xyz, and assert riskCategory = MEDIUM in the existing API test.
```

Framework updates:

- `AGENTS.md` now requires exact case-sensitive filename verification under
  YAML-declared test roots.
- `skills/microservice-change/SKILL.md` now treats "add one more API test" like
  an existing-test edit unless the user explicitly asks for a new file.
- `docs/prompts/existing-test-assertion.md` now forbids invented endpoints,
  base URLs, request bodies, and near-match test projects.

Validation:

- `cd /Users/balaji/agentic-workspace/projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test-compile`
- `cd /Users/balaji/agentic-workspace/projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test -Dapi.port=8081`

Validation result:

```text
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

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
