---
description: Add one assertion to an existing API test without creating new files
argument-hint: "[endpoint or field details]"
---
For the existing API test, add only this missing assertion:

$ARGUMENTS

Before editing:

- Read AGENTS.md.
- Read contexts/current/service-context.yml.
- If target_files.api_test exists in the YAML, open and edit that exact file.
- Follow repository_topology and related_repositories.local_path.
- List existing test files under the QA or service test path declared by the YAML.
- Verify any user-mentioned test filename/class against the exact
  case-sensitive file path on disk. If the prompt uses a near-match name, map it
  to the real existing file and report that mapping.
- Edit the existing test file that already covers the endpoint.

Do not create, rename, or append to unrelated test files. Do not invent
frameworks, paths, DTOs, methods, endpoints, base URLs, or request bodies. Use
the repo's existing Java, JUnit, RestAssured, Maven, fixtures, controller, and
OpenAPI patterns. Apply the file edit with tools, then run the relevant
verification command and report changed files plus test result.
