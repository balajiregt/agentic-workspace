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

    ui_health = data["testHealth"].setdefault("ui", data["testHealth"].get("playwright", {}))
    data["testHealth"].pop("playwright", None)
    ui_health["status"] = "fail"
    ui_health["failedTests"] = [
        "role-ui.spec.ts › viewer cannot access admin-only action",
        "feature-flags.spec.ts › downstream workspace error banner",
    ]

    data["coverage"]["endpointCoverage"] = [
        {"endpoint": "GET /xyz", "covered": True},
        {"endpoint": "POST /xyz/review", "covered": False},
        {"endpoint": "PATCH /xyz/{customerId}/decision", "covered": False},
    ]
    data["coverage"]["roleCoverage"] = [
        {"role": "admin", "covered": True},
        {"role": "viewer", "covered": False},
        {"role": "vip", "covered": True},
        {"role": "reviewer", "covered": False},
    ]
    data["coverage"]["gaps"] = [
        "Endpoint POST /xyz/review has no mapped API test case.",
        "Endpoint PATCH /xyz/{customerId}/decision is present in synthetic intent but has no mapped test-case verification edge.",
        "Field reviewDecision is in synthetic ticket intent but has no assertion evidence.",
        "Role viewer is not mapped to a role coverage edge for the review approval flow.",
        "Role reviewer is in synthetic ticket intent but is missing from the resolved UI role matrix.",
        "Flow review approval is not present in the resolved active UI mapping.",
        "UI test spec is outside resolved active mapping: projects/ui-automation/role-aware-mockserver/playwright/tests/review-flow.spec.ts",
        "API test class is outside resolved active mapping: projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiDuplicateCandidateTest.java",
    ]
    data["coverage"]["orphanTestCases"] = [
        {
            "id": "synthetic-orphan-review-test",
            "label": "review flow saves draft without mapped story or endpoint",
            "layer": "ui",
            "path": "projects/ui-automation/role-aware-mockserver/playwright/tests/review-flow.spec.ts",
        },
        {
            "id": "synthetic-orphan-api-decision-test",
            "label": "PATCH /xyz decision accepts review approval without mapped endpoint",
            "layer": "api",
            "path": "projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiDuplicateCandidateTest.java",
        }
    ]
    data["negativeEvidence"] = {
        "mappingAudit": [
            {
                "area": "API endpoint",
                "intent": "POST /xyz/review",
                "source": "synthetic work item affected_endpoints",
                "status": "gap",
                "evidence": "No test-case verification edge exists in the test graph.",
                "nextAction": "Add or map an API test, then rebuild context and graph.",
            },
            {
                "area": "API endpoint",
                "intent": "PATCH /xyz/{customerId}/decision",
                "source": "synthetic work item affected_endpoints",
                "status": "gap",
                "evidence": "Endpoint appears in intent but not in mapped dashboard coverage.",
                "nextAction": "Confirm contract scope; add RestAssured coverage if in scope.",
            },
            {
                "area": "API field",
                "intent": "reviewDecision",
                "source": "synthetic work item affected_fields",
                "status": "gap",
                "evidence": "No assertion evidence is linked to this field.",
                "nextAction": "Add assertion mapping or document product/contract gap.",
            },
            {
                "area": "UI flow",
                "intent": "review approval",
                "source": "synthetic ui-context affected_flows",
                "status": "gap",
                "evidence": "Flow is missing from resolved active UI mapping.",
                "nextAction": "Update ui-context.yml and regenerate resolved UI context.",
            },
            {
                "area": "UI role",
                "intent": "viewer",
                "source": "synthetic ui-context affected_roles",
                "status": "gap",
                "evidence": "Role has no coverage edge for the review approval flow.",
                "nextAction": "Add role-aware UI automation coverage or mark out of scope.",
            },
            {
                "area": "UI role",
                "intent": "reviewer",
                "source": "synthetic ui-context affected_roles",
                "status": "gap",
                "evidence": "Role is missing from the resolved role matrix.",
                "nextAction": "Add role fixture/session-storage coverage if this role is real.",
            },
            {
                "area": "UI spec",
                "intent": "review-flow.spec.ts",
                "source": "test inventory",
                "status": "gap",
                "evidence": "Spec exists outside resolved active mapping.",
                "nextAction": "Map it to the work item or remove stale/unowned test.",
            },
            {
                "area": "API duplicate",
                "intent": "medium risk review customer",
                "source": "duplicate candidate scan",
                "status": "review",
                "evidence": "Two API tests share high semantic overlap with score 0.92.",
                "nextAction": "Decide whether this is a duplicate or a deliberate coverage variant.",
            },
        ],
        "scenarios": [
            {
                "scenario": "Missing endpoint mapping",
                "injectedCondition": "Ticket intent contains POST /xyz/review but graph has no verifying test edge.",
                "dashboardSignal": "Coverage table marks endpoint as gap; confidence reason mentions coverage gaps.",
                "debugQuestion": "Do we need a new API test, or is the endpoint out of scope?",
            },
            {
                "scenario": "Missing field assertion",
                "injectedCondition": "Ticket intent contains reviewDecision but no assertion evidence is linked.",
                "dashboardSignal": "Negative evidence table marks API field as gap.",
                "debugQuestion": "Are we validating the exact changed field or only the HTTP status?",
            },
            {
                "scenario": "Missing role mapping",
                "injectedCondition": "viewer/reviewer roles are in intent but missing coverage edges or resolved role matrix.",
                "dashboardSignal": "Coverage table marks roles as gap; mapping audit shows next action.",
                "debugQuestion": "Does the role matrix match the business access rule?",
            },
            {
                "scenario": "Unmapped UI flow",
                "injectedCondition": "review approval flow exists in test intent but is absent from resolved active UI mapping.",
                "dashboardSignal": "Gap signals list the missing flow and orphan spec.",
                "debugQuestion": "Should ui-context.yml be updated before the agent writes tests?",
            },
            {
                "scenario": "Orphan test file",
                "injectedCondition": "review-flow.spec.ts and duplicate API candidate are outside resolved active mapping.",
                "dashboardSignal": "Gap signals identify the exact file paths.",
                "debugQuestion": "Is this useful automation, stale code, or a test in the wrong slice?",
            },
            {
                "scenario": "Duplicate-risk candidate",
                "injectedCondition": "Two API test names overlap strongly without clear contrast intent.",
                "dashboardSignal": "Duplicate table shows near-duplicate review with score 0.92.",
                "debugQuestion": "Can we reuse/extend an existing test instead of adding another one?",
            },
            {
                "scenario": "Coverage sibling guard",
                "injectedCondition": "Positive/negative role and validation tests are similar but intentionally contrast behavior.",
                "dashboardSignal": "Duplicate table labels them coverage sibling, not near duplicate.",
                "debugQuestion": "Is the similarity expected because the tests cover opposite outcomes?",
            },
            {
                "scenario": "Stale graph evidence",
                "injectedCondition": "Graphify commit is set to synthetic-old-commit.",
                "dashboardSignal": "Graph freshness is stale and release confidence drops.",
                "debugQuestion": "Should graph/context be rebuilt before trusting impact and duplicate signals?",
            },
        ],
    }

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
            "reason": "Synthetic contract change introduces review endpoints and fields without mapped API coverage.",
            "files": [
                "projects/microservices/xyz-service/src/main/resources/openapi/xyz-service.openapi.yml",
                "projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java",
            ],
            "commands": [
                "cd projects/microservices && mvn -pl qa-projects/xyz-service-api-tests -am test -Dapi.port=8081",
            ],
        },
        {
            "area": "UI automation",
            "priority": "high",
            "reason": "Synthetic review-flow and reviewer role are outside resolved active UI mapping.",
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
        "score": 28,
        "status": "risk",
        "reasons": [
            "API health is not passing.",
            "UI automation health is not passing.",
            "Graphify graph is stale against the current commit.",
            "8 coverage and mapping gap signal(s) found.",
            "1 high-similarity duplicate candidate needs review.",
            "2 orphan test case(s) are outside active mapping.",
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
    print("Negative scenario: synthetic failures=api+ui, gaps=8, orphanTests=2, nearDuplicate=1, graphStale=true")


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
