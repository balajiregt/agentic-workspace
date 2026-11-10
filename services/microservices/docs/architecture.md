# Microservices ownership and working context

This is the Maven aggregate for the sample API implementation and RestAssured
automation. Its entrypoint is [AGENTS.md](../AGENTS.md). Project knowledge lives
in these docs and existing module READMEs; there is no second contract or test
framework in a separate knowledge folder.

## Sources of truth

| Owner | Authoritative files and guidance |
| --- | --- |
| Module graph and build | [Aggregate POM](../pom.xml) |
| API request and response contract | [OpenAPI](../xyz-service/src/main/resources/openapi/xyz-service.openapi.yml) |
| Request handling and validation | [Controller](../xyz-service/src/main/java/com/agentic/workspace/xyz/api/CustomerRiskController.java) |
| Implemented decision behaviour | [Service](../xyz-service/src/main/java/com/agentic/workspace/xyz/service/CustomerRiskService.java), its DTO/domain source and [unit tests](../xyz-service/src/test/java/com/agentic/workspace/xyz/service/CustomerRiskServiceTest.java) |
| Reusable API support | [qa-steps](../qa-steps/README.md): fixtures, client, configuration and assertions |
| External API checks | [API test module](../qa-projects/xyz-service-api-tests/README.md) and [existing test class](../qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java) |
| Deployment assumptions | [Deployment guidance](../xyz-deployments/README.md), [Compose](../xyz-deployments/docker-compose.yml) and [Kubernetes manifests](../xyz-deployments/k8s/xyz-service.yaml) |

The service and API tests are separate modules under this aggregate; reusable
support is separate from service-specific cases. Deployment assets are a
companion directory and are not a Maven module. Consult actual repository
boundaries and the selected task's topology before moving ownership.

Read the contract and implementation when deciding whether an expectation is
supported. Do not copy endpoint schemas, response strings, risk thresholds or
validation rules into YAML context or this document. A discrepancy between
contract, source and an expected assertion must be reported explicitly.

## Task inputs, derived context and knowledge

- `contexts/tasks/<work-item>.yml` contains task intent, acceptance criteria,
  affected behaviour, topology and scope. The committed `ABC-123.yml` is a
  sanitized example. New requirements or downloaded exports remain private and
  ignored by default; never treat the example as the current request.
- `contexts/.resolved/<work-item>.yml` is generated, ignored routing information
  derived from the selected task and current source. Use exact paths from it
  before fuzzy search. Regenerate after relevant changes; do not hand-maintain
  generated paths or copy an output from another task.
- Existing source, OpenAPI, configuration and module READMEs hold durable facts.
  Store a verified, reusable explanation or a material decision in `docs/` with
  links to its owner. Keep transient task notes, secrets and execution dumps out
  of durable documentation.
- Keep execution reports in module `target/` directories and additional private
  evidence in ignored `artifacts/`. Record the actual command, source revision,
  task and outcome. A failed or unrun gate remains failed or unrun.

The workspace resolver is a convenience, not a runtime dependency of this
aggregate. Outside the workspace, start with the ownership map above and run
the existing Maven commands in [AGENTS.md](../AGENTS.md). Keep API base URI, port
and base path aligned between the service and test configuration.

## Validation and evaluation ownership

Unit tests cover service logic. RestAssured tests exercise the external API with
shared fixtures and assertions. Both remain beside their owning modules.
Inspect deployment impact when a change affects runtime assumptions; do not
deploy as a side effect of a code or documentation task.

Shared controlled trials compare agent workflows across API and Playwright
projects. Their protocols and collectors remain workspace-owned. This aggregate
provides the API implementation and executable oracle; its green test reports
alone do not prove coverage completeness, agent accuracy, cost or speed gains.

Work in this order: choose the project, read local instructions, select the task,
inspect authoritative source, make the change, run local checks, retain evidence,
and promote only reusable verified lessons into project docs.
