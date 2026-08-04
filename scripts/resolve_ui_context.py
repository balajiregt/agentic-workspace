#!/usr/bin/env python3
"""Generate resolved agent context for the isolated Playwright UI slice."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - local setup guard
    raise SystemExit("PyYAML is required for UI context resolution: python3 -m pip install pyyaml") from exc


DEFAULT_WORKSPACE = Path(__file__).resolve().parents[1]


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Expected YAML mapping in {path}")
    return data


def rel(path: Path, workspace: Path) -> str:
    return str(path.resolve().relative_to(workspace.resolve()))


def find_one(root: Path, pattern: str, contains: str | None = None) -> Path:
    matches = []
    if root.exists():
        for path in sorted(root.rglob(pattern)):
            if not path.is_file():
                continue
            if contains is None:
                matches.append(path)
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if contains in text:
                matches.append(path)
    if not matches:
        detail = f" containing {contains!r}" if contains else ""
        raise SystemExit(f"No file found under {root} matching {pattern}{detail}")
    return matches[0]


def build_resolved(workspace: Path, task: dict[str, Any]) -> dict[str, Any]:
    ui_project_name = task.get("ui_project_name")
    if not ui_project_name:
        raise SystemExit("Missing ui_project_name in current UI context")

    ui_root = workspace / "projects/ui-automation"
    ui_project = ui_root / ui_project_name
    app_dir = ui_project / "app"
    mockserver_dir = ui_project / "mockserver"
    playwright_dir = ui_project / "playwright"

    if not ui_project.exists():
        raise SystemExit(f"UI project not found: {ui_project}")

    runtime = task.get("runtime", {}) or {}
    app_url = str(runtime.get("app_url", "http://127.0.0.1:5173"))
    mockserver_url = str(runtime.get("mockserver_url", "http://127.0.0.1:3333"))
    affected_roles = list(task.get("work_item", {}).get("affected_roles", []))

    package_json = ui_project / "package.json"
    if not package_json.is_file():
        raise SystemExit(f"UI project package.json not found: {package_json}")
    playwright_config = find_one(playwright_dir, "playwright.config.ts")
    role_test = find_one(playwright_dir / "tests", "*role*.spec.ts")
    feature_flag_test = find_one(playwright_dir / "tests", "*feature*.spec.ts")
    legacy_test = find_one(playwright_dir / "tests", "*legacy*.spec.ts")
    helper = find_one(playwright_dir / "helpers", "*.ts", "mockAgentRoles")
    page_object = find_one(playwright_dir / "pages", "*.page.ts")
    assertions = find_one(playwright_dir / "pages", "*.assertions.ts")
    mockserver_entrypoint = find_one(mockserver_dir / "src", "mock-server.js")
    mockserver_routes = find_one(mockserver_dir / "src/backend", "index.js")
    token_route = find_one(mockserver_dir / "src/backend/endpoints", "token.js")
    workspace_route = find_one(mockserver_dir / "src/backend/endpoints", "workspace.js")
    app_entrypoint = find_one(app_dir, "server.mjs")
    app_script = find_one(app_dir / "public", "app.js")
    app_markup = find_one(app_dir / "public", "index.html")

    prefix = f"npm --prefix {rel(ui_project, workspace)} run"

    return {
        "generated": {
            "at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "by": "scripts/resolve_ui_context.py",
            "note": "Generated file. Do not hand-maintain; update current UI task context or repo conventions instead.",
        },
        "task_context": {
            "path": rel(workspace / "contexts/current/ui-context.yml", workspace),
            "ui_project_name": ui_project_name,
            "work_item": task.get("work_item", {}),
            "quality_gates": task.get("quality_gates", {}),
        },
        "ui_context": {
            "source": "derived from current UI task context and repo layout",
            "architecture": "playwright-ui-with-role-aware-mockserver",
            "repository_topology": task.get("repository_topology", {}),
            "runtime": {
                "app_url": app_url,
                "mockserver_url": mockserver_url,
            },
        },
        "resolved_repositories": {
            "ui_automation_root": rel(ui_root, workspace),
            "ui_project": rel(ui_project, workspace),
            "app": rel(app_dir, workspace),
            "mockserver": rel(mockserver_dir, workspace),
            "playwright": rel(playwright_dir, workspace),
        },
        "resolved_files": {
            "package_json": rel(package_json, workspace),
            "playwright_config": rel(playwright_config, workspace),
            "role_test": rel(role_test, workspace),
            "feature_flag_test": rel(feature_flag_test, workspace),
            "legacy_interception_test": rel(legacy_test, workspace),
            "helper": rel(helper, workspace),
            "page_object": rel(page_object, workspace),
            "assertions": rel(assertions, workspace),
            "mockserver_entrypoint": rel(mockserver_entrypoint, workspace),
            "mockserver_routes": rel(mockserver_routes, workspace),
            "token_route": rel(token_route, workspace),
            "workspace_route": rel(workspace_route, workspace),
            "app_entrypoint": rel(app_entrypoint, workspace),
            "app_script": rel(app_script, workspace),
            "app_markup": rel(app_markup, workspace),
        },
        "derived_validation": {
            "roles": affected_roles,
            "mockserver_owned_behavior": [
                "Token roles are injected by Playwright through the agent-roles request header.",
                "Role-specific workspace responses are owned by the mockserver workspace endpoint.",
                "Legacy direct response fulfillment remains isolated to the legacy interception comparison test.",
            ],
            "isolation_guardrails": [
                "Do not edit Maven parent modules for UI test changes.",
                "Do not add Playwright dependencies to RestAssured API projects.",
                "Do not add API/OpenAPI behavior expectations to UI context.",
            ],
        },
        "verification": {
            "commands": [
                f"{prefix} test:e2e",
                f"{prefix} test:roles",
                f"{prefix} test:legacy-interception",
            ],
            "notes": [
                "The Playwright config starts the mockserver and demo app through webServer entries.",
                "Use APP_URL and MOCKSERVER_URL environment variables to target non-default local ports.",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--workspace",
        default=str(DEFAULT_WORKSPACE),
        help="Agentic workspace root. Defaults to this script's parent repo.",
    )
    parser.add_argument("--context", default="contexts/current/ui-context.yml")
    parser.add_argument("--output", default="contexts/current/resolved-ui-context.yml")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    context_path = workspace / args.context
    task = read_yaml(context_path)
    resolved = build_resolved(workspace, task)

    output = workspace / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(resolved, handle, sort_keys=False, width=1000)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
