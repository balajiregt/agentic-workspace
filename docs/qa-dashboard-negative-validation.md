# QA Dashboard Negative-Case Validation

Date: 2026-08-08

## Purpose

Before merging V2, validate that the QA dashboard is useful when things are not
green. This document uses a synthetic, non-destructive negative dashboard so the
real API and Playwright suites can remain clean.

Generate it with:

```bash
npm run dashboard:negative
```

Output:

```text
artifacts/qa-dashboard-negative/dashboard.json
artifacts/qa-dashboard-negative/index.html
```

The generated page includes a banner:

```text
Synthetic negative validation...
```

That banner is important. The artifact is only for dashboard validation, not
real release status.

## Injected Negative Signals

| Scenario | Expected Dashboard Signal | Debugging Value |
| --- | --- | --- |
| API failure | API health turns `fail`; API Test Health shows `synthetic.qa.dashboard.NegativeApiCoverageTest` with 1 failure | Useful. Points to the failing suite and keeps the failure close to the summary. |
| Playwright failure | Playwright health turns `fail`; failed test count becomes 2; failed test names appear in Playwright Mapping | Useful. Summary is clear and the visible failed-test list gives reviewers a direct next debugging target. |
| Missing API coverage | Coverage table shows `Endpoint: POST /xyz/review` as `gap` | Useful. A stakeholder can see the exact endpoint missing mapped coverage. |
| Missing role coverage | Coverage table shows `Role: viewer` as `gap` | Useful. Makes role-matrix holes visible without opening specs. |
| Unmapped spec | Gap signals list `review-flow.spec.ts` outside resolved active mapping | Useful. This is directly actionable for agents and reviewers. |
| Duplicate-risk candidate | Duplicate table shows a `near-duplicate review` row with score `0.92` | Useful. Shows both test names, both file paths, score, and shared terms. |
| Coverage sibling distinction | Existing positive/negative pairs remain `coverage sibling` | Useful. Avoids treating deliberate contrast tests as duplicates. |
| Stale graph | Graph freshness bar turns stale and confidence drops | Useful. Makes it obvious the graph should be rebuilt before trusting impact mapping. |
| Changed-file impact | Impact recommendations show high-priority API and Playwright rows | Useful. Helps pick separate validation commands for API vs UI. |

## Expected Synthetic Summary

```text
confidence: risk / 36
api health: fail
playwright health: fail
mapped coverage: 3/5
near duplicate risks: 1
graph freshness: stale
gap signals: 3
```

## Debugging Assessment

The dashboard is helpful for debugging these pre-merge questions:

- Which framework is impacted: API, Playwright, or graph intelligence?
- Is the issue a test failure, missing mapping, duplicate risk, stale graph, or
  unmapped test file?
- Which validation command should be run next?
- Does the candidate duplicate look like a real duplicate or a coverage sibling?
- Can a non-IDE stakeholder understand why confidence dropped?

## Suggested Follow-Up Improvements

- Add a first-class orphan-test table if suites grow beyond the current mapped
  examples.
- Add a real `artifacts/usage-metrics/usage.example.json` once runtime usage
  metrics become part of release discussions.
- Add a CI check that builds both normal and negative dashboard artifacts.
