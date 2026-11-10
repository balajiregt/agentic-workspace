#!/usr/bin/env python3
"""Check whether the local OpenAI-compatible server returns structured tool calls."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8080/v1")
    parser.add_argument("--model", default="local-model")
    parser.add_argument("--max-preview-chars", type=int, default=400)
    args = parser.parse_args()

    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": "Read AGENTS.md"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "read",
                    "description": "Read a file from disk",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            }
        ],
        "tool_choice": "required",
        "temperature": 0,
        "max_tokens": 200,
    }

    try:
        result = post_json(f"{args.base_url.rstrip('/')}/chat/completions", payload)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"TOOL_CALL_CHECK=ERROR server request failed: {exc}", file=sys.stderr)
        return 2

    message = result.get("choices", [{}])[0].get("message", {})
    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        names = ", ".join(call.get("function", {}).get("name", "unknown") for call in tool_calls)
        print(f"TOOL_CALL_CHECK=PASS structured tool_calls returned: {names}")
        return 0

    content = (message.get("content") or "").strip().replace("\n", "\\n")
    if len(content) > args.max_preview_chars:
        content = content[: args.max_preview_chars] + "..."
    print("TOOL_CALL_CHECK=FAIL no structured tool_calls returned")
    print(f"message.content preview: {content}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
