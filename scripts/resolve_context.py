#!/usr/bin/env python3
"""Generate resolved agent context from a small task YAML plus repo conventions."""

from __future__ import annotations

import argparse
import datetime as dt
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


def openapi_query_parameter(openapi: Path, path: str) -> dict[str, Any]:
    data = read_yaml(openapi)
    operation = data.get("paths", {}).get(path, {}).get("get", {})
    for parameter in operation.get("parameters", []):
        if parameter.get("in") != "query":
            continue
        schema = parameter.get("schema", {}) or {}
        return {
            "name": parameter.get("name"),
            "required": bool(parameter.get("required", False)),
            "schema": schema,
            "has_pattern": "pattern" in schema,
            "pattern": schema.get("pattern"),
            "minLength": schema.get("minLength"),
        }
    return {}


def source_validation(controller: Path, service_file: Path) -> dict[str, Any]:
    controller_text = controller.read_text(encoding="utf-8", errors="ignore")
    service_text = service_file.read_text(encoding="utf-8", errors="ignore")
    return {
        "controller_annotations": {
            "has_not_blank": "@NotBlank" in controller_text,
            "has_pattern": "@Pattern" in controller_text,
        },
        "service_behavior": {
            "trims_customer_id": ".trim()" in service_text,
            "uppercases_customer_id": ".toUpperCase()" in service_text,
            "has_invalid_format_check": "INVALID_ID_FORMAT" in service_text or "@Pattern" in service_text,
        },
    }


def first_affected_endpoint(task: dict[str, Any]) -> str:
    endpoints = task.get("work_item", {}).get("affected_endpoints", [])
    if not endpoints:
        raise SystemExit("Missing work_item.affected_endpoints in current task context")
    return str(endpoints[0])


def deployment_repo_for(microservices_root: Path, service_name: str) -> Path:
    prefix = service_name.removesuffix("-service")
    candidates = [
        microservices_root / f"{prefix}-deployments",
        microservices_root / f"{service_name}-deployments",
        microservices_root / "deployments",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def build_resolved(workspace: Path, task: dict[str, Any]) -> dict[str, Any]:
    service_name = task.get("service_name")
    if not service_name:
        raise SystemExit("Missing service_name in current task context")

    microservices_root = workspace / "projects/microservices"
    service_repo = microservices_root / service_name
    qa_steps = microservices_root / "qa-steps"
    qa_project = microservices_root / "qa-projects" / f"{service_name}-api-tests"
    deployment_repo = deployment_repo_for(microservices_root, service_name)
    endpoint = first_affected_endpoint(task)
    path = endpoint_path(endpoint)

    controller = find_one(service_repo / "src/main/java", "*Controller.java", f'"{path}"')
    service_file = find_one(service_repo / "src/main/java", "*Service.java")
    openapi = find_one(service_repo / "src/main/resources", "*.yml", path)
    api_test = find_one(qa_project / "src/test/java", "*Test.java", f'get("{path}")')
    fixtures = find_one(qa_steps / "src/main/java", "*Fixtures.java")
    assertions = find_one(qa_steps / "src/main/java", "*Assertions.java")
    openapi_query = openapi_query_parameter(openapi, path)
    source_validation_result = source_validation(controller, service_file)

    service_port = int(task.get("local_validation", {}).get("service_port", 8081))
    test_port_property = str(task.get("local_validation", {}).get("test_port_property", "api.port"))
    service_command = command_with_cd(
        f"mvn spring-boot:run -Dspring-boot.run.arguments=--server.port={service_port}",
        service_repo,
    )
    test_command = command_with_cd(
        f"mvn -pl qa-projects/{service_name}-api-tests -am test -D{test_port_property}={service_port}",
        microservices_root,
    )

    return {
        "generated": {
            "at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "by": "scripts/resolve_context.py",
            "note": "Generated file. Do not hand-maintain; update current task context or repo conventions instead.",
        },
        "task_context": {
            "path": rel(workspace / "contexts/current/service-context.yml", workspace),
            "service_name": service_name,
            "work_item": task.get("work_item", {}),
            "quality_gates": task.get("quality_gates", {}),
        },
        "service_context": {
            "source": "derived from current task context, repo layout, and OpenAPI",
            "architecture": "microservice",
            "repository_topology": task.get("repository_topology", {}),
            "api": {
                "endpoint": endpoint,
                "path": path,
                "contract_source": str(openapi),
            },
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
        "derived_validation": {
            "query_parameter": openapi_query,
            "source": source_validation_result,
            "unsupported_gap_hints": [
                "A 400 expectation for a nonblank customerId requires explicit service validation and OpenAPI documentation.",
                "If OpenAPI has minLength but no pattern, format validation is not documented.",
                "If the controller has @NotBlank but no @Pattern, missing/blank values are validated but arbitrary nonblank format is not.",
            ],
        },
        "verification": {
            "commands": [service_command, test_command],
            "notes": [
                "Start the service command first and keep it running while API tests execute.",
                f"Use port {service_port} because local llama.cpp may already use 8080.",
            ],
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

    resolved = build_resolved(workspace, task)

    output = workspace / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(resolved, handle, sort_keys=False, width=1000)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
