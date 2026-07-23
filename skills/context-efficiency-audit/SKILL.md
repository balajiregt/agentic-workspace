---
name: context-efficiency-audit
description: Measure and explain local-agent context efficiency for the agentic workspace. Use when asked to validate token efficiency, compare central YAML context against full repository context, produce metrics for an 8 GB MacBook Air, or gather evidence for a blog about bounded agent context.
---

# Context Efficiency Audit

## Goal

Show that the workspace is context-efficient: the agent starts from a compact
YAML control plane and reads exact local paths only when needed.

## Inputs

- Workspace root: current repository root.
- Context file: `contexts/current/service-context.yml`
- Corpus root: `projects/microservices`
- Script: `scripts/context_efficiency_report.py`

## Procedure

1. Run the context efficiency script.
2. Capture central context tokens, corpus tokens, tokens saved, corpus
   percentage, and compression ratio.
3. If validating the full workflow, run the service/unit tests and API tests
   for the demo or target project.
4. For 8 GB MacBook Air claims, report bounded-context behavior rather than
   promising raw speed.

## Commands

```bash
python3 scripts/context_efficiency_report.py
```

```bash
python3 scripts/context_efficiency_report.py --format json
```

## Metrics To Report

- Central context tokens
- Full microservices corpus tokens
- Tokens saved versus full prompt dump
- Central context as percentage of corpus
- Compression ratio
- Test pass rate
- Wall-clock time for validation commands
- Memory pressure observation when local model and tests are running

## Blog Claim Template

```text
The workspace uses a YAML control plane instead of dumping every repository file
into the model. In this run, the central context used <N> approximate tokens
against <M> tokens in the microservice corpus, a <R>x compression ratio.
```

## Stop Condition

Stop when the metrics are reported with the command used, the approximate-token
caveat is included, and any unrun validation is clearly named.
