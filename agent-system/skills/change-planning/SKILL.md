---
name: change-planning
description: Plan a substantial feature or change from known requirements, map its existing files and interfaces, and define verifiable implementation slices. Use for multi-file feature plans, PRDs, or architecture decisions; small fixes can proceed directly.
---

# Change Planning

## Inputs

Read AGENTS.md, the relevant service or UI context and resolved paths, the request, and existing implementation. Use existing acceptance criteria before asking for more information.

## Procedure

1. State the requested outcome, observable acceptance criteria, and material unknowns. Resolve routine choices from the project. Ask only for decisions that change the product or scope.
2. Map the actual files, callers, contracts, and tests. Use resolved context before repository searches. Identify any source/contract gaps.
3. Split substantial work into vertical slices that each produce usable, checkable behavior. Name dependencies, the public interface affected, and the verification command for each slice.
4. Use existing project frameworks. Document a new dependency or architecture decision only when needed. Prefer one short plan; create API/database/design documents only for substantive decisions.
5. Define review focus: relevant failure inputs, authorization boundaries, compatibility, and operating constraints. Keep requested behavior intact while simplifying the implementation.
6. Continue authorized implementation when the request includes building it; a plan is not a substitute for completed work. Do not introduce another approval checkpoint for an already agreed routine step.

## Quality Gates

Every slice has an observable outcome and meaningful check. No speculative endpoint, file path, or framework is treated as existing.

## Sources

Adapted practices from Matt Pocock, Superpowers, and Addy Osmani; [source library](../../../knowledge/docs/instagram/source-library.md).
