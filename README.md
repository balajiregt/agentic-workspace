# Agentic Workspace

This repository is a portable workspace pattern for local coding-agent work. It
does not vendor a local model runtime. Instead, it keeps the context files,
skills, validation projects, and docs that a local agent should use.

```text
agentic-workspace/
  config/             -> local agent model profiles
  contexts/
    current/          -> current Jira/service context used by the agent
    examples/         -> microservice and monolith context examples
  docs/               -> validation docs and workflow diagrams
  skills/             -> compact reusable agent instructions
  projects/
    microservices/    -> Spring Boot service/deployment repos
    monolithic/       -> monolithic application repos
  scripts/            -> context efficiency utilities
```

## 8 GB MacBook Air Local Agent Setup

This repo does not include a `local-agents/` folder. For an 8 GB MacBook Air,
use a small GGUF model through `llama.cpp`, then run your coding agent from the
repo you want to edit.

Install the runtime tools:

```bash
brew install llama.cpp
npm install -g @earendil-works/pi-coding-agent
```

Recommended model:

```text
Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M
```

Fallback model when memory pressure is high:

```text
Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M
```

Start the recommended model:

```bash
llama serve -hf Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M --alias local-model
```

Configure Pi:

```bash
mkdir -p ~/.pi/agent
cp /Users/balaji/agentic-workspace/config/pi-models-8gb.json ~/.pi/agent/models.json
```

Then run Pi from the repo you want it to edit:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices/xyz-service
pi
```

Prompt the agent with the central context file:

```text
Use the Jira context in /Users/balaji/agentic-workspace/contexts/current/service-context.yml.
Follow repository_topology before deciding where tests or deployment changes belong.
Update service code, OpenAPI, tests, and deployment impact only as required by the context.
```

More detail lives at:

```text
docs/local-agent-runtime.md
config/pi-models-8gb.json
```

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
docs/local-agent-runtime.md
```
