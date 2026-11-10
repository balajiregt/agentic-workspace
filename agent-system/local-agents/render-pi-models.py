#!/usr/bin/env python3
"""Render Pi models.json from a local RAM/model profile."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default=os.environ.get("AGENTIC_PROFILE", "8gb"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--model-ref", default=os.environ.get("AGENTIC_MODEL_REF"))
    parser.add_argument("--context-window", type=int, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    profiles = json.loads((root / "config/model-profiles.json").read_text())["profiles"]

    if args.profile not in profiles:
        available = ", ".join(sorted(profiles))
        raise SystemExit(f"Unknown profile '{args.profile}'. Available profiles: {available}")

    profile = dict(profiles[args.profile])
    port = args.port or int(os.environ.get("AGENTIC_LLAMA_PORT", profile["port"]))
    context_window = args.context_window or int(
        os.environ.get("AGENTIC_CONTEXT_WINDOW", profile["contextWindow"])
    )
    max_tokens = args.max_tokens or int(os.environ.get("AGENTIC_MAX_TOKENS", profile["maxTokens"]))
    model_ref = args.model_ref or profile["modelRef"]
    base_url = args.base_url or f"http://localhost:{port}/v1"

    rendered = {
        "providers": {
            profile["providerName"]: {
                "baseUrl": base_url,
                "api": "openai-completions",
                "apiKey": "local",
                "compat": {
                    "supportsDeveloperRole": False,
                    "supportsReasoningEffort": False,
                    "supportsUsageInStreaming": False,
                    "maxTokensField": "max_tokens",
                },
                "models": [
                    {
                        "id": "local-model",
                        "name": profile["displayName"],
                        "reasoning": False,
                        "input": ["text"],
                        "contextWindow": context_window,
                        "maxTokens": max_tokens,
                        "cost": {
                            "input": 0,
                            "output": 0,
                            "cacheRead": 0,
                            "cacheWrite": 0,
                        },
                    }
                ],
            }
        }
    }

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rendered, indent=2) + "\n")

    print(f"Wrote {output}")
    print(f"Profile: {args.profile}")
    print(f"Model ref: {model_ref}")
    print(f"Context window: {context_window}")
    print(f"Max output tokens: {max_tokens}")
    print(f"Base URL: {base_url}")


if __name__ == "__main__":
    main()
