# Agent trial protocol

This directory owns the workspace's controlled-trial protocol and shared
collection tools: does workspace context help an agent complete a fixed task?
Playwright test-quality evaluation belongs to Playwright Agent's `quality/`. Project-specific tests, fixtures, mutation tooling and private evidence
remain with the owning project. Follow [the project workflow](../../knowledge/docs/project-workflow.md)
before selecting context or running an experiment; this organisation change
does not run or republish any benchmark.

This is benchmark instrumentation, not evidence that an AI agent is faster or better. No live agent baseline/framework comparison has been completed. The CRM and Java oracles run against synthetic fixtures.

## Run a matched experiment

1. Select an immutable task from `evidence/trials/tasks.json`; its `target` names the project, path and independent oracle. Freeze the target source snapshot, external oracle and exact prompt. Use SHA256 hashes of the prompt and target snapshot in the metadata; a Git SHA1 is not a SHA256 snapshot hash.
2. Use separate clean branches/worktrees for baseline and framework arms. Baseline gets the same requirements and target; framework additionally gets its documented context/helpers. Keep model/version, permissions, machine, oracle and time budget identical. Alternate arm order across at least three repeat numbers. Never change the gold/oracle to accommodate an agent answer.
3. Record actual UTC start/finish timestamps including model/tool execution. Copy `trial-template.json`, supply a unique trial ID, task, arm, repeat, model/version and hashes. Use `live-agent` for real model work and `scripted-validation` only for collector smoke checks. Do not relabel browser runtime as agent completion time.
4. Execute the independent required tests with retries disabled and export a JSON report. Capture provider token usage and its evidence source when available. A dated public price converts actual tokens to an **estimate**, not invoice cost. Leave usage/pricing null otherwise.
5. Review the diff: record incorrect changes and human correction time with a reviewer evidence reference, or keep both null. Count unrelated regressions, invalid assertions and unwanted application edits separately in that review. Passing the required oracle is operational completion, not exhaustive correctness.
6. Run `npm run evidence:trial:collect -- METADATA.json REPORT.json`, then `npm run evidence:trial:summary`. Trial writes reject overwrites. Summaries reject duplicate arm/repeat identities and separate incompatible model, target and evidence kinds. Retain failed/skipped/missing required checks as incomplete work.

Results, traces, trial records and reviewer notes stay ignored under `evidence/results/`. Publish only reviewed aggregate evidence, with denominator, date, environment, source revision, report hash and limitations. Prompt/target hashes do not prove a fair experiment by themselves; retain the underlying controlled records privately. Human time and unknown costs must never become zero.

## Maven API evidence without a browser dependency

Use the existing `services/microservices/xyz-service` and `CustomerRiskApiTest` oracle for task `api-customer-risk`. Start the service with `mvn spring-boot:run -Dspring-boot.run.arguments=--server.port=4283` from its module. From `services/microservices`, run `mvn -pl qa-projects/xyz-service-api-tests -am test -Dapi.port=4283`.

Normalize its exact Surefire report using `python3 evidence/trials/junit_to_report.py evidence/results/api-oracle.json services/microservices/qa-projects/xyz-service-api-tests/target/surefire-reports/TEST-com.agentic.workspace.qa.xyz.tests.CustomerRiskApiTest.xml`. Then collect that JSON with the task metadata. The adapter preserves failures and skips, rejects empty XML and DTD/entities, hashes input reports, and retains method identities. Run `npm run evidence:test` for collector/adapter regression checks.

The three CRM tasks target Playwright Agent's bundled synthetic CRM (`qa/playwright-agent/examples/sample-crm-app`), which serves `/api/session`, `/api/accounts/export` and `/crm/admin/users`. Run their oracles from that project; this repository does not import UI dependencies into Maven. Use the same target/oracle snapshots when comparing those tasks across workflows.

Local validation 2026-10-11: all five existing RestAssured API cases passed against the isolated sample service; collector and JUnit adapter checks passed. This validates the oracle and instrumentation, not agent performance.

## Retired generation-trial tracks

The cloud and local (Pi + llama.cpp) generation pilots ran through the retired
framework-benchmark dashboard's `trials/` scripts. Their wrapper and publisher
are preserved under ignored `artifacts/retired/evaluation-publication-20261111/`.
Any earlier published charts were pilot instrumentation, not evidence that an
agent is faster or better. A future trial should run with the protocol above and
the collector in this folder, keeping results private until reviewed.
