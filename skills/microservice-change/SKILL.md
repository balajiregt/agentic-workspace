---
name: microservice-change
description: Make context-aware microservice changes in the agentic workspace across same-repo or split-repo topologies. Use when a task references service-context.yml, Jira-driven service changes, API code, OpenAPI alignment, deployment impact checks, service-owned tests, shared QA utilities, or API tests under projects/microservices.
---

# Microservice Change

## Goal

Change the smallest correct set of files across service code, contract,
deployment, and tests for the topology declared in the context YAML.

## Inputs

- Read `contexts/current/service-context.yml` from the workspace root.
- Read `contexts/current/resolved-context.yml` when it exists. If it is missing,
  run `npm run context:resolve`.
- Treat `resolved_repositories.*` as the source of truth for repo paths when
  resolved context exists.
- Treat `resolved_files.*` as the first-choice file map when present. It narrows
  the task from repo-level routing to exact controller, service, OpenAPI, API
  test, fixture, or assertion files.
- Treat `repository_topology` as the source of truth for whether tests and
  deployment assets live in the service repo or separate repos.
- Treat OpenAPI and service code as the source of truth for expected API
  behavior. Resolved context points to those files; it should not duplicate the
  API contract.
- Treat `work_item.affected_endpoints`, `affected_fields`, and `acceptance_criteria`
  as the behavioral target.

## Procedure

1. Inspect the context YAML before editing.
2. If resolved context exists, open the relevant exact target file before
   searching. For API-test edits, open `resolved_files.api_test`.
3. Use OpenAPI and service code for expected API values before inventing
   assertions. For new assertions, confirm exact strings or values from those
   sources.
4. Inspect only the files needed to confirm the endpoint, DTO, contract, tests,
   and deployment impact.
5. Prefer existing project patterns over new abstractions.
6. If `service_and_tests` is `same-repo`, keep unit, integration, and API tests
   inside the service repo.
7. If `service_and_tests` is `split-qa`, keep reusable API-test support in the
   shared QA project and actual service API tests in the service-specific QA
   project resolved from context.
8. If the user names a test file or class, validate the exact case-sensitive
   file path from disk under the YAML-declared test roots. If casing or spelling
   differs, use the existing file and say which prompt name was mapped. If
   `resolved_files.api_test` exists, use it as the mapping candidate.
9. Before adding a new API test, inspect the existing test file for equivalent
   endpoint, fixture/input, and expected behavior coverage. If the exact
   scenario is already covered, add only a missing assertion to that existing
   test or report that coverage already exists; do not duplicate the test unless
   the user explicitly asks for duplicate coverage.
10. For "add one assertion", "add one more API test", or "modify existing test"
   requests, edit the existing test file that already covers the endpoint; do
   not create, rename, append to, or assume files that were not listed from disk.
   Keep the repo's existing API test framework; do not introduce a different
   language, runner, or file type unless the user explicitly asks for a
   framework migration.
11. If a test expects behavior that is not implemented or documented, stop and
   report a QA/product gap instead of silently removing or rewriting the test.
   Example: a new negative test that expects a 4xx response for an input value
   allowed by the current contract requires a source/contract change before it
   can become passing coverage. If the user asks to classify whether an
   expectation is supported, a test bug, or a product/contract gap, do read-only
   analysis and do not edit tests. Use `derived_validation` from resolved
   context when present.
12. If a task asks for a code or test change, use file tools to make the change.
   Do not respond with a tool-shaped JSON object or patch suggestion as the
   final result. Do not invent endpoints, base URLs, request bodies, or DTOs;
   derive test inputs from existing fixtures, service decision rules,
   controller mappings, OpenAPI, or existing tests.
13. Update the OpenAPI contract when response fields or endpoint behavior changes.
14. Check deployment assets for ports, probes, env vars, image names, or runtime
   assumptions affected by the change.
15. Run verification commands in the YAML order. If the first command starts a
   long-running service, keep it running while executing the test command in a
   second terminal/session.

## Quality Gates

- Service behavior matches acceptance criteria.
- API assertions use exact values from service code or OpenAPI; no guessed
  substrings are used for expected response fields.
- OpenAPI contract matches response shape.
- Unit or focused service tests cover behavior changes.
- API tests cover the external contract using the existing project framework.
- Existing equivalent API coverage is reused or enhanced instead of duplicated.
- Deployment impact is checked and either updated or explicitly reported as no
  change needed.
- No broad repo scan is used when the YAML points to exact files or folders.
- `resolved_files` paths are used before fuzzy file search when present.
- No hallucinated paths or test files are used; every edited test file exists
  before modification unless the task explicitly asks for a new test file.
- No placeholder hosts, invented endpoint paths, invented request bodies, or
  made-up API projects are used.
- No "edit JSON" or pseudo-tool output is returned in place of an actual file
  change.
- Unsupported test expectations are reported as implementation/OpenAPI gaps
  with options, not hidden by deleting the test.
- Verification uses the configured API port from the YAML command, not an
  implicit default port.

## Example Prompts

```text
Use the context in contexts/current/service-context.yml. Add a response field to
the affected endpoint, update OpenAPI, and add API test coverage.
```

```text
Using the current service context, verify whether this change needs deployment
updates and add only the missing API tests.
```

```text
For the existing API test that covers the affected endpoint, add one missing
assertion for the affected response field.
```

```text
Add one more API test for the affected endpoint and response field.
```

```text
I added a negative API test expectation. Run a read-only analysis and tell me
whether the service supports that behavior or whether this is a product/contract
gap.
```

## Stop Condition

Stop when the requested behavior is implemented, the relevant verification
commands have run or blockers are reported, and the final answer names the files
changed plus the validation result.
