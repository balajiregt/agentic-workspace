# Shared evaluation tooling

`benchmarks/` contains shared controlled-trial tooling and evidence collection.
Results belong to the project being evaluated; the public showcase is maintained
in `products/agent-tools/framework-benchmark-dashboard/`.

Playwright acceptance assessment and behavioral mutation tools belong exclusively
to [Playwright Agent](../qa/playwright-agent/README.md),
inside its `quality/` module. The former `playwright-decision-bench/` working
folder and forwarding commands are retired. Its complete source, Git metadata
and private runtime are preserved under ignored
`artifacts/focused-restructure-20261031/recovery/decision-bench/`.

API trials and browser execution keep their existing distinct test targets.
Moving folders does not run a benchmark or publish metrics.
