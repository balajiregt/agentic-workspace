# API Test Change Prompt

Use this prompt to validate that the workspace routes a test-only request
through the central context even when the user does not spell out every repo
path.

```text
Add RestAssured coverage for the GET /xyz blank customerId validation case.

Use the workspace instructions and current service context to decide where the
test belongs. Do not change service code unless the existing behavior is wrong.
If the requested assertion expects behavior that is not implemented or
documented in OpenAPI, report it as a QA/product gap instead of deleting or
rewriting the test.
After the change, run the relevant Maven verification command and report the
context files inspected, files changed, and validation result.
```
