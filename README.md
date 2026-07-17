# Agentic Workspace

This folder is the combined workspace for local coding-agent work.

```text
agentic-workspace/
  local-agents/       -> local GGUF, llama.cpp, Pi, and Kilo runtime
  context-starter/    -> agentic context reference material
  contexts/
    current/          -> current Jira/service context used by the agent
    examples/         -> microservice and monolith context examples
  projects/
    microservices/    -> Spring Boot service/deployment repos
    monolithic/       -> monolithic application repos
```

The `local-agents` and `context-starter` entries are symlinks, so this
workspace does not duplicate model files or llama.cpp builds.

## Local Models

From this workspace root:

```bash
npm run models
```

After extracting the clean zip, this will say no GGUF models are found. That is
expected because models are intentionally excluded. The first `serve:*` or
`agent:*` command downloads its GGUF on demand.

Manual server commands are still available:

```bash
npm run serve:gemma
npm run serve:fluently
npm run serve:qwen
```

For the 16 GB Mac only, start the larger Gemma 4 12B agentic v2 profile:

```bash
npm run serve:gemma12b-agentic16
```

The OpenAI-compatible endpoint is:

```text
http://127.0.0.1:8082/v1
```

Use model ID:

```text
local-model
```

## One-Command Pi Agent

Run these from the repo you want Pi to edit. Each command starts the matching
llama server if needed, waits for it, then launches Pi in the current repo:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices/YOUR_REPO
npm --prefix /Users/balaji/agentic-workspace run agent:fluently
```

Prompt the agent with the central context file, not repo-local `.github` files:

```text
Use the Jira context in /Users/balaji/agentic-workspace/contexts/current/service-context.yml.
Use the configured service repo path to confirm the response DTO and OpenAPI contract.
Reuse shared QA steps and scenario patterns before adding any local step definitions.
```

For monoliths, use the same agent command from the monolith repo:

```bash
cd /Users/balaji/agentic-workspace/projects/monolithic/YOUR_REPO
npm --prefix /Users/balaji/agentic-workspace run agent:fluently
```

Useful profiles:

```bash
npm --prefix /Users/balaji/agentic-workspace run agent:gemma
npm --prefix /Users/balaji/agentic-workspace run agent:fluently
npm --prefix /Users/balaji/agentic-workspace run agent:qwen
```

On the 16 GB Mac:

```bash
npm --prefix /Users/balaji/agentic-workspace run agent:gemma16
npm --prefix /Users/balaji/agentic-workspace run agent:fluently16
npm --prefix /Users/balaji/agentic-workspace run agent:qwen16
npm --prefix /Users/balaji/agentic-workspace run agent:gemma12b-agentic16
```

By default the wrapper stops a server it started when Pi exits. To keep the
server warm, use the wrapper directly:

```bash
/Users/balaji/agentic-workspace/local-agents/agent.py fluently --keep-server
```

If a different untracked process is already using port `8082`, stop it first.

## Other Mac Setup

After copying or unzipping this workspace on another Mac:

```bash
cd /path/to/agentic-workspace/local-agents
npm install
python3 -m pip install -U huggingface_hub
mkdir -p ~/.pi/agent
cp config/pi/models.json ~/.pi/agent/models.json
```

Then run the one-command agent profile from a target repo as shown above.
The first run may take time while the selected GGUF downloads.

If the workspace is not extracted at `/Users/balaji/agentic-workspace`, adjust
the absolute paths in `contexts/current/service-context.yml` before starting a
ticket.

## Central Context

Current ticket context lives at:

```text
/Users/balaji/agentic-workspace/contexts/current/service-context.yml
```

Put the current Jira ticket summary, description, acceptance criteria, scope,
repo paths, affected endpoints, and verification notes there. Repos under
`projects/` do not need to be modified just to use the local agent framework.

Examples live at:

```text
/Users/balaji/agentic-workspace/contexts/examples/service-context.microservice.yml
/Users/balaji/agentic-workspace/contexts/examples/service-context.service-owned-tests.yml
/Users/balaji/agentic-workspace/contexts/examples/service-context.monolithic.yml
```

The `context-starter/` folder is now reference material only. Use it for shared
guidelines and prompt wording, not for installing files into every repo.

## Microservice Validation Slice

The workspace includes a concrete dummy service setup that mirrors the current
split-QA microservice context file:

```text
projects/microservices/
  xyz-service/                         -> Spring Boot dummy API
  xyz-deployments/                     -> deployment companion assets
  qa-steps/                            -> shared RestAssured utilities
  qa-projects/xyz-service-api-tests/   -> actual API tests
```

The same context format also supports the more common service-owned topology,
where endpoint code, OpenAPI, and API tests live in the service repo. See:

```text
contexts/examples/service-context.service-owned-tests.yml
```

Run the service:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices/xyz-service
mvn spring-boot:run
```

Run the RestAssured API tests:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices
mvn -pl qa-projects/xyz-service-api-tests -am test
```

The Medium draft explaining the framework and validation slice lives at:

```text
/Users/balaji/agentic-workspace/docs/medium-blog-agentic-workspace.md
```

## Agent Skills

Workspace-local skills use a compact Karpathy-style Markdown format:
frontmatter for routing, then short sections for goal, inputs, procedure,
quality gates, examples, and stop condition.

```text
skills/microservice-change/SKILL.md
skills/context-efficiency-audit/SKILL.md
docs/karpathy-style-skill-format.md
docs/agentic-workflow-diagrams.md
```
