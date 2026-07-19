# Business Flow Walkthrough Prompt

Use this prompt to evaluate read-only business-flow explanation quality.

```text
Walk through the business flow for GET /xyz from HTTP request to response.

Use the workspace instructions and current service context. Do not edit files.
Explain the controller entrypoint, validation behavior, service decision rules,
response fields, OpenAPI contract, and tests that prove the behavior.
Keep the answer concise and include file references.
```

Expected routing:

- Read `AGENTS.md`.
- Read `contexts/current/service-context.yml`.
- Read endpoint/controller/service/DTO/OpenAPI/test files only.
- Do not edit files.
- Explain low, medium, high, missing customerId, and blank customerId behavior.
- Call out that nonblank arbitrary customerId values are evaluated by the
  service unless a separate format validation rule is added to service code and
  OpenAPI.
- Include precise file references.
