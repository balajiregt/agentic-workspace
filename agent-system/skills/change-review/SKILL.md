---
name: change-review
description: Review a requested diff or completed change for correctness, acceptance criteria, regression risk, and unnecessary complexity. Use for code reviews and verification before completion.
---

# Change Review

## Procedure

1. Establish the reviewed diff or file set and acceptance criteria. Separate pre-existing edits from the current task. For a review-only request, keep the source unchanged.
2. Trace changed behavior through real callers and contracts. Look for concrete failures, incomplete requirements, error paths, authorization mistakes, and regressions.
3. Assess tests: do they exercise the actual changed behavior and fail for the intended reason? Passing status alone is insufficient. Use test-integrity when the evidence is questionable.
4. Run the relevant checks when authorized and practical. Report the command, result, and unverified conditions; do not present static inspection as a runtime pass.
5. Report actionable findings with file/line evidence, triggering input, impact, and smallest effective fix. Distinguish findings from optional suggestions.
6. Avoid reviewing unrelated files or turning style preferences into blockers. Recheck only changed or unresolved concerns after fixes.

## Stop Condition

The review names concrete findings or states no findings in the reviewed scope, with the actual verification limits.

## Sources

Adapted from Addy Osmani code review, Superpowers verification, and ECC review practices; [source library](../../../knowledge/docs/instagram/source-library.md).
