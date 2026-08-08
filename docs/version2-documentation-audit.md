# Agentic Workspace V2 Documentation Audit

Date: 2026-08-08

## Summary

The documentation is directionally consistent, but it now represents two
generations of the workspace:

- V1: API automation with compact task context, generated resolved context,
  RestAssured validation, local-agent runtime, and QA gap guardrails.
- V2: one workspace with isolated API and Playwright UI slices, graph-based
  test intelligence, Graphify exploration, Docker-served graph views, and a
  stakeholder QA dashboard.

The safest public-story path is to keep the existing V1 blog draft unchanged
and add a separate V2 draft.

## High-Signal Sources

- `README.md`: best current technical overview.
- `STATE.md`: best current quick-state reference.
- `docs/loop-run-log.md`: strongest validation evidence, but intentionally
  historical and too detailed for public narrative.
- `docs/medium-blog-agentic-workspace.md`: V1 API-focused blog draft.
- `skills/microservice-change/SKILL.md`: API/RestAssured agent guardrails.
- `skills/playwright-ui-change/SKILL.md`: Playwright/UI agent guardrails.
- `scripts/build_test_graph.py`: deterministic API/UI test-impact graph.
- `scripts/build_qa_dashboard.py`: V2 stakeholder dashboard.

## Redundancies And Duplications

### README vs STATE

Both describe the current API/UI/graph state. This is acceptable because they
serve different purposes:

- `README.md` is onboarding and public-facing.
- `STATE.md` is an operator quick reference.

Recommendation: keep both, but avoid adding long examples to `STATE.md`.

### README vs docs/local-agent-runtime.md

Both describe local-agent setup and the token metrics dashboard. This is
acceptable, but the README should stay short and point to the deeper runtime
doc.

Action taken: clarified that the token metrics dashboard uses port `8764`, so
the QA dashboard can own port `8765`.

### Existing Blog Draft vs V2 Story

`docs/medium-blog-agentic-workspace.md` is now a V1 article. It is still useful,
but it does not cover:

- isolated Playwright UI automation,
- `ui-context.yml` and `resolved-ui-context.yml`,
- graph-based impact mapping,
- Graphify as optional broad exploration,
- Docker-served dashboard/graphs for non-IDE stakeholders,
- scalable QA dashboard controls.

Recommendation: do not overwrite the V1 post. Publish V2 as a follow-up.

### Loop Log Length

`docs/loop-run-log.md` is intentionally verbose and historical. It repeats
validation commands and earlier design decisions.

Recommendation: do not reduce it; treat it as evidence, not marketing copy.
For blogs and LinkedIn posts, pull only the validated outcomes.

### Dashboard Terminology

The repo has two dashboards:

- Token metrics dashboard: local model/Pi runtime metrics, port `8764`.
- QA intelligence dashboard: API/UI graph, test health, duplicate signals,
  coverage, and stakeholder view, port `8765`.

Action taken: docs and npm scripts now avoid the old `8765` collision.

## Public Narrative Guidance

For V2, the strongest story is not "we added charts." The stronger story is:

```text
Agents need routing, test intent, graph evidence, and stakeholder visibility.
```

The V2 blog should emphasize:

1. Same workspace, separate frameworks.
2. API tasks route to API context and RestAssured skill.
3. UI tasks route to UI context and Playwright skill.
4. Graphs help agents and humans see impacted tests.
5. Duplicate prevention remains instruction-first, with graph/similarity as
   supporting evidence.
6. The dashboard makes mappings visible without an IDE.
7. The dashboard is intentionally lightweight and scalable.

## Suggested Cleanup Later

- Add a short `docs/version-history.md` with V1 and V2 milestones.
- Add screenshots under a dedicated ignored/public docs strategy if images are
  needed for the blog.
- Add a sample `artifacts/usage-metrics/usage.example.json` if real-world usage
  metrics become part of the public story.
- Consider separating README "Local Agent Setup" and "QA Intelligence Dashboard"
  into concise summaries with links to deeper docs if the README grows again.

