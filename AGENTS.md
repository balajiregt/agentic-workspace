# Agentic Workspace Instructions

For microservice, API test, OpenAPI, or deployment work:

1. Read `contexts/current/service-context.yml`.
2. Read `contexts/current/resolved-context.yml`; if it is missing or stale, run
   `npm run context:resolve`.
3. Follow `skills/microservice-change/SKILL.md`.

Keep the current task context small. Do not add stable service paths, commands,
or behavior examples to `service-context.yml`; the resolver derives exact paths
from repo layout, OpenAPI, and source code.

Core guardrails:

- Use `repository_topology` before deciding where code, tests, and deployment
  changes belong.
- Prefer `resolved_files.*` and `resolved_repositories.*` over fuzzy search.
- Keep the existing API test framework; do not invent new paths, file types,
  endpoints, base URLs, request bodies, or DTOs.
- If an API test expects behavior not implemented by source or documented in
  OpenAPI, report a product/contract gap. Do not rewrite the test just to make
  the suite pass.
- If the user asks whether an expectation is supported, a test bug, or a gap,
  treat it as read-only analysis unless implementation is explicitly requested.
- Report changed files, verification commands, and skipped gates.
