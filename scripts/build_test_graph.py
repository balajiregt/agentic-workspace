#!/usr/bin/env python3
"""Build a small API/UI test relationship graph for local inspection."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - local setup guard
    raise SystemExit("PyYAML is required for test graph generation: python3 -m pip install pyyaml") from exc


DEFAULT_WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = "artifacts/test-graph"


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Expected YAML mapping in {path}")
    return data


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def rel(path: Path, workspace: Path) -> str:
    return str(path.resolve().relative_to(workspace.resolve()))


def node(
    graph: dict[str, Any],
    node_id: str,
    label: str,
    kind: str,
    layer: str,
    path: str | None = None,
    detail: str | None = None,
) -> None:
    if node_id in graph["_node_ids"]:
        return
    graph["_node_ids"].add(node_id)
    item: dict[str, Any] = {
        "id": node_id,
        "label": label,
        "kind": kind,
        "layer": layer,
    }
    if path:
        item["path"] = path
    if detail:
        item["detail"] = detail
    graph["nodes"].append(item)


def edge(graph: dict[str, Any], source: str, target: str, label: str) -> None:
    edge_id = (source, target, label)
    if edge_id in graph["_edge_ids"]:
        return
    graph["_edge_ids"].add(edge_id)
    graph["edges"].append({"source": source, "target": target, "label": label})


def java_tests(text: str) -> list[str]:
    names = re.findall(r'@DisplayName\("([^"]+)"\)\s+void\s+(\w+)\(', text)
    if names:
        return [display for display, _method in names]
    return re.findall(r"@Test\s+void\s+(\w+)\(", text)


def playwright_tests(text: str) -> list[str]:
    pattern = re.compile(r"test\((['\"])(.*?)\1\s*,", re.DOTALL)
    return [re.sub(r"\\s+", " ", title).strip() for _quote, title in pattern.findall(text)]


def compact_path(path: str) -> str:
    parts = Path(path).parts
    return "/".join(parts[-3:]) if len(parts) > 3 else path


def add_api_graph(graph: dict[str, Any], workspace: Path, resolved: dict[str, Any]) -> None:
    files = resolved.get("resolved_files", {})
    repos = resolved.get("resolved_repositories", {})
    api = resolved.get("service_context", {}).get("api", {})
    verification = resolved.get("verification", {}).get("commands", [])
    endpoint = str(api.get("endpoint", "API endpoint"))
    service_name = str(resolved.get("task_context", {}).get("service_name", "service"))

    node(graph, "api-context", "service-context.yml", "context", "api", "contexts/current/service-context.yml")
    node(graph, "api-resolved", "resolved-context.yml", "context", "api", "contexts/current/resolved-context.yml")
    node(graph, "service-repo", service_name, "repository", "api", repos.get("service_repo"))
    node(graph, "api-endpoint", endpoint, "endpoint", "api", detail="External API contract under test")
    edge(graph, "api-context", "api-resolved", "generates")
    edge(graph, "api-resolved", "service-repo", "routes")
    edge(graph, "service-repo", "api-endpoint", "owns")

    file_nodes = [
        ("controller", "controller", "maps request"),
        ("service", "service", "implements behavior"),
        ("openapi", "contract", "documents"),
        ("shared_fixtures", "fixture", "provides data"),
        ("shared_assertions", "assertion", "reuses assertions"),
        ("api_test", "api_test", "tests endpoint"),
    ]
    for key, kind, relation in file_nodes:
        path = files.get(key)
        if not path:
            continue
        node_id = f"api-{key}"
        node(graph, node_id, Path(path).name, kind, "api", path, compact_path(path))
        edge(graph, "api-endpoint" if key in {"api_test", "openapi"} else "service-repo", node_id, relation)

    if files.get("controller"):
        edge(graph, "api-controller", "api-service", "calls")
        edge(graph, "api-openapi", "api-controller", "contract aligns")
    if files.get("api_test"):
        edge(graph, "api-api_test", "api-shared_fixtures", "uses")
        edge(graph, "api-api_test", "api-shared_assertions", "uses")
        api_test_text = read_text(workspace / files["api_test"])
        for index, title in enumerate(java_tests(api_test_text), start=1):
            test_id = f"api-testcase-{index}"
            node(graph, test_id, title, "test_case", "api", files["api_test"])
            edge(graph, "api-api_test", test_id, "contains")
            edge(graph, test_id, "api-endpoint", "verifies")

    for index, command in enumerate(verification, start=1):
        command_id = f"api-command-{index}"
        label = "start API service" if "spring-boot:run" in command else "run API tests"
        node(graph, command_id, label, "command", "api", detail=command)
        edge(graph, "api-api_test", command_id, "validated by")


def add_ui_graph(graph: dict[str, Any], workspace: Path, resolved: dict[str, Any]) -> None:
    files = resolved.get("resolved_files", {})
    repos = resolved.get("resolved_repositories", {})
    roles = resolved.get("derived_validation", {}).get("roles", [])
    verification = resolved.get("verification", {}).get("commands", [])
    project_name = str(resolved.get("task_context", {}).get("ui_project_name", "ui project"))

    node(graph, "ui-context", "ui-context.yml", "context", "ui", "contexts/current/ui-context.yml")
    node(graph, "ui-resolved", "resolved-ui-context.yml", "context", "ui", "contexts/current/resolved-ui-context.yml")
    node(graph, "ui-project", project_name, "repository", "ui", repos.get("ui_project"))
    node(graph, "ui-flow", "role-aware operations console", "flow", "ui")
    edge(graph, "ui-context", "ui-resolved", "generates")
    edge(graph, "ui-resolved", "ui-project", "routes")
    edge(graph, "ui-project", "ui-flow", "owns")

    file_nodes = [
        ("playwright_config", "config", "starts app/mockserver"),
        ("helper", "helper", "injects headers"),
        ("page_object", "page_object", "locates UI"),
        ("assertions", "assertion", "asserts UI"),
        ("role_test", "e2e_test", "role matrix"),
        ("feature_flag_test", "e2e_test", "feature/error paths"),
        ("legacy_interception_test", "e2e_test", "legacy comparison"),
        ("token_route", "mock_route", "signs roles"),
        ("workspace_route", "mock_route", "returns workspace"),
        ("app_script", "app", "renders"),
    ]
    for key, kind, relation in file_nodes:
        path = files.get(key)
        if not path:
            continue
        node_id = f"ui-{key}"
        node(graph, node_id, Path(path).name, kind, "ui", path, compact_path(path))
        edge(graph, "ui-flow", node_id, relation)

    if files.get("role_test"):
        edge(graph, "ui-role_test", "ui-helper", "uses")
        edge(graph, "ui-role_test", "ui-page_object", "uses")
        edge(graph, "ui-role_test", "ui-assertions", "uses")
    if files.get("feature_flag_test"):
        edge(graph, "ui-feature_flag_test", "ui-helper", "uses")
    if files.get("helper"):
        edge(graph, "ui-helper", "ui-token_route", "adds agent-roles")
        edge(graph, "ui-helper", "ui-workspace_route", "forces errors")
    if files.get("app_script"):
        edge(graph, "ui-app_script", "ui-token_route", "calls")
        edge(graph, "ui-app_script", "ui-workspace_route", "calls")

    for role in roles:
        role_id = f"role-{role}"
        node(graph, role_id, str(role), "role", "ui")
        edge(graph, "ui-token_route", role_id, "embeds")
        edge(graph, role_id, "ui-workspace_route", "selects response")
        edge(graph, "ui-role_test", role_id, "covers")

    for key in ("role_test", "feature_flag_test", "legacy_interception_test"):
        path = files.get(key)
        if not path:
            continue
        text = read_text(workspace / path)
        parent_id = f"ui-{key}"
        for index, title in enumerate(playwright_tests(text), start=1):
            test_id = f"{parent_id}-case-{index}"
            node(graph, test_id, title, "test_case", "ui", path)
            edge(graph, parent_id, test_id, "contains")
            edge(graph, test_id, "ui-flow", "verifies")

    for index, command in enumerate(verification, start=1):
        command_id = f"ui-command-{index}"
        label = command.rsplit(" ", 1)[-1]
        node(graph, command_id, label, "command", "ui", detail=command)
        edge(graph, "ui-project", command_id, "validated by")


def build_graph(workspace: Path) -> dict[str, Any]:
    api_resolved = read_yaml(workspace / "contexts/current/resolved-context.yml")
    ui_resolved = read_yaml(workspace / "contexts/current/resolved-ui-context.yml")
    graph: dict[str, Any] = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "workspace": str(workspace),
        "nodes": [],
        "edges": [],
        "_node_ids": set(),
        "_edge_ids": set(),
    }
    node(graph, "workspace", "agentic-workspace", "workspace", "shared", detail=str(workspace))
    add_api_graph(graph, workspace, api_resolved)
    add_ui_graph(graph, workspace, ui_resolved)
    edge(graph, "workspace", "api-context", "has API context")
    edge(graph, "workspace", "ui-context", "has UI context")
    graph.pop("_node_ids")
    graph.pop("_edge_ids")
    return graph


def kind_counts(graph: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in graph["nodes"]:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    return dict(sorted(counts.items()))


def render_html(graph: dict[str, Any]) -> str:
    data = json.dumps(graph, indent=2)
    counts = kind_counts(graph)
    counts_label = " | ".join(f"{key}: {value}" for key, value in counts.items())
    escaped_counts = html.escape(counts_label)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Agentic Workspace Test Graph</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f7f9fb;
        --panel: #ffffff;
        --ink: #14213d;
        --muted: #667085;
        --line: #d7dee8;
        --api: #2563eb;
        --ui: #16a34a;
        --shared: #7c3aed;
        --test: #f59e0b;
        --command: #dc2626;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        background: var(--bg);
        color: var(--ink);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }}
      main {{
        display: grid;
        gap: 12px;
        height: 100vh;
        padding: 16px;
      }}
      header {{
        align-items: center;
        display: flex;
        gap: 12px;
        justify-content: space-between;
      }}
      h1 {{
        font-size: 20px;
        line-height: 1.2;
        margin: 0;
      }}
      .subtext {{
        color: var(--muted);
        font-size: 13px;
        margin-top: 4px;
      }}
      .toolbar {{
        align-items: center;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
      }}
      button {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        color: var(--ink);
        cursor: pointer;
        font: inherit;
        font-size: 13px;
        font-weight: 700;
        min-height: 34px;
        padding: 0 12px;
      }}
      button.active {{
        background: var(--ink);
        border-color: var(--ink);
        color: #fff;
      }}
      .surface {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        display: grid;
        grid-template-columns: minmax(0, 1fr) 320px;
        height: calc(100vh - 112px);
        min-height: 620px;
        overflow: hidden;
      }}
      .graph-wrap {{
        height: 100%;
        min-height: 0;
        overflow: hidden;
        position: relative;
      }}
      svg {{
        display: block;
        height: 100%;
        max-height: 100%;
        width: 100%;
      }}
      aside {{
        border-left: 1px solid var(--line);
        display: grid;
        gap: 12px;
        grid-template-rows: auto auto 1fr;
        padding: 14px;
      }}
      .legend {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px 12px;
      }}
      .legend span {{
        align-items: center;
        color: var(--muted);
        display: inline-flex;
        font-size: 12px;
        gap: 6px;
      }}
      .dot {{
        border-radius: 999px;
        display: inline-block;
        height: 10px;
        width: 10px;
      }}
      .details {{
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 12px;
      }}
      .details h2 {{
        font-size: 15px;
        line-height: 1.25;
        margin: 0 0 8px;
      }}
      .details p {{
        color: var(--muted);
        font-size: 13px;
        line-height: 1.35;
        margin: 6px 0 0;
        overflow-wrap: anywhere;
      }}
      .list {{
        border-top: 1px solid var(--line);
        min-height: 0;
        overflow: auto;
        padding-top: 10px;
      }}
      .list button {{
        border: 0;
        border-radius: 6px;
        display: block;
        font-weight: 500;
        margin-bottom: 4px;
        min-height: 28px;
        overflow: hidden;
        padding: 5px 7px;
        text-align: left;
        text-overflow: ellipsis;
        white-space: nowrap;
        width: 100%;
      }}
      .edge {{
        stroke: #b8c1cc;
        stroke-opacity: .75;
        stroke-width: 1.2;
      }}
      .edge-label {{
        fill: var(--muted);
        font-size: 10px;
        pointer-events: none;
      }}
      .node circle {{
        cursor: pointer;
        stroke: #fff;
        stroke-width: 2;
      }}
      .node text {{
        fill: var(--ink);
        font-size: 11px;
        font-weight: 650;
        paint-order: stroke;
        pointer-events: none;
        stroke: var(--panel);
        stroke-width: 4px;
      }}
      .node.dim, .edge.dim, .edge-label.dim {{
        opacity: .14;
      }}
      .node.selected circle {{
        stroke: var(--ink);
        stroke-width: 3;
      }}
      @media (max-width: 900px) {{
        main {{ height: auto; }}
        header {{ align-items: flex-start; flex-direction: column; }}
        .toolbar {{ justify-content: flex-start; }}
        .surface {{ grid-template-columns: 1fr; }}
        aside {{ border-left: 0; border-top: 1px solid var(--line); }}
      }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <div>
          <h1>Agentic Workspace Test Graph</h1>
          <div class="subtext">{len(graph["nodes"])} nodes | {len(graph["edges"])} relationships | {escaped_counts}</div>
        </div>
        <div class="toolbar" aria-label="Graph filters">
          <button class="active" type="button" data-filter="all">All</button>
          <button type="button" data-filter="api">API</button>
          <button type="button" data-filter="ui">UI</button>
          <button type="button" data-filter="tests">Tests</button>
          <button type="button" data-filter="commands">Commands</button>
        </div>
      </header>
      <section class="surface">
        <div class="graph-wrap">
          <svg id="graph" role="img" aria-label="Relationship graph for API and Playwright tests"></svg>
        </div>
        <aside>
          <div class="legend">
            <span><i class="dot" style="background: var(--api)"></i>API</span>
            <span><i class="dot" style="background: var(--ui)"></i>UI</span>
            <span><i class="dot" style="background: var(--shared)"></i>Context</span>
            <span><i class="dot" style="background: var(--test)"></i>Test</span>
            <span><i class="dot" style="background: var(--command)"></i>Command</span>
          </div>
          <div class="details" id="details">
            <h2>Select a node</h2>
            <p>Click a dot to see its path, type, and direct relationships.</p>
          </div>
          <div class="list" id="node-list" aria-label="Graph nodes"></div>
        </aside>
      </section>
    </main>
    <script>
      const graph = {data};
      const svg = document.getElementById('graph');
      const details = document.getElementById('details');
      const list = document.getElementById('node-list');
      const filters = document.querySelectorAll('[data-filter]');
      const width = 1160;
      const height = 680;
      let selected = null;
      let currentFilter = 'all';
      svg.setAttribute('viewBox', `0 0 ${{width}} ${{height}}`);
      svg.setAttribute('preserveAspectRatio', 'xMidYMin meet');

      const colorFor = (node) => {{
        if (node.kind === 'command') return 'var(--command)';
        if (node.kind.includes('test')) return 'var(--test)';
        if (node.kind === 'context' || node.kind === 'workspace') return 'var(--shared)';
        if (node.layer === 'api') return 'var(--api)';
        if (node.layer === 'ui') return 'var(--ui)';
        return 'var(--muted)';
      }};

      const radiusFor = (node) => {{
        if (node.kind === 'workspace') return 16;
        if (node.kind === 'endpoint' || node.kind === 'flow') return 13;
        if (node.kind.includes('test')) return 10;
        return 8;
      }};

      const layerSlots = {{}};
      graph.nodes.forEach((node) => {{
        const key = node.layer;
        layerSlots[key] = layerSlots[key] || 0;
        node.slot = layerSlots[key]++;
      }});

      const layerPosition = (node) => {{
        if (node.id === 'workspace') return {{ x: width / 2, y: 70 }};
        if (node.layer === 'api') return {{ x: 130 + (node.slot % 4) * 120, y: 155 + Math.floor(node.slot / 4) * 82 }};
        if (node.layer === 'ui') return {{ x: 610 + (node.slot % 5) * 104, y: 155 + Math.floor(node.slot / 5) * 76 }};
        return {{ x: width / 2, y: 100 }};
      }};

      graph.nodes.forEach((node) => {{
        const pos = layerPosition(node);
        node.x = pos.x;
        node.y = pos.y;
        node.vx = 0;
        node.vy = 0;
      }});

      const byId = new Map(graph.nodes.map((node) => [node.id, node]));
      const linked = new Set();
      graph.edges.forEach((edge) => {{
        edge.sourceNode = byId.get(edge.source);
        edge.targetNode = byId.get(edge.target);
        linked.add(`${{edge.source}}|${{edge.target}}`);
        linked.add(`${{edge.target}}|${{edge.source}}`);
      }});

      function isConnected(a, b) {{
        return a === b || linked.has(`${{a}}|${{b}}`);
      }}

      function matchesFilter(node) {{
        if (currentFilter === 'all') return true;
        if (currentFilter === 'api') return node.layer === 'api' || node.id === 'workspace';
        if (currentFilter === 'ui') return node.layer === 'ui' || node.id === 'workspace';
        if (currentFilter === 'tests') return node.kind.includes('test');
        if (currentFilter === 'commands') return node.kind === 'command';
        return true;
      }}

      function tick() {{
        for (let step = 0; step < 80; step++) {{
          graph.edges.forEach((edge) => {{
            const a = edge.sourceNode;
            const b = edge.targetNode;
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            const distance = Math.max(1, Math.hypot(dx, dy));
            const target = 105;
            const force = (distance - target) * 0.0025;
            const fx = dx / distance * force;
            const fy = dy / distance * force;
            a.vx += fx;
            a.vy += fy;
            b.vx -= fx;
            b.vy -= fy;
          }});
          for (let i = 0; i < graph.nodes.length; i++) {{
            for (let j = i + 1; j < graph.nodes.length; j++) {{
              const a = graph.nodes[i];
              const b = graph.nodes[j];
              const dx = b.x - a.x;
              const dy = b.y - a.y;
              const distance = Math.max(1, Math.hypot(dx, dy));
              const force = 55 / (distance * distance);
              const fx = dx / distance * force;
              const fy = dy / distance * force;
              a.vx -= fx;
              a.vy -= fy;
              b.vx += fx;
              b.vy += fy;
            }}
          }}
          graph.nodes.forEach((node) => {{
            const anchor = layerPosition(node);
            node.vx += (anchor.x - node.x) * 0.003;
            node.vy += (anchor.y - node.y) * 0.003;
            node.x = Math.max(28, Math.min(width - 28, node.x + node.vx));
            node.y = Math.max(34, Math.min(height - 28, node.y + node.vy));
            node.vx *= 0.76;
            node.vy *= 0.76;
          }});
        }}
      }}

      function render() {{
        tick();
        svg.replaceChildren();
        const edgeLayer = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        const labelLayer = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        const nodeLayer = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        svg.append(edgeLayer, labelLayer, nodeLayer);

        graph.edges.forEach((edge) => {{
          const dim = selected && !isConnected(selected.id, edge.source) && !isConnected(selected.id, edge.target);
          const filterDim = !matchesFilter(edge.sourceNode) && !matchesFilter(edge.targetNode);
          const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
          line.setAttribute('class', `edge${{dim || filterDim ? ' dim' : ''}}`);
          line.setAttribute('x1', edge.sourceNode.x);
          line.setAttribute('y1', edge.sourceNode.y);
          line.setAttribute('x2', edge.targetNode.x);
          line.setAttribute('y2', edge.targetNode.y);
          edgeLayer.append(line);
          if (!dim && !filterDim && (edge.sourceNode.kind === 'endpoint' || edge.targetNode.kind === 'flow' || edge.label === 'validated by')) {{
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('class', 'edge-label');
            text.setAttribute('x', (edge.sourceNode.x + edge.targetNode.x) / 2);
            text.setAttribute('y', (edge.sourceNode.y + edge.targetNode.y) / 2 - 5);
            text.textContent = edge.label;
            labelLayer.append(text);
          }}
        }});

        graph.nodes.forEach((node) => {{
          const dim = selected && !isConnected(selected.id, node.id);
          const filterDim = !matchesFilter(node);
          const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
          group.setAttribute('class', `node${{selected?.id === node.id ? ' selected' : ''}}${{dim || filterDim ? ' dim' : ''}}`);
          group.setAttribute('transform', `translate(${{node.x}}, ${{node.y}})`);
          const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          circle.setAttribute('r', radiusFor(node));
          circle.setAttribute('fill', colorFor(node));
          circle.addEventListener('click', () => selectNode(node));
          const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          text.setAttribute('x', radiusFor(node) + 6);
          text.setAttribute('y', 4);
          text.textContent = node.label.length > 34 ? node.label.slice(0, 31) + '...' : node.label;
          group.append(circle, text);
          nodeLayer.append(group);
        }});

        list.replaceChildren();
        graph.nodes
          .filter(matchesFilter)
          .sort((a, b) => a.layer.localeCompare(b.layer) || a.kind.localeCompare(b.kind) || a.label.localeCompare(b.label))
          .forEach((node) => {{
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = `${{node.kind}} | ${{node.label}}`;
            button.addEventListener('click', () => selectNode(node));
            list.append(button);
          }});
      }}

      function selectNode(node) {{
        selected = node;
        const relationships = graph.edges
          .filter((edge) => edge.source === node.id || edge.target === node.id)
          .map((edge) => {{
            const other = edge.source === node.id ? byId.get(edge.target) : byId.get(edge.source);
            const direction = edge.source === node.id ? '->' : '<-';
            return `${{direction}} ${{edge.label}} ${{other.label}}`;
          }});
        details.innerHTML = `
          <h2>${{node.label}}</h2>
          <p><strong>Type:</strong> ${{node.kind}} | <strong>Layer:</strong> ${{node.layer}}</p>
          ${{node.path ? `<p><strong>Path:</strong> ${{node.path}}</p>` : ''}}
          ${{node.detail ? `<p><strong>Detail:</strong> ${{node.detail}}</p>` : ''}}
          <p><strong>Relationships:</strong><br>${{relationships.slice(0, 8).join('<br>') || 'none'}}</p>
        `;
        render();
      }}

      filters.forEach((button) => {{
        button.addEventListener('click', () => {{
          filters.forEach((item) => item.classList.remove('active'));
          button.classList.add('active');
          currentFilter = button.dataset.filter;
          selected = null;
          details.innerHTML = '<h2>Select a node</h2><p>Click a dot to see its path, type, and direct relationships.</p>';
          render();
        }});
      }});

      render();
    </script>
  </body>
</html>
"""


def write_outputs(workspace: Path, output_dir: Path) -> tuple[Path, Path]:
    graph = build_graph(workspace)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "test-graph.json"
    html_path = output_dir / "index.html"
    json_path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(graph), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {html_path}")
    print(f"Graph nodes: {len(graph['nodes'])}")
    print(f"Graph edges: {len(graph['edges'])}")
    return json_path, html_path


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass


def serve(output_dir: Path, host: str, port: int) -> None:
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(output_dir), **kwargs)
    server = ThreadingHTTPServer((host, port), handler)
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    print(f"Serving test graph at http://{display_host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE))
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    output_dir = (workspace / args.output_dir).resolve()
    write_outputs(workspace, output_dir)
    if args.serve:
        serve(output_dir, args.host, args.port)


if __name__ == "__main__":
    main()
