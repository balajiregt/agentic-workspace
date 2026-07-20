# Agentic Workspace Instructions

Before any microservice code, API test, OpenAPI, or deployment change, read the
small current task context:

```text
contexts/current/service-context.yml
```

Then read the generated resolved context when it exists:

```text
contexts/current/resolved-context.yml
```

If the resolved context is missing or stale, run:

```text
npm run context:resolve
```

Use `repository_topology` from the task or resolved YAML before deciding where
tests or deployment changes belong.

For service/API/test work, follow:

```text
skills/microservice-change/SKILL.md
```

Default routing:

- If `service_and_tests` is `same-repo`, keep service-owned tests inside the
  service repo.
- If `service_and_tests` is `split-qa`, keep reusable API-test utilities in the
  shared QA project and actual service API tests in the service-specific QA
  project.
- If deployment is separate, inspect deployment files only for relevant ports,
  probes, images, env vars, or runtime assumptions.

Context discipline:

- Start from YAML and skills, then open only the files needed for the endpoint,
  field, test, or deployment impact.
- Keep `contexts/current/service-context.yml` small and task-specific. Do not
  bloat it with stable service paths, commands, or response examples.
- Use `contexts/current/resolved-context.yml` for exact repo paths, resolved
  files, contract/source hints, and verification commands.
- For API-test edits, prefer `resolved_files.api_test` over filename guessing or
  broad search.
- Before creating, renaming, or appending to a test file, list existing test
  files under the path declared by `resolved_repositories` and choose the
  matching existing file.
- If the user names a test file or class, verify the exact case-sensitive path
  from disk under the YAML-declared test roots. If the prompt's spelling or
  casing differs, map it to the existing file and report that mapping; do not
  create a new near-match path.
- Do not invent test frameworks, file extensions, or repo paths. Keep the API
  testing framework already present in the resolved test project.
- Do not invent endpoints, base URLs, request bodies, or DTOs. Use the endpoint,
  fixtures, controller, OpenAPI, and existing test patterns found in the scoped
  files.
- Do not use a broad repo dump when the YAML points to exact repos or folders.
- When the user asks for a code/test change, apply the change with file tools.
  Do not answer with a JSON object that describes an edit; that is only a plan,
  not a completed change.
- When a new or modified test expects behavior not implemented by the service
  or documented in OpenAPI, treat it as a QA/product gap. Do not silently delete
  or rewrite the test just to make the suite pass. Report the gap and the
  concrete options: update service plus OpenAPI, mark the test pending/disabled
  with a reason, or change the test expectation.
- If the user asks whether an expectation is supported, a test bug, or a
  product/contract gap, treat the task as read-only analysis unless they
  explicitly ask to implement the service/contract change.
- Run the verification commands from the YAML when the change touches behavior.
- Report changed files, validation commands, and any skipped gates.
