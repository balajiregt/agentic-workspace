# xyz-service

Dummy Spring Boot microservice for validating the local agentic workspace flow.

The service exposes one business endpoint:

```text
GET /xyz?customerId=CUST-1001
```

It returns a deterministic risk decision so API tests can assert behavior without
external dependencies.

## Run Locally

```bash
cd projects/microservices/xyz-service
mvn spring-boot:run
```

## Useful Checks

```bash
curl "http://localhost:8080/xyz?customerId=CUST-1001"
curl "http://localhost:8080/actuator/health"
```

The OpenAPI contract lives at:

```text
src/main/resources/openapi/xyz-service.openapi.yml
```
