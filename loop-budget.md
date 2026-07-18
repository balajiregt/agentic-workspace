# Loop Budget

The workspace is tuned for local coding-agent use on small machines. Token
budgets are guidance, not hard limits.

| Machine profile | Model profile | Context window | Max output tokens | Use case |
| --- | --- | ---: | ---: | --- |
| Low memory | `low-memory` | 4096 | 1024 | Heavy multitasking or memory pressure |
| 8 GB MacBook Air | `8gb` | 8192 | 2048 | Default local microservice work |
| 16 GB Mac | `16gb` | 12288 | 3072 | Larger edits and longer summaries |

Runtime overrides:

```bash
AGENTIC_CONTEXT_WINDOW=4096 npm run agent:8gb
AGENTIC_MAX_TOKENS=1024 npm run agent:8gb
AGENTIC_MODEL_REF="Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M" npm run agent:8gb
```

Context-efficiency checks:

```bash
npm run context:report
python3 scripts/context_efficiency_report.py --task-profile api-test-change
```
