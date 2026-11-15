---
name: context-cost-control
description: Measure and improve coding-agent context use or application model costs without losing required behavior. Use for prompt caching, token usage, local model sizing, or context efficiency requests.
---

# Context and Cost Control

## Inputs

Read knowledge/docs/agent-workflow/loop-budget.md, the existing context-efficiency-audit skill, and local-agent runtime documents when the task concerns this workspace. Use the relevant resolved context before broad source reads.

## Procedure

1. Establish baseline task quality, elapsed time, model/provider, input/output/cached tokens, and cost where telemetry exists. Distinguish measured usage from approximate token counts and unavailable metrics.
2. Keep the always-on instructions short and load only the matching skill and exact files. Reuse resolved file maps and existing graph evidence, checking staleness against source.
3. Keep repeated stable prompt prefixes consistent when the API supports caching. Verify the provider's current minimums, usage fields, retention, and pricing before implementing explicit caches. An implicit-cache hit is not guaranteed.
4. Do not cache secrets or cross-user data without the application's intended isolation and lifecycle controls. Include storage and output charges when calculating net savings.
5. For local inference, measure hardware fit, runtime overhead, context/KV cache, tool-call correctness, and observed speed. Memory fit alone does not prove a useful coding agent.
6. Use concise, clear output and smallest-correct changes. Do not remove requested features, verification evidence, or important explanations merely to reduce tokens.
7. Compare the same task after changes. Report quality and observed cost together; no blanket savings percentage.

## Sources

Gemini caching: https://ai.google.dev/gemini-api/docs/caching

Related saved ideas: Caveman, Ponytail, caching, Graphify, and local models; [catalogue](../../../knowledge/docs/instagram/catalog.md).
