# Instagram engineering resources in the workspace

The reviewed saved posts are represented as focused active skills, existing integrations, pinned source references, and a catalogue of application frameworks and unresolved ideas. Use the existing service/UI contexts first, then load the guide matching the task.

## Active capabilities

| Request | Skill |
| --- | --- |
| Plan a change from known requirements | [change-planning](../../../agent-system/skills/change-planning/SKILL.md) |
| Build behavior test first | [tdd](../../../agent-system/skills/tdd/SKILL.md) |
| Diagnose a reproducible failure | [diagnosing-bugs](../../../agent-system/skills/diagnosing-bugs/SKILL.md) |
| Design a module interface | [codebase-design](../../../agent-system/skills/codebase-design/SKILL.md) |
| Review a diff with evidence | [change-review](../../../agent-system/skills/change-review/SKILL.md) |
| Prove a test catches its intended failure | [test-integrity](../../../agent-system/skills/test-integrity/SKILL.md) |
| Build or review a rendered interface | [frontend-design-review](../../../agent-system/skills/frontend-design-review/SKILL.md) |
| Review a source security boundary | [security-review](../../../agent-system/skills/security-review/SKILL.md) |
| Choose an AI architecture or runtime | [ai-framework-selection](../../../agent-system/skills/ai-framework-selection/SKILL.md) |
| Measure context use and cache economics | [context-cost-control](../../../agent-system/skills/context-cost-control/SKILL.md) |
| Capture a handoff or architecture decision | [engineering-handoff](../../../agent-system/skills/engineering-handoff/SKILL.md) |
| Simplify without dropping requirements | [simplicity-check](../../../agent-system/skills/simplicity-check/SKILL.md) |
| Adopt another saved resource | [resource-adoption](../../../agent-system/skills/resource-adoption/SKILL.md) |

The three existing skills remain canonical under agent-system/skills/: microservice-change, playwright-ui-change, and context-efficiency-audit. They also have native discovery entrypoints now.

## Using the skills in VS Code

Open agentic-workspace as the repository root and start a new agent chat to refresh discovery. In Copilot, inspect Chat Customizations for the .agents/skills entries. Claude Code uses .claude/skills, linked to the same entries. Kilo receives a rule pointing to AGENTS.md and the canonical guides. Agent extensions differ in discovery support; the explicit fallback is always: "Read agent-system/skills/<name>/SKILL.md and use it for this task."

Existing local-agent launchers keep their original agent-system/skills/ paths. They do not automatically preload the new catalogue; point a local agent at the one matching guide when needed. No model-provider settings, global instructions, paid subscriptions, hooks, or running services were changed.

## Coverage and evidence

The starting material was the captions and accessible descriptions for 72 encountered posts in the AI collection, not every video frame or carousel slide or the complete Instagram account. [The catalogue](catalog.md) maps the named resources and learning topics to an adoption decision. It is not a claim that every framework is installed or benchmarked.

The [source library](source-library.md) contains documentation snapshots from eight verified repositories at recorded commits. These include the broader skill catalogues for on-demand consultation, outside discovery paths. Executables, installers, binaries, images, and some non-document resources are deliberately omitted and listed in each snapshot.json; the snapshots are not runnable upstream plugin distributions. Raw upstream instructions are subordinate to AGENTS.md and the active workspace adapters.

See [guardrails](guardrails.md), [framework choices](frameworks.md), [prompt recipes](prompt-recipes.md), and [validation](validation.md).
