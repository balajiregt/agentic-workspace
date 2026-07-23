# Current Workspace State

Active validation slice:

```text
contexts/current/service-context.yml
```

Current service:

```text
projects/microservices/xyz-service
```

Current topology:

```text
service_and_tests: split-qa
deployment: separate-repo
```

Implication:

- Service code and OpenAPI live in `xyz-service`.
- Shared RestAssured support lives in `qa-steps`.
- Actual service API tests live in `qa-projects/xyz-service-api-tests`.
- Deployment impact is checked in `xyz-deployments`.

Current validation command:

```bash
cd projects/microservices
mvn -pl qa-projects/xyz-service-api-tests -am test
```
