# Framework choices from the saved posts

Application dependencies belong in the project that needs them. This workspace already separates API automation, Playwright automation, local inference, and generated graph views. Use ai-framework-selection before adding another runtime.

| Candidate | Useful question or experiment | Current workspace treatment |
| --- | --- | --- |
| Direct model call | Can one bounded request solve the task? | Baseline before adding orchestration. |
| [LangChain](https://docs.langchain.com/oss/python/langchain/overview) | Do model/tool/retrieval integrations remove meaningful project code? | Selection guidance; no new dependency installed. |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) | Is durable state, branching, resumption, or human intervention needed? | Evaluate when the workflow actually needs it. |
| [LangSmith](https://docs.langchain.com/langsmith/home) | Which trace/evaluation evidence is missing? | Compare with existing instrumentation; account and data destination remain explicit. |
| Vector RAG | Does retrieval improve an independently labelled task set? | Baseline measured on the actual corpus, with access filtering and source citations. |
| Graph RAG | Do relationships improve answers compared with simpler retrieval? | Use existing graph evidence where applicable; confirm freshness against source. |
| Agentic and multi-agent RAG | Do tool choice and multiple reasoning passes improve quality enough to justify latency and cost? | Experiment only for demonstrated needs. |
| [PageIndex](https://github.com/VectifyAI/PageIndex) | Does tree navigation improve retrieval on this document set? | Candidate experiment; compare quality, citations, indexing updates, cost, and latency. |
| [TurboVec](https://github.com/RyanCodrai/turbovec) | Is compressed in-process vector search useful at the actual dataset size? | Candidate library; benchmark recall, memory, filtering, persistence, and target hardware. |
| Graphify | Which source relationships aid broad exploration? | Existing tooling/scripts/graphify_local.py and graphifyy 0.9.33 remain; generated graphs support rather than replace source and resolved context. |
| [Paperclip](https://github.com/paperclipai/paperclip) | Is there an actual need to operate several persistent agents with task and cost ownership? | Reference candidate. Installing a server and adding agents is separate operational work. |
| [OmniRoute](https://github.com/diegosouzapw/OmniRoute) | Is there a routing or availability problem worth another gateway? | Reference candidate; no credential changes or traffic rerouting. Never equate fallback with free or unlimited usage. |
| RuFlow | Does a coordinated team outperform a simpler agent on this workload? | Exact saved repo unresolved; no substitute package installed. |
| [whichllm](https://github.com/Andyyyy64/whichllm) | Which model fits the actual hardware? | Resource link from the saved caption; verify package and results before executing. |
| Ollama, MLX, Exo, AirLLM, and streamed-expert demonstrations | Does the runtime support the required model, context, tool calls, and useful observed speed? | Existing local runtime stays primary; no model or hardware purchase inferred. |
| LlamaIndex, AutoGen, CrewAI | Does one solve a concrete retrieval or coordination requirement better than the baseline? | Learning and comparison candidates; inspect current primary docs before selecting versions. |

Prompt caching is an API optimization, not a universal IDE switch. The [Gemini documentation](https://ai.google.dev/gemini-api/docs/caching) describes conditional implicit cache hits and explicit caching. Verify current model/API support and measure actual cached tokens, storage charges, and output costs before claiming savings.

Social-post claims about replacing subscriptions, matching model quality, running huge models in little memory, or guaranteed reductions are hypotheses until reproduced on the selected system. The memory of model weights is only part of runtime memory; context/KV cache and overhead matter too.
