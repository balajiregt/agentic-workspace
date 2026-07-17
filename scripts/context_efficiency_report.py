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


def pct(part: int, whole: int) -> float:
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, 2)


def build_report(
    workspace: Path,
    context_file: Path,
    microservices_root: Path,
    skills_root: Path,
) -> dict[str, object]:
    context = file_stats(context_file)
    workspace_files = [file_stats(path) for path in iter_files(microservices_root, DEFAULT_INCLUDE_SUFFIXES)]
    skill_files = [file_stats(path) for path in sorted(skills_root.glob("*/SKILL.md"))]
    workspace_totals = totals(workspace_files)
    skill_totals = totals(skill_files)

    current_context_tokens = int(context["estimated_tokens"])
    all_context_tokens = int(workspace_totals["estimated_tokens"])
    instruction_tokens = current_context_tokens + int(skill_totals["estimated_tokens"])

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
    return report


def markdown(report: dict[str, object]) -> str:
    efficiency = report["efficiency"]
    corpus = report["microservices_corpus"]
    central = report["central_context"]
    skills = report["workspace_skills"]
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
        "## Largest Files",
        "",
        "| Estimated tokens | Lines | File |",
        "| ---: | ---: | --- |",
    ]

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
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    report = build_report(
        workspace=workspace,
        context_file=workspace / "contexts/current/service-context.yml",
        microservices_root=workspace / "projects/microservices",
        skills_root=workspace / "skills",
    )

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(markdown(report))


if __name__ == "__main__":
    main()
