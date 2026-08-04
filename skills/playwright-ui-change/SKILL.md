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

## Quality Gates

- UI tests use the existing Playwright framework and TypeScript conventions.
- Role expectations are derived from mockserver behavior or existing test data,
  not guessed.
- API and UI frameworks remain isolated.
- Playwright reports, traces, screenshots, and `node_modules` stay out of Git.
- Verification commands and skipped gates are reported.
