# Workspace and GitHub security remediation

The current reviewed result and per-repository commit index are in [the remediation report](../../artifacts/github-security-fixes-2026-10-31/RESULTS.md). The report distinguishes local commits, applied account settings, unmerged changes, credential rotation, hosted access and remaining container findings.

Before commits run npm run security:staged. Install the local hook with npm run security:hooks. Run the full audit with the runtimes pinned in .nvmrc and .python-version; npm run security:check -- --include-global also checks installed tools. See [security maintenance](security-maintenance.md) for usage and limitations.
