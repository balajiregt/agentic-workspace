#!/usr/bin/env python3
"""Run one task-profile prompt against a local OpenAI-compatible model server."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib import request

from context_efficiency_report import TASK_PROFILES

DEFAULT_WORKSPACE = Path(__file__).resolve().parents[1]


PROMPTS = {
    "new-endpoint-change": "docs/prompts/new-endpoint-change-prompt.md",
    "shared-qa-utility-change": "docs/prompts/shared-qa-utility-change-prompt.md",
    "business-flow-walkthrough": "docs/prompts/business-flow-walkthrough-prompt.md",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def build_prompt(workspace: Path, task_profile: str) -> str:
    profile = TASK_PROFILES[task_profile]
    sections = [
        "You are evaluating an agentic workspace task.",
        "Follow AGENTS.md, service-context.yml, and SKILL.md if present.",
        "Answer concisely with: context used, files to inspect, files to change, verification, and any risk.",
        "",
        "## Task Prompt",
        read(workspace / PROMPTS[task_profile]),
        "",
        "## Task Profile Files",
    ]

    for relative_path in profile["files"]:
        path = workspace / relative_path
        if not path.exists():
            continue
        sections.extend([
            "",
            f"### {relative_path}",
            "```",
            read(path),
            "```",
        ])

    return "\n".join(sections)


def call_model(base_url: str, prompt: str, max_tokens: int) -> dict[str, object]:
    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()
    with request.urlopen(req, timeout=240) as response:
        body = json.loads(response.read().decode("utf-8"))
    elapsed = round(time.perf_counter() - started, 2)
    body["_elapsed_seconds"] = elapsed
    return body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE))
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--task-profile", choices=sorted(PROMPTS), required=True)
    parser.add_argument("--max-tokens", type=int, default=384)
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    prompt = build_prompt(workspace, args.task_profile)
    result = call_model(args.base_url, prompt, args.max_tokens)
    content = result["choices"][0]["message"]["content"]

    print(f"# Benchmark Result: {args.task_profile}")
    print()
    print(f"- Base URL: `{args.base_url}`")
    print(f"- Elapsed seconds: {result['_elapsed_seconds']}")
    usage = result.get("usage", {})
    if usage:
        print(f"- Usage: `{json.dumps(usage, sort_keys=True)}`")
    print()
    print(content.strip())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        raise
