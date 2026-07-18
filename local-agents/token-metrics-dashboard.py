#!/usr/bin/env python3
"""Serve a small HTML dashboard for llama.cpp/Pi token metrics."""

from __future__ import annotations

import argparse
import json
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agentic Workspace Token Metrics</title>
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #627084;
      --line: #d8dee8;
      --accent: #0969da;
      --good: #1a7f37;
      --warn: #bf8700;
      --bad: #cf222e;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0d1117;
        --panel: #161b22;
        --text: #e6edf3;
        --muted: #8b949e;
        --line: #30363d;
        --accent: #58a6ff;
      }
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font: 14px/1.45 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    header {
      padding: 20px 24px 12px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 2;
    }
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 650;
      letter-spacing: 0;
    }
    .sub {
      margin-top: 6px;
      color: var(--muted);
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    main { padding: 20px 24px 32px; max-width: 1180px; margin: 0 auto; }
    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(150px, 1fr));
      gap: 12px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 92px;
    }
    .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
    .value { font-size: 24px; font-weight: 700; margin-top: 8px; word-break: break-word; }
    .small-value { font-size: 15px; font-weight: 600; margin-top: 8px; word-break: break-word; }
    .ok { color: var(--good); }
    .warn { color: var(--warn); }
    .bad { color: var(--bad); }
    .bar {
      height: 10px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--line) 70%, transparent);
      overflow: hidden;
      margin-top: 12px;
    }
    .fill { height: 100%; width: 0%; background: var(--accent); transition: width .2s ease; }
    section { margin-top: 18px; }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }
    th, td {
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }
    th { color: var(--muted); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
    tr:last-child td { border-bottom: 0; }
    code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }
    pre {
      margin: 0;
      padding: 12px;
      overflow: auto;
      max-height: 300px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    @media (max-width: 820px) {
      .grid { grid-template-columns: repeat(2, minmax(140px, 1fr)); }
    }
    @media (max-width: 520px) {
      main, header { padding-left: 14px; padding-right: 14px; }
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Agentic Workspace Token Metrics</h1>
    <div class="sub">
      <span id="status">Connecting...</span>
      <span id="updated">Last update: never</span>
      <span id="llamaUrl"></span>
    </div>
  </header>
  <main>
    <div class="grid">
      <div class="card">
        <div class="label">Prompt Tokens</div>
        <div id="promptTokens" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Output Tokens</div>
        <div id="outputTokens" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Total Tokens</div>
        <div id="totalTokens" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Generation Rate</div>
        <div id="tokenRate" class="value">0/s</div>
      </div>
      <div class="card">
        <div class="label">Context Window</div>
        <div id="contextWindow" class="value">-</div>
        <div class="bar"><div id="contextFill" class="fill"></div></div>
      </div>
      <div class="card">
        <div class="label">Max Output Tokens</div>
        <div id="maxTokens" class="value">-</div>
      </div>
      <div class="card">
        <div class="label">Active Slot Tokens</div>
        <div id="activeTokens" class="value">0</div>
      </div>
      <div class="card">
        <div class="label">Model</div>
        <div id="modelName" class="small-value">-</div>
      </div>
    </div>

    <section>
      <table>
        <thead><tr><th>Metric</th><th>Value</th></tr></thead>
        <tbody id="metricsTable"></tbody>
      </table>
    </section>

    <section>
      <h2 class="label">Slots</h2>
      <pre id="slots">[]</pre>
    </section>
  </main>
  <script>
    const fmt = new Intl.NumberFormat();
    function n(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
      return fmt.format(Math.round(Number(value)));
    }
    function set(id, value) { document.getElementById(id).textContent = value; }
    function statusClass(ok) {
      const el = document.getElementById("status");
      el.className = ok ? "ok" : "bad";
    }
    async function refresh() {
      try {
        const response = await fetch("/api/metrics", { cache: "no-store" });
        const data = await response.json();
        statusClass(data.ok);
        set("status", data.ok ? "Connected" : `Disconnected: ${data.error || "unknown"}`);
        set("updated", `Last update: ${new Date().toLocaleTimeString()}`);
        set("llamaUrl", data.llamaUrl || "");
        set("promptTokens", n(data.summary.promptTokens));
        set("outputTokens", n(data.summary.outputTokens));
        set("totalTokens", n(data.summary.totalTokens));
        set("tokenRate", `${Number(data.summary.outputTokensPerSecond || 0).toFixed(2)}/s`);
        set("contextWindow", n(data.config.contextWindow));
        set("maxTokens", n(data.config.maxTokens));
        set("activeTokens", n(data.summary.activeSlotTokens));
        set("modelName", data.config.modelName || data.config.modelId || "-");

        const context = Number(data.config.contextWindow || 0);
        const used = Number(data.summary.activeSlotTokens || data.summary.totalTokens || 0);
        const pct = context ? Math.min(100, (used / context) * 100) : 0;
        document.getElementById("contextFill").style.width = `${pct}%`;

        const rows = data.tokenMetrics.map((item) =>
          `<tr><td><code>${item.name}</code></td><td>${n(item.value)}</td></tr>`
        ).join("");
        document.getElementById("metricsTable").innerHTML = rows || "<tr><td colspan='2'>No token metrics exposed yet</td></tr>";
        document.getElementById("slots").textContent = JSON.stringify(data.slots || [], null, 2);
      } catch (err) {
        statusClass(false);
        set("status", `Dashboard error: ${err.message}`);
      }
    }
    refresh();
    setInterval(refresh, 2000);
  </script>
</body>
</html>
"""


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.expanduser().read_text())
    except Exception:
        return {}


def http_text(url: str, timeout: float = 2.0) -> str:
    with urlopen(url, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")


def http_json(url: str, timeout: float = 2.0):
    return json.loads(http_text(url, timeout))


def parse_prometheus(text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([a-zA-Z_:][a-zA-Z0-9_:]*(?:\{[^}]*\})?)\s+(-?\d+(?:\.\d+)?)", line)
        if not match:
            continue
        name = match.group(1)
        value = float(match.group(2))
        metrics[name] = metrics.get(name, 0.0) + value
    return metrics


def token_metrics(metrics: dict[str, float]) -> list[dict[str, float | str]]:
    items = []
    for name, value in metrics.items():
        lower = name.lower()
        if "token" in lower or "prompt" in lower or "slot" in lower:
            items.append({"name": name, "value": value})
    return sorted(items, key=lambda item: str(item["name"]))


def sum_matching(metrics: dict[str, float], include: tuple[str, ...], exclude: tuple[str, ...] = ()) -> float:
    total = 0.0
    for name, value in metrics.items():
        lower = name.lower()
        if all(part in lower for part in include) and not any(part in lower for part in exclude):
            total += value
    return total


def derive_summary(metrics: dict[str, float], slots) -> dict[str, float]:
    prompt_tokens = sum_matching(metrics, ("prompt", "token"), ("second", "duration", "time"))
    output_tokens = (
        sum_matching(metrics, ("predicted", "token"), ("second", "duration", "time"))
        or sum_matching(metrics, ("completion", "token"), ("second", "duration", "time"))
        or sum_matching(metrics, ("eval", "token"), ("second", "duration", "time"))
    )
    total_tokens = prompt_tokens + output_tokens
    active_slot_tokens = 0.0
    output_tokens_per_second = (
        sum_matching(metrics, ("predicted", "tokens", "seconds"), ("total",))
        or sum_matching(metrics, ("completion", "tokens", "seconds"), ("total",))
    )

    if isinstance(slots, list):
        for slot in slots:
            if not isinstance(slot, dict):
                continue
            prompt_tokens = prompt_tokens or float(slot.get("n_prompt_tokens_processed") or 0)
            for item in slot.get("next_token", []):
                if isinstance(item, dict):
                    output_tokens = output_tokens or float(item.get("n_decoded") or 0)
            if slot.get("is_processing") or slot.get("state") not in (None, "idle"):
                for key in ("n_past", "n_tokens", "n_prompt_tokens", "n_decoded"):
                    value = slot.get(key)
                    if isinstance(value, (int, float)):
                        active_slot_tokens += value

    return {
        "promptTokens": prompt_tokens,
        "outputTokens": output_tokens,
        "totalTokens": total_tokens,
        "activeSlotTokens": active_slot_tokens,
        "outputTokensPerSecond": output_tokens_per_second,
    }


def pi_config(path: Path) -> dict[str, object]:
    data = load_json(path)
    providers = data.get("providers", {})
    for provider in providers.values():
        models = provider.get("models", [])
        if models:
            model = models[0]
            return {
                "provider": provider.get("baseUrl", ""),
                "modelId": model.get("id", ""),
                "modelName": model.get("name", ""),
                "contextWindow": model.get("contextWindow"),
                "maxTokens": model.get("maxTokens"),
            }
    return {}


class Handler(BaseHTTPRequestHandler):
    llama_url = "http://localhost:8080"
    pi_models_path = Path.home() / ".pi/agent/models.json"
    started = time.time()

    def log_message(self, format, *args):  # noqa: A002
        return

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/metrics":
            payload = self.collect()
            self.send_json(payload)
            return

        self.send_json({"error": "not found"}, 404)

    def collect(self) -> dict:
        config = pi_config(self.pi_models_path)
        models = {}
        slots = []
        metrics_text = ""
        error = ""
        ok = True

        try:
            models = http_json(f"{self.llama_url}/v1/models")
        except Exception as exc:
            ok = False
            error = f"/v1/models: {exc}"

        try:
            slots = http_json(f"{self.llama_url}/slots")
        except Exception:
            slots = []

        try:
            metrics_text = http_text(f"{self.llama_url}/metrics")
        except Exception as exc:
            ok = False
            error = error or f"/metrics: {exc}"

        metrics = parse_prometheus(metrics_text)
        if not config:
            config = {"contextWindow": None, "maxTokens": None}
        if isinstance(models, dict) and models.get("data"):
            model = models["data"][0]
            config.setdefault("modelId", model.get("id"))
            config.setdefault("modelName", model.get("id"))

        return {
            "ok": ok,
            "error": error,
            "llamaUrl": self.llama_url,
            "uptimeSeconds": round(time.time() - self.started, 1),
            "config": config,
            "summary": derive_summary(metrics, slots),
            "tokenMetrics": token_metrics(metrics),
            "slots": slots,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--llama-url", default="http://localhost:8080")
    parser.add_argument("--pi-models", default=str(Path.home() / ".pi/agent/models.json"))
    args = parser.parse_args()

    Handler.llama_url = args.llama_url.rstrip("/")
    Handler.pi_models_path = Path(args.pi_models).expanduser()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Token metrics dashboard: http://{args.host}:{args.port}")
    print(f"llama.cpp URL: {Handler.llama_url}")
    print(f"Pi models config: {Handler.pi_models_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping token metrics dashboard")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
