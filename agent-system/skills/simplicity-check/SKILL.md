---
name: simplicity-check
description: Simplify an implementation or assess overengineering while preserving acceptance criteria, validation, and required behavior. Use for requests to reduce complexity, reuse existing code, or review a proposed abstraction.
---

# Simplicity Check

## Procedure

1. List the required behavior and relevant invariants before reducing code. Smallest correct implementation does not mean a smaller product than requested.
2. Look for an existing helper, standard library function, or local pattern that satisfies the requirement. Remove unnecessary indirection before introducing another layer.
3. Introduce an abstraction when real callers or variants justify it. Preserve useful error handling, security boundaries, accessibility, and regression coverage.
4. Compare readability and maintenance cost, not line count alone. Avoid terse one-liners that hide behavior or break project conventions.
5. Apply the requested simplification, run relevant checks, and report the remaining trade-off. Avoid unrelated refactors.

## Sources

Adapted from the saved minimal-instructions and Ponytail ideas, plus Addy Osmani code simplification. Source reference only; no automatic session hooks or mandatory output dialect are installed.

[Source library](../../../knowledge/docs/instagram/source-library.md)
