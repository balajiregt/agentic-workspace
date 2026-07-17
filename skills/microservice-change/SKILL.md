---
name: microservice-change
description: Make context-aware microservice changes in the agentic workspace across same-repo or split-repo topologies. Use when a task references service-context.yml, Jira-driven service changes, Spring Boot code, OpenAPI alignment, deployment impact checks, service-owned tests, shared QA utilities, or RestAssured API tests under projects/microservices.
---

# Microservice Change

## Goal

Change the smallest correct set of files across service code, contract,
deployment, and tests for the topology declared in the context YAML.

## Inputs

- Read `/Users/balaji/agentic-workspace/contexts/current/service-context.yml`.
- Treat `related_repositories.*.local_path` as the source of truth for repo paths.
- Treat `repository_topology` as the source of truth for whether tests and
  deployment assets live in the service repo or separate repos.
- Treat `work_item.affected_endpoints`, `affected_fields`, and `acceptance_criteria`
  as the behavioral target.

## Procedure

1. Inspect the context YAML before editing.
2. Inspect only the files needed to confirm the endpoint, DTO, contract, tests,
   and deployment impact.
3. Prefer existing project patterns over new abstractions.
4. If `service_and_tests` is `same-repo`, keep unit, integration, and API tests
   inside the service repo.
5. If `service_and_tests` is `split-qa`, keep reusable RestAssured support in
   `qa-steps` and actual service API tests in `qa-projects/<service>-api-tests`.
6. Update the OpenAPI contract when response fields or endpoint behavior changes.
7. Check deployment assets for ports, probes, env vars, image names, or runtime
   assumptions affected by the change.

## Quality Gates

- Service behavior matches acceptance criteria.
- OpenAPI contract matches response shape.
- Unit or focused service tests cover behavior changes.
- RestAssured or service-owned API tests cover the external contract.
- Deployment impact is checked and either updated or explicitly reported as no
  change needed.
- No broad repo scan is used when the YAML points to exact files or folders.

## Example Prompts

```text
Use the context in contexts/current/service-context.yml. Add a response field to
GET /xyz, update OpenAPI, and add RestAssured coverage.
```

```text
Using the current service context, verify whether this change needs deployment
updates and add only the missing API tests.
```

## Stop Condition

Stop when the requested behavior is implemented, the relevant verification
commands have run or blockers are reported, and the final answer names the files
changed plus the validation result.
