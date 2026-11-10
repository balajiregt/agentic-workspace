---
description: Add one assertion to an existing API test without creating new files
argument-hint: "[endpoint or field details]"
---
For the existing API test, add only this missing assertion:

$ARGUMENTS

Before editing:

- Read projects/microservices/AGENTS.md and select the requested task under
  projects/microservices/contexts/tasks/; ABC-123.yml is a sanitized example.
- Read that task's matching project contexts/.resolved/ output. Regenerate with
  the workspace resolver and an explicit --context argument if missing or stale.
- If resolved_files.api_test exists, open and edit that exact file.
- Use resolved_files.openapi and resolved_files.service for exact expected
  values before adding assertions.
- Follow repository_topology and resolved_repositories from the resolved context.
- List existing test files under the QA or service test path from resolved
  context.
- Verify any user-mentioned test filename/class against the exact
  case-sensitive file path on disk. If the prompt uses a near-match name, map it
  to the real existing file and report that mapping.
- Check whether the exact endpoint/input/expected behavior is already covered.
  If yes, enhance the existing test with a missing assertion or report existing
  coverage instead of adding a duplicate test.
- Edit the existing test file that already covers the endpoint.

Do not create, rename, or append to unrelated test files. Do not invent
frameworks, paths, DTOs, methods, endpoints, base URLs, request bodies, or
expected response text. Use the repo's existing API test framework, fixtures or
test data helpers, controller, service code, and OpenAPI patterns.
Apply the file edit with tools, then run the relevant verification command and
report changed files plus test result.

Paths in this template are workspace-relative. From the project root use local
equivalents; outside the workspace follow local instructions and native checks.
