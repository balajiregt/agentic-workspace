#!/usr/bin/env python3
"""Report approximate context-token efficiency for the agentic workspace.

The goal is not to match a provider tokenizer exactly. It gives a stable local
yardstick for comparing "central context + referenced files" against dumping an
entire microservice workspace into the prompt.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


DEFAULT_INCLUDE_SUFFIXES = {
    ".java",
    ".md",
    ".xml",
    ".yml",
    ".yaml",
    ".json",
    ".properties",
}

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".idea",
    "target",
    "build",
    "node_modules",
    "__pycache__",
}

TASK_PROFILES = {
    "api-test-change": {
        "description": "Focused context for adding or modifying RestAssured tests for GET /xyz.",
        "files": [
            "contexts/current/service-context.yml",
            "skills/microservice-change/SKILL.md",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/api/CustomerRiskController.java",
            "projects/microservices/xyz-service/src/main/resources/openapi/xyz-service.openapi.yml",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/client/RestClientFactory.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/config/ApiTestConfig.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/assertions/JsonFieldAssertions.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/fixtures/CustomerFixtures.java",
            "projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java",
        ],
    },
    "new-endpoint-change": {
        "description": "Focused context for adding a new endpoint with service behavior, OpenAPI, tests, and deployment impact check.",
        "files": [
            "contexts/current/service-context.yml",
            "skills/microservice-change/SKILL.md",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/api/CustomerRiskController.java",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/service/CustomerRiskService.java",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/dto/CustomerRiskResponse.java",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/domain/RiskCategory.java",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/exception/ApiExceptionHandler.java",
            "projects/microservices/xyz-service/src/main/resources/openapi/xyz-service.openapi.yml",
            "projects/microservices/xyz-service/src/test/java/com/agentic/workspace/xyz/service/CustomerRiskServiceTest.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/client/RestClientFactory.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/config/ApiTestConfig.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/assertions/JsonFieldAssertions.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/fixtures/CustomerFixtures.java",
            "projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java",
            "projects/microservices/xyz-deployments/k8s/xyz-service.yaml",
        ],
    },
    "shared-qa-utility-change": {
        "description": "Focused context for deciding whether reusable RestAssured helpers belong in qa-steps or only in a service API test.",
        "files": [
            "contexts/current/service-context.yml",
            "skills/microservice-change/SKILL.md",
            "projects/microservices/qa-steps/pom.xml",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/client/RestClientFactory.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/config/ApiTestConfig.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/assertions/JsonFieldAssertions.java",
            "projects/microservices/qa-steps/src/main/java/com/agentic/workspace/qa/fixtures/CustomerFixtures.java",
            "projects/microservices/qa-projects/xyz-service-api-tests/pom.xml",
            "projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java",
        ],
    },
    "business-flow-walkthrough": {
        "description": "Read-only context for explaining endpoint behavior and business flow without editing files.",
        "files": [
            "AGENTS.md",
            "contexts/current/service-context.yml",
            "skills/microservice-change/SKILL.md",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/api/CustomerRiskController.java",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/service/CustomerRiskService.java",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/dto/CustomerRiskResponse.java",
            "projects/microservices/xyz-service/src/main/java/com/agentic/workspace/xyz/domain/RiskCategory.java",
            "projects/microservices/xyz-service/src/main/resources/openapi/xyz-service.openapi.yml",
            "projects/microservices/xyz-service/src/test/java/com/agentic/workspace/xyz/service/CustomerRiskServiceTest.java",
            "projects/microservices/qa-projects/xyz-service-api-tests/src/test/java/com/agentic/workspace/qa/xyz/tests/CustomerRiskApiTest.java",
        ],
    },
}


def estimate_tokens(text: str) -> int:
    """Conservative approximation for mixed prose, YAML, and Java code."""
    if not text:
        return 0

    char_estimate = len(text) / 4
    word_estimate = len(text.split()) * 1.3
    return int(max(char_estimate, word_estimate))


def iter_files(root: Path, suffixes: set[str]) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in DEFAULT_EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in suffixes:
            yield path


def file_stats(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "path": str(path),
        "bytes": len(text.encode("utf-8")),
        "estimated_tokens": estimate_tokens(text),
        "lines": text.count("\n") + (1 if text else 0),
    }


def totals(files: list[dict[str, object]]) -> dict[str, int]:
    return {
        "files": len(files),
        "bytes": sum(int(item["bytes"]) for item in files),
        "estimated_tokens": sum(int(item["estimated_tokens"]) for item in files),
        "lines": sum(int(item["lines"]) for item in files),
    }


def task_profile_stats(workspace: Path, profile_name: str | None) -> dict[str, object] | None:
    if not profile_name:
        return None
    if profile_name not in TASK_PROFILES:
        available = ", ".join(sorted(TASK_PROFILES))
        raise SystemExit(f"Unknown task profile '{profile_name}'. Available profiles: {available}")

    profile = TASK_PROFILES[profile_name]
    files = []
    missing = []
    for relative_path in profile["files"]:
        path = workspace / relative_path
        if path.exists():
            files.append(file_stats(path))
        else:
            missing.append(str(path))

    return {
        "name": profile_name,
        "description": profile["description"],
        "totals": totals(files),
        "files": files,
        "missing_files": missing,
    }


def pct(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, 2)


def build_report(
    workspace: Path,
    context_file: Path,
    microservices_root: Path,
    skills_root: Path,
    task_profile: str | None = None,
) -> dict[str, object]:
    context = file_stats(context_file)
    workspace_files = [file_stats(path) for path in iter_files(microservices_root, DEFAULT_INCLUDE_SUFFIXES)]
    skill_files = [file_stats(path) for path in sorted(skills_root.glob("*/SKILL.md"))]
    workspace_totals = totals(workspace_files)
    skill_totals = totals(skill_files)

    current_context_tokens = int(context["estimated_tokens"])
    all_context_tokens = int(workspace_totals["estimated_tokens"])
    instruction_tokens = current_context_tokens + int(skill_totals["estimated_tokens"])
    task = task_profile_stats(workspace, task_profile)

    report = {
        "workspace": str(workspace),
        "context_file": str(context_file),
        "microservices_root": str(microservices_root),
        "skills_root": str(skills_root),
        "metric_note": "Token counts are approximate and intended for relative comparison.",
        "central_context": context,
        "workspace_skills": {
            "totals": skill_totals,
            "files": skill_files,
        },
        "microservices_corpus": workspace_totals,
        "task_profile": task,
        "efficiency": {
            "central_context_tokens": current_context_tokens,
            "central_context_plus_skills_tokens": instruction_tokens,
            "microservices_corpus_tokens": all_context_tokens,
            "tokens_saved_vs_full_microservices_dump": max(all_context_tokens - current_context_tokens, 0),
            "tokens_saved_with_skills_vs_full_microservices_dump": max(
                all_context_tokens - instruction_tokens,
                0,
            ),
            "central_context_as_percent_of_corpus": pct(current_context_tokens, all_context_tokens),
            "central_context_plus_skills_as_percent_of_corpus": pct(
                instruction_tokens,
                all_context_tokens,
            ),
            "compression_ratio": (
                round(all_context_tokens / current_context_tokens, 2)
                if current_context_tokens
                else 0
            ),
            "compression_ratio_with_skills": (
                round(all_context_tokens / instruction_tokens, 2)
                if instruction_tokens
                else 0
            ),
        },
        "largest_files_by_estimated_tokens": sorted(
            workspace_files,
            key=lambda item: int(item["estimated_tokens"]),
            reverse=True,
        )[:10],
    }
    if task:
        task_tokens = int(task["totals"]["estimated_tokens"])
        report["efficiency"]["task_profile_tokens"] = task_tokens
        report["efficiency"]["task_profile_as_percent_of_corpus"] = pct(
            task_tokens,
            all_context_tokens,
        )
        report["efficiency"]["task_profile_compression_ratio"] = (
            round(all_context_tokens / task_tokens, 2)
            if task_tokens
            else 0
        )
    return report


def markdown(report: dict[str, object]) -> str:
    efficiency = report["efficiency"]
    corpus = report["microservices_corpus"]
    central = report["central_context"]
    skills = report["workspace_skills"]
    task = report["task_profile"]
    largest = report["largest_files_by_estimated_tokens"]

    lines = [
        "# Context Efficiency Report",
        "",
        str(report["metric_note"]),
        "",
        "## Summary",
        "",
        f"- Central context tokens: {efficiency['central_context_tokens']}",
        f"- Central context plus skills tokens: {efficiency['central_context_plus_skills_tokens']}",
        f"- Full microservices corpus tokens: {efficiency['microservices_corpus_tokens']}",
        f"- Tokens saved versus full dump: {efficiency['tokens_saved_vs_full_microservices_dump']}",
        f"- Tokens saved with skills versus full dump: {efficiency['tokens_saved_with_skills_vs_full_microservices_dump']}",
        f"- Central context as corpus percentage: {efficiency['central_context_as_percent_of_corpus']}%",
        f"- Central context plus skills as corpus percentage: {efficiency['central_context_plus_skills_as_percent_of_corpus']}%",
        f"- Compression ratio: {efficiency['compression_ratio']}x",
        f"- Compression ratio with skills: {efficiency['compression_ratio_with_skills']}x",
    ]

    if task:
        lines.extend([
            f"- Task profile tokens ({task['name']}): {efficiency['task_profile_tokens']}",
            f"- Task profile as corpus percentage: {efficiency['task_profile_as_percent_of_corpus']}%",
            f"- Task profile compression ratio: {efficiency['task_profile_compression_ratio']}x",
        ])

    lines.extend([
        "",
        "## Corpus",
        "",
        f"- Files scanned: {corpus['files']}",
        f"- Lines scanned: {corpus['lines']}",
        f"- Bytes scanned: {corpus['bytes']}",
        "",
        "## Central Context",
        "",
        f"- Path: `{central['path']}`",
        f"- Lines: {central['lines']}",
        f"- Bytes: {central['bytes']}",
        "",
        "## Workspace Skills",
        "",
        f"- Skill files: {skills['totals']['files']}",
        f"- Skill tokens: {skills['totals']['estimated_tokens']}",
        "",
    ])

    if task:
        lines.extend([
            "## Task Profile",
            "",
            f"- Name: `{task['name']}`",
            f"- Description: {task['description']}",
            f"- Files: {task['totals']['files']}",
            f"- Lines: {task['totals']['lines']}",
            f"- Bytes: {task['totals']['bytes']}",
            f"- Estimated tokens: {task['totals']['estimated_tokens']}",
            "",
            "| Estimated tokens | Lines | File |",
            "| ---: | ---: | --- |",
        ])
        for item in task["files"]:
            lines.append(f"| {item['estimated_tokens']} | {item['lines']} | `{item['path']}` |")
        if task["missing_files"]:
            lines.extend(["", "Missing task-profile files:"])
            for path in task["missing_files"]:
                lines.append(f"- `{path}`")
        lines.append("")

    lines.extend([
        "## Largest Files",
        "",
        "| Estimated tokens | Lines | File |",
        "| ---: | ---: | --- |",
    ])

    for item in largest:
        lines.append(f"| {item['estimated_tokens']} | {item['lines']} | `{item['path']}` |")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workspace",
        default="/Users/balaji/agentic-workspace",
        help="Agentic workspace root.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Report output format.",
    )
    parser.add_argument(
        "--task-profile",
        choices=sorted(TASK_PROFILES),
        default=None,
        help="Optional focused task profile to compare against the full corpus.",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    report = build_report(
        workspace=workspace,
        context_file=workspace / "contexts/current/service-context.yml",
        microservices_root=workspace / "projects/microservices",
        skills_root=workspace / "skills",
        task_profile=args.task_profile,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(markdown(report))


if __name__ == "__main__":
    main()
