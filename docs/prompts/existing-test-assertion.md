---
description: Add one assertion to an existing API test without creating new files
argument-hint: "[endpoint or field details]"
---
For the existing API test, add only this missing assertion:

$ARGUMENTS

Before editing:

- Read AGENTS.md.
- Read contexts/current/service-context.yml.
- Read contexts/current/resolved-context.yml. If it is missing, run
  `npm run context:resolve`.
- If resolved_files.api_test exists, open and edit that exact file.
- If service_context.behavior_contract exists, use its exact expected values.
- Follow repository_topology and resolved_repositories from the resolved context.
- List existing test files under the QA or service test path declared by the YAML.
- Verify any user-mentioned test filename/class against the exact
  case-sensitive file path on disk. If the prompt uses a near-match name, map it
  to the real existing file and report that mapping.
- Check whether the exact endpoint/input/expected behavior is already covered.
  If yes, enhance the existing test with a missing assertion or report existing
  coverage instead of adding a duplicate test.
- Edit the existing test file that already covers the endpoint.

Do not create, rename, or append to unrelated test files. Do not invent
frameworks, paths, DTOs, methods, endpoints, base URLs, request bodies, or
expected response text. Use the repo's existing Java, JUnit, RestAssured, Maven,
fixtures, controller, service_context.behavior_contract, and OpenAPI patterns.
Apply the file edit with tools, then run the relevant verification command and
report changed files plus test result.
