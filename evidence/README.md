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
npm run context:report             # API workspace context report (detailed)
npm run evidence:trial:collect -- METADATA.json REPORT.json
npm run evidence:trial:summary
npm run evidence:test              # collector and JUnit adapter tests
```

## History

Created on 11 November 2026 from `evaluation/benchmarks/` and
`tooling/scripts/context_efficiency_report.py`. Earlier publication tooling for
the retired framework-benchmark dashboard is preserved under ignored
`artifacts/retired/evaluation-publication-20261111/`.
