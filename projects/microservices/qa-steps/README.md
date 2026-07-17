# qa-steps

Shared API testing support for microservice projects.

This project intentionally contains reusable utilities, not service-specific
test cases. Keep real tests in `qa-projects/<service>-api-tests`.

Common folders:

```text
src/main/java/com/agentic/workspace/qa/
  assertions/   -> reusable response/body assertions
  client/       -> RestAssured request specification builders
  config/       -> base URI, port, and path configuration
  fixtures/     -> stable test data helpers
```
