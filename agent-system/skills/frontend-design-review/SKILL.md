---
name: frontend-design-review
description: Build or refine a frontend with deliberate visual hierarchy, or review its rendered UX, responsiveness, and accessibility. Use for UI design, critique, polish, and visual quality requests; exclude backend-only changes.
---

# Frontend Design Review

## Inputs

Read existing product/design documents if present and inspect the current UI. Preserve the product's established conventions for a refinement; follow the user's visual direction for a redesign.

## Procedure

1. Define the user's task, intended audience, and surface: operating a tool, reading, choosing an offer, or experiencing a portfolio. Match visual emphasis to that purpose.
2. Inspect the rendered current state before a critique. If the app cannot run, identify the freshness and scope of available screenshots rather than inventing screen details.
3. Reuse the existing components and tokens. Check hierarchy, spacing, typography, contrast, keyboard focus, labels, and clear interactive states.
4. Cover loading, empty, error, long-content, and disabled states relevant to the request. Check at the actual desktop and narrow viewport sizes the product supports.
5. Make focused changes, then inspect the rendered result and test the relevant interaction. For a review-only request, return evidence and recommendations without changing code.
6. Use the Impeccable reference snapshot for a specific design question when helpful. It is a reference-only snapshot: its binary launcher, hooks, and downloads are not installed. Use the existing browser and testing tools directly.

## Stop Condition

Deliver the requested UI or critique, with visual evidence where available and any unverified state stated clearly.

## Sources

Adapted from Impeccable and Addy Osmani UI guidance; [source library](../../../knowledge/docs/instagram/source-library.md).
