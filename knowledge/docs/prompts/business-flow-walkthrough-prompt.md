# Business Flow Walkthrough Prompt

Use this prompt to evaluate read-only business-flow explanation quality.

```text
Walk through the business flow for GET /xyz from HTTP request to response.

Use the project instructions and explicitly selected service task. Do not edit files.
Explain the controller entrypoint, validation behavior, service decision rules,
response fields, OpenAPI contract, and tests that prove the behavior.
Keep the answer concise and include file references.
```

Expected routing:

- Read root routing and `services/microservices/AGENTS.md`.
- Select the requested project task under `contexts/tasks/`; `ABC-123.yml` is
  a sanitized example. Read its matching `contexts/.resolved/` output, using an
  explicit `--context` path when resolving missing or stale output.
- Read endpoint/controller/service/DTO/OpenAPI/test files only.
- Do not edit files.
- Explain low, medium, high, missing customerId, and blank customerId behavior.
- Call out that nonblank arbitrary customerId values are evaluated by the
  service unless a separate format validation rule is added to service code and
  OpenAPI.
- Include precise file references.

Paths in this template are workspace-relative. From the project root use local
equivalents; outside the workspace follow local instructions and native checks.
