# Controlled agent trials

This is benchmark instrumentation, not evidence that an AI agent is faster or better. No live agent baseline/framework comparison has been completed. The CRM and Java oracles run against synthetic fixtures.

## Run a matched experiment

1. Select an immutable task from `benchmarks/tasks.json`. Freeze the target source snapshot, external oracle and exact prompt. Use SHA256 hashes of the prompt and target snapshot in the metadata; a Git SHA1 is not a SHA256 snapshot hash.
2. Use separate clean branches/worktrees for baseline and framework arms. Baseline gets the same requirements and target; framework additionally gets its documented context/helpers. Keep model/version, permissions, machine, oracle and time budget identical. Alternate arm order across at least three repeat numbers. Never change the gold/oracle to accommodate an agent answer.
3. Record actual UTC start/finish timestamps including model/tool execution. Copy `trial-template.json`, supply a unique trial ID, task, arm, repeat, model/version and hashes. Use `live-agent` for real model work and `scripted-validation` only for collector smoke checks. Do not relabel browser runtime as agent completion time.
4. Execute the independent required tests with retries disabled and export a JSON report. Capture provider token usage and its evidence source when available. A dated public price converts actual tokens to an **estimate**, not invoice cost. Leave usage/pricing null otherwise.
5. Review the diff: record incorrect changes and human correction time with a reviewer evidence reference, or keep both null. Count unrelated regressions, invalid assertions and unwanted application edits separately in that review. Passing the required oracle is operational completion, not exhaustive correctness.
6. Run `npm run benchmark:collect -- METADATA.json REPORT.json`, then `npm run benchmark:summary`. Trial writes reject overwrites. Summaries reject duplicate arm/repeat identities and separate incompatible model, target and evidence kinds. Retain failed/skipped/missing required checks as incomplete work.

Results, traces, trial records and reviewer notes stay ignored under `benchmark-results/`. Publish only reviewed aggregate evidence, with denominator, date, environment, source revision, report hash and limitations. Prompt/target hashes do not prove a fair experiment by themselves; retain the underlying controlled records privately. Human time and unknown costs must never become zero.

## Maven API evidence without a browser dependency

Use the existing `projects/microservices/xyz-service` and `CustomerRiskApiTest` oracle for task `api-customer-risk`. Start the service with `mvn spring-boot:run -Dspring-boot.run.arguments=--server.port=4283` from its module. From `projects/microservices`, run `mvn -pl qa-projects/xyz-service-api-tests -am test -Dapi.port=4283`.

Normalize its exact Surefire report using `python3 benchmarks/junit_to_report.py benchmark-results/api-oracle.json projects/microservices/qa-projects/xyz-service-api-tests/target/surefire-reports/TEST-com.agentic.workspace.qa.xyz.tests.CustomerRiskApiTest.xml`. Then collect that JSON with the task metadata. The adapter preserves failures and skips, rejects empty XML and DTD/entities, hashes input reports, and retains method identities. Run `npm run benchmark:test` for collector/adapter regression checks.

The shared CRM tasks can also use the companion Playwright harness demo and oracle; this repository does not import UI dependencies into Maven. Use the same target/oracle snapshots when comparing those tasks across workflows.

Local validation 2026-10-11: all five existing RestAssured API cases passed against the isolated sample service; collector and JUnit adapter checks passed. This validates the oracle and instrumentation, not agent performance.

See [automatic dashboard publication](AUTOMATIC-PUBLICATION.md) for the canonical runner, CI, privacy controls and retry behaviour.

## Controlled baseline / framework generation trials

The first live pilot uses the existing sample app, three repeats per condition, the same model settings, and an independent healthy-app + fault-injection evaluation of unchanged generated tests. This is a context-assisted generation experiment, not the complete autonomous workflow. Human correction effort remains unmeasured; standard API-equivalent cost is an estimate, not billed spend.

[Protocol, runner and limitations](https://github.com/balajiregt/framework-benchmark-dashboard/blob/main/trials/README.md) · [Live charts and evidence](https://framework-benchmarks-balaji.netlify.app/#controlled-trials)

Run from this checkout after installing the documented prerequisites:

```sh
npm run benchmark:trials -- --dashboard /path/to/framework-benchmark-dashboard --peer /path/to/other-app-repo --campaign /path/to/private-campaign
```

Use the API checkout as peer from Playwright, or Playwright as peer from API. The campaign directory must be outside all source checkouts. The command prepares/resumes 12 calls, evaluates them and publishes both result feeds automatically. Use `--no-publish` for local-only work. A future run reads new results without dashboard deployment. These model calls are explicit local runs, not automatically triggered by every source push. Existing `npm run benchmark` continues to run only the original browser/API execution benchmark.

### Local model trials

The workspace's Pi + llama.cpp setup is also benchmarked as a separate **local generation** track. The first run reuses the installed Gemma 4 E2B QAT model and existing 8192-token server. It uses the same API prompt pairs and fault checks as the cloud pilot, with three seeds per condition. Pi's tool/edit loop is outside this first protocol. Local output throughput and wall time are measured; electricity and total operating cost remain unknown. Instructions are in the [local trial protocol](https://github.com/balajiregt/framework-benchmark-dashboard/blob/main/trials/README.md#local-llamacpp--gemma-api-track). Results automatically publish to `benchmark-results/local-trials.json` and appear in the dashboard's Local Gemma tab.

```sh
npm run benchmark:trials:local -- --dashboard /path/to/framework-benchmark-dashboard --cloud-campaign /path/to/private-cloud-campaign --campaign /path/to/private-local-campaign
```

This command retains failed attempts and stops on provider errors for inspection. It publishes accounted-for campaigns automatically after generation and independent grading finish.
