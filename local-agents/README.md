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
  config/pi-models-8gb.json  -> Pi model config
  setup-8gb.sh               -> install/check runtime tools
  run-agent.sh               -> start llama.cpp and launch Pi
```
