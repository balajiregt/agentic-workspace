---
name: microservice-change
description: Make context-aware microservice changes in the agentic workspace across same-repo or split-repo topologies. Use when a task references service-context.yml, Jira-driven service changes, Spring Boot code, OpenAPI alignment, deployment impact checks, service-owned tests, shared QA utilities, or RestAssured API tests under projects/microservices.
---

# Microservice Change

## Goal

Change the smallest correct set of files across service code, contract,
deployment, and tests for the topology declared in the context YAML.

## Inputs

- Read `/Users/balaji/agentic-workspace/contexts/current/service-context.yml`.
- Treat `related_repositories.*.local_path` as the source of truth for repo paths.
- Treat `target_files.*` as the first-choice file map when present. It narrows
  the task from repo-level routing to exact controller, service, OpenAPI, API
  test, fixture, or assertion files.
- Treat `repository_topology` as the source of truth for whether tests and
  deployment assets live in the service repo or separate repos.
- Treat `work_item.affected_endpoints`, `affected_fields`, and `acceptance_criteria`
  as the behavioral target.

## Procedure

1. Inspect the context YAML before editing.
2. If `target_files` is present, open the relevant exact target file before
   searching. For API-test edits, open `target_files.api_test`.
3. Inspect only the files needed to confirm the endpoint, DTO, contract, tests,
   and deployment impact.
4. Prefer existing project patterns over new abstractions.
5. If `service_and_tests` is `same-repo`, keep unit, integration, and API tests
   inside the service repo.
6. If `service_and_tests` is `split-qa`, keep reusable RestAssured support in
   `qa-steps` and actual service API tests in `qa-projects/<service>-api-tests`.
7. If the user names a test file or class, validate the exact case-sensitive
   file path from disk under the YAML-declared test roots. If casing or spelling
   differs, use the existing file and say which prompt name was mapped. If
   `target_files.api_test` exists, use it as the mapping candidate.
8. For "add one assertion", "add one more API test", or "modify existing test"
   requests, edit the
   existing test file that already covers the endpoint; do not create, rename,
   append to, or assume files that were not listed from disk.
9. Keep the repo's existing test framework. In this workspace, API tests are
   Java/JUnit/RestAssured under Maven; do not invent TypeScript specs.
10. If a task asks for a code or test change, use file tools to make the change.
   Do not respond with a tool-shaped JSON object or patch suggestion as the
   final result. Do not invent endpoints, base URLs, request bodies, or DTOs;
   derive test inputs from existing fixtures, service decision rules,
   controller mappings, OpenAPI, or existing tests.
11. If a test expects behavior that is not implemented or documented, stop and
   report a QA/product gap instead of silently removing or rewriting the test.
   Example: a `400` expectation for `customerId=INVALID_ID_FORMAT` requires
   actual format validation plus OpenAPI updates; `@NotBlank` only covers
   missing or blank values.
12. Update the OpenAPI contract when response fields or endpoint behavior changes.
13. Check deployment assets for ports, probes, env vars, image names, or runtime
   assumptions affected by the change.

## Quality Gates

- Service behavior matches acceptance criteria.
- OpenAPI contract matches response shape.
- Unit or focused service tests cover behavior changes.
- RestAssured or service-owned API tests cover the external contract.
- Deployment impact is checked and either updated or explicitly reported as no
  change needed.
- No broad repo scan is used when the YAML points to exact files or folders.
- `target_files` paths are used before fuzzy file search when present.
- No hallucinated paths or test files are used; every edited test file exists
  before modification unless the task explicitly asks for a new test file.
- No placeholder hosts, invented endpoint paths, invented request bodies, or
  made-up API projects are used.
- No "edit JSON" or pseudo-tool output is returned in place of an actual file
  change.
- Unsupported test expectations are reported as implementation/OpenAPI gaps
  with options, not hidden by deleting the test.

## Example Prompts

```text
Use the context in contexts/current/service-context.yml. Add a response field to
GET /xyz, update OpenAPI, and add RestAssured coverage.
```

```text
Using the current service context, verify whether this change needs deployment
updates and add only the missing API tests.
```

```text
For the existing customer risk API test, add one assertion that riskCategory is
not empty.
```

```text
Add one more API test in CustomerRiskApiTest.java for riskCategory when it is
MEDIUM.
```

```text
I added an invalid customerId API test. Run it and tell me whether the service
supports that behavior or whether this is a product/contract gap.
```

## Stop Condition

Stop when the requested behavior is implemented, the relevant verification
commands have run or blockers are reported, and the final answer names the files
changed plus the validation result.
