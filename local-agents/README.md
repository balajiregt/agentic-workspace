# Local Agents

This folder is the lightweight local-agent runtime wrapper for the workspace.
It is committed intentionally so a fresh clone has a clear setup path.

It does not contain:

- GGUF model files
- llama.cpp source/build output
- npm `node_modules`

Those stay in user-level caches or ignored local folders.

## 8 GB MacBook Air

One-time setup:

```bash
npm run setup:8gb
```

Run the sample agent flow:

```bash
npm run agent:8gb
```

Run against another repo:

```bash
bash local-agents/run-agent.sh /path/to/your/service-repo
```

Use the lower-memory fallback model:

```bash
AGENTIC_MODEL_REF="Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M" npm run agent:8gb
```

## Files

```text
local-agents/
  config/model-profiles.json -> RAM/model profiles
  render-pi-models.py        -> renders ~/.pi/agent/models.json
  setup.sh                   -> install/check runtime tools
  run-agent.sh               -> start llama.cpp and launch Pi
```

## Profiles

```bash
npm run setup:8gb
npm run agent:8gb

npm run setup:16gb
npm run agent:16gb

npm run setup:low-memory
npm run agent:low-memory
```

Override output tokens for one run:

```bash
AGENTIC_MAX_TOKENS=4096 npm run agent:16gb
```

Override context window and model:

```bash
AGENTIC_CONTEXT_WINDOW=16384 \
AGENTIC_MODEL_REF="Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M" \
  npm run agent:16gb
```
