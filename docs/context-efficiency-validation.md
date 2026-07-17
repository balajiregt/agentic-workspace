# Validating Context Efficiency on an 8 GB MacBook Air

This workspace should be validated on two axes:

1. The agent receives enough context to make the right cross-repo change.
2. The prompt stays small enough for a local 8 GB machine to remain usable.

## Metrics to Show

Use these numbers in the blog or README:

- **Central context tokens**: approximate tokens in `contexts/current/service-context.yml`.
- **Central context plus skills tokens**: approximate tokens in YAML plus local `SKILL.md` files.
- **Full corpus tokens**: approximate tokens if all relevant microservice files were pasted into the prompt.
- **Compression ratio**: `full corpus tokens / central context tokens`.
- **Compression ratio with skills**: `full corpus tokens / (central context tokens + skill tokens)`.
- **Tokens saved**: `full corpus tokens - central context tokens`.
- **Agent hit rate**: whether the agent touches the expected service, contract, deployment, shared QA, and API test folders.
- **Verification pass rate**: unit/API tests passing after the agent change.
- **Wall-clock time**: time to complete the validation commands.
- **Memory pressure**: Activity Monitor memory pressure while the local model and tests are running.

The token counts are approximate. They are still useful because the same script
can be run before and after the workspace grows.

## Run the Context Report

```bash
python3 /Users/balaji/agentic-workspace/scripts/context_efficiency_report.py
```

JSON output for charts:

```bash
python3 /Users/balaji/agentic-workspace/scripts/context_efficiency_report.py --format json
```

## Run the Build and API Validation

If Maven is installed:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices
mvn -pl xyz-service,qa-steps -am test
```

Start the service:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices/xyz-service
mvn spring-boot:run
```

Run the API tests in another terminal:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices
mvn -pl qa-projects/xyz-service-api-tests -am test
```

## Local-Agent Efficiency Claim

A practical claim for the blog:

> Instead of pushing the whole microservice workspace into the model, the agent
> starts from a small YAML control plane and follows explicit local paths only
> when needed. This keeps the prompt compact, reduces hallucinated ownership, and
> leaves more context budget for the actual code diff.

For an 8 GB MacBook Air, the most useful proof is not raw speed. It is showing
that the local workflow remains bounded: small prompt, explicit paths, focused
file reads, passing tests, and no need to preload every repository file.
