# Agentic Workspace Loop

This repo uses a lightweight loop-engineering pattern for local coding-agent
work. The loop is human-started and verification-focused.

```mermaid
flowchart TD
  A["User prompt"] --> B["Read AGENTS.md"]
  B --> C["Read small task context"]
  C --> D{"resolved-context.yml exists?"}
  D -->|No| E["Run npm run context:resolve"]
  D -->|Yes| F["Read resolved context"]
  E --> F
  F --> G["Load matching SKILL.md"]
  G --> H["Inspect only resolved task-relevant files"]
  H --> I["Edit smallest correct file set or report gap"]
  I --> J["Run verification commands"]
  J --> K["Write proof to docs/loop-run-log.md"]
  K --> L["Report changed files and validation"]
```

## Required Loop Inputs

- `AGENTS.md` for default repo behavior.
- `contexts/current/service-context.yml` for the small current task/ticket state.
- `contexts/current/resolved-context.yml` for generated exact paths and
  verification commands. Regenerate with `npm run context:resolve` when missing
  or stale.
- `skills/microservice-change/SKILL.md` for microservice/API/test workflow.
- `loop-budget.md` for local machine context and output-token budgets.
- `STATE.md` for the active validation slice.

## Context Rule

Do not turn the current task YAML into a service catalog. Keep it small and let
the resolver derive exact files from repo conventions, OpenAPI, and source code.

## Stop Condition

Stop only when the requested change is complete, verification has run or a
blocker is recorded, and the log identifies the context files, edited files, and
validation result.
