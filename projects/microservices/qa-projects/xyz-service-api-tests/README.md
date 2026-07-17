# xyz-service-api-tests

RestAssured tests for `xyz-service`.

Start the service first:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices/xyz-service
mvn spring-boot:run
```

Run the API tests from another terminal:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices
mvn -pl qa-projects/xyz-service-api-tests -am test
```

Override the target environment with system properties:

```bash
mvn -pl qa-projects/xyz-service-api-tests -am test \
  -Dapi.baseUri=http://localhost \
  -Dapi.port=8080 \
  -Dapi.basePath=
```
