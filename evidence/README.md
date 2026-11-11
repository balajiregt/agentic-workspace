# Workspace evidence

This folder measures whether the agentic workspace delivers what it claims, for
each project: the API workspace (`services/microservices`), the role-aware
mockserver and Playwright Agent.

| Measurement | Question | Location |
| --- | --- | --- |
| Context | Workspace context needs X tokens; giving the whole project would need Y | `context/` |
| Agent trials | With workspace help the agent passed the required tests; without it, it failed K | `trials/` ([protocol](trials/PROTOCOL.md)) |
| Project evidence | Each project's own results, imported as they are | Owned by each project |

Projects keep their own tools and still work standalone. This folder calls them
from the workspace root; it never copies them or adds workspace-only scripts to
an independent repository.

Results are private and stay under ignored `evidence/results/`. Failed and
skipped runs are kept, unknown values stay null rather than zero, and nothing is
published automatically.

## Commands

```sh
npm run evidence                                  # all projects
npm run evidence -- --project playwright-agent    # or api-workspace, mockserver
npm run evidence:context                          # context only
npm run evidence:trial:collect -- METADATA.json REPORT.json
npm run evidence:trial:summary
npm run evidence:test                             # evidence tool tests
npm run context:report                            # detailed API workspace context report
```

Profiles live in [`projects.json`](projects.json). Each context profile names the
routing instructions, the one skill an agent loads, the task input and either its
resolved context or an explicit file list. API and mockserver profiles read
`contexts/.resolved/`; regenerate with `npm run context:resolve` or
`npm run context:ui:resolve` after task or layout changes.

## Reading the context numbers

`instructions` is the fixed cost of workspace guidance (root routing, project
instructions and one skill), about 5k tokens. `task files` is what the task needs
from the project. The comparison corpus is the project's Git-tracked text files.
Workspace guidance pays off on larger projects and can cost more than reading a
very small project in full; the report keeps that visible instead of hiding it.

## History

Created on 11 November 2026 from `evaluation/benchmarks/` and
`tooling/scripts/context_efficiency_report.py`. Earlier publication tooling for
the retired framework-benchmark dashboard is preserved under ignored
`artifacts/retired/evaluation-publication-20261111/`.
