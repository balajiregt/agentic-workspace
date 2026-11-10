# QA Gap Analysis Prompt

Use this read-only prompt when a new or modified API test fails because it may
be asking for behavior the service does not currently implement.

```text
I added or modified an API test with this expectation:

<describe the test expectation or paste the failing assertion>

Read projects/microservices/AGENTS.md and select the requested task under
projects/microservices/contexts/tasks/. Read its matching contexts/.resolved/
output; regenerate it with the workspace resolver and an explicit --context
argument if missing or stale. ABC-123.yml is a sanitized example, not the active task.
Inspect only the resolved controller, service, OpenAPI, shared QA utilities, and
API test files.

This is a read-only classification task. Do not edit files unless I explicitly
ask you to implement the service/contract change.

Do not delete, rename, or rewrite the test just to make the suite pass.
Do not add a new test for the unsupported expectation during this analysis.

Tell me whether the expectation is:
- already supported by service code and OpenAPI,
- a test bug, or
- a product/contract gap that needs service code plus OpenAPI updates.

If it is a gap, name the exact files that need behavior and contract updates,
and report the verification commands to run.

Answer in this order:

1. Classification: supported behavior, test bug, or product/contract gap.
2. Evidence from resolved_files.controller and resolved_files.service.
3. Evidence from resolved_files.openapi.
4. Files that would need changes if the gap should become supported behavior.
5. Verification commands.
```

Example:

```text
I added a negative API test that expects 4xx for a request value that currently
passes the OpenAPI schema. Run/analyze it and tell me whether this is supported
behavior, a test bug, or a product/contract gap.
```

Paths in this template are workspace-relative. From the project root use local
equivalents; outside the workspace follow local instructions and native checks.
