# Model Comparison Log

This log compares local models against the same agentic workspace prompts.

## Models Under Evaluation

| Label | Model ref | Intended runtime |
| --- | --- | --- |
| Qwen Coder 3B | `Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M` | `llama.cpp` / Pi |
| Gemma E4B | `unsloth/gemma-4-E4B-it-GGUF:Q4_K_M` | `llama.cpp` / Pi |

References:

- `https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF`
- `https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF`

## Scoring Rubric

Each prompt is scored from 0 to 2 for each criterion.

| Criterion | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Context routing | Ignores YAML/topology | Mentions it but misses scope | Uses YAML/topology correctly |
| File precision | Broad or wrong files | Mostly right with noise | Minimal correct file set |
| Shared utility judgment | Misplaces helper | Ambiguous placement | Correctly separates shared vs service-specific |
| Verification | Missing or wrong command | Partial command | Correct Maven/service checks |
| Output discipline | Verbose or vague | Useful but bulky | Concise and actionable |

Maximum score per prompt: 10.

## Runtime Availability Check

Current machine:

```text
MacBook Air class machine, arm64, 8 GB RAM
```

Current shell availability:

```text
llama-server: installed during this benchmark via brew
llama: not found
pi: not found
ollama: found
```

Because the repo runtime uses `llama.cpp` + Pi, a direct benchmark requires:

```bash
npm run setup:8gb
```

Then run each model with:

```bash
AGENTIC_MODEL_REF="Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M" npm run agent:8gb
AGENTIC_MODEL_REF="unsloth/gemma-4-E4B-it-GGUF:Q4_K_M" npm run agent:8gb
```

## Task Context Sizes

| Task profile | Estimated tokens | 4096 ctx fit | 8192 ctx fit | Notes |
| --- | ---: | --- | --- | --- |
| `shared-qa-utility-change` | 2988 | Borderline | Yes | Fits only if output is kept small |
| `business-flow-walkthrough` | 3470 | Borderline | Yes | Better as read-only explanation |
| `new-endpoint-change` | 4128 | No | Yes | Needs 8192 context on 8 GB profile |

## Runtime Results

Benchmark settings:

```text
Machine: arm64 MacBook Air class machine, 8 GB RAM
Runtime: llama-server
Context: 8192
Parallel slots: 1
Temperature: 0.1
```

| Prompt | Qwen Coder 3B score | Gemma E4B score | Notes |
| --- | ---: | ---: | --- |
| `new-endpoint-change` | 5/10 | Not run | Qwen fit in 8192 ctx but missed split-QA API test changes and was broad on service files |
| `shared-qa-utility-change` | 6/10 | Not run | Qwen routed to QA correctly but listed too many files as changes |
| `business-flow-walkthrough` | 8/10 | Not run | Qwen correctly stayed read-only and referenced the right files; explanation depth was limited by the benchmark format |

## Tool-Call Doctor

Pi can only apply file edits when the selected provider returns structured
`message.tool_calls`. A local model that prints tool-shaped JSON in
`message.content` is useful for planning, but it is not a reliable editing
agent.

Run:

```bash
npm run agent:doctor
```

Observed with the current 8 GB Qwen profile on llama.cpp port `8080`:

```text
TOOL_CALL_CHECK=FAIL no structured tool_calls returned
message.content preview: ```json\n{\n  "name": "read",\n  "arguments": {\n    "path": "AGENTS.md"\n  }\n}\n```
```

Practical meaning:

- Qwen Coder 3B remains efficient for context-routing and token-budget
  experiments.
- This exact Qwen Coder 3B + llama.cpp OpenAI endpoint should not be presented
  as a validated Pi editing-agent profile until the doctor passes.
- Use a tool-call-capable provider/model for real Pi file-edit automation, or
  treat the local profile as advisory/read-only.

Observed with `Salesforce/xLAM-2-3b-fc-r-gguf:Q4_K_M`:

```text
TOOL_CALL_CHECK=ERROR server request failed: HTTP Error 500: Internal Server Error
llama.cpp log: The model produced output that does not match the expected peg-native format
unparsed peg-native output: {"name": "read", "arguments": {"path": "AGENTS.md"}}]
```

Practical meaning:

- xLAM 2 3B loaded on the 8 GB machine, but did not pass llama.cpp structured
  tool-call parsing in this setup.
- Do not use this xLAM profile for Pi edits until a different quant/template or
  server version passes `npm run agent:doctor`.

Next candidate:

```text
second-state/functionary-small-v3.2-GGUF:Q2_K
```

Reason:

- Functionary is a function-calling-oriented model family.
- The workspace now exposes it as `npm run agent:tool-agent`.
- It is the next model to validate for Pi edits; proceed only if
  `npm run agent:doctor` returns `TOOL_CALL_CHECK=PASS`.

## Qwen Coder 3B Evidence

Startup:

```bash
llama-server -hf Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M \
  --alias local-model \
  --port 8091 \
  --ctx-size 8192 \
  --parallel 1
```

The first run downloaded `qwen2.5-coder-3b-instruct-q4_k_m.gguf`, then loaded
successfully:

```text
model loaded
listening on http://127.0.0.1:8091
```

Measured prompt runs:

| Task | Prompt tokens | Completion tokens | Elapsed | Generation rate observed |
| --- | ---: | ---: | ---: | --- |
| `shared-qa-utility-change` | 3330 | 384 | 63.95s | ~12.5 tok/s |
| `business-flow-walkthrough` | 3504 | 509 | 73.71s | ~12.5 tok/s |
| `new-endpoint-change` | 4294 | 475 | 89.02s | ~10.6 tok/s |

Qwen conclusion:

- Efficient enough for the 8 GB profile at `ctx-size=8192`.
- Good at following context files and staying inside the workspace structure.
- Needs stricter prompts for minimal edit sets, especially new endpoint work.
- Best current default for this repo because it started, fit the profiles, and
  completed all three benchmark prompts.

## Gemma E4B Evidence

Startup attempted:

```bash
llama-server -hf unsloth/gemma-4-E4B-it-GGUF:Q4_K_M \
  --alias local-model \
  --port 8092 \
  --ctx-size 8192 \
  --parallel 1
```

Observed behavior:

```text
Downloading mmproj-BF16.gguf ... 100%
Downloading gemma-4-E4B-it-Q4_K_M.gguf ... 6%
```

The run was stopped before the main model finished downloading because the
first-run setup was much heavier than Qwen on this 8 GB machine. No precision
score is assigned because the model did not reach runnable state in this pass.

Gemma conclusion:

- Valid model ref for llama.cpp/Pi style use.
- Heavier first-run setup than Qwen because it also downloads a multimodal
  projection file.
- Not recommended as the default 8 GB profile until the model is fully cached
  and measured.
- Candidate for a 16 GB or experimental profile after cache warm-up.

## Practical Recommendation

Current winner for this framework:

```text
Qwen/Qwen2.5-Coder-3B-Instruct-GGUF:Q4_K_M
```

Why:

- Runs on the 8 GB machine with `ctx-size=8192`.
- Handles all three task profiles without runtime failure.
- Gives usable routing decisions from the YAML/skill context.
- Lower first-run setup friction than Gemma E4B.

Gemma E4B should be treated as experimental until it is fully downloaded and
benchmarked from cache.
