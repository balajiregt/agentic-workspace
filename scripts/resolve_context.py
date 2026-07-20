#!/usr/bin/env python3
"""Generate resolved agent context from a small task YAML plus service metadata."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - local setup guard
    raise SystemExit("PyYAML is required for context resolution: python3 -m pip install pyyaml") from exc


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Expected YAML mapping in {path}")
    return data


def rel(path: Path, workspace: Path) -> str:
    return str(path.resolve().relative_to(workspace.resolve()))


def endpoint_path(endpoint: str) -> str:
    parts = endpoint.strip().split(maxsplit=1)
    return parts[1] if len(parts) == 2 else endpoint.strip()


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


def command_with_cd(command: str, cwd: Path) -> str:
    return f"cd {cwd} && {command}"


def build_resolved(workspace: Path, task: dict[str, Any], service: dict[str, Any]) -> dict[str, Any]:
    service_name = task.get("service_name")
    if service_name != service.get("service_name"):
        raise SystemExit(
            f"Task service_name {service_name!r} does not match metadata service_name {service.get('service_name')!r}"
        )

    repos = service["repositories"]
    microservices_root = workspace / repos["microservices_root"]
    service_repo = microservices_root / repos["service_repo"]
    qa_steps = microservices_root / repos["qa_steps"]
    qa_project = microservices_root / repos["qa_project"]
    deployment_repo = microservices_root / repos["deployment_repo"]
    endpoint = service["api"]["endpoint"]
    path = endpoint_path(endpoint)

    controller = find_one(service_repo / "src/main/java", "*Controller.java", f'"{path}"')
    service_file = find_one(service_repo / "src/main/java", "*Service.java")
    openapi = find_one(service_repo / "src/main/resources", "*.yml", path)
    api_test = find_one(qa_project / "src/test/java", "*Test.java", f'get("{path}")')
    fixtures = find_one(qa_steps / "src/main/java", "*Fixtures.java")
    assertions = find_one(qa_steps / "src/main/java", "*Assertions.java")

    validation = service["validation"]
    service_command = command_with_cd(validation["service_start_command"], service_repo)
    test_command = command_with_cd(validation["api_test_command"], microservices_root)

    return {
        "generated": {
            "at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "by": "scripts/resolve_context.py",
            "note": "Generated file. Do not hand-maintain; update current task context or service metadata instead.",
        },
        "task_context": {
            "path": rel(workspace / "contexts/current/service-context.yml", workspace),
            "service_name": service_name,
            "work_item": task.get("work_item", {}),
            "quality_gates": task.get("quality_gates", {}),
        },
        "service_context": {
            "path": rel(workspace / f"contexts/services/{service_name}.yml", workspace),
            "architecture": service.get("architecture"),
            "repository_topology": task.get("repository_topology") or service.get("repository_topology"),
            "api": service.get("api", {}),
            "behavior_contract": service.get("behavior_contract", {}),
        },
        "resolved_repositories": {
            "microservices_root": str(microservices_root),
            "service_repo": str(service_repo),
            "deployment_repo": str(deployment_repo),
            "qa_steps": str(qa_steps),
            "qa_project": str(qa_project),
        },
        "resolved_files": {
            "controller": str(controller),
            "service": str(service_file),
            "openapi": str(openapi),
            "api_test": str(api_test),
            "shared_fixtures": str(fixtures),
            "shared_assertions": str(assertions),
        },
        "verification": {
            "commands": [service_command, test_command],
            "notes": validation.get("notes", []),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="/Users/balaji/agentic-workspace")
    parser.add_argument("--context", default="contexts/current/service-context.yml")
    parser.add_argument("--output", default="contexts/current/resolved-context.yml")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    context_path = workspace / args.context
    task = read_yaml(context_path)
    service_name = task.get("service_name")
    if not service_name:
        raise SystemExit(f"Missing service_name in {context_path}")

    service_path = workspace / "contexts/services" / f"{service_name}.yml"
    service = read_yaml(service_path)
    resolved = build_resolved(workspace, task, service)

    output = workspace / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(resolved, handle, sort_keys=False, width=1000)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
