---
name: test-integrity
description: Assess whether an API or Playwright test proves the intended behavior, including assertion sensitivity, duplicate coverage, locator specificity, and evidence of failure. Use for test quality audits, suspicious green tests, or false done claims.
---

# Test Integrity

## Inputs

Use the existing microservice-change or playwright-ui-change skill first for framework ownership and exact paths. Derive expected behavior from the contract, app, mockserver, or independent accepted examples.

## Procedure

1. Identify the behavior, public interface, fixture, role, and assertion. Classify coverage as already present, missing assertion, new scenario, or product/contract gap.
2. Check that setup reaches the intended path. For UI tests, ensure the locator identifies the intended element and the mock or role signal reaches the app.
3. Reject assertions that recompute the implementation, assert a constant against itself, check only that a request succeeded, or observe the wrong record or UI instance.
4. Only when fault-execution/mutation verification is explicitly requested, prove sensitivity in a disposable fixture or temporary copy: break the intended behavior, run the focused check, and verify it fails for the expected reason. Otherwise report static sensitivity concerns without injecting faults. Restore and verify green after authorized fault execution; never mutate a shared service or another person's working files.
5. Check that fixtures, independent expected values, cleanup, and async waits make the signal deterministic. Prefer web-first assertions to fixed sleeps.
6. Keep evidence proportional: actual command, expected failure, observed failure, and restored pass. Do not claim a mutation check ran unless it did.

## Stop Condition

State what the test proves, what it misses, and whether failure sensitivity was observed or only inspected.

## Sources

Inspired by the saved Japneet SDET post and the workspace's existing duplicate and framework rules; [catalogue](../../../knowledge/docs/instagram/catalog.md).
