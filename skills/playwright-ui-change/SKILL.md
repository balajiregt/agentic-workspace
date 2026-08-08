---
name: playwright-ui-change
description: Make context-aware Playwright UI automation changes in the agentic workspace without mixing them into the RestAssured API framework.
---

# Playwright UI Change

## Goal

Change the smallest correct set of UI automation, mockserver, or demo app files
for the Playwright slice declared in the UI context YAML.

## Inputs

- Read `contexts/current/ui-context.yml` from the workspace root.
- Read `contexts/current/resolved-ui-context.yml` when it exists. If it is
  missing or stale, run `npm run context:ui:resolve`.
- Treat `resolved_repositories.*` as the source of truth for UI project paths
  when resolved context exists.
- Treat `resolved_files.*` as the first-choice file map for Playwright config,
  tests, helpers, page objects, mockserver routes, and app files.
- Treat `repository_topology` as the source of truth for keeping API and UI
  automation isolated.

## Procedure

1. Inspect the UI context YAML before editing.
2. If resolved UI context exists, open the relevant exact target file before
   searching.
3. Keep Playwright code under the resolved UI project. Do not add Playwright
   dependencies, tests, or mockserver code to the Maven parent, `qa-steps`, or
   service-specific RestAssured API projects.
4. Use existing Playwright helpers, page objects, assertions, test tags, and
   mockserver request-header patterns before adding new abstractions.
5. For role-specific UI behavior, confirm the expected role, token, mockserver
   response, and UI assertion path from existing tests and mockserver routes.
6. Prefer mockserver-owned behavior for backend responses. Use Playwright route
   interception for request setup headers or explicit legacy comparison tests.
7. If a UI test expects behavior not represented in the app or mockserver,
   report an app/mockserver/product gap instead of rewriting the test just to
   pass.
8. Run the verification commands from resolved UI context after changes.

## Duplicate Coverage Check

Before adding a new Playwright test, inspect the resolved UI test files and
classify the request:

- Exact flow, role, mock setup, visible action, and assertion already covered:
  do not add a duplicate test.
- Same flow is covered but one assertion is missing: add only that assertion to
  the existing test.
- Role, route, feature flag, error state, or user workflow is genuinely new:
  add a focused test using existing helpers/page objects.
- Expected behavior is not represented by the app or mockserver: report an
  app/mockserver/product gap.

Use the resolved Playwright test directory, helpers, page objects, assertions,
and mockserver routes for this check. Do not broaden into unrelated projects
unless the UI context points there.

## Playwright Framework Conventions

- Prefer existing project structure: tests in `playwright/tests`, reusable
  request setup in `playwright/helpers`, locators/actions in `playwright/pages`,
  and assertion helpers beside the page object when that pattern exists.
- Keep specs readable as behavior flows. Use `test.step` for meaningful
  GIVEN/WHEN/THEN boundaries when the surrounding tests do.
- Instantiate page objects and assertion wrappers in `beforeEach` or a typed
  fixture when multiple tests share them. Do not instantiate page objects at
  module scope because they depend on the per-test `page`.
- Add `test.extend` fixtures only when setup is reused across multiple specs or
  needs typed dependency injection. For one or two local tests, prefer the
  existing helper functions and `beforeEach`.
- Keep test data close to the behavior when it is scenario-specific. Promote it
  to a helper only when it is reused or part of the framework contract.

## Locator Priority

Use Playwright locators in this order unless the existing project has a stronger
local convention:

1. User-facing accessibility locators: `getByRole`, `getByLabel`,
   `getByPlaceholder`, `getByText`, or `getByAltText`.
2. Stable test IDs with `getByTestId` for non-semantic dynamic UI, repeated
   action cards, technical status values, or existing app conventions.
3. Page-object methods that wrap one of the above.
4. CSS locators only for stable structural hooks that cannot be expressed
   semantically.
5. Avoid XPath and brittle selectors based on DOM depth, generated classes,
   styling, or exact layout.

In this workspace's current role-aware slice, `data-testid` is the established
app contract, so prefer page-object methods backed by `getByTestId` before
adding raw locators in specs.

## Session, Storage, and Auth State

- Prefer Playwright `storageState` files or authenticated fixtures for stable
  login/session reuse when the app has a real login flow.
- Use `page.addInitScript` for `localStorage` or `sessionStorage` setup only
  when the app genuinely reads browser storage before or during navigation.
- Set storage before `page.goto`; document the storage keys through helper
  names rather than inline magic strings in each spec.
- Keep role/auth identity setup in helpers or fixtures. In the current
  mockserver-backed slice, role identity is injected through request headers via
  `mockAgentRoles(page, roles)`, not direct session storage.
- Do not mix multiple auth setup patterns in the same flow unless the app
  requires it. If a new test needs storage state while existing tests use
  mockserver token headers, explain why.

## Network and Mockserver Boundaries

- Prefer mockserver-owned backend behavior for API responses used by UI tests.
  Add or adjust mockserver routes when the backend behavior is part of the
  scenario.
- Use `page.route(... route.continue({ headers }))` for request setup signals
  such as roles, feature flags, or failure toggles.
- Use `route.fulfill` only for explicit legacy-interception comparison tests or
  narrow browser-only behavior that should not become mockserver behavior.
- Keep URL globs specific enough to avoid intercepting unrelated calls.

## Assertions

- Assert user-visible behavior first: visible labels, role-specific actions,
  status messages, navigation state, and accessibility-visible controls.
- Prefer web-first assertions such as `toBeVisible`, `toHaveText`,
  `toContainText`, `toHaveCount`, and `expect.poll` for derived async values.
- Put repeated assertions in assertion helpers. Keep one-off assertions in the
  spec when abstraction would hide the behavior.
- Avoid fixed sleeps. Use Playwright auto-waiting, web-first assertions, or
  explicit waits for app-owned signals.

## Quality Gates

- UI tests use the existing Playwright framework and TypeScript conventions.
- Role expectations are derived from mockserver behavior or existing test data,
  not guessed.
- New tests pass the duplicate coverage check before creation.
- Locators follow the locator priority and existing page-object conventions.
- Auth/session setup uses one clear helper, fixture, or storage-state pattern.
- API and UI frameworks remain isolated.
- Playwright reports, traces, screenshots, and `node_modules` stay out of Git.
- Verification commands and skipped gates are reported.
