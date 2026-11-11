# Workspace evaluation

This folder answers one workspace-level question: **do the workspace's context,
skills and routing help a coding agent complete a fixed task correctly?** It
holds the controlled-trial protocol, four fixed tasks and the shared collection
tools in [`benchmarks/`](benchmarks/README.md).

It does not own every project's evaluation:

| Question | Owner |
| --- | --- |
| Does a workspace-assisted agent complete fixed tasks better than a baseline? | `evaluation/benchmarks/` (this folder) |
| Do Playwright tests cover the criteria, is the matrix complete, do assertions catch faults? | [Playwright Agent `quality/`](../qa/playwright-agent/quality/README.md) and its [evaluation reports](../qa/playwright-agent/docs/evaluation-reports.md) |
| Role-aware mockserver versus browser interception | The mockserver's own `benchmarks/` |
| Products and labs (FinFolio, career agent, portfolio, Kafka) | Their own tests; agent trials are not required |

Results stay with the project being evaluated, private under ignored
`benchmark-results/`. Nothing here publishes automatically.

## Retired on 11 November 2026

The public framework-benchmark dashboard was retired, along with the pieces that
only fed it: the dashboard runner and publisher, the cloud/local trial wrapper
(`controlled-trials.py`), the automatic-publication guide, the
`benchmark`, `benchmark:publish` and `benchmark:trials*` npm scripts, the
`Publish benchmark evidence` GitHub workflow and its publisher test. Copies are
preserved under ignored `artifacts/retired/evaluation-publication-20261111/`
and remain in Git history. The former `playwright-decision-bench/` folder was
retired earlier; its copy is under ignored
`artifacts/focused-restructure-20261031/recovery/decision-bench/`.
