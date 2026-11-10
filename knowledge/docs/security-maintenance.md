# Workspace security maintenance

Verified 31 October 2026. Evidence and rollback copies are under the ignored
`artifacts/security-remediation-2026-10-31/` directory.

## Selected runtimes

- Node.js **26.13.0**, also pinned in `.nvmrc` and GitHub Actions.
- Python **3.15.2** for new shells and both workspace virtual environments, pinned in `.python-version`.
- Java **17.0.21.0.3** for new shells and Maven; CI selects Temurin 17.0.21.
- Graphify **0.9.70**, with its Fortran include fix, installed in an isolated environment.

Open a new terminal after the machine runtime changes. Check `node --version`,
`python3 --version`, `java -version`, and `mvn -version` before work.
Original environments and older installed runtimes were retained for rollback;
their presence is not a claim that those inactive installations are patched.

The Homebrew Python bottles had an expat linkage mismatch on this Mac. The installed
Python extension was backed up, relinked to Homebrew expat 2.9.0, and signed locally.
After a Homebrew Python upgrade, verify `python3 -c 'import pyexpat; print(pyexpat.EXPAT_VERSION)'`.

## Repeatable dependency checks

```sh
npm run security:check
npm run security:check -- --include-global
```

The gate audits all five npm lockfiles, both Python dependency locks, the Python
build-tool lock, installed workspace environments, and both resolved Maven trees.
`--include-global` also inventories installed global npm tools, the active npm
installation, and the selected native Claude version. It does not install packages
or run npm lifecycle scripts. Network/resolution failures fail the check.
It also rejects Node/Python runtimes and installed Python environments older than
the reviewed workspace pins.
`--skip-java` is available only for an explicitly narrower check.

The 31 October check scanned **1,656** distinct package/version combinations:
zero unaddressed OSV matches and zero vulnerabilities in all five npm audits.
One Netlify `deepmerge` advisory remains visible as a verified local backport;
the original upstream package version is preserved.

The latest vendor tools still required local dependency overrides. Future CLI
updates can replace those overrides. Re-run the global check after every update.
`tooling/scripts/patch_global_deepmerge.mjs` is an explicit manual backport with regression
assertions; it is never an installation hook. Its receipt is accepted only while
all patched file hashes match. A mismatch restores the advisory to the findings.

## Python environments

Do not enable `--system-site-packages`. Package inputs are hash locked. Python 3.15
requires source builds for PyYAML and Graphify's tree-sitter binding; all other
inputs use wheels. Build tools are separately pinned and audited.

```sh
python3 -m venv evaluation/playwright-decision-bench/.venv
evaluation/playwright-decision-bench/.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r tooling/scripts/requirements-python-build.lock
PYYAML_FORCE_LIBYAML=0 evaluation/playwright-decision-bench/.venv/bin/python -m pip install --no-build-isolation --require-hashes --only-binary=:all: --no-binary=PyYAML -r evaluation/playwright-decision-bench/python/requirements.lock
npm run graphify:setup
```

The locks were resolved on macOS arm64. Re-resolve and audit for other platforms.
The graph Docker build also verifies the same inputs on Linux arm64, builds the two
source packages in a separate stage, and leaves compilers out of the runtime image.
Offline import/extraction checks passed; no model weights or hosted inference were run.

## Local services and containers

Lab services bind to loopback. Compose publishes only `127.0.0.1` ports; container
internal listeners can still use `0.0.0.0`. Recursive Docker exclusions cover local
environment files, credentials directories, runtime state, virtual environments,
dependency trees and test artifacts. Synthetic private-marker exclusion was verified
with Docker itself.

The broker uses `labs/kafka-test-project/Dockerfile.kafka`, based on an immutable
Apache Kafka image with Alpine security updates and checksum-pinned lz4/snappy fixes.
Before Docker-enabled Kafka tests:

```sh
cd labs/kafka-test-project
docker compose build kafka
mvn test
```

The optional Kafka UI service was removed with your approval because the latest vendor image retains Critical advisories. The broker, application and tests remain available.

Container scans are separate from the dependency gate. On the verified Grype database
from 30 October, the default graph, patched broker and Java runtime images had no
matches with an available fix. They still had 159, 15 and 174 raw OS/CPE matches
respectively, including High matches in the graph base. These have not all been
proven exploitable or dismissed. The optional UI had 102 matches, including three
Critical matches and 96 matches with an available dependency fix; two Critical
Spring WebFlux advisories had no fix on the bundled vendor line. A maintained vendor
upgrade or separately reviewed application migration is still required.

Raw scans and `container-summary.json` preserve those findings. A clean package gate
does not certify the host or container images as vulnerability free.

## Application and CI boundaries

The Kafka assistant accepts a request-scoped user key only, with no environment-key
fallback. Outbound requests must match the server-configured HTTPS provider endpoint.
Imported comparison metrics are validated and escaped in both renderer copies.

GitHub Actions use commit-pinned actions, checkout without persisted credentials,
and read-only default permissions. Benchmark execution transfers only a validated
aggregate to a separate publishing job; only that job receives write permission.
Local validation used publication-disabled fixtures. No workflow, deployment or
publication was triggered as part of this remediation.

## Checks before commits and after publication

`npm run security:staged` scans the Git index for secrets using Gitleaks 8.30.1,
blocks credential/runtime files and committed `node_modules`, and audits staged
npm locks against the public registry. Dependency edits must include the updated
lock. Unstaged working copies cannot hide a staged secret. Matching secret values
are suppressed. An unavailable scanner or failed network audit blocks the check.

`npm run security:hooks` enables `.githooks/pre-commit` for this checkout only.
It refuses to replace an existing hook or hooks directory. It has been enabled in
this workspace. New clones must run the command themselves; Git does not propagate
local hook settings. It is also enabled in the four existing nested Git checkouts listed in the remediation report. Other clones need their own setup.

The official Gitleaks 8.30.1 macOS arm64 archive was checksum verified and extracted
into ignored `artifacts/tools/gitleaks-8.30.1/`. Alternatively put that version on
PATH or set `SECURITY_GITLEAKS` to its binary. CI downloads the Linux archive and
checks a literal SHA-256 before executing it. There is no automatic install hook.

The GitHub security workflow runs on PRs, pushes to main, manual dispatch and each
Monday. It scans current tracked files for secrets with redaction and runs the full dependency
gate. Dependabot checks updates weekly; routine npm updates use a seven-day cooldown.
Security updates and fixes should still be reviewed and tested. A hook can be
bypassed with Git flags. On 31 October you chose to keep the security checks
advisory: no required status checks were added. A subsequent approved change to
RestAssured rule1 allows solo-maintainer merges: zero required approvals, no
required Code Owner approval, and no restrict-updates rule. Its PR requirement,
force-push block, creation/deletion restrictions and conversation resolution remain.
Check the security results before merging. Account Dependabot alerts,
grouped security-update PRs and defaults for future repositories are enabled.
No check guarantees that a new release is benign or that unknown vulnerabilities
are absent.

The updated Homebrew Python is /opt/homebrew/bin/python3 (3.15.2). If a terminal still selects the older framework Python, put /opt/homebrew/bin first on PATH or select .python-version before running the full audit. The final audit used the explicit 3.15.2 interpreter and included installed tools.
