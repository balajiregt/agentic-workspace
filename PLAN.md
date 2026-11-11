# Agentic workspace ownership

Component ownership comes from workspace.projects.json. The checkboxes below describe only this Agenttrail Map installation, with source and execution evidence. Components without tasks make no implementation-completion claim.

## Workspace core {#core}
files: [AGENTS.md, README.md, workspace.projects.json, package.json, .agents/**, agent-system/**, tooling/**, knowledge/docs/**]
links: [finfolio-app, finfolio-agent, career-agent, portfolio-web, portfolio-template, agent-dashboard, microservices, playwright-framework, role-aware-ui, playwright-template, kafka, benchmarks]

## FinFolio app {#finfolio-app}
files: [products/finance/finfolio-app/**]
links: [core]

## FinFolio agent {#finfolio-agent}
files: [products/finance/finfolio-agent/**]
links: [core]

## Career agent {#career-agent}
files: [products/career/career-agent/**]
links: [core]

## Portfolio website {#portfolio-web}
files: [products/portfolio/portfolio-web/**]
links: [core]

## Portfolio template {#portfolio-template}
files: [products/portfolio/portfolio-template/**]
links: [core]

## Agenttrail dashboard {#agent-dashboard}
files: [products/agent-tools/agent-dashboard/**]
links: [core]

- [x] Install pinned Agenttrail Map 0.2.0 {#map-install-package}
  tech: products/agent-tools/agent-dashboard/package.json and package-lock.json; npm install completed with lifecycle scripts disabled and zero audit findings.
- [x] Add isolated Map launch, status and stop controls {#map-install-launch}
  tech: products/agent-tools/agent-dashboard/scripts/map-server.mjs and manage.mjs; startup and workspace identity verified on port 5330, eight manager/adapter tests passed.
- [x] Verify the rendered Map and managed stop/restart behavior {#map-install-verification}
  tech: Readiness and identity passed on port 5330; nine components rendered in browser; managed stop/restart passed, and reuse retained the same running PID.

## API services and RestAssured {#microservices}
files: [services/microservices/**]
links: [core]

## Playwright Agent {#playwright-framework}
files: [qa/playwright-agent/**]
links: [core]

## Role-aware UI automation {#role-aware-ui}
files: [qa/ui-automation/role-aware-mockserver/**]
links: [core]

## Playwright template {#playwright-template}
files: [qa/playwright-template/**]
links: [core]

## Kafka testing lab {#kafka}
files: [labs/kafka-test-project/**]
links: [core]

## Shared agent benchmarks {#benchmarks}
files: [evaluation/benchmarks/**]
links: [core]
