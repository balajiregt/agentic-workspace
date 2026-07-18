# Local Agent Runtime

This repository includes a lightweight `local-agents/` wrapper folder. It is not
a vendored runtime: model files, llama.cpp builds, and npm dependencies remain
outside Git.

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

## One-Command Setup

From the workspace root:

```bash
npm run setup:8gb
```

This checks for `llama.cpp`, installs Pi if needed, and renders:

```text
local-agents/config/model-profiles.json -> generated ~/.pi/agent/models.json
```

Then start the recommended model and Pi from the sample service repo:

```bash
npm run agent:8gb
```

Other RAM profiles:

```bash
npm run setup:16gb
npm run agent:16gb

npm run setup:low-memory
npm run agent:low-memory
```

The first run downloads the GGUF model through `llama.cpp` and stores it in the
user-level Hugging Face/llama.cpp cache. It does not commit models into
`local-agents/`.

The run script starts `llama-server` with the same context window declared in
the selected profile. If an existing llama server is already running on the
configured port, the script reuses it and assumes the server was started with
compatible settings.

To run against another repo:

```bash
bash local-agents/run-agent.sh /path/to/your/service-repo
```

## Profile Budgets

| Profile | Model | Context window | Max output tokens |
| --- | --- | ---: | ---: |
| `low-memory` | Qwen2.5 Coder 1.5B Q4_K_M | 4096 | 1024 |
| `8gb` | Qwen2.5 Coder 3B Q4_K_M | 8192 | 2048 |
| `16gb` | Qwen2.5 Coder 3B Q4_K_M | 12288 | 3072 |

Override for one run:

```bash
AGENTIC_MAX_TOKENS=4096 npm run agent:16gb
AGENTIC_CONTEXT_WINDOW=16384 npm run agent:16gb
AGENTIC_MODEL_REF="Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M" npm run agent:8gb
```

## Manual Runtime Setup

The scripts above are preferred. Manual setup is:

```bash
brew install llama.cpp
npm install -g @earendil-works/pi-coding-agent
```

## Start the Recommended 8 GB Model

```bash
llama-server -hf Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M --alias local-model --ctx-size 8192
```

If the machine feels constrained:

```bash
llama-server -hf Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M --alias local-model --ctx-size 4096
```

The llama.cpp server exposes an OpenAI-compatible API at:

```text
http://localhost:8080/v1
```

## Configure Pi

Copy the committed 8 GB model profile:

```bash
mkdir -p ~/.pi/agent
python3 /Users/balaji/agentic-workspace/local-agents/render-pi-models.py \
  --profile 8gb \
  --output ~/.pi/agent/models.json
```

Then run Pi from the repository you want the agent to edit:

```bash
cd /Users/balaji/agentic-workspace
pi --approve \
  --skill skills/microservice-change \
  --prompt-template docs/prompts \
  --tools read,bash,edit,write,grep,find,ls
```

The `npm run agent:*` scripts do this automatically. Starting from the
workspace root is important because the root contains `AGENTS.md`, the current
service YAML, and sibling service/QA/deployment folders.

Use a prompt that points to the central context file:

```text
Use the Jira context in /Users/balaji/agentic-workspace/contexts/current/service-context.yml.
Follow the repository_topology field before deciding where tests or deployment changes belong.
Update service code, OpenAPI, tests, and deployment impact only as required by the context.
```

For existing API-test assertions, Pi also exposes a prompt template:

```text
/existing-test-assertion riskCategory is not empty for the customer risk response
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

Run setup and launch scripts:

```bash
npm run setup:8gb
npm run agent:8gb
```

Check whether the current local model/server can execute Pi file tools:

```bash
npm run agent:doctor
```

The doctor sends a forced tool-call request to the OpenAI-compatible
`/chat/completions` endpoint. `TOOL_CALL_CHECK=PASS` means the server returned
structured `message.tool_calls`. `TOOL_CALL_CHECK=FAIL` means the server put the
tool request in normal text, which usually appears in Pi as JSON such as
`{"name":"edit",...}` instead of an actual edit.

Run the token metrics dashboard in another terminal while Pi is running:

```bash
npm run metrics:8gb
open http://localhost:8765
```

The dashboard reads:

- Pi's rendered model config from `~/.pi/agent/models.json`.
- llama.cpp model status from `/v1/models`.
- live slot state from `/slots`.
- prompt/output token counters from `/metrics`.

`local-agents/run-agent.sh` starts `llama-server` with `--metrics`, so this
works automatically when this repo launches llama.cpp. If you start llama.cpp
manually, include:

```bash
llama-server ... --metrics --slots
```

## Notes

The model choices are intentionally small. This workspace gets leverage from
compact YAML context and explicit repo paths, not from loading every file into a
large local model.

Model references:

- `Qwen/Qwen2.5-Coder-3B-Instruct-GGUF`
- `Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF`
