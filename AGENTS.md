# Agentic Workspace Instructions

Before any microservice code, API test, OpenAPI, or deployment change, read:

```text
contexts/current/service-context.yml
```

Use `repository_topology` from that YAML before deciding where tests or
deployment changes belong.

For service/API/test work, follow:

```text
skills/microservice-change/SKILL.md
```

Default routing:

- If `service_and_tests` is `same-repo`, keep service-owned tests inside the
  service repo.
- If `service_and_tests` is `split-qa`, keep reusable RestAssured utilities in
  `qa-steps` and actual API tests in `qa-projects/<service>-api-tests`.
- If deployment is separate, inspect deployment files only for relevant ports,
  probes, images, env vars, or runtime assumptions.

Context discipline:

- Start from YAML and skills, then open only the files needed for the endpoint,
  field, test, or deployment impact.
- Before creating, renaming, or appending to a test file, list existing test
  files under the path declared by `related_repositories` and choose the
  matching existing file.
- Do not invent test frameworks, file extensions, or repo paths. This workspace
  uses Java, JUnit, RestAssured, and Maven for API tests; do not create
  TypeScript test files unless the repo already contains that framework.
- Do not use a broad repo dump when the YAML points to exact repos or folders.
- When the user asks for a code/test change, apply the change with file tools.
  Do not answer with a JSON object that describes an edit; that is only a plan,
  not a completed change.
- Run the verification commands from the YAML when the change touches behavior.
- Report changed files, validation commands, and any skipped gates.
