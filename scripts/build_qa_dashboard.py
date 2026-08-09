#!/usr/bin/env python3
"""Build a static QA intelligence dashboard from workspace graph/test artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - local setup guard
    raise SystemExit("PyYAML is required for dashboard generation: python3 -m pip install pyyaml") from exc


WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = "artifacts/qa-dashboard"
DEFAULT_TABLE_LIMIT = 10


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def parse_surefire(root: Path) -> list[dict[str, Any]]:
    results = []
    for path in sorted(root.glob("projects/**/target/surefire-reports/TEST-*.xml")):
        try:
            element = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        tests = int(float(element.attrib.get("tests", 0)))
        failures = int(float(element.attrib.get("failures", 0)))
        errors = int(float(element.attrib.get("errors", 0)))
        skipped = int(float(element.attrib.get("skipped", 0)))
        results.append(
            {
                "suite": element.attrib.get("name", path.stem),
                "path": str(path.relative_to(root)),
                "tests": tests,
                "failures": failures,
                "errors": errors,
                "skipped": skipped,
                "status": "pass" if failures == 0 and errors == 0 else "fail",
            }
        )
    return results


def summarize_ui_automation(root: Path) -> dict[str, Any]:
    report = root / "projects/ui-automation/role-aware-mockserver/playwright/playwright-report/index.html"
    last_run = root / "projects/ui-automation/role-aware-mockserver/test-results/.last-run.json"
    last = read_json(last_run)
    failed = list(last.get("failedTests", [])) if isinstance(last.get("failedTests"), list) else []
    return {
        "reportPath": str(report.relative_to(root)),
        "reportExists": report.is_file(),
        "lastRunPath": str(last_run.relative_to(root)),
        "lastRunExists": last_run.is_file(),
        "framework": "Playwright",
        "status": "fail" if failed else "pass" if last_run.is_file() else "unknown",
        "failedTests": failed,
    }


def graph_summary(path: Path) -> dict[str, Any]:
    data = read_json(path)
    return {
        "path": str(path.relative_to(WORKSPACE)),
        "exists": path.is_file(),
        "nodes": len(data.get("nodes", [])),
        "edges": len(data.get("edges", data.get("links", []))),
        "generatedAt": data.get("generatedAt"),
    }


def graph_data(path: Path) -> dict[str, Any]:
    data = read_json(path)
    nodes = data.get("nodes", [])
    edges = data.get("edges", data.get("links", []))
    return {
        "nodes": nodes if isinstance(nodes, list) else [],
        "edges": edges if isinstance(edges, list) else [],
    }


def graphify_summary(root: Path) -> dict[str, Any]:
    graph = read_json(root / "graphify-out/graph.json")
    report = read_text(root / "graphify-out/GRAPH_REPORT.md")
    summary_match = re.search(r"- (\d+) nodes · (\d+) edges · (\d+) communities", report)
    commit_match = re.search(r"Built from commit: `([^`]+)`", report)
    if summary_match:
        nodes, edges, communities = map(int, summary_match.groups())
    else:
        nodes = len(graph.get("nodes", []))
        edges = len(graph.get("links", graph.get("edges", [])))
        communities = 0
    return {
        "path": "graphify-out/graph.html",
        "reportPath": "graphify-out/GRAPH_REPORT.md",
        "exists": (root / "graphify-out/graph.html").is_file(),
        "nodes": nodes,
        "edges": edges,
        "communities": communities,
        "builtAtCommit": commit_match.group(1) if commit_match else graph.get("built_at_commit"),
    }


def duplicate_decisions(loop_log: str) -> list[dict[str, str]]:
    decisions = []
    for heading, body in re.findall(r"##\s+([^\n]+)\n(.*?)(?=\n##\s+|\Z)", loop_log, flags=re.S):
        if re.search(r"duplicate|coverage|missing assertion|gap", body, flags=re.I):
            decisions.append({"entry": heading.strip(), "signal": "documented"})
    return decisions[:8]


def git_lines(root: Path, *args: str) -> list[str]:
    try:
        output = subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def changed_files(root: Path) -> list[str]:
    tracked = git_lines(root, "diff", "--name-only", "HEAD")
    untracked = git_lines(root, "ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked + untracked))


def current_commit(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        return ""


def relative_existing(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def test_file_inventory(root: Path, api: dict[str, Any], ui: dict[str, Any]) -> dict[str, Any]:
    api_declared = {api.get("resolved_files", {}).get("api_test")}
    ui_declared = {
        ui.get("resolved_files", {}).get("role_test"),
        ui.get("resolved_files", {}).get("feature_flag_test"),
        ui.get("resolved_files", {}).get("legacy_interception_test"),
    }
    api_files = sorted(
        relative_existing(path, root)
        for path in root.glob("projects/microservices/qa-projects/**/*Test.java")
        if path.is_file()
    )
    ui_files = sorted(
        relative_existing(path, root)
        for path in root.glob("projects/ui-automation/**/playwright/tests/*.spec.ts")
        if path.is_file()
    )
    return {
        "api": {
            "totalFiles": len(api_files),
            "declaredFiles": sorted(item for item in api_declared if item),
            "unmappedFiles": [path for path in api_files if path not in api_declared],
        },
        "ui": {
            "totalFiles": len(ui_files),
            "declaredFiles": sorted(item for item in ui_declared if item),
            "unmappedFiles": [path for path in ui_files if path not in ui_declared],
        },
    }


def recommendation(area: str, priority: str, reason: str, files: list[str], commands: list[str]) -> dict[str, Any]:
    return {
        "area": area,
        "priority": priority,
        "reason": reason,
        "files": sorted(set(files)),
        "commands": commands,
    }


def impacted_recommendations(api: dict[str, Any], ui: dict[str, Any], files: list[str]) -> list[dict[str, Any]]:
    api_files = api.get("resolved_files", {})
    ui_files = ui.get("resolved_files", {})
    api_commands = api.get("verification", {}).get("commands", [])
    ui_commands = ui.get("verification", {}).get("commands", [])
    recommendations: list[dict[str, Any]] = []

    api_source_prefixes = (
        "projects/microservices/xyz-service/src/main/java/",
        "projects/microservices/xyz-service/src/main/resources/openapi/",
    )
    api_test_prefixes = (
        "projects/microservices/qa-projects/",
        "projects/microservices/qa-steps/",
    )
    ui_prefixes = (
        "projects/ui-automation/role-aware-mockserver/app/",
        "projects/ui-automation/role-aware-mockserver/mockserver/",
        "projects/ui-automation/role-aware-mockserver/playwright/",
    )
    graph_prefixes = ("scripts/", "contexts/", "skills/", "docs/", "README.md", "STATE.md")

    api_hits = [path for path in files if path.startswith(api_source_prefixes + api_test_prefixes)]
    ui_hits = [path for path in files if path.startswith(ui_prefixes)]
    graph_hits = [path for path in files if path.startswith(graph_prefixes) or path in {"package.json", "Dockerfile.graphs", "docker-compose.graphs.yml"}]

    if api_hits:
        recommendations.append(
            recommendation(
                "API",
                "high" if any(path.startswith(api_source_prefixes) for path in api_hits) else "medium",
                "API source, contract, shared QA utilities, or RestAssured tests changed.",
                [api_files.get("api_test", ""), *api_hits],
                api_commands,
            )
        )
    if ui_hits:
        recommendations.append(
            recommendation(
                "UI automation",
                "high",
                "UI app, mock services, automation config, helpers, page objects, or specs changed.",
                [
                    ui_files.get("role_test", ""),
                    ui_files.get("feature_flag_test", ""),
                    ui_files.get("legacy_interception_test", ""),
                    *ui_hits,
                ],
                ui_commands,
            )
        )
    if graph_hits:
        recommendations.append(
            recommendation(
                "Graph intelligence",
                "medium",
                "Context, skill, dashboard, graph, or documentation files changed.",
                graph_hits,
                ["npm run context:resolve", "npm run context:ui:resolve", "npm run graph:test", "npm run dashboard:build"],
            )
        )
    if not recommendations:
        recommendations.append(
            recommendation(
                "Current mapped slice",
                "medium",
                "No changed source files were detected; use the active API/UI context mappings.",
                [
                    api_files.get("api_test", ""),
                    ui_files.get("role_test", ""),
                    ui_files.get("feature_flag_test", ""),
                    ui_files.get("legacy_interception_test", ""),
                ],
                [*api_commands[-1:], *ui_commands],
            )
        )
    for item in recommendations:
        item["files"] = [path for path in item["files"] if path]
    return recommendations


def coverage_insights(api: dict[str, Any], ui: dict[str, Any], graph: dict[str, Any], inventory: dict[str, Any]) -> dict[str, Any]:
    nodes = {item.get("id"): item for item in graph["nodes"]}
    edges = graph["edges"]
    api_endpoint = api.get("service_context", {}).get("api", {}).get("endpoint")
    roles = ui.get("derived_validation", {}).get("roles", [])
    endpoint_covered = any(
        edge.get("target") == "api-endpoint"
        and edge.get("label") == "verifies"
        and nodes.get(edge.get("source"), {}).get("kind") == "test_case"
        for edge in edges
    )
    role_coverage = []
    for role in roles:
        role_id = f"role-{role}"
        covered = any(edge.get("target") == role_id and edge.get("label") == "covers" for edge in edges)
        role_coverage.append({"role": role, "covered": covered})
    orphan_cases = []
    for node in graph["nodes"]:
        if node.get("kind") != "test_case":
            continue
        has_verifies_edge = any(edge.get("source") == node.get("id") and edge.get("label") == "verifies" for edge in edges)
        if not has_verifies_edge:
            orphan_cases.append({"id": node.get("id"), "label": node.get("label"), "layer": node.get("layer"), "path": node.get("path")})
    gaps = []
    if api_endpoint and not endpoint_covered:
        gaps.append(f"Endpoint {api_endpoint} has no test-case verification edge.")
    for item in role_coverage:
        if not item["covered"]:
            gaps.append(f"Role {item['role']} is not mapped to a role coverage edge.")
    for path in inventory["api"]["unmappedFiles"]:
        gaps.append(f"API test file is outside resolved active mapping: {path}")
    for path in inventory["ui"]["unmappedFiles"]:
        gaps.append(f"UI test spec is outside resolved active mapping: {path}")
    return {
        "endpointCoverage": [{"endpoint": api_endpoint, "covered": endpoint_covered}],
        "roleCoverage": role_coverage,
        "orphanTestCases": orphan_cases,
        "unmappedTestFiles": inventory,
        "gaps": gaps,
    }


STOPWORDS = {
    "a",
    "an",
    "and",
    "can",
    "for",
    "get",
    "only",
    "the",
    "to",
    "with",
    "without",
}


def title_tokens(label: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", label.lower()) if token not in STOPWORDS and len(token) > 1}


def is_contrast_pair(left: str, right: str) -> bool:
    left_terms = set(re.findall(r"[a-z0-9]+", left.lower()))
    right_terms = set(re.findall(r"[a-z0-9]+", right.lower()))
    polarity_terms = {"cannot", "without", "missing", "blank", "rejects", "force", "error"}
    positive_terms = {"can", "with", "returns", "access", "passes", "supports"}
    return bool((left_terms & polarity_terms and right_terms & positive_terms) or (right_terms & polarity_terms and left_terms & positive_terms))


def duplicate_candidates(graph: dict[str, Any]) -> list[dict[str, Any]]:
    tests = [node for node in graph["nodes"] if node.get("kind") == "test_case"]
    candidates = []
    for index, left in enumerate(tests):
        left_tokens = title_tokens(str(left.get("label", "")))
        if not left_tokens:
            continue
        for right in tests[index + 1 :]:
            right_tokens = title_tokens(str(right.get("label", "")))
            if not right_tokens:
                continue
            union = left_tokens | right_tokens
            overlap = left_tokens & right_tokens
            score = len(overlap) / len(union) if union else 0
            if score < 0.42 or len(overlap) < 3:
                continue
            signal = "near-duplicate review" if score >= 0.72 and not is_contrast_pair(str(left.get("label", "")), str(right.get("label", ""))) else "coverage sibling"
            candidates.append(
                {
                    "left": left.get("label"),
                    "right": right.get("label"),
                    "leftPath": left.get("path"),
                    "rightPath": right.get("path"),
                    "layer": left.get("layer") if left.get("layer") == right.get("layer") else "cross-layer",
                    "score": round(score, 2),
                    "sharedTerms": sorted(overlap),
                    "signal": signal,
                }
            )
    return sorted(candidates, key=lambda item: item["score"], reverse=True)[:50]


def usage_metrics(root: Path, api: dict[str, Any], ui: dict[str, Any]) -> dict[str, Any]:
    path = root / "artifacts/usage-metrics/usage.json"
    payload = read_json(path)
    if not payload:
        return {
            "path": str(path.relative_to(root)),
            "exists": False,
            "summary": "No runtime usage export found yet.",
            "requiredInputs": [
                "API gateway or service access counts by endpoint",
                "UI analytics, browser automation, or mock-service access counts by flow and actor",
                "Recent production-like error counts by endpoint or flow",
            ],
            "hotspots": [],
        }
    endpoint = api.get("service_context", {}).get("api", {}).get("endpoint")
    flow = (ui.get("task_context", {}).get("work_item", {}).get("affected_flows") or [None])[0]
    endpoints = payload.get("endpoints", {})
    flows = payload.get("flows", {})
    hotspots = []
    if endpoint in endpoints:
        hotspots.append({"type": "endpoint", "name": endpoint, "usage": endpoints[endpoint]})
    if flow in flows:
        hotspots.append({"type": "flow", "name": flow, "usage": flows[flow]})
    return {
        "path": str(path.relative_to(root)),
        "exists": True,
        "summary": f"Loaded {len(endpoints)} endpoint metric(s) and {len(flows)} flow metric(s).",
        "requiredInputs": [],
        "hotspots": hotspots,
    }


def confidence_score(api_health: dict[str, Any], ui_health: dict[str, Any], graphs: dict[str, Any], coverage: dict[str, Any], duplicates: list[dict[str, Any]]) -> dict[str, Any]:
    score = 100
    reasons = []
    if api_health["status"] != "pass":
        score -= 20
        reasons.append("API health is not passing.")
    if ui_health["status"] != "pass":
        score -= 20
        reasons.append("UI automation health is not passing.")
    if graphs["stale"]:
        score -= 12
        reasons.append("Graphify graph is stale against the current commit.")
    if coverage["gaps"]:
        score -= min(20, len(coverage["gaps"]) * 5)
        reasons.append(f"{len(coverage['gaps'])} coverage gap signal(s) found.")
    near_duplicates = [item for item in duplicates if item["signal"] == "near-duplicate review"]
    if near_duplicates:
        score -= min(12, len(near_duplicates) * 4)
        reasons.append(f"{len(near_duplicates)} high-similarity duplicate candidate(s) need review.")
    if not reasons:
        reasons.append("Mapped API/UI tests are passing and graph artifacts are fresh.")
    return {"score": max(score, 0), "status": "strong" if score >= 85 else "watch" if score >= 65 else "risk", "reasons": reasons}


def test_composition(graph: dict[str, Any]) -> dict[str, int]:
    api = 0
    ui = 0
    for node in graph["nodes"]:
        if node.get("kind") != "test_case":
            continue
        if node.get("layer") == "api":
            api += 1
        if node.get("layer") == "ui":
            ui += 1
    return {"api": api, "ui": ui, "total": api + ui}


def percentage(value: int | float, total: int | float) -> int:
    if not total:
        return 0
    return max(0, min(100, round((value / total) * 100)))


def build_dashboard(root: Path) -> dict[str, Any]:
    api = read_yaml(root / "contexts/current/resolved-context.yml")
    ui = read_yaml(root / "contexts/current/resolved-ui-context.yml")
    surefire = parse_surefire(root)
    api_tests = sum(item["tests"] for item in surefire)
    api_failures = sum(item["failures"] + item["errors"] for item in surefire)
    graphify = graphify_summary(root)
    commit = current_commit(root)
    graph = graph_data(root / "artifacts/test-graph/test-graph.json")
    files = changed_files(root)
    inventory = test_file_inventory(root, api, ui)
    coverage = coverage_insights(api, ui, graph, inventory)
    duplicates = duplicate_candidates(graph)
    covered_targets = len([item for item in coverage["endpointCoverage"] if item["covered"]]) + len([item for item in coverage["roleCoverage"] if item["covered"]])
    total_targets = len(coverage["endpointCoverage"]) + len(coverage["roleCoverage"])
    graphs = {
        "testImpact": graph_summary(root / "artifacts/test-graph/test-graph.json"),
        "graphify": graphify,
        "stale": bool(graphify.get("builtAtCommit") and commit and not commit.startswith(str(graphify.get("builtAtCommit")))),
        "currentCommit": commit,
    }
    api_health = {
        "suites": surefire,
        "tests": api_tests,
        "failures": api_failures,
        "status": "pass" if surefire and api_failures == 0 else "fail" if api_failures else "unknown",
    }
    ui_health = summarize_ui_automation(root)
    return {
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "ticket": {
            "api": api.get("task_context", {}).get("work_item", {}),
            "ui": ui.get("task_context", {}).get("work_item", {}),
        },
        "graphs": graphs,
        "testHealth": {
            "api": api_health,
            "ui": ui_health,
        },
        "impacted": {
            "api": {
                "endpoint": api.get("service_context", {}).get("api", {}).get("endpoint"),
                "testFile": api.get("resolved_files", {}).get("api_test"),
                "commands": api.get("verification", {}).get("commands", []),
            },
            "ui": {
                "flow": (ui.get("task_context", {}).get("work_item", {}).get("affected_flows") or [None])[0],
                "roles": ui.get("derived_validation", {}).get("roles", []),
                "testFiles": [
                    ui.get("resolved_files", {}).get("role_test"),
                    ui.get("resolved_files", {}).get("feature_flag_test"),
                    ui.get("resolved_files", {}).get("legacy_interception_test"),
                ],
                "commands": ui.get("verification", {}).get("commands", []),
            },
        },
        "changeImpact": {
            "changedFiles": files,
            "recommendations": impacted_recommendations(api, ui, files),
        },
        "coverage": coverage,
        "duplicates": {
            "candidates": duplicates,
            "nearDuplicateCount": len([item for item in duplicates if item["signal"] == "near-duplicate review"]),
            "coverageSiblingCount": len([item for item in duplicates if item["signal"] == "coverage sibling"]),
        },
        "usageMetrics": usage_metrics(root, api, ui),
        "confidence": confidence_score(api_health, ui_health, graphs, coverage, duplicates),
        "visuals": {
            "testComposition": test_composition(graph),
            "coverage": {
                "covered": covered_targets,
                "total": total_targets,
                "percent": percentage(covered_targets, total_targets),
            },
            "duplicateSignal": {
                "clearPercent": max(0, 100 - (len([item for item in duplicates if item["signal"] == "near-duplicate review"]) * 25)),
            },
        },
        "duplicateDecisions": duplicate_decisions(read_text(root / "docs/loop-run-log.md")),
    }


def pill_class(status: str) -> str:
    return "good" if status == "pass" else "bad" if status == "fail" else "warn"


def render_dashboard(data: dict[str, Any]) -> str:
    payload = json.dumps(data, indent=2)
    api = data["testHealth"]["api"]
    ui = data["testHealth"].get("ui", data["testHealth"].get("playwright", {}))
    test_graph = data["graphs"]["testImpact"]
    graphify = data["graphs"]["graphify"]
    api_ticket = data["ticket"]["api"]
    ui_ticket = data["ticket"]["ui"]
    api_impacted = data["impacted"]["api"]
    ui_impacted = data["impacted"]["ui"]
    stale = "stale" if data["graphs"]["stale"] else "fresh"
    stale_class = "bad" if data["graphs"]["stale"] else "good"
    limit = DEFAULT_TABLE_LIMIT
    api_rows = "".join(
        f"<tr data-row><td>{html.escape(item['suite'])}</td><td>{item['tests']}</td><td>{item['failures'] + item['errors']}</td><td>{item['skipped']}</td><td><span class=\"pill {pill_class(item['status'])}\">{item['status']}</span></td></tr>"
        for item in api["suites"]
    ) or "<tr data-row><td>No API report found</td><td>0</td><td>0</td><td>0</td><td><span class=\"pill warn\">unknown</span></td></tr>"
    duplicate_rows = "".join(
        f"<tr data-row><td>{html.escape(item['entry'])}</td><td>{html.escape(item['signal'])}</td></tr>"
        for item in data["duplicateDecisions"]
    ) or "<tr data-row><td>No duplicate decision recorded yet</td><td>pending</td></tr>"
    api_commands = "".join(f"<li>{html.escape(command)}</li>" for command in api_impacted["commands"])
    ui_commands = "".join(f"<li>{html.escape(command)}</li>" for command in ui_impacted["commands"])
    ui_files = "".join(f"<li>{html.escape(path or 'missing')}</li>" for path in ui_impacted["testFiles"])
    ui_failures = ""
    if ui["failedTests"]:
        failure_items = "".join(f"<li>{html.escape(str(item))}</li>" for item in ui["failedTests"])
        ui_failures = f"<h3>Failed UI tests</h3><ul>{failure_items}</ul>"
    confidence = data["confidence"]
    confidence_class = "good" if confidence["status"] == "strong" else "warn" if confidence["status"] == "watch" else "bad"
    confidence_reasons = "".join(f"<li>{html.escape(reason)}</li>" for reason in confidence["reasons"])
    changed_count = len(data["changeImpact"]["changedFiles"])
    impact_rows = "".join(
        f"<tr data-row><td><span class=\"pill {pill_class('pass' if item['priority'] == 'high' else 'unknown')}\">{html.escape(item['priority'])}</span></td><td><strong>{html.escape(item['area'])}</strong><p class=\"muted\">{html.escape(item['reason'])}</p></td><td>{len(item['files'])}</td><td>{len(item['commands'])}</td></tr>"
        for item in data["changeImpact"]["recommendations"]
    )
    changed_files = "".join(f"<li>{html.escape(path)}</li>" for path in data["changeImpact"]["changedFiles"][:10])
    if changed_count > 10:
        changed_files += f"<li>{changed_count - 10} more changed file(s)</li>"
    changed_files = changed_files or "<li>No changed files detected from git status</li>"
    endpoint_rows = "".join(
        f"<tr data-row><td>Endpoint: {html.escape(str(item['endpoint']))}</td><td><span class=\"pill {pill_class('pass' if item['covered'] else 'fail')}\">{'covered' if item['covered'] else 'gap'}</span></td></tr>"
        for item in data["coverage"]["endpointCoverage"]
    )
    role_rows = "".join(
        f"<tr data-row><td>Role: {html.escape(str(item['role']))}</td><td><span class=\"pill {pill_class('pass' if item['covered'] else 'fail')}\">{'covered' if item['covered'] else 'gap'}</span></td></tr>"
        for item in data["coverage"]["roleCoverage"]
    )
    gap_items = "".join(f"<li>{html.escape(item)}</li>" for item in data["coverage"]["gaps"])
    gap_items = gap_items or "<li>No deterministic coverage gaps found in the active graph.</li>"
    negative_evidence_section = ""
    negative_evidence = data.get("negativeEvidence", {})
    mapping_rows = "".join(
        f"<tr data-row><td>{html.escape(str(item.get('area', '')))}</td><td>{html.escape(str(item.get('intent', '')))}<p class=\"muted\">Source: {html.escape(str(item.get('source', '')))}</p></td><td><span class=\"pill {pill_class('pass' if item.get('status') == 'mapped' else 'fail' if item.get('status') == 'gap' else 'unknown')}\">{html.escape(str(item.get('status', 'review')))}</span></td><td>{html.escape(str(item.get('evidence', '')))}</td><td>{html.escape(str(item.get('nextAction', '')))}</td></tr>"
        for item in negative_evidence.get("mappingAudit", [])
    )
    scenario_rows = "".join(
        f"<tr data-row><td>{html.escape(str(item.get('scenario', '')))}</td><td>{html.escape(str(item.get('injectedCondition', '')))}</td><td>{html.escape(str(item.get('dashboardSignal', '')))}</td><td>{html.escape(str(item.get('debugQuestion', '')))}</td></tr>"
        for item in negative_evidence.get("scenarios", [])
    )
    if mapping_rows or scenario_rows:
        mapping_table = (
            f"<h3>Mapping audit</h3><div class=\"table-tools\"><input type=\"search\" placeholder=\"Search mapping evidence\" data-table-filter=\"mapping-audit-table\"><span class=\"count\" data-table-count=\"mapping-audit-table\"></span><button type=\"button\" data-table-toggle=\"mapping-audit-table\">Show all</button></div><div class=\"table-wrap\"><table id=\"mapping-audit-table\" data-table-limit=\"{limit}\"><thead><tr><th>Area</th><th>Intent</th><th>Status</th><th>Evidence</th><th>Next action</th></tr></thead><tbody>{mapping_rows}</tbody></table></div>"
            if mapping_rows
            else ""
        )
        scenario_table = (
            f"<h3>Scenario checks</h3><div class=\"table-tools\"><input type=\"search\" placeholder=\"Search negative scenarios\" data-table-filter=\"negative-scenario-table\"><span class=\"count\" data-table-count=\"negative-scenario-table\"></span><button type=\"button\" data-table-toggle=\"negative-scenario-table\">Show all</button></div><div class=\"table-wrap\"><table id=\"negative-scenario-table\" data-table-limit=\"{limit}\"><thead><tr><th>Scenario</th><th>Injected condition</th><th>Dashboard signal</th><th>Debug question</th></tr></thead><tbody>{scenario_rows}</tbody></table></div>"
            if scenario_rows
            else ""
        )
        negative_evidence_section = f"""
      <section class="card">
        <h2>Negative Scenario Evidence</h2>
        <p class="muted">Synthetic checks for missing mapping, missing coverage, orphan tests, duplicate risk, and stale graph behavior. This section validates whether the dashboard explains the risk clearly.</p>
        {mapping_table}
        {scenario_table}
      </section>
"""
    duplicate_candidate_rows = "".join(
        f"<tr data-row><td>{html.escape(item['left'])}<p class=\"muted\">{html.escape(str(item.get('leftPath', '')))}</p></td><td>{html.escape(item['right'])}<p class=\"muted\">{html.escape(str(item.get('rightPath', '')))}</p></td><td>{item['score']}</td><td><span class=\"pill {'bad' if item['signal'] == 'near-duplicate review' else 'warn'}\">{html.escape(item['signal'])}</span><p class=\"muted\">Shared: {html.escape(', '.join(item['sharedTerms']))}</p></td></tr>"
        for item in data["duplicates"]["candidates"]
    )
    duplicate_candidate_rows = duplicate_candidate_rows or "<tr data-row><td>No overlap candidates found</td><td></td><td>0</td><td><span class=\"pill good\">clear</span></td></tr>"
    usage = data["usageMetrics"]
    usage_inputs = "".join(f"<li>{html.escape(item)}</li>" for item in usage["requiredInputs"])
    usage_hotspots = "".join(
        f"<li>{html.escape(item['type'])}: {html.escape(item['name'])} · {html.escape(str(item['usage']))}</li>"
        for item in usage["hotspots"]
    )
    usage_details = usage_hotspots or usage_inputs or "<li>Runtime usage metrics loaded with no active hotspots for this slice.</li>"
    visuals = data["visuals"]
    api_status_percent = 100 if api["status"] == "pass" else 0
    ui_status_percent = 100 if ui["status"] == "pass" else 0
    graph_fresh_percent = 0 if data["graphs"]["stale"] else 100
    confidence_percent = max(0, min(100, int(confidence["score"])))
    coverage_percent = visuals["coverage"]["percent"]
    duplicate_clear_percent = visuals["duplicateSignal"]["clearPercent"]
    composition = visuals["testComposition"]
    api_case_percent = 0 if composition["total"] == 0 else round((composition["api"] / composition["total"]) * 100)
    ui_case_percent = 100 - api_case_percent if composition["total"] else 0
    quality_bars = [
        ("Release confidence", confidence_percent, confidence_class, str(confidence["score"])),
        ("API health", api_status_percent, pill_class(api["status"]), api["status"]),
        ("UI automation health", ui_status_percent, pill_class(ui["status"]), ui["status"]),
        ("Mapped coverage", coverage_percent, "good" if coverage_percent == 100 else "warn", f"{visuals['coverage']['covered']}/{visuals['coverage']['total']}"),
        ("Duplicate safety", duplicate_clear_percent, "good" if duplicate_clear_percent == 100 else "warn", f"{data['duplicates']['nearDuplicateCount']} risk"),
        ("Graph freshness", graph_fresh_percent, stale_class, stale),
    ]
    quality_rows = "".join(
        f"<div class=\"bar-row\"><div><strong>{html.escape(label)}</strong><span>{html.escape(value)}</span></div><div class=\"bar\"><i class=\"{css_class}\" style=\"width: {width}%\"></i></div></div>"
        for label, width, css_class, value in quality_bars
    )
    duplicate_near_width = min(100, data["duplicates"]["nearDuplicateCount"] * 25)
    duplicate_sibling_width = min(100, data["duplicates"]["coverageSiblingCount"] * 12)
    impact_bars = "".join(
        f"<div class=\"bar-row\"><div><strong>{html.escape(item['area'])}</strong><span>{len(item['files'])} files</span></div><div class=\"bar\"><i class=\"warn\" style=\"width: {min(100, max(8, len(item['files']) * 8))}%\"></i></div></div>"
        for item in data["changeImpact"]["recommendations"]
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Agentic QA Dashboard</title>
    <style>
      :root {{ color-scheme: light; --bg: #f5f7fb; --panel: #fff; --ink: #172033; --muted: #64748b; --line: #d8e0ea; --blue: #2563eb; }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
      main {{ display: grid; gap: 18px; margin: 0 auto; max-width: 1320px; padding: 22px; }}
      header {{ align-items: flex-start; display: flex; gap: 16px; justify-content: space-between; }}
      h1, h2, h3, p {{ margin: 0; }}
      h1 {{ font-size: 28px; line-height: 1.1; }}
      h2 {{ font-size: 17px; margin-bottom: 12px; }}
      h3 {{ font-size: 14px; margin: 14px 0 7px; }}
      a {{ color: var(--blue); font-weight: 700; text-decoration: none; }}
      .muted {{ color: var(--muted); font-size: 13px; line-height: 1.35; margin-top: 6px; overflow-wrap: anywhere; }}
      .grid {{ display: grid; gap: 14px; grid-template-columns: repeat(4, minmax(0, 1fr)); }}
      .two {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
      .metric strong {{ display: block; font-size: 26px; line-height: 1; margin: 6px 0; }}
      .metric span {{ color: var(--muted); font-size: 12px; font-weight: 800; text-transform: uppercase; }}
      .score {{ align-items: center; display: flex; gap: 12px; margin: 6px 0 12px; }}
      .score strong {{ font-size: 34px; line-height: 1; }}
      .bar-row {{ display: grid; gap: 7px; margin: 10px 0; }}
      .bar-row div:first-child {{ align-items: center; display: flex; justify-content: space-between; gap: 12px; }}
      .bar-row strong {{ font-size: 13px; }}
      .bar-row span {{ color: var(--muted); font-size: 12px; font-weight: 700; }}
      .bar {{ background: #e9eef6; border-radius: 999px; height: 10px; overflow: hidden; }}
      .bar i {{ border-radius: inherit; display: block; height: 100%; }}
      .stack {{ background: #e9eef6; border-radius: 999px; display: flex; height: 14px; overflow: hidden; }}
      .stack span {{ display: block; min-width: 3px; }}
      .api-fill {{ background: #2563eb; }}
      .ui-fill {{ background: #14b8a6; }}
      .graph-fill {{ background: #8b5cf6; }}
      .pill {{ border-radius: 999px; display: inline-block; font-size: 12px; font-weight: 800; padding: 4px 8px; }}
      .good {{ background: #dcfce7; color: #15803d; }} .bad {{ background: #fee2e2; color: #b91c1c; }} .warn {{ background: #fef3c7; color: #a16207; }}
      .bar i.good {{ background: #22c55e; }} .bar i.bad {{ background: #ef4444; }} .bar i.warn {{ background: #f59e0b; }}
      .links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
      .links a {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 9px 11px; }}
      .legend {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 10px; }}
      .legend span {{ align-items: center; color: var(--muted); display: inline-flex; font-size: 12px; gap: 6px; }}
      .dot {{ border-radius: 999px; display: inline-block; height: 9px; width: 9px; }}
      .table-tools {{ align-items: center; display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; margin: 8px 0 10px; }}
      .table-tools input {{ background: #f8fafc; border: 1px solid var(--line); border-radius: 6px; color: var(--ink); min-height: 34px; min-width: min(260px, 100%); padding: 7px 9px; }}
      .table-tools button {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; color: var(--blue); cursor: pointer; font-weight: 800; min-height: 34px; padding: 7px 10px; }}
      .table-tools .count {{ color: var(--muted); font-size: 12px; font-weight: 700; }}
      .table-wrap {{ border: 1px solid var(--line); border-radius: 8px; max-height: 360px; overflow: auto; }}
      .table-wrap table th {{ background: var(--panel); position: sticky; top: 0; z-index: 1; }}
      tr.is-hidden {{ display: none; }}
      ul {{ margin: 0; padding-left: 18px; }} li {{ color: var(--muted); font-size: 13px; line-height: 1.45; margin: 4px 0; overflow-wrap: anywhere; }}
      table {{ border-collapse: collapse; width: 100%; }} th, td {{ border-bottom: 1px solid var(--line); font-size: 13px; padding: 9px 6px; text-align: left; vertical-align: top; }} th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; }}
      pre {{ background: #0f172a; border-radius: 8px; color: #e2e8f0; font-size: 12px; line-height: 1.45; margin: 0; max-height: 360px; overflow: auto; padding: 12px; }}
      .notice {{ background: #fff7ed; border: 1px solid #fed7aa; border-radius: 8px; color: #9a3412; font-size: 13px; font-weight: 700; padding: 12px 14px; }}
      @media (max-width: 980px) {{ header {{ flex-direction: column; }} .grid, .two {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <h1>Agentic QA Dashboard</h1>
          <p class="muted">Generated {html.escape(data["generatedAt"])} from resolved contexts, graph artifacts, test reports, and loop evidence.</p>
        </div>
        <div class="links"><a href="http://127.0.0.1:8766/">Test-impact graph</a><a href="http://127.0.0.1:8767/graph.html">Graphify graph</a></div>
      </header>
      {f'<section class="notice">{html.escape(str(data["validationMode"]))}</section>' if data.get("validationMode") else ''}
      <section class="grid">
        <div class="card metric"><span>API health</span><strong>{api["status"]}</strong><p class="muted">{api["tests"]} tests, {api["failures"]} failures</p></div>
        <div class="card metric"><span>UI automation health</span><strong>{ui["status"]}</strong><p class="muted">{len(ui["failedTests"])} failed tests in last run</p></div>
        <div class="card metric"><span>Test graph</span><strong>{test_graph["nodes"]}/{test_graph["edges"]}</strong><p class="muted">nodes / relationships</p></div>
        <div class="card metric"><span>Graphify</span><strong>{graphify["nodes"]}/{graphify["communities"]}</strong><p class="muted">nodes / communities · <span class="pill {stale_class}">{stale}</span></p></div>
      </section>
      <section class="grid two">
        <div class="card">
          <h2>Quality Snapshot</h2>
          {quality_rows}
        </div>
        <div class="card">
          <h2>Test Mix And Signals</h2>
          <h3>Automated test cases</h3>
          <div class="stack" aria-label="API and UI test case mix"><span class="api-fill" style="width: {api_case_percent}%"></span><span class="ui-fill" style="width: {ui_case_percent}%"></span></div>
          <div class="legend"><span><i class="dot api-fill"></i>API {composition["api"]}</span><span><i class="dot ui-fill"></i>UI {composition["ui"]}</span><span>Total {composition["total"]}</span></div>
          <h3>Duplicate signals</h3>
          <div class="bar-row"><div><strong>Near-duplicate risks</strong><span>{data["duplicates"]["nearDuplicateCount"]}</span></div><div class="bar"><i class="bad" style="width: {duplicate_near_width}%"></i></div></div>
          <div class="bar-row"><div><strong>Coverage siblings</strong><span>{data["duplicates"]["coverageSiblingCount"]}</span></div><div class="bar"><i class="warn" style="width: {duplicate_sibling_width}%"></i></div></div>
          <h3>Current impact focus</h3>
          {impact_bars}
        </div>
      </section>
      <section class="grid two">
        <div class="card">
          <h2>Release Confidence</h2>
          <div class="score"><strong>{confidence["score"]}</strong><span class="pill {confidence_class}">{html.escape(confidence["status"])}</span></div>
          <ul>{confidence_reasons}</ul>
        </div>
        <div class="card">
          <h2>Real-World Usage Readiness</h2>
          <p><strong>{html.escape(usage["summary"])}</strong></p>
          <p class="muted">Source: {html.escape(usage["path"])}</p>
          <ul>{usage_details}</ul>
        </div>
      </section>
      <section class="grid two">
        <div class="card"><h2>API Work Item Mapping</h2><p><strong>{html.escape(str(api_ticket.get("key", "API ticket")))}</strong> · {html.escape(str(api_ticket.get("summary", "")))}</p><p class="muted">Endpoint: {html.escape(str(api_impacted.get("endpoint")))}</p><p class="muted">Test file: {html.escape(str(api_impacted.get("testFile")))}</p><h3>Verification</h3><ul>{api_commands}</ul></div>
        <div class="card"><h2>UI Work Item Mapping</h2><p><strong>{html.escape(str(ui_ticket.get("key", "UI ticket")))}</strong> · {html.escape(str(ui_ticket.get("summary", "")))}</p><p class="muted">Flow: {html.escape(str(ui_impacted.get("flow")))}</p><p class="muted">Actors/Roles: {html.escape(", ".join(ui_impacted.get("roles", [])))}</p><h3>Mapped UI tests</h3><ul>{ui_files}</ul><h3>Verification</h3><ul>{ui_commands}</ul>{ui_failures}</div>
      </section>
      <section class="grid two">
        <div class="card">
          <h2>Impacted Test Recommendations</h2>
          <p class="muted">{changed_count} changed file(s) detected from git status.</p>
          <div class="table-tools"><input type="search" placeholder="Search recommendations" data-table-filter="impact-table"><span class="count" data-table-count="impact-table"></span><button type="button" data-table-toggle="impact-table">Show all</button></div>
          <div class="table-wrap"><table id="impact-table" data-table-limit="{limit}"><thead><tr><th>Priority</th><th>Area</th><th>Files</th><th>Commands</th></tr></thead><tbody>{impact_rows}</tbody></table></div>
          <h3>Changed files</h3><ul>{changed_files}</ul>
        </div>
        <div class="card">
          <h2>Coverage And Gap Signals</h2>
          <h3>Mapped targets</h3>
          <div class="table-tools"><input type="search" placeholder="Search coverage" data-table-filter="coverage-table"><span class="count" data-table-count="coverage-table"></span><button type="button" data-table-toggle="coverage-table">Show all</button></div>
          <div class="table-wrap"><table id="coverage-table" data-table-limit="{limit}"><thead><tr><th>Target</th><th>Status</th></tr></thead><tbody>{endpoint_rows}{role_rows}</tbody></table></div>
          <h3>Gap signals</h3><ul>{gap_items}</ul>
        </div>
      </section>
      {negative_evidence_section}
      <section class="grid two">
        <div class="card"><h2>API Test Health</h2><div class="table-tools"><input type="search" placeholder="Search API suites" data-table-filter="api-health-table"><span class="count" data-table-count="api-health-table"></span><button type="button" data-table-toggle="api-health-table">Show all</button></div><div class="table-wrap"><table id="api-health-table" data-table-limit="{limit}"><thead><tr><th>Suite</th><th>Tests</th><th>Failures</th><th>Skipped</th><th>Status</th></tr></thead><tbody>{api_rows}</tbody></table></div></div>
        <div class="card"><h2>Duplicate-Prevention Evidence</h2><div class="table-tools"><input type="search" placeholder="Search loop evidence" data-table-filter="evidence-table"><span class="count" data-table-count="evidence-table"></span><button type="button" data-table-toggle="evidence-table">Show all</button></div><div class="table-wrap"><table id="evidence-table" data-table-limit="{limit}"><thead><tr><th>Loop log entry</th><th>Signal</th></tr></thead><tbody>{duplicate_rows}</tbody></table></div></div>
      </section>
      <section class="card">
        <h2>Duplicate And Overlap Candidates</h2>
        <p class="muted">{data["duplicates"]["nearDuplicateCount"]} near-duplicate review candidate(s), {data["duplicates"]["coverageSiblingCount"]} coverage sibling candidate(s). Showing top {limit} by default; use search or Show all for larger suites.</p>
        <div class="table-tools"><input type="search" placeholder="Search duplicate candidates by test, file, score, or signal" data-table-filter="duplicate-candidates-table"><span class="count" data-table-count="duplicate-candidates-table"></span><button type="button" data-table-toggle="duplicate-candidates-table">Show all</button></div>
        <div class="table-wrap"><table id="duplicate-candidates-table" data-table-limit="{limit}"><thead><tr><th>Test A</th><th>Test B</th><th>Score</th><th>Signal</th></tr></thead><tbody>{duplicate_candidate_rows}</tbody></table></div>
      </section>
      <section class="card"><h2>Raw Dashboard JSON</h2><pre>{html.escape(payload)}</pre></section>
    </main>
    <script>
      const tableState = new Map();

      function rowMatches(row, query) {{
        return !query || row.innerText.toLowerCase().includes(query);
      }}

      function refreshTable(id) {{
        const table = document.getElementById(id);
        if (!table) return;
        const rows = Array.from(table.querySelectorAll('tbody tr[data-row]'));
        const input = document.querySelector(`[data-table-filter="${{id}}"]`);
        const count = document.querySelector(`[data-table-count="${{id}}"]`);
        const toggle = document.querySelector(`[data-table-toggle="${{id}}"]`);
        const query = (input?.value || '').trim().toLowerCase();
        const limit = Number(table.dataset.tableLimit || {limit});
        const expanded = tableState.get(id) === true || Boolean(query);
        let matched = 0;
        rows.forEach((row) => {{
          const matches = rowMatches(row, query);
          matched += matches ? 1 : 0;
          const beyondLimit = !expanded && matched > limit;
          row.classList.toggle('is-hidden', !matches || beyondLimit);
        }});
        if (count) {{
          const visible = expanded ? matched : Math.min(matched, limit);
          count.textContent = `${{visible}} of ${{matched}} shown`;
        }}
        if (toggle) {{
          toggle.hidden = matched <= limit || Boolean(query);
          toggle.textContent = expanded ? `Show top ${{limit}}` : 'Show all';
        }}
      }}

      document.querySelectorAll('table[data-table-limit]').forEach((table) => refreshTable(table.id));
      document.querySelectorAll('[data-table-filter]').forEach((input) => {{
        input.addEventListener('input', () => refreshTable(input.dataset.tableFilter));
      }});
      document.querySelectorAll('[data-table-toggle]').forEach((button) => {{
        button.addEventListener('click', () => {{
          const id = button.dataset.tableToggle;
          tableState.set(id, tableState.get(id) !== true);
          refreshTable(id);
        }});
      }});
    </script>
  </body>
</html>
"""


def write_outputs(root: Path, output_dir: Path) -> None:
    data = build_dashboard(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "dashboard.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (output_dir / "index.html").write_text(render_dashboard(data), encoding="utf-8")
    print(f"Wrote {output_dir / 'dashboard.json'}")
    print(f"Wrote {output_dir / 'index.html'}")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass


def serve(output_dir: Path, host: str, port: int) -> None:
    if not (output_dir / "index.html").is_file():
        raise SystemExit("Missing dashboard index. Run `npm run dashboard:build` first.")
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(output_dir), **kwargs)
    server = ThreadingHTTPServer((host, port), handler)
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    print(f"Serving QA dashboard at http://{display_host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=str(WORKSPACE))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    root = Path(args.workspace).expanduser().resolve()
    output_dir = (root / args.output_dir).resolve()
    write_outputs(root, output_dir)
    if args.serve:
        serve(output_dir, args.host, args.port)


if __name__ == "__main__":
    main()
