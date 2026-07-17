# Karpathy-Style Skill Format

Use this format for workspace `SKILL.md` files and short agent-facing Markdown.
The style is intentionally compact: route with metadata, give direct procedures,
show examples, and avoid teaching the model things it already knows.

## Shape

```markdown
---
name: short-hyphen-name
description: What this skill does. Include concrete trigger phrases and contexts.
---

# Human Title

## Goal

One or two sentences describing the outcome.

## Inputs

- Exact files, folders, URLs, commands, or assumptions.

## Procedure

1. Do the first required action.
2. Do the next required action.
3. Prefer project-local patterns.

## Quality Gates

- Observable checks that prove the work is correct.

## Example Prompts

```text
Concrete user prompt that should trigger this skill.
```

## Stop Condition

When to stop and what to report.
```

## Rules

- Put routing details in `description`, not in a "when to use" body section.
- Keep the body below 150 lines unless the workflow is genuinely complex.
- Prefer examples over explanations.
- Prefer executable scripts over long repeated instructions.
- Put large references in linked `references/*.md` files.
- Do not add README files inside skill folders.
- Do not duplicate context that already lives in `service-context.yml`.

## Workspace Skills

```text
skills/
  microservice-change/SKILL.md
  context-efficiency-audit/SKILL.md
```

## Why This Helps the Blog

This format supports the same efficiency claim as the central YAML file:
instruction context stays small, routing is explicit, and the agent loads
detailed files only after the task requires them.
