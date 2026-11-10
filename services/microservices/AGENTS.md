# Microservices and API automation

This aggregate owns the sample Spring Boot service, its contract and deployment
assets, shared RestAssured support, and service-specific API tests. Read
[architecture and ownership](docs/architecture.md) for the source map. Commands
below run from this directory unless stated otherwise.

## Work on one task

1. Select the requested task under `contexts/tasks/`; the sanitized example is
   `ABC-123.yml`. Treat it as a work item, not an instruction to repeat its work
   on every request. Keep new private requirements and exports ignored.
2. In the workspace, follow the shared `microservice-change` skill. Resolve the
   selected task from the workspace root:
   `npm run context:resolve -- --context services/microservices/contexts/tasks/ABC-123.yml`.
   Read `contexts/.resolved/ABC-123.yml`; paths and generated commands are relative
   to the workspace root. Use the selected task's corresponding output, never
   another session's output. Regenerate after task or relevant source changes.
3. Inspect `repository_topology` and the resolved exact files before searching.
   When working outside the workspace, use this aggregate's source map, module
   READMEs and commands directly; the shared resolver is optional tooling.
4. Confirm expectations against OpenAPI, controller, service, DTOs and existing
   tests. Task YAML holds intent; source and contract hold implemented facts.
5. Make the smallest authorized change and run the applicable local checks.
6. Retain ignored evidence, report actual results and skipped gates, then update
   project docs only for durable, verified lessons relevant to future work.

## Boundaries

- Keep service code and unit tests in `xyz-service`; real API cases in
  `qa-projects/xyz-service-api-tests`; reusable fixtures, client setup and
  assertions in `qa-steps`. These are Maven modules, not additional frameworks.
- Keep deployment changes in `xyz-deployments`. Review ports, probes, environment
  and image assumptions when service changes affect them.
- Keep Playwright, mockserver behaviour and UI dependencies outside this
  aggregate. Do not introduce another API test language or runner.
- Reuse equivalent API coverage; add a missing assertion before duplicating a
  scenario. Derive exact values from source, contract and existing fixtures.
- An expectation unsupported by source or contract is a product/contract gap.
  Report it; do not weaken tests to obtain a pass. Requests to classify a gap
  remain read-only unless implementation is requested.
- Keep credentials, raw private requirements and reports out of committed docs.
  Do not publish metrics, deploy, change providers or enable hooks incidentally.

## Local checks and evidence

- Service logic: `mvn -pl xyz-service test`.
- API behaviour: start `mvn -pl xyz-service spring-boot:run -Dspring-boot.run.arguments=--server.port=8081`
  in one terminal; in another run
  `mvn -pl qa-projects/xyz-service-api-tests -am test -Dapi.port=8081`.
  Use an explicitly selected matching port if 8081 is occupied.
- Reports: each tested module's ignored `target/surefire-reports/`. Retain
  additional private evidence under ignored `artifacts/`; include task, source
  revision, command, environment and outcome when recording it.
- API oracles prove exercised service behaviour. Cross-project agent comparisons
  remain in the workspace's shared evaluation tooling; passing API tests alone
  does not establish agent quality or performance.

Finish by reporting changed files, commands run, evidence locations, failures,
skipped gates and any remaining contract or deployment gap.
