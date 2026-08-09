const MAX_FILE_BYTES = 5 * 1024 * 1024;

const state = {
  dashboard: null,
  testGraph: null,
  graphify: null,
  htmlPreview: "",
  loaded: {
    dashboard: "",
    testGraph: "",
    graphify: "",
    htmlPreview: "",
  },
  graphUi: {
    testGraph: { query: "", focusNodeId: "" },
    graphify: { query: "", focusNodeId: "" },
  },
};

const demoDashboard = {
  generatedAt: new Date().toISOString(),
  testHealth: {
    api: { tests: 7, failures: 0, status: "pass", suites: [] },
    ui: { status: "pass", failedTests: [], framework: "Playwright" },
  },
  graphs: {
    testImpact: { nodes: 45, edges: 74, exists: true },
    graphify: { nodes: 350, edges: 582, communities: 30, exists: true },
    stale: false,
  },
  coverage: {
    endpointCoverage: [{ endpoint: "GET /xyz", covered: true }],
    roleCoverage: [
      { role: "admin", covered: true },
      { role: "viewer", covered: true },
      { role: "vip", covered: true },
    ],
    gaps: [],
    orphanTestCases: [],
  },
  duplicates: {
    nearDuplicateCount: 0,
    coverageSiblingCount: 2,
    candidates: [
      {
        left: "admin can access admin actions",
        right: "non-admin cannot access admin actions",
        score: 0.83,
        signal: "coverage sibling",
        sharedTerms: ["admin", "access", "actions"],
      },
    ],
  },
  confidence: { score: 92, status: "strong", reasons: ["Mapped API/UI tests are passing and graph artifacts are fresh."] },
  visuals: {
    coverage: { covered: 4, total: 4, percent: 100 },
    duplicateSignal: { clearPercent: 100 },
    testComposition: { api: 5, ui: 7, total: 12 },
  },
  ticket: {
    api: { key: "ABC-123", summary: "Add API coverage for medium customer risk" },
    ui: { key: "UI-ROLE-001", summary: "Validate role-aware UI automation" },
  },
  changeImpact: { changedFiles: [], recommendations: [] },
};

const demoTestGraph = {
  nodes: [
    { id: "api-endpoint", label: "GET /xyz", kind: "endpoint", layer: "api" },
    { id: "api-test", label: "CustomerRiskApiTest", kind: "test_case", layer: "api" },
    { id: "ui-flow", label: "operations console", kind: "flow", layer: "ui" },
    { id: "ui-test", label: "role-ui.spec.ts", kind: "test_case", layer: "ui" },
    { id: "role-admin", label: "admin", kind: "role", layer: "ui" },
  ],
  edges: [
    { source: "api-test", target: "api-endpoint", label: "verifies" },
    { source: "ui-test", target: "ui-flow", label: "verifies" },
    { source: "ui-test", target: "role-admin", label: "covers" },
  ],
};

const demoGraphify = {
  nodes: [
    { id: "run_agent", label: "run-agent.sh", community: 1, source_file: "local-agents/run-agent.sh" },
    { id: "dashboard", label: "build_qa_dashboard.py", community: 2, source_file: "scripts/build_qa_dashboard.py" },
    { id: "ui_skill", label: "playwright-ui-change", community: 3, source_file: "skills/playwright-ui-change/SKILL.md" },
  ],
  links: [
    { source: "run_agent", target: "ui_skill" },
    { source: "dashboard", target: "ui_skill" },
  ],
};

function byId(id) {
  return document.getElementById(id);
}

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function statusClass(status) {
  if (status === "pass" || status === "strong" || status === true || status === "fresh") return "good";
  if (status === "fail" || status === "risk" || status === false || status === "stale") return "bad";
  return "warn";
}

function setStatus(message, level = "info") {
  byId("statusPanel").innerHTML = message ? `<span class="pill ${level === "error" ? "bad" : level === "ok" ? "good" : "warn"}">${esc(level)}</span> ${esc(message)}` : "";
}

function table(headers, rows) {
  if (!rows.length) return '<div class="empty">No rows available.</div>';
  return `
    <div class="table-wrap">
      <table>
        <thead><tr>${headers.map((header) => `<th>${esc(header)}</th>`).join("")}</tr></thead>
        <tbody>${rows.join("")}</tbody>
      </table>
    </div>
  `;
}

function bar(label, value, text, klass = "good") {
  const width = Math.max(0, Math.min(100, Number(value) || 0));
  return `
    <div class="bar-row">
      <div><strong>${esc(label)}</strong><span>${esc(text ?? `${width}%`)}</span></div>
      <div class="bar"><i class="${klass}" style="width:${width}%"></i></div>
    </div>
  `;
}

function metric(label, value, detail) {
  return `<div class="card metric"><span>${esc(label)}</span><strong>${esc(value)}</strong><p class="muted">${esc(detail)}</p></div>`;
}

function normalizeDashboard(data) {
  if (!data || typeof data !== "object") return null;
  if (!data.testHealth && !data.coverage && !data.confidence) return null;
  const ui = data.testHealth?.ui || data.testHealth?.playwright || {};
  return {
    ...data,
    testHealth: {
      api: data.testHealth?.api || {},
      ui,
    },
  };
}

function renderOverview() {
  const data = normalizeDashboard(state.dashboard);
  if (!data) {
    byId("overview").innerHTML = '<div class="empty">Upload <strong>dashboard.json</strong> or load the demo to view QA metrics.</div>';
    return;
  }

  const api = data.testHealth.api || {};
  const ui = data.testHealth.ui || {};
  const confidence = data.confidence || {};
  const graph = data.graphs?.testImpact || {};
  const graphify = data.graphs?.graphify || {};
  const visuals = data.visuals || {};
  const coverage = visuals.coverage || {};
  const duplicate = data.duplicates || {};
  const stale = data.graphs?.stale ? "stale" : "fresh";

  byId("overview").innerHTML = `
    <section class="grid">
      ${metric("API health", api.status || "unknown", `${api.tests || 0} tests, ${api.failures || 0} failures`)}
      ${metric("UI automation health", ui.status || "unknown", `${(ui.failedTests || []).length} failed tests${ui.framework ? ` · ${ui.framework}` : ""}`)}
      ${metric("Test graph", `${graph.nodes || 0}/${graph.edges || 0}`, "nodes / relationships")}
      ${metric("Graphify", `${graphify.nodes || 0}/${graphify.communities || 0}`, `nodes / communities · ${stale}`)}
    </section>
    <section class="grid two">
      <div class="card">
        <h2>Quality Snapshot</h2>
        ${bar("Release confidence", confidence.score || 0, confidence.score ?? "unknown", statusClass(confidence.status))}
        ${bar("API health", api.status === "pass" ? 100 : 0, api.status || "unknown", statusClass(api.status))}
        ${bar("UI automation health", ui.status === "pass" ? 100 : 0, ui.status || "unknown", statusClass(ui.status))}
        ${bar("Mapped coverage", coverage.percent || 0, `${coverage.covered || 0}/${coverage.total || 0}`, (coverage.percent || 0) === 100 ? "good" : "warn")}
        ${bar("Duplicate safety", visuals.duplicateSignal?.clearPercent ?? 100, `${duplicate.nearDuplicateCount || 0} risk`, (duplicate.nearDuplicateCount || 0) ? "warn" : "good")}
        ${bar("Graph freshness", data.graphs?.stale ? 0 : 100, stale, statusClass(stale))}
      </div>
      <div class="card">
        <h2>Work Item Mapping</h2>
        <p><strong>${esc(data.ticket?.api?.key || "API")}</strong> · ${esc(data.ticket?.api?.summary || "No API work item loaded")}</p>
        <p class="muted"><strong>${esc(data.ticket?.ui?.key || "UI")}</strong> · ${esc(data.ticket?.ui?.summary || "No UI work item loaded")}</p>
        <h3>Confidence reasons</h3>
        <ul>${(confidence.reasons || ["No confidence reasons available."]).map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
      </div>
    </section>
  `;
}

function renderCoverage() {
  const data = normalizeDashboard(state.dashboard);
  if (!data) {
    byId("coverage").innerHTML = '<div class="empty">Upload dashboard JSON to view coverage and gap signals.</div>';
    return;
  }
  const coverage = data.coverage || {};
  const endpoints = (coverage.endpointCoverage || []).map((item) => `
    <tr><td>Endpoint</td><td>${esc(item.endpoint)}</td><td><span class="pill ${statusClass(item.covered)}">${item.covered ? "covered" : "gap"}</span></td></tr>
  `);
  const roles = (coverage.roleCoverage || []).map((item) => `
    <tr><td>Actor/Role</td><td>${esc(item.role)}</td><td><span class="pill ${statusClass(item.covered)}">${item.covered ? "covered" : "gap"}</span></td></tr>
  `);
  const orphanRows = (coverage.orphanTestCases || []).map((item) => `
    <tr><td>${esc(item.layer || "")}</td><td>${esc(item.label || item.id)}</td><td>${esc(item.path || "")}</td></tr>
  `);
  byId("coverage").innerHTML = `
    <section class="grid two">
      <div class="card">
        <h2>Mapped Targets</h2>
        ${table(["Type", "Target", "Status"], [...endpoints, ...roles])}
      </div>
      <div class="card">
        <h2>Gap Signals</h2>
        <ul>${(coverage.gaps || ["No deterministic gaps found."]).map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
      </div>
    </section>
    <section class="card">
      <h2>Orphan Test Cases</h2>
      ${table(["Layer", "Test", "Path"], orphanRows)}
    </section>
  `;
}

function renderDuplicates() {
  const data = normalizeDashboard(state.dashboard);
  if (!data) {
    byId("duplicates").innerHTML = '<div class="empty">Upload dashboard JSON to view duplicate and overlap candidates.</div>';
    return;
  }
  const candidates = data.duplicates?.candidates || [];
  const rows = candidates.map((item) => `
    <tr>
      <td>${esc(item.left)}<p class="muted">${esc(item.leftPath || "")}</p></td>
      <td>${esc(item.right)}<p class="muted">${esc(item.rightPath || "")}</p></td>
      <td>${esc(item.score ?? "")}</td>
      <td><span class="pill ${item.signal === "near-duplicate review" ? "bad" : "warn"}">${esc(item.signal || "review")}</span><p class="muted">${esc((item.sharedTerms || []).join(", "))}</p></td>
    </tr>
  `);
  byId("duplicates").innerHTML = `
    <section class="grid two">
      ${metric("Near-duplicate risks", data.duplicates?.nearDuplicateCount || 0, "review before adding tests")}
      ${metric("Coverage siblings", data.duplicates?.coverageSiblingCount || 0, "intentional positive/negative variants")}
    </section>
    <section class="card">
      <h2>Duplicate And Overlap Candidates</h2>
      ${table(["Test A", "Test B", "Score", "Signal"], rows)}
    </section>
  `;
}

function normalizeGraph(data, type) {
  if (!data || typeof data !== "object") return { nodes: [], edges: [] };
  const nodes = Array.isArray(data.nodes) ? data.nodes.filter((node) => node && node.id != null).map((node) => ({ ...node, id: String(node.id) })) : [];
  const rawEdges = Array.isArray(data.edges) ? data.edges : Array.isArray(data.links) ? data.links : [];
  const edges = rawEdges
    .map((edge) => ({
      source: String(typeof edge.source === "object" ? edge.source.id : edge.source),
      target: String(typeof edge.target === "object" ? edge.target.id : edge.target),
      label: edge.label || edge.kind || "",
    }))
    .filter((edge) => edge.source && edge.target && edge.source !== "undefined" && edge.target !== "undefined");
  return { nodes, edges, type };
}

function colorFor(node, index) {
  const layer = node.layer || node.file_type || node.community_name || "";
  if (layer === "api") return "#2563eb";
  if (layer === "ui") return "#14b8a6";
  if (layer === "shared") return "#8b5cf6";
  const palette = ["#2563eb", "#14b8a6", "#8b5cf6", "#f59e0b", "#ec4899", "#22c55e", "#64748b"];
  const key = Number(node.community ?? index);
  return palette[Math.abs(key) % palette.length];
}

function graphNodeText(node) {
  return [
    node.id,
    node.label,
    node.kind,
    node.layer,
    node.path,
    node.source_file,
    node.detail,
    node.file_type,
    node.community_name,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function graphNodeTitle(node) {
  return String(node.label || node.id);
}

function buildAdjacency(graph, nodeById) {
  const adjacency = new Map();
  const connectedEdges = [];
  for (const node of graph.nodes) adjacency.set(node.id, new Set());
  for (const edge of graph.edges) {
    if (!nodeById.has(edge.source) || !nodeById.has(edge.target)) continue;
    adjacency.get(edge.source).add(edge.target);
    adjacency.get(edge.target).add(edge.source);
    connectedEdges.push(edge);
  }
  return { adjacency, connectedEdges };
}

function graphSearchResults(graph, query) {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return [];
  return graph.nodes.filter((node) => graphNodeText(node).includes(normalized)).slice(0, 12);
}

function graphInspectorHtml(node, neighbors, incidentEdges) {
  const neighborRows = neighbors.slice(0, 30).map((neighbor) => {
    const edge = incidentEdges.find((item) => item.source === neighbor.id || item.target === neighbor.id) || {};
    return `<li><strong>${esc(graphNodeTitle(neighbor))}</strong><span>${esc(neighbor.kind || neighbor.layer || neighbor.file_type || edge.label || "related")}</span></li>`;
  });
  return `
    <strong>${esc(graphNodeTitle(node))}</strong>
    <p class="muted">${esc([node.kind, node.layer, node.file_type, node.community_name].filter(Boolean).join(" · "))}</p>
    <p class="muted">${esc(node.path || node.source_file || node.detail || "")}</p>
    <div class="inspector-meta">
      <span class="pill good">${neighbors.length} connected node${neighbors.length === 1 ? "" : "s"}</span>
      <span class="pill warn">${incidentEdges.length} relationship${incidentEdges.length === 1 ? "" : "s"}</span>
    </div>
    ${neighborRows.length ? `<ul class="connected-list">${neighborRows.join("")}</ul>` : '<p class="muted">No direct connections found for this node.</p>'}
  `;
}

function renderGraph(containerId, graph, title) {
  const container = byId(containerId);
  if (!graph.nodes.length) {
    container.innerHTML = `<div class="empty">Upload ${esc(title)} JSON to view the graph.</div>`;
    return;
  }
  const ui = state.graphUi[containerId] || { query: "", focusNodeId: "" };
  const nodeById = new Map(graph.nodes.map((node) => [node.id, node]));
  const { adjacency, connectedEdges } = buildAdjacency(graph, nodeById);
  if (ui.focusNodeId && !nodeById.has(ui.focusNodeId)) ui.focusNodeId = "";
  const matches = graphSearchResults(graph, ui.query);
  const visibleIds = new Set();
  let renderMode = "overview";
  if (ui.focusNodeId) {
    renderMode = "connected";
    visibleIds.add(ui.focusNodeId);
    for (const id of adjacency.get(ui.focusNodeId) || []) visibleIds.add(id);
  } else if (ui.query.trim()) {
    renderMode = "search";
    for (const match of matches) {
      visibleIds.add(match.id);
      for (const id of adjacency.get(match.id) || []) visibleIds.add(id);
    }
  }
  const width = 1180;
  const height = 560;
  const hasActiveFilter = ui.focusNodeId || ui.query.trim();
  const visibleNodes = hasActiveFilter ? graph.nodes.filter((node) => visibleIds.has(node.id)) : graph.nodes;
  const nodes = visibleNodes.slice(0, 180);
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = connectedEdges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)).slice(0, 360);
  const groups = [...new Set(nodes.map((node) => node.layer || node.community_name || node.file_type || "graph"))];
  const positioned = nodes.map((node, index) => {
    const group = groups.indexOf(node.layer || node.community_name || node.file_type || "graph");
    const angle = (index / Math.max(nodes.length, 1)) * Math.PI * 2;
    const ring = 120 + (group % 4) * 52;
    const cx = width / 2 + Math.cos(angle) * ring + (group - groups.length / 2) * 44;
    const cy = height / 2 + Math.sin(angle) * ring;
    return { ...node, x: Math.max(30, Math.min(width - 30, cx)), y: Math.max(30, Math.min(height - 30, cy)) };
  });
  const lookup = new Map(positioned.map((node) => [node.id, node]));
  const degree = new Map();
  for (const edge of edges) {
    degree.set(edge.source, (degree.get(edge.source) || 0) + 1);
    degree.set(edge.target, (degree.get(edge.target) || 0) + 1);
  }
  const labelCap = nodes.length > 80 ? 24 : 60;
  const edgeMarkup = edges
    .map((edge) => {
      const source = lookup.get(edge.source);
      const target = lookup.get(edge.target);
      if (!source || !target) return "";
      return `<line class="graph-edge" x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}"></line>`;
    })
    .join("");
  const nodeMarkup = positioned
    .map((node, index) => `
      <g data-node="${esc(node.id)}">
        <circle class="graph-node ${node.id === ui.focusNodeId ? "selected" : ""}" cx="${node.x}" cy="${node.y}" r="${node.kind === "test_case" ? 8 : 6}" fill="${colorFor(node, index)}"></circle>
        ${index < labelCap && (nodes.length <= 80 || (degree.get(node.id) || 0) > 1) ? `<text class="graph-label" x="${node.x + 9}" y="${node.y + 4}">${esc(String(node.label || node.id).slice(0, 28))}</text>` : ""}
      </g>
    `)
    .join("");
  const resultMarkup = ui.query.trim()
    ? matches.length
      ? matches
          .map((node) => `<button class="result-chip" type="button" data-search-result="${esc(node.id)}">${esc(graphNodeTitle(node).slice(0, 54))}</button>`)
          .join("")
      : '<span class="muted">No matching nodes found.</span>'
    : '<span class="muted">Search by spec, test, endpoint, role, helper, path, or node id.</span>';
  const focusedNode = ui.focusNodeId ? nodeById.get(ui.focusNodeId) : null;
  const focusedNeighbors = focusedNode ? [...(adjacency.get(focusedNode.id) || [])].map((id) => nodeById.get(id)).filter(Boolean) : [];
  const focusedEdges = focusedNode ? connectedEdges.filter((edge) => edge.source === focusedNode.id || edge.target === focusedNode.id) : [];
  const nodeDetail = hasActiveFilter ? `${nodes.length} shown in ${renderMode} view` : `${Math.max(0, graph.nodes.length - nodes.length)} hidden after cap`;
  const edgeDetail = hasActiveFilter ? `${edges.length} shown in ${renderMode} view` : `${Math.max(0, graph.edges.length - edges.length)} hidden after cap`;
  container.innerHTML = `
    <section class="grid">
      ${metric("Nodes", graph.nodes.length, nodeDetail)}
      ${metric("Edges", graph.edges.length, edgeDetail)}
      ${metric("Groups", groups.length, "layers / communities")}
      ${metric("Render mode", renderMode, renderMode === "connected" ? "selected node neighborhood" : "client-side SVG")}
    </section>
    <section class="card">
      <div class="graph-heading">
        <h2>${esc(title)}</h2>
        <button class="secondary compact" type="button" data-clear-graph>Clear Focus</button>
      </div>
      <div class="graph-tools">
        <label>
          <span>Search test/spec</span>
          <input type="search" value="${esc(ui.query)}" placeholder="Example: role-aware-mockserver spec" data-graph-search>
        </label>
        <div class="search-results">${resultMarkup}</div>
      </div>
      <div class="graph-shell">
        <svg class="graph-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)}">${edgeMarkup}${nodeMarkup}</svg>
        <div class="inspector" id="${containerId}Inspector">${focusedNode ? graphInspectorHtml(focusedNode, focusedNeighbors, focusedEdges) : "Select a node to inspect details and show only its connected nodes."}</div>
      </div>
    </section>
  `;
  container.querySelector("[data-graph-search]").addEventListener("input", (event) => {
    const nextQuery = event.target.value;
    state.graphUi[containerId].query = nextQuery;
    state.graphUi[containerId].focusNodeId = "";
    renderGraph(containerId, graph, title);
    const input = container.querySelector("[data-graph-search]");
    input.focus();
    input.setSelectionRange(nextQuery.length, nextQuery.length);
  });
  container.querySelector("[data-graph-search]").addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    const first = graphSearchResults(graph, state.graphUi[containerId].query)[0];
    if (!first) return;
    state.graphUi[containerId].focusNodeId = first.id;
    renderGraph(containerId, graph, title);
  });
  container.querySelector("[data-clear-graph]").addEventListener("click", () => {
    state.graphUi[containerId].query = "";
    state.graphUi[containerId].focusNodeId = "";
    renderGraph(containerId, graph, title);
  });
  container.querySelectorAll("[data-search-result]").forEach((el) => {
    el.addEventListener("click", () => {
      state.graphUi[containerId].focusNodeId = el.dataset.searchResult;
      renderGraph(containerId, graph, title);
    });
  });
  container.querySelectorAll("[data-node]").forEach((el) => {
    el.addEventListener("click", () => {
      const node = lookup.get(el.dataset.node);
      state.graphUi[containerId].focusNodeId = node.id;
      renderGraph(containerId, graph, title);
    });
  });
}

function renderPreview() {
  if (!state.htmlPreview) {
    byId("preview").innerHTML = '<div class="empty">Upload a generated HTML file to preview it in a sandboxed frame.</div>';
    return;
  }
  byId("preview").innerHTML = `
    <section class="card">
      <h2>Sandboxed HTML Preview</h2>
      <p class="muted">Previewing ${esc(state.loaded.htmlPreview)}. Scripts are sandboxed and cannot submit forms.</p>
      <iframe class="html-frame" sandbox="allow-scripts" srcdoc="${esc(state.htmlPreview)}"></iframe>
    </section>
  `;
}

function renderAll() {
  renderOverview();
  renderCoverage();
  renderDuplicates();
  renderGraph("testGraph", normalizeGraph(state.testGraph, "test"), "Test-Impact Graph");
  renderGraph("graphify", normalizeGraph(state.graphify, "graphify"), "Graphify Graph");
  renderPreview();
}

function classifyJson(data) {
  if (normalizeDashboard(data)) return "dashboard";
  if (Array.isArray(data.nodes) && (Array.isArray(data.edges) || Array.isArray(data.links))) {
    return data.links ? "graphify" : "testGraph";
  }
  return "";
}

async function readFile(file, expectedType) {
  if (!file) return;
  if (file.size > MAX_FILE_BYTES) {
    setStatus(`${file.name} is larger than 5 MB. Use a smaller artifact or trim the graph first.`, "error");
    return;
  }
  const text = await file.text();
  try {
    if (expectedType === "html") {
      state.htmlPreview = text;
      state.loaded.htmlPreview = file.name;
      setStatus(`Loaded HTML preview: ${file.name}`, "ok");
    } else {
      const data = JSON.parse(text);
      const type = expectedType || classifyJson(data);
      if (!type || !["dashboard", "testGraph", "graphify"].includes(type)) {
        setStatus(`${file.name} is valid JSON, but it does not look like a supported QA artifact.`, "error");
        return;
      }
      state[type] = data;
      state.loaded[type] = file.name;
      setStatus(`Loaded ${type}: ${file.name}`, "ok");
    }
    renderAll();
  } catch (error) {
    setStatus(`${file.name} could not be parsed: ${error.message}`, "error");
  }
}

function wireUpload(id, type) {
  byId(id).addEventListener("change", (event) => {
    readFile(event.target.files[0], type);
    event.target.value = "";
  });
}

function wireTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      byId(button.dataset.tab).classList.add("active");
    });
  });
}

function init() {
  wireUpload("dashboardFile", "dashboard");
  wireUpload("testGraphFile", "testGraph");
  wireUpload("graphifyFile", "graphify");
  wireUpload("htmlFile", "html");
  wireTabs();
  byId("loadDemo").addEventListener("click", () => {
    state.dashboard = demoDashboard;
    state.testGraph = demoTestGraph;
    state.graphify = demoGraphify;
    state.loaded.dashboard = "demo dashboard";
    state.loaded.testGraph = "demo test graph";
    state.loaded.graphify = "demo graphify graph";
    setStatus("Loaded built-in demo data. Upload generated artifacts to replace it.", "ok");
    renderAll();
  });
  renderAll();
}

init();
