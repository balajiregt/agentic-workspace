# Local Agents

This folder contains the local Pi + llama.cpp wrapper for the validated editing
model:

```text
unsloth/gemma-4-E2B-it-qat-GGUF:UD-Q4_K_XL
```

Run:

```bash
npm run setup:tool-agent
npm run agent:tool-agent
```

For longer edit loops:

```bash
npm run setup:tool-agent-long
npm run agent:tool-agent-long
```

For explicit high-budget experiments:

```bash
npm run setup:tool-agent-25k
npm run agent:tool-agent-25k
```

The legacy 8 GB aliases point to the same profile:

```bash
npm run setup:8gb
npm run agent:8gb
```

Before trusting Pi edits:

```bash
npm run agent:doctor
```

Expected:

```text
TOOL_CALL_CHECK=PASS
```

Model files stay in the Hugging Face/llama.cpp cache, not in this repository.
