# Agentic Workspace V2: From API Test Changes to QA Intelligence

Draft date: 2026-08-08

Repo:

```text
https://github.com/balajiregt/agentic-workspace
```

## Short LinkedIn Post Draft

I have been evolving my agentic QA workspace from a small API automation
experiment into a broader QA intelligence workspace.

Version 1 focused on one hard problem: how can a coding agent safely modify API
tests without inventing endpoints, ignoring OpenAPI, duplicating coverage, or
deleting a failing test that is actually exposing a product/contract gap?

Version 2 adds the next layer:

- RestAssured API automation and Playwright UI automation in the same
  workspace, but isolated as separate frameworks.
- Separate context routing for API and UI work.
- Role-aware Playwright tests backed by a mockserver.
- A deterministic API/UI test-impact graph.
- Optional Graphify exploration for broader workspace knowledge.
- A lightweight QA dashboard for stakeholders who do not use an IDE.
- Duplicate/overlap signals, coverage/gap signals, changed-file impact, test
  health, and release confidence in one view.

The important design choice was not to merge everything into one giant test
framework. API automation stays Java/Maven/RestAssured. UI automation stays
Node/TypeScript/Playwright. The shared layer is context, graph evidence, and
agent routing.

This is still a practical reference implementation, not a universal framework.
But the direction feels right: agents should not only write tests. They should
understand test intent, repo topology, duplicate coverage, impacted flows, and
the evidence needed for humans to trust the change.

## Blog Draft

Most agent demos stop at "the agent edited code."

In QA automation, that is not enough.

A useful QA agent must know where the test belongs, whether coverage already
exists, which framework owns the workflow, whether an expectation is supported
by source code and contract, and how to prove the change did not hide a real
quality signal.

That is the idea behind my agentic workspace.

Version 1 was focused on API automation. Version 2 expands the same pattern
into UI automation, graph-based test intelligence, and a lightweight dashboard
for QA visibility.

## Where V1 Started

The first version explored a practical API testing problem:

```text
Can an agent add or modify API tests without losing QA intent?
```

The validation slice used:

- a Spring Boot dummy service,
- OpenAPI as the contract source,
- shared RestAssured utilities,
- a split QA project for service-level API tests,
- compact task context in `service-context.yml`,
- generated exact paths in `resolved-context.yml`,
- a `microservice-change` skill for agent guardrails.

The core split was:

```text
service-context.yml   -> small ticket facts
OpenAPI + repo layout -> stable service facts
resolved-context.yml  -> generated exact paths and commands
SKILL.md              -> reusable agent playbook
```

That helped avoid common agent mistakes:

- creating a new test file when the endpoint already had coverage,
- inventing endpoint paths or request bodies,
- ignoring shared API test utilities,
- skipping OpenAPI/source checks,
- rewriting a failing test just to make the suite green.

The most important guardrail was simple:

```text
If a test expects behavior that is not implemented or documented, report a
product/contract gap. Do not hide it by changing the test.
```

That was V1: context-aware API automation.

## What Changed In V2

V2 adds a second automation slice and a visibility layer.

The workspace now supports:

- Java/Maven/RestAssured API tests under `projects/microservices`,
- Node/TypeScript/Playwright UI tests under `projects/ui-automation`,
- separate API and UI context files,
- separate API and Playwright skills,
- role-aware UI tests backed by a Koa mockserver,
- deterministic graph generation for test-impact mapping,
- optional Graphify exploration,
- a Docker-served QA dashboard for non-IDE stakeholders.

The key architectural decision:

```text
same workspace, separate frameworks
```

I did not merge Playwright into the Maven parent. I did not push UI tests into
the RestAssured API project. I did not make the API context resolver responsible
for browser automation.

Instead:

```text
API work        -> service-context.yml -> resolved-context.yml -> microservice-change skill
Playwright work -> ui-context.yml      -> resolved-ui-context.yml -> playwright-ui-change skill
```

The frameworks remain isolated. The agent routing becomes shared.

## Why Isolated Frameworks Matter

In real teams, API automation and UI automation often have different owners,
dependencies, reports, fixtures, runtime assumptions, and failure modes.

Combining them too early creates confusion:

- Maven starts owning Playwright dependencies.
- UI tests inherit API-only rules.
- API tests start depending on browser state.
- Mock behavior gets split between Playwright route interception and backend
  mocks without a clear boundary.

V2 keeps the boundary explicit:

- API automation remains Java/Maven/RestAssured.
- UI automation remains Node/TypeScript/Playwright.
- Mockserver-owned backend behavior stays in the UI mockserver.
- Playwright routing is used only for request setup headers or deliberate
  comparison tests.
- Shared concepts such as role, flow, endpoint, and duplicate coverage are
  represented in context and graph evidence, not by merging codebases.

That gives the agent less room to improvise in the wrong place.

## The Playwright Slice

The UI validation slice is a role-aware Playwright project with:

- a demo app,
- a Koa mockserver,
- role-aware token/workspace responses,
- Playwright helpers,
- page objects,
- assertions,
- role matrix tests,
- feature flag tests,
- one legacy interception comparison test.

The Playwright skill includes rules for:

- duplicate coverage checks,
- fixture usage,
- page-object boundaries,
- locator priority,
- storage state and session storage,
- mockserver vs Playwright network responsibilities,
- web-first assertions.

This matters because browser automation agents can easily become messy. They
may choose brittle selectors, duplicate scenarios, fulfill backend responses in
the wrong layer, or bypass existing fixtures.

The UI context gives them a smaller path:

```text
Read UI context.
Use resolved UI files.
Reuse helpers/page objects/assertions.
Keep mockserver-owned behavior in the mockserver.
Run the focused Playwright verification commands.
```

## Graph-Based Test Intelligence

The next question was:

```text
Can agents and humans see which tests relate to a change?
```

V2 adds a deterministic test graph built from the resolved API and UI contexts.

It maps relationships like:

```text
endpoint -> controller -> service -> OpenAPI -> RestAssured test
UI flow -> Playwright spec -> helper -> mockserver route -> role
```

The current graph is intentionally small. It is not trying to be a full
enterprise knowledge graph. It is trying to answer a practical QA question:

```text
For this ticket, which tests, files, roles, commands, and mocks are relevant?
```

That graph is useful for agents because it can guide impact analysis. It is
useful for humans because it makes the test mapping visible.

Graphify is also wired as an optional broader exploration layer. I treat it as
supporting context for repo exploration, not as the source of truth for
duplicate detection or test routing.

The distinction is important:

```text
Built-in graph -> deterministic QA/test-impact graph
Graphify       -> optional broad workspace knowledge graph
```

## Duplicate Prevention: Instruction First, Graph Assisted

One tempting idea is to make duplicate detection fully tool-driven.

I am not doing that yet.

In this workspace, duplicate prevention remains instruction-first:

```text
Before adding a test, inspect existing resolved tests and classify the case.
```

The agent should decide whether the requested scenario is:

- already covered,
- missing only an assertion,
- genuinely new,
- a product/contract gap,
- a mockserver behavior gap,
- or a deliberate coverage sibling.

The dashboard now shows duplicate and overlap candidates, but those are signals
for review. They do not replace QA judgment.

For example, two tests can look similar by text:

```text
admin can access admin actions
non-admin cannot access admin actions
```

Those are not duplicates. They are a useful positive/negative pair.

That is why the V2 dashboard classifies near matches as either duplicate-risk
or coverage-sibling signals.

## Stakeholder Dashboard

One of the bigger V2 goals was visibility for people who do not live in the
IDE.

Business users, QA leads, clients, and release stakeholders often want to know:

- what tests map to this story,
- whether API and UI tests are passing,
- what changed,
- what tests are impacted,
- whether there are coverage gaps,
- whether duplicate test creation was avoided,
- whether the graph is stale,
- whether a release looks risky.

So V2 adds a lightweight static QA dashboard.

It shows:

- API health,
- Playwright health,
- test graph node/relationship counts,
- Graphify node/community counts,
- release confidence,
- test mix,
- changed-file impact recommendations,
- endpoint and role coverage,
- duplicate/overlap candidates,
- duplicate-prevention evidence from the loop log,
- runtime usage readiness.

It uses CSS-only bars and small vanilla JavaScript table controls. There is no
heavy frontend framework and no charting dependency.

For larger suites, tables are bounded by default:

- top 10 rows first,
- local search,
- row counts,
- Show all / Show top 10 toggle,
- scrollable tables with sticky headers.

The point is not to build a commercial QA platform in one pass. The point is to
create a practical stakeholder view that grows with the workspace.

## Containerized Viewing

The graph views and dashboard can also run in Docker:

```bash
npm run graphs:docker:build
npm run graphs:docker:up
```

Default URLs:

```text
QA dashboard:      http://127.0.0.1:8765/
Test-impact graph: http://127.0.0.1:8766/
Graphify graph:    http://127.0.0.1:8767/graph.html
```

This matters because not every stakeholder should need an IDE or a local
developer setup to inspect test mappings.

## What V2 Proves

V2 proves a narrower but useful point:

```text
Agentic QA is not just about generating tests.
It is about routing, boundaries, evidence, and visibility.
```

The agent needs routing:

```text
API task or UI task?
service context or UI context?
RestAssured skill or Playwright skill?
```

The agent needs boundaries:

```text
API framework stays API.
Playwright framework stays UI.
Mockserver owns mocked backend behavior.
```

The agent needs evidence:

```text
OpenAPI, source code, resolved files, graph mappings, test reports.
```

Humans need visibility:

```text
dashboard, graph views, duplicate decisions, coverage gaps, release confidence.
```

That is the real V2 shift.

## Current Limits

This is still a reference implementation.

Some important limits remain:

- The demo service and UI app are intentionally small.
- Real-world usage metrics are only a readiness slot until a team feeds API
  gateway logs, UI analytics, or mockserver traffic into
  `artifacts/usage-metrics/usage.json`.
- Duplicate detection is heuristic and instruction-first; semantic embeddings
  can be added later.
- Graphify is optional exploration, not the source of truth.
- Local model editing still requires structured tool-call validation before
  trusting autonomous edits.

Those limits are intentional. I would rather keep the architecture honest than
pretend a demo repo is a complete enterprise QA platform.

## Final Thought

The biggest lesson from V2 is that agents become more useful when the workspace
teaches them how the QA system is organized.

Not with a massive prompt.

With:

- small task context,
- generated resolved context,
- framework-specific skills,
- deterministic graph evidence,
- focused verification commands,
- and dashboards that expose the result to humans.

That is the direction I want to keep exploring: QA agents that do not just
write tests, but preserve test intent and make quality evidence easier to see.

