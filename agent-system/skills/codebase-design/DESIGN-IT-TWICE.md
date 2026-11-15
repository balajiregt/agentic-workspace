# Compare interface designs

Use this exercise when the user requests alternatives or an unresolved interface trade-off justifies it. Read the vocabulary in [SKILL.md](SKILL.md) and dependency categories in [DEEPENING.md](DEEPENING.md).

1. State the actual callers, required behavior, constraints, dependencies, and test surface.
2. Sketch two or three materially different interfaces: a minimal interface, one optimized for the common caller, and a more flexible alternative if needed. Work sequentially by default. Use subagents only when available and authorized for the task.
3. For each design, show a short caller example, what complexity it hides, dependency handling, and failure behavior.
4. Compare caller effort, locality of changes, testability, and migration cost. Recommend one and explain the deciding trade-off. Do not implement speculative alternatives.
