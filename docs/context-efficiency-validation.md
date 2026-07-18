# Validating Context Efficiency on an 8 GB MacBook Air

This workspace should be validated on two axes:

1. The agent receives enough context to make the right cross-repo change.
2. The prompt stays small enough for a local 8 GB machine to remain usable.

## Metrics to Show

Use these numbers in the blog or README:

- **Central context tokens**: approximate tokens in `contexts/current/service-context.yml`.
- **Central context plus skills tokens**: approximate tokens in YAML plus local `SKILL.md` files.
- **Task profile tokens**: approximate tokens for a realistic focused change,
  such as YAML + skill + endpoint contract + existing API test + shared QA
  utilities.
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

Focused API-test-change output:

```bash
npm run context:api-test
```

Other focused task profiles:

```bash
npm run context:new-endpoint
npm run context:shared-qa
npm run context:walkthrough
```

This reports three useful layers:

```text
baseline context = service-context.yml
workflow context = service-context.yml + SKILL.md files
task context     = workflow context + only files needed for the endpoint/test change
```

Current focused API-test-change proof:

```text
Central context tokens: 594
Central context plus skills tokens: 1754
Full microservices corpus tokens: 5077
Task profile tokens (api-test-change): 3001
Central context compression ratio: 8.55x
Task profile compression ratio: 1.69x
```

The task profile is larger than the YAML because it includes the actual code,
contract, shared RestAssured helpers, and API test file needed for the change.
It is still bounded by the context route instead of loading every microservice
file up front.

Current task-profile sizing:

| Task profile | Estimated tokens | Local 4096 ctx action |
| --- | ---: | --- |
| `shared-qa-utility-change` | 2988 | Fits if output stays focused |
| `business-flow-walkthrough` | 3470 | Fits as read-only explanation |
| `api-test-change` | 3001 | Fits if scoped to existing tests |
| `new-endpoint-change` | 4128 | Split into service/contract, tests, deployment passes |

The validated local edit profile intentionally keeps `contextWindow=4096`.
When a task profile exceeds that budget, the scalable approach is staged
execution, not loading a larger unvalidated local profile.

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

## Editing-Agent Validation

Context efficiency and edit automation are separate checks. Before claiming a
local Pi profile can apply edits, verify structured tool-call support:

```bash
npm run agent:doctor
```

Current working local model proof:

```text
Model: unsloth/gemma-4-E2B-it-qat-GGUF:UD-Q4_K_XL
TOOL_CALL_CHECK=PASS structured tool_calls returned: read
```

Use this model for Pi file-edit validation. A model/profile is only accepted in
this workspace after the doctor passes and the relevant Maven verification also
passes.
