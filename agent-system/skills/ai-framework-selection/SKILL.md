---
name: ai-framework-selection
description: Choose an AI application architecture or library for a concrete requirement, comparing direct calls, RAG, graph workflows, retrieval indices, local inference, and agent orchestration. Use before adding an AI framework or switching model runtimes.
---

# AI Framework Selection

## Procedure

1. Define the actual application task, data, required tools, acceptable error rate, latency, privacy constraints, hardware, and cost envelope. An IDE skill is separate from an application dependency.
2. Start with a direct model call or deterministic workflow when it meets the requirement. Add retrieval for a demonstrated knowledge need and tool orchestration for actual branching or durable state.
3. Choose a small representative evaluation set and compare correctness, citation fidelity, failure recovery, latency, memory, and measured usage under equivalent conditions.
4. Use [framework notes](../../../knowledge/docs/instagram/frameworks.md) for candidates from the saved posts: LangChain, LangGraph, LangSmith, vector RAG, PageIndex, TurboVec, local runtimes, Paperclip, and OmniRoute.
5. Inspect the exact package, license, maintained revision, dependency requirements, and data destinations. Use established project patterns before adding a new framework.
6. Produce a small implementation experiment when requested. Record the reason for the selected option and what evidence would justify changing it. Do not install every candidate or equate promotional benchmarks with project performance.

## Stop Condition

Give a concrete choice or a bounded experiment with measurable acceptance criteria. Record unresolved external-service requirements.
