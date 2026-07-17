# Local Agent Runtime

This repository does not include a `local-agents/` runtime folder. It is a
portable workspace pattern: context files, skills, validation projects, and
docs. Bring your own local coding agent runtime and point it at this workspace.

## 8 GB MacBook Air Baseline

Recommended default:

```text
Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M
```

Fallback when memory pressure is high:

```text
Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M
```

Why this sizing:

- 8 GB unified memory is tight for local coding agents.
- 3B Q4_K_M is a practical default for small, context-aware repo tasks.
- 1.5B Q4_K_M is useful when the browser, IDE, test runner, and model are all
  open at the same time.
- Larger 7B+ or 12B+ models are better treated as 16 GB+ profiles.

## Install Runtime Tools

```bash
brew install llama.cpp
npm install -g @earendil-works/pi-coding-agent
```

## Start the Recommended 8 GB Model

```bash
llama serve -hf Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M --alias local-model
```

If the machine feels constrained:

```bash
llama serve -hf Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M --alias local-model
```

The llama.cpp server exposes an OpenAI-compatible API at:

```text
http://localhost:8080/v1
```

## Configure Pi

Copy the committed 8 GB model profile:

```bash
mkdir -p ~/.pi/agent
cp /Users/balaji/agentic-workspace/config/pi-models-8gb.json ~/.pi/agent/models.json
```

Then run Pi from the repository you want the agent to edit:

```bash
cd /Users/balaji/agentic-workspace/projects/microservices/xyz-service
pi
```

Use a prompt that points to the central context file:

```text
Use the Jira context in /Users/balaji/agentic-workspace/contexts/current/service-context.yml.
Follow the repository_topology field before deciding where tests or deployment changes belong.
Update service code, OpenAPI, tests, and deployment impact only as required by the context.
```

## Useful Workspace Commands

Show configured 8 GB model profile:

```bash
npm run models:8gb
```

Run the context efficiency report:

```bash
npm run context:report
```

## Notes

The model choices are intentionally small. This workspace gets leverage from
compact YAML context and explicit repo paths, not from loading every file into a
large local model.

Model references:

- `Qwen/Qwen2.5-Coder-3B-Instruct-GGUF`
- `Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF`
