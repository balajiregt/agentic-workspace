# Agentic Workspace

This repository is a portable workspace pattern for local coding-agent work. It
does not vendor a local model runtime. Instead, it keeps the context files,
skills, validation projects, and docs that a local agent should use.

```text
agentic-workspace/
  local-agents/       -> lightweight setup/run wrappers for local models
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

This repo includes a lightweight `local-agents/` folder. For an 8 GB MacBook
Air, it sets up `llama.cpp`, configures Pi, starts the model, and launches the
agent. It does not commit model files, llama.cpp builds, or `node_modules`.

Run one setup command:

```bash
npm run setup:8gb
```

Recommended model:

```text
Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M
```

Fallback model when memory pressure is high:

```text
Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M
```

Then start the model and Pi agent from the sample service repo:

```bash
npm run agent:8gb
```

For a 16 GB Mac:

```bash
npm run setup:16gb
npm run agent:16gb
```

For tighter memory:

```bash
npm run setup:low-memory
npm run agent:low-memory
```

The first run downloads the GGUF model through `llama.cpp` and stores it in the
user-level Hugging Face/llama.cpp cache, not inside this repository.

The selected RAM profile controls both Pi's `contextWindow`/`maxTokens` and the
`llama-server` context size used when this repo starts the server.

To run against another repo:

```bash
bash local-agents/run-agent.sh /path/to/your/service-repo
```

To switch models for a single run:

```bash
AGENTIC_MODEL_REF="Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M" npm run agent:8gb
```

To change output tokens for one run:

```bash
AGENTIC_MAX_TOKENS=4096 npm run agent:16gb
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
local-agents/README.md
local-agents/config/model-profiles.json
local-agents/setup.sh
local-agents/run-agent.sh
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
