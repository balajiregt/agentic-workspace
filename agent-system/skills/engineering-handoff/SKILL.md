---
name: engineering-handoff
description: Capture the state of an unfinished engineering task for another session, or document a meaningful architecture decision. Use for handoffs, continuation notes, ADRs, and preserving project terminology.
---

# Engineering Handoff

## Procedure

1. Capture the requested outcome, acceptance criteria, current implementation state, and remaining work.
2. Identify changed files and their ownership, source revision or dirty state, exact verification commands and results, and unresolved assumptions. Do not overwrite another agent's changes.
3. Give the next concrete action and the files needed to do it. Prefer a short local handoff over repeating the whole chat or dumping the repository.
4. Write an ADR only for a durable trade-off: context, decision, alternatives, and consequences. Reuse existing domain terms and document a glossary only when ambiguity matters.
5. Exclude credentials, private session data, and unrelated personal context. Do not automatically send a handoff to another chat, issue tracker, or person.

## Stop Condition

Another session can continue using the handoff and referenced files without treating an unverified claim as completed work.

## Sources

Adapted from Matt Pocock handoff and domain-modeling, and Addy Osmani documentation practices; [source library](../../../knowledge/docs/instagram/source-library.md).
