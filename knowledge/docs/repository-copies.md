# Workspace ownership and Git boundaries

Verified on 11 November 2026. Each active product has one working checkout.

| Repository / responsibility | Working location |
| --- | --- |
| Workspace core, context, skills and Maven projects | `.` and `services/microservices/` |
| [Playwright Agent](https://github.com/balajiregt/playwright-agent) | `qa/playwright-agent/` |
| [Role-Aware Mockserver](https://github.com/balajiregt/plawright-role-aware-mockserver) | `qa/ui-automation/role-aware-mockserver/` |
| [Portfolio website](https://github.com/balajiregt/portfolio-web) | `products/portfolio/portfolio-web/` |
| FinFolio app, FinFolio agent, career agent | `products/finance/`, `products/career/` |
| Kafka/event quality lab | `labs/kafka-test-project/` |
| Reference Playwright starter template | `qa/playwright-template/` |

The mockserver's existing standalone Git metadata moved with its source into the
canonical UI location. Its origin, commits and security tooling are preserved.
Root UI commands and resolved context already use this path. The parent workspace
ignores the nested checkout so it cannot become an accidental embedded repository.
There is no second mockserver project registration.

Playwright Agent owns its internal `quality/` package; that directory is not a
separate Git repository. The GitHub decision-bench repository is archived and
read-only. Its complete local checkout, including private evidence/environments
and Git metadata, is recovery data under
`artifacts/focused-restructure-20261031/recovery/decision-bench/`. Its source
history also remains in Playwright Agent's `archive/playwright-decision-bench-20261031`
branch. It has no active source folder or forwarding entrypoints under evaluation/.

The old integrated mockserver source is preserved at
`artifacts/focused-restructure-20261031/recovery/integrated-mockserver/`. Its installed
dependencies and test evidence moved into the canonical checkout. The empty extra
API placeholder is also retained only as recovery data; real API tests remain
under `services/microservices/qa-projects/xyz-service-api-tests/`.

The standalone QA viewer was retired from active projects. Its source/local edits
remain at `artifacts/product-retirement-20261031/qa-dashboard-viewer/`. No separate
hosted viewer site was deleted. Recovery copies
under artifacts are excluded from active registration, watches and publication.
The two clean task-created release worktrees were removed without force; all
repository refs and generated/private recovery data were preserved.

Existing user changes and nested Git boundaries are preserved. This restructure
does not publish source, deploy applications, rerun benchmarks or publish metrics.
The platform's deployed UI edits and the wider workspace reorganisation remain
in their existing local working trees until separately committed.
