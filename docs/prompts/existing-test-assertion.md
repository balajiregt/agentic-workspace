---
description: Add one assertion to an existing API test without creating new files
argument-hint: "[endpoint or field details]"
---
For the existing API test, add only this missing assertion:

$ARGUMENTS

Before editing:

- Read AGENTS.md.
- Read contexts/current/service-context.yml.
- Follow repository_topology and related_repositories.local_path.
- List existing test files under the QA or service test path declared by the YAML.
- Edit the existing test file that already covers the endpoint.

Do not create, rename, or append to unrelated test files. Do not invent
frameworks, paths, DTOs, methods, or endpoints. Use the repo's existing Java,
JUnit, RestAssured, and Maven patterns. Apply the file edit with tools, then run
the relevant verification command and report changed files plus test result.
