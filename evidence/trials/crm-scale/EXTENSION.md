# CRM-Scale tools-first extension: pre-registration

Written before any extension session runs. `freeze-extension.json` records the
Playwright Agent commit and the SHA-256 of every input. `analyze.py --prefix crm-tools`
applies the rules in [PREREGISTRATION.md](PREREGISTRATION.md) to these runs only.
They are never pooled with Phase 2.

## Why

Phase 2 (frozen rules, Opus 5.5, 15 assessment pairs) found no measurable accuracy
gain from Playwright Agent. Recall was 90.2% alone vs 91.7% with Playwright Agent,
and Playwright Agent cost more in 11 of 15 pairs. Both arms missed the same four
role-permission gaps in most runs. In the 3 mutation pairs collected before the
batch was stopped, the framework arm used a disposable copy every time but still
edited the real source in 2.

Playwright Agent was then changed (commit in `freeze-extension.json`) to hand
repeatable work to deterministic tools and shorten its guidance:

- `npm run coverage:matrix`: a criterion-to-candidate-test index with roles and
  denial checks. It flags "only X can…" rules whose allowed or denied roles are never checked.
- `npm run mutate`: one fault on a disposable copy, two healthy baselines, two faulted
  runs, and a verdict. It proves the original unchanged.
- Router plus one skill shrank from about 7.7 KB to 4.3 KB. The framework arm no
  longer receives the workspace-wide AGENTS.md (8 KB).

The question: does the tools-first Playwright Agent add accuracy, safety or
efficiency to Claude Opus where the Phase 2 version did not?

## Design

- The same app, variants, answer key (revision 2), faults, prompts and oracles as
  Phase 2. Only the Playwright Agent commit and the framework arm's context profile
  (`crm-tools-*`) differ.
- The baseline arm is built as in Phase 2: the same commit with all agent guidance
  removed. The project's scripts, including the new tools, stay in both arms, as the
  quality runner did in Phase 2. Opus alone gets no pointer to them.
- Model Claude Opus 5.5, the same allowlist, arm order alternating by repeat.
- Assessment: variants A–E × 3 repeats = 15 pairs. Mutation proof: MS1–MS6 × 2
  repeats = 12 pairs. Authoring is not re-run: its skill did not change, and Phase 2
  authoring tied 4/4.

## Decision rules

The primary rules, margins, efficiency rule and exclusions are exactly those of
PREREGISTRATION.md. Also reported, as pre-specified secondary measures:

1. **Role-permission gaps:** how often each arm finds PERM-EXPORT, PERM-AUDIT,
   ACC-DELETE and QUO-APPROVE-ROLE (60 chances per arm).
2. **Tool use:** framework runs that ran `coverage:matrix` or `mutate`.
3. **Mutation safety:** safe method (disposable copy, real source never edited), per arm.

Comparisons with the Phase 2 framework arm are descriptive only (different sessions
and dates). The baseline arm of this extension is the control.
