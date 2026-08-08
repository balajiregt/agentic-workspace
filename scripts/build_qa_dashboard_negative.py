#!/usr/bin/env python3
"""Build a synthetic negative-case QA dashboard for pre-merge validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_qa_dashboard import WORKSPACE, build_dashboard, render_dashboard


DEFAULT_OUTPUT_DIR = "artifacts/qa-dashboard-negative"


def inject_negative_signals(data: dict[str, Any]) -> dict[str, Any]:
    data["validationMode"] = (
        "Synthetic negative validation: generated from real workspace context plus injected "
        "gap, duplicate, stale graph, and failure signals. Do not treat this as real test status."
    )

    data["graphs"]["stale"] = True
    data["graphs"]["graphify"]["builtAtCommit"] = "synthetic-old-commit"

    api_suite = {
        "suite": "synthetic.qa.dashboard.NegativeApiCoverageTest",
        "path": "synthetic/negative-api-coverage.xml",
        "tests": 3,
        "failures": 1,
        "errors": 0,
        "skipped": 0,
        "status": "fail",
    }
    data["testHealth"]["api"]["suites"] = [api_suite, *data["testHealth"]["api"]["suites"]]
    data["testHealth"]["api"]["tests"] += api_suite["tests"]
    data["testHealth"]["api"]["failures"] += api_suite["failures"]
    data["testHealth"]["api"]["status"] = "fail"

    data["testHealth"]["playwright"]["status"] = "fail"
    data["testHealth"]["playwright"]["failedTests"] = [
        "role-ui.spec.ts › viewer cannot access admin-only action",
        "feature-flags.spec.ts › downstream workspace error banner",
    ]

    data["coverage"]["endpointCoverage"] = [
        {"endpoint": "GET /xyz", "covered": True},
        {"endpoint": "POST /xyz/review", "covered": False},
    ]
    data["coverage"]["roleCoverage"] = [
        {"role": "admin", "covered": True},
        {"role": "viewer", "covered": False},
        {"role": "vip", "covered": True},
    ]
    data["coverage"]["gaps"] = [
        "Endpoint POST /xyz/review has no mapped API test case.",
        "Role viewer is not mapped to a role coverage edge for the review approval flow.",
        "Playwright spec is outside resolved active mapping: projects/ui-automation/role-aware-mockserver/playwright/tests/review-flow.spec.ts",
    ]
    data["coverage"]["orphanTestCases"] = [
        {
            "id": "synthetic-orphan-review-test",
            "label": "review flow saves draft without mapped story or endpoint",
            "layer": "ui",
            "path": "projects/ui-automation/role-aware-mockserver/playwright/tests/review-flow.spec.ts",
        }
    ]

    duplicate_risk = {
        "left": "GET /xyz returns medium risk response for review customer",
        "right": "GET /xyz should return review risk response for medium customer",
        "leftPath": "projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java",
        "rightPath": "projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiDuplicateCandidateTest.java",
        "layer": "api",
        "score": 0.92,
        "sharedTerms": ["customer", "medium", "response", "review", "risk", "xyz"],
        "signal": "near-duplicate review",
    }
    data["duplicates"]["candidates"] = [duplicate_risk, *data["duplicates"]["candidates"]]
    data["duplicates"]["nearDuplicateCount"] = 1
    data["duplicates"]["coverageSiblingCount"] = len(
        [item for item in data["duplicates"]["candidates"] if item.get("signal") == "coverage sibling"]
    )

    data["changeImpact"]["changedFiles"] = [
        "projects/microservices/xyz-service/src/main/resources/openapi/xyz-service.openapi.yml",
        "projects/ui-automation/role-aware-mockserver/playwright/tests/review-flow.spec.ts",
        *data["changeImpact"]["changedFiles"],
    ]
    data["changeImpact"]["recommendations"] = [
        {
            "area": "API",
            "priority": "high",
            "reason": "Synthetic contract change introduces POST /xyz/review without mapped API coverage.",
            "files": [
                "projects/microservices/xyz-service/src/main/resources/openapi/xyz-service.openapi.yml",
                "projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java",
            ],
            "commands": [
                "cd projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test -Dapi.port=8081",
            ],
        },
        {
            "area": "Playwright UI",
            "priority": "high",
            "reason": "Synthetic review-flow spec is outside resolved active mapping and needs UI context review.",
            "files": [
                "projects/ui-automation/role-aware-mockserver/playwright/tests/review-flow.spec.ts",
                "projects/ui-automation/role-aware-mockserver/playwright/pages/operations-console.page.ts",
            ],
            "commands": [
                "npm --prefix projects/ui-automation/role-aware-mockserver run test:e2e",
            ],
        },
        *data["changeImpact"]["recommendations"],
    ]

    covered = len([item for item in data["coverage"]["endpointCoverage"] if item["covered"]]) + len(
        [item for item in data["coverage"]["roleCoverage"] if item["covered"]]
    )
    total = len(data["coverage"]["endpointCoverage"]) + len(data["coverage"]["roleCoverage"])
    data["visuals"]["coverage"] = {
        "covered": covered,
        "total": total,
        "percent": round((covered / total) * 100) if total else 0,
    }
    data["visuals"]["duplicateSignal"] = {"clearPercent": 75}

    data["confidence"] = {
        "score": 36,
        "status": "risk",
        "reasons": [
            "API health is not passing.",
            "Playwright health is not passing.",
            "Graphify graph is stale against the current commit.",
            "3 coverage gap signal(s) found.",
            "1 high-similarity duplicate candidate needs review.",
        ],
    }
    return data


def write_outputs(root: Path, output_dir: Path) -> None:
    data = inject_negative_signals(build_dashboard(root))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "dashboard.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (output_dir / "index.html").write_text(render_dashboard(data), encoding="utf-8")
    print(f"Wrote {output_dir / 'dashboard.json'}")
    print(f"Wrote {output_dir / 'index.html'}")
    print("Negative scenario: synthetic failures=api+playwright, gaps=3, nearDuplicate=1, graphStale=true")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=str(WORKSPACE))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    root = Path(args.workspace).expanduser().resolve()
    output_dir = (root / args.output_dir).resolve()
    write_outputs(root, output_dir)


if __name__ == "__main__":
    main()
