# Prompts for the integrated workspace skills

Use the named guide explicitly when testing discovery. Once an agent reliably selects it for the right request, naming the guide should be optional.

| Goal | Prompt |
| --- | --- |
| Plan | Read agent-system/skills/change-planning/SKILL.md. Plan this feature using the existing contexts and frameworks: [requirements]. Then implement the authorized slices. |
| Test first | Use tdd and the current service/UI context to implement [behavior]. Preserve the existing framework and prove the intended failure first. |
| Debug | Use diagnosing-bugs to reproduce [symptom], find its cause, and verify the smallest effective fix. |
| Check suspicious tests | Use test-integrity to assess whether [test file] would fail when [behavior] breaks. Report observed evidence and any unrun checks. |
| Review | Use change-review to review [diff or file set] against [acceptance criteria]. Keep the source unchanged. |
| Simplify | Use simplicity-check on [implementation]. Preserve all requested behavior, error handling, and relevant tests. |
| Design | Use frontend-design-review to improve [screen]. Preserve its current product behavior and verify the rendered result. |
| Security | Use security-review for a focused source review of [boundary and paths]. Distinguish confirmed findings from unresolved hypotheses. |
| Cost | Use context-cost-control to compare usage for [same task] before and after [change]. Report quality alongside available usage telemetry. |
| Choose framework | Use ai-framework-selection for [application requirement]. Compare the simplest baseline with [candidate] on explicit acceptance criteria. |
| Handoff | Use engineering-handoff to record current state, actual verification, remaining work, and the next action. |
| Adopt another post | Use resource-adoption for [post/repo]. Resolve the primary source, check overlap and supporting resources, then integrate what fits. |
