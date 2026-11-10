---
name: security-review
description: Perform a focused source review for security boundaries and evidence-backed vulnerability findings. Use for requested security reviews or investigations; does not automatically run a full audit or probe deployed systems.
---

# Security Review

## Inputs

Identify the target files, relevant source revision or dirty diff, lower-trust input, protected resource, and requested scope. Default to focused source review.

## Procedure

1. Trace input through validation, authorization, processing, and output. Identify the actual principal and resource whose boundary could fail.
2. Review relevant authentication, tenant isolation, injection, secret handling, dependency execution, and output handling paths. Inspect only areas relevant to the scope.
3. Separate confirmed behavior from a source-grounded hypothesis and from optional hardening. Missing best practice alone is not a demonstrated vulnerability.
4. Use existing local fixtures with dummy data for bounded verification when the environment permits it. A full Cloudflare audit requires its documented OS isolation, resource limits, validators, and independent verification; this adapter does not establish those capabilities.
5. Do not run target-controlled audit harnesses without the required isolation or probe live/shared endpoints as a side effect of source review. Record the exact blocked fact and a safe validation plan.
6. Report affected file/line, triggering input, boundary, observed or unverified result, and the smallest effective fix. Assign severity only when impact is supported.

## Stop Condition

State the reviewed scope and whether each finding is confirmed, needs validation, or rejected. A focused review is not a complete security certification.

## Sources

Adapted from Cloudflare security-audit-skill and Addy Osmani security guidance; [source library](../../../knowledge/docs/instagram/source-library.md).
