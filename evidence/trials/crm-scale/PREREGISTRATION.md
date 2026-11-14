# CRM-Scale trials: pre-registration (Phase 2)

Written and frozen before any Phase 2 agent session runs. `freeze.json` records the
SHA-256 of every input below; `analyze.py` applies these rules mechanically. Any change
after the first session is disclosed in APPROACH.md with the reason, and both the
original and the changed analysis are reported.

## Question

What does Playwright Agent add to Claude Opus on harder test work? The comparison is
Claude Opus alone vs Claude Opus + Playwright Agent, with the same model, prompt and
project copy. Playwright Agent is an add-on to a coding agent, not an alternative to one.

Phase 1 found a ceiling: on the small sample CRM, Opus alone found every coverage gap.
CRM-Scale is larger (11 modules, 5 roles, 216 tests, a 3-layer framework, 90 criteria)
and its gaps are harder to see.

## Fixed inputs

| Input | File |
| --- | --- |
| Application and suite | `qa/playwright-agent/examples/crm-scale` at the commit in `freeze.json` |
| Acceptance criteria (90) | `examples/crm-scale/requirements/acceptance-criteria.json` |
| Answer key, variants, mutation and authoring cases | `evidence/trials/crm-scale/cases.json` |
| Faults (49 exact patches) | `evidence/trials/crm-scale/faults.json` |
| Key validation report | `evidence/results/assessments/crm-scale-key-validation.json` (must be VALID) |
| Tasks and prompts | `evidence/trials/tasks.json` (ids starting `crm-scale-`) |
| Authoring oracle | `evidence/trials/oracles/crm-scale.playwright.config.ts` |

The answer key (revision 2) has 70 covered criteria, 14 natural gaps (missed by the
unweakened suite) and 6 ambiguous criteria (answered, never scored). Variants B–E plant 18 more gaps with
hidden techniques: buried helpers, data-table rows removed, permissive patterns, a
conditional skip, the wrong role, a mocked response, swallowed assertions, and test
data that can no longer fail. Every gap is proven with a fault; every covered criterion
with a fault is proven caught, and every variant is proven to weaken only what the key says.

## Revision before scoring

One calibration pair (assessment variant B, repeat 0) ran against key revision 1. Both
arms independently marked the same seven "covered" criteria as partial, with correct
reasons. The key was too lenient. Six of those became fault-proven natural gaps, one
became ambiguous, five criteria were reworded to remove untestable or loose clauses, and
the seed gained a deal won before the quarter so that cutoff is testable. The key was
then re-validated and re-frozen. The calibration pair is kept in
`evidence/results/calibration/` and excluded from scoring. No other session ran before
this revision.

## Model and runs

- Model: Claude Opus 5.5, fresh headless Claude Code sessions, the same allowlist as Phase 1.
- Assessment: 5 variants × 3 repeats = 15 pairs (30 sessions).
- Mutation proof: 6 cases (3 caught, 3 not caught) × 2 repeats = 12 pairs (24 sessions).
- Authoring: 4 tasks × 3 repeats = 12 pairs (24 sessions).
- Arm order alternates by repeat. Total 78 sessions on the existing subscription.

## Primary measures and decision rules

A difference counts only if it clears the margin below. Otherwise the verdict is
"no measurable difference".

**Assessment.** Primary: gap recall (gaps marked partial or missing ÷ gaps in the key)
and false alarms (covered criteria marked partial or missing), pooled over runs.
- *Adds accuracy* if pooled recall with Playwright Agent is at least 10 points higher,
  and the framework arm wins more pairs than it loses. A pair is won by higher recall
  with no more false alarms, or equal recall with fewer false alarms.
- *Ceiling* if Opus alone has 100% recall and no false alarms in all 15 runs. This
  triggers the Haiku extension below.

**Authoring.** Primary: *correct*, meaning the required test exists and passes, the
whole suite stays green, and the new test fails under the gap's fault. Secondary:
*framework fit*, meaning the app is unchanged, only `examples/crm-scale` changes, the
spec uses the project fixture, and there are no raw request contexts.
- *Adds value* if the framework arm has at least 2 more correct runs out of 12, or
  correctness within 1 run and framework fit in at least 4 more runs out of 12.

**Mutation proof.** Primary: a correct verdict that is *fully proven* (tests run, a fault
actually introduced, and the app and tests restored). Secondary: *safe method*, meaning a
disposable copy was used and the real source never edited.
- *Adds value* if the framework arm has at least 2 more fully proven correct runs out of
  12, or correctness within 1 run and a safe method in at least 4 more runs out of 12.

## Efficiency (secondary, judged only when the primary measure ties)

Per run: input tokens (cached and fresh), output tokens, tool calls, distinct files
read, turns, wall time and Claude Code's estimated cost. Per arm: **cost per successful
completion** (total cost ÷ correct runs).
- *Adds efficiency* if the framework arm is cheaper in at least 2/3 of the pairs and the
  bootstrap 95% CI of the median paired cost saving excludes zero.
- *Costs more* if the same holds in the other direction. Both outcomes are reported.

## Consistency and uncertainty

- pass^k: for each task, whether every repeat was correct.
- 95% Wilson intervals for every rate; paired wins, losses and ties for every measure.
- With 12–15 pairs per skill, results show direction and size, not significance.

## Haiku extension (conditional)

Only for a skill where Opus alone hits the ceiling above: run the same pairs with
Claude Haiku 5.5. The question becomes whether Playwright Agent lets a smaller, cheaper
model match Opus alone. Haiku runs are reported separately and never pooled with Opus.

## Exclusions (kept and reported, never silently dropped)

- Sessions refused by a usage limit: not scored; the pair is re-run.
- Any genuine permission denial: the pair is flagged and reviewed.
- Any tool call that touches the workspace (where keys and faults live): the run is
  excluded from scoring and disclosed.
- A framework arm that never received skill content is reported as such. It stays in
  the primary analysis and is also shown separately.
