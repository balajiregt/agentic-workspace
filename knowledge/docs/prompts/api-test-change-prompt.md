# API Test Change Prompt

Use this prompt to validate that the workspace routes a test-only request
through project-local instructions and a selected task without requiring the
user to spell out every source path.

```text
Add API test coverage for an uncovered validation case on the affected endpoint.

Use the project instructions and explicitly selected service task to decide where the
test belongs. Do not change service code unless the existing behavior is wrong.
If the requested assertion expects behavior that is not implemented or
documented in OpenAPI, report it as a QA/product gap instead of deleting or
rewriting the test.
After the change, run the relevant verification command and report the context
files inspected, files changed, and validation result.
```

Paths in this template are workspace-relative. From the project root use local
equivalents; outside the workspace follow local instructions and native checks.
