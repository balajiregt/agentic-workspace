#!/usr/bin/env python3
"""Build a private, self-contained HTML page from saved evidence results."""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import subprocess
import sys
import webbrowser
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
RESULTS = WORKSPACE / "evidence" / "results"
LABELS = {"api-workspace": "API workspace", "mockserver": "Role-aware mockserver", "playwright-agent": "Playwright Agent"}

CSS = """
:root{--bg:#f6f5f1;--surface:#fff;--ink:#16181c;--muted:#5f656d;--line:#dcd9d0;--accent:#0b6e51;--task:#6b8afd;--warn:#9a5b00;--bad:#a8321f;--soft:#eeece6;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0f1113;--surface:#16191c;--ink:#ecebe6;--muted:#9a9f9b;--line:#2b3034;--accent:#43c89a;--task:#8ea6ff;--warn:#f0b54a;--bad:#ff8a73;--soft:#1d2125;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",sans-serif}
main{width:min(100% - 32px,1100px);margin:0 auto;padding:40px 0 64px}
h1{font:600 32px/1.15 ui-serif,Georgia,serif;margin:0 0 6px}h2{font:600 22px/1.2 ui-serif,Georgia,serif;margin:0}
h3{font:600 12px/1.4 ui-monospace,Menlo,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:22px 0 10px}
.lede{color:var(--muted);max-width:70ch;margin:0 0 28px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:24px;margin-bottom:20px}
.head{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:baseline}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:13px}.muted{color:var(--muted)}
.row{display:grid;grid-template-columns:minmax(0,190px) minmax(0,1fr) auto;gap:14px;align-items:center;padding:10px 0;border-top:1px solid var(--line)}
.bar{position:relative;height:14px;background:var(--soft);border-radius:7px;overflow:hidden;display:flex}
.bar span{height:100%}.bar .i{background:var(--accent)}.bar .t{background:var(--task)}
.ratio{font:600 20px/1 ui-serif,Georgia,serif;text-align:right;min-width:90px}
.legend{display:flex;gap:16px;font-size:13px;color:var(--muted);margin-top:8px;flex-wrap:wrap}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.badge{display:inline-block;font:600 12px/1 ui-monospace,Menlo,monospace;padding:5px 8px;border-radius:999px;background:var(--soft);color:var(--ink)}
.badge.ok{color:var(--accent)}.badge.warn{color:var(--warn)}.badge.bad{color:var(--bad)}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:8px 6px;border-top:1px solid var(--line);vertical-align:top}
th{font:600 11px/1.4 ui-monospace,Menlo,monospace;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
code{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;background:var(--soft);padding:2px 6px;border-radius:4px;overflow-wrap:anywhere}
.note{font-size:13px;color:var(--muted);margin-top:10px}
.scroll{overflow-x:auto;max-width:100%}.head .mono{overflow-wrap:anywhere;min-width:0}
@media (max-width:640px){table,thead,tbody,tr,td{display:block}thead{display:none}tr{border-top:1px solid var(--line);padding:8px 0}td{border:0;padding:3px 0}}
@media (max-width:640px){.row{grid-template-columns:1fr}.ratio{text-align:left}}
"""


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def load_results(base: Path) -> dict[str, list[dict]]:
    by_project: dict[str, list[dict]] = {}
    for path in sorted(base.glob("*/*.json")):
        if path.parent.name == "trials":
            continue
        try:
            record = json.loads(path.read_text())
        except ValueError:
            continue
        by_project.setdefault(record.get("project", path.parent.name), []).append(record)
    return by_project


def trial_summary(base: Path) -> list[dict]:
    if not (base / "trials").is_dir():
        return []
    result = subprocess.run(["node", str(WORKSPACE / "evidence/trials/trials.mjs"), "summary"], cwd=WORKSPACE,
                            capture_output=True, text=True, env={**__import__("os").environ, "EVIDENCE_RESULTS": str(base)})
    if result.returncode:
        return [{"error": result.stderr.strip()}]
    return json.loads(result.stdout).get("groups", [])


def context_section(records: list[dict]) -> str:
    rows = [r for r in records if r.get("kind") == "context"]
    if not rows:
        return '<p class="muted">No context measurement yet. Run <code>npm run evidence</code>.</p>'
    out = []
    for r in rows:
        s, corpus = r["selected"], r["corpus"]["tokens"] or 1
        scale = max(corpus, s["tokens"])
        i_pct, t_pct = s["instructionTokens"] / scale * 100, s["taskTokens"] / scale * 100
        ratio = f"{r['corpusToSelectedRatio']}×" if r.get("corpusToSelectedRatio") else "n/a"
        summary = (f"{s['tokens']:,} selected vs {r['corpus']['tokens']:,} in the project "
                   f"({r['selectedAsPercentOfCorpus']}%)" if r.get("selectedAsPercentOfCorpus") is not None else "incomplete")
        out.append(f'<div class="row"><div><strong>{esc(r["profile"])}</strong><div class="muted" style="font-size:13px">{esc(summary)}</div></div>'
                   f'<div class="bar" role="img" aria-label="{esc(summary)}"><span class="i" style="width:{i_pct:.2f}%"></span><span class="t" style="width:{t_pct:.2f}%"></span></div>'
                   f'<div class="ratio" title="project size divided by selected context">{esc(ratio)}</div></div>')
        if r["status"] != "complete":
            out.append(f'<p class="note">Incomplete: {esc("; ".join(r["missing"] + r["notes"]))}</p>')
    out.append('<div class="legend"><span><i style="background:var(--accent)"></i>Instructions (routing + one skill)</span>'
               '<span><i style="background:var(--task)"></i>Task files</span><span><i style="background:var(--soft);border:1px solid var(--line)"></i>Rest of the project</span>'
               '<span>Ratio = project size ÷ selected context; below 1× means guidance costs more than the whole project</span></div>')
    return "".join(out)


def native_section(records: list[dict]) -> str:
    rows = [r for r in records if r.get("kind") == "native"]
    if not rows:
        return '<p class="muted">No project evidence configured.</p>'
    out = ['<div class="scroll"><table><thead><tr><th>Source</th><th>Status</th><th>Result</th><th>Recorded</th></tr></thead><tbody>']
    for r in rows:
        status = r["status"]
        cls = {"imported": "ok", "not-run": "warn"}.get(status, "bad")
        if status == "imported":
            h = r["headline"]
            if "groups" in h and isinstance(h["groups"], dict):
                result = "; ".join(f"{k}: {v.get('passed')}/{v.get('attempted')} passed, mean journey {round(v['meanJourneyAndOracleMs'] or 0)} ms"
                                   for k, v in h["groups"].items())
            elif "killed" in h:
                result = (f"{h['faults']} faults: {h['killed']} killed, {h['survived']} survived; "
                          f"{h['greenBaselines']}× green baseline of {h['testsPerBaseline']} tests; "
                          f"restored {'green' if h['restoredGreen'] else 'NOT green'}, source {'unchanged' if h['originalUnchanged'] else 'CHANGED'}")
            elif "capabilities" in h:
                result = f"{h['task']}: " + "; ".join(f"{k}: {v['pass']} pass, {v['fail']} fail, {v['needsReview']} need review of {v['cases']}" for k, v in h["capabilities"].items())
            else:
                result = f"{h.get('passed')}/{h.get('tests')} passed, {h.get('failures')} failed, {h.get('errors')} errors, {h.get('skipped')} skipped"
            kind = f'<div class="muted" style="font-size:12px">{esc(r.get("evidenceKind"))} · <code>{esc(r.get("source"))}</code></div>'
            when = esc((r.get("generatedAt") or r.get("sourceModifiedAt") or "")[:10])
        else:
            result = esc("; ".join(r.get("notes", [])))
            kind, when = "", "—"
        out.append(f'<tr><td><strong>{esc(r["profile"])}</strong><div class="muted" style="font-size:12px">{esc(r["description"])}</div></td>'
                   f'<td><span class="badge {cls}">{esc(status)}</span></td><td>{esc(result) if status == "imported" else result}{kind}</td><td class="mono">{when}</td></tr>')
    out.append("</tbody></table></div>")
    return "".join(out)


def trials_section(project: str, groups: list[dict]) -> str:
    tasks = json.loads((WORKSPACE / "evidence/trials/tasks.json").read_text())
    mine = {t["id"] for t in tasks if t["target"].get("evidenceProject") == project}
    if not mine:
        return '<p class="muted">No trial task defined for this project yet (add one to <code>evidence/trials/tasks.json</code>).</p>'
    rows = [g for g in groups if g.get("taskId") in mine]
    if not rows:
        first = sorted(mine)[0]
        return (f'<p class="muted">Tasks: {", ".join(f"<code>{esc(t)}</code>" for t in sorted(mine))}. No trials recorded yet. '
                f'Start one with <code>npm run evidence:trial -- prepare --task {esc(first)}</code>.</p>')
    out = ['<div class="scroll"><table><thead><tr><th>Task</th><th>Model</th><th>Kind</th><th>Agent alone</th><th>Agent + guidance</th><th>Paired</th></tr></thead><tbody>']
    for g in rows:
        cell = lambda s: f"{s['correct']}/{s['trials']} completed" + (f", median {round(s['medianElapsedMs'] / 60000, 1)} min" if s.get("medianElapsedMs") else "")  # noqa: E731
        out.append(f"<tr><td><code>{esc(g['taskId'])}</code></td><td>{esc(g['model'])} {esc(g['modelVersion'])}</td><td>{esc(g['evidenceKind'])}</td>"
                   f"<td>{esc(cell(g['baseline']))}</td><td>{esc(cell(g['framework']))}</td><td>{esc(g['pairedRepeats'])}</td></tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def build(base: Path) -> str:
    results = load_results(base)
    groups = trial_summary(base)
    manifest = json.loads((WORKSPACE / "evidence/projects.json").read_text())
    cards = []
    for project in manifest["projects"]:
        records = results.get(project, [])
        recorded = max((r.get("recordedAt", "") for r in records), default="")
        source = next((r.get("source") for r in records if r.get("kind") == "context"), None) or {}
        rev = f"{source.get('commit') or 'unknown'}{' + uncommitted changes' if source.get('uncommittedChanges') else ''}"
        cards.append(f'<section class="card" aria-labelledby="{project}"><div class="head"><h2 id="{project}">{esc(LABELS.get(project, project))}</h2>'
                     f'<span class="muted mono">{esc(manifest["projects"][project]["root"])} @ {esc(rev)} · measured {esc(recorded[:16].replace("T", " "))}</span></div>'
                     f'<h3>Context: workspace guidance vs the whole project</h3>{context_section(records)}'
                     f'<h3>Agent trials: the agent alone vs with guidance</h3>{trials_section(project, groups)}'
                     f'<h3>Project evidence</h3>{native_section(records)}</section>')
    generated = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Workspace evidence</title><style>{CSS}</style></head><body><main>'
            f'<h1>Workspace evidence</h1><p class="lede">Does the agentic workspace deliver what it claims? Per project: how much context an agent needs, '
            f'whether workspace guidance changes agent results, and each project\'s own evidence. Private and local; generated {esc(generated)}. '
            f'Token counts are approximate; unknown values are shown as unknown, never zero.</p>'
            f'{"".join(cards)}</main></body></html>')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS)
    parser.add_argument("--open", action="store_true", help="open the page in the default browser")
    args = parser.parse_args(argv)
    base = args.results_dir.resolve()
    base.mkdir(parents=True, exist_ok=True)
    out = base / "dashboard.html"
    out.write_text(build(base), encoding="utf-8")
    print(f"Wrote {out}")
    if args.open:
        webbrowser.open(out.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
