#!/usr/bin/env python3
"""Apply the CRM-Scale pre-registered decision rules (PREREGISTRATION.md) to collected runs.

Reads evidence/results/{assessments,authoring,mutation-proofs} for crm-scale tasks, pairs
the two arms of each run, and writes evidence/results/crm-scale-analysis.json. Runs are
grouped by model family and never pooled across models.
"""
from __future__ import annotations

import json
import math
import random
import statistics
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
RESULTS = WORKSPACE / "evidence/results"
ARMS = ("baseline", "framework")


def wilson(k: int, n: int) -> list[float] | None:
    if not n:
        return None
    z, p = 1.96, k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def bootstrap_median(diffs: list[float], rounds: int = 5000) -> list[float] | None:
    if not diffs:
        return None
    rng = random.Random(20261115)
    medians = sorted(statistics.median(rng.choices(diffs, k=len(diffs))) for _ in range(rounds))
    return [round(medians[int(0.025 * rounds)], 4), round(medians[int(0.975 * rounds) - 1], 4)]


def family(row: dict) -> str:
    version = str(row.get("modelVersion") or "").lower()
    return next((f for f in ("opus", "sonnet", "haiku", "fable") if f in version), version or "unknown")


def load(kind_dir: str, prefix: str) -> dict[str, dict[str, dict]]:
    """{model family: {run id: {arm: row}}} for complete, unexcluded pairs; exclusions listed separately."""
    grouped: dict[str, dict[str, dict]] = {}
    for path in sorted((RESULTS / kind_dir).glob("*.json")):
        row = json.loads(path.read_text())
        if not str(row.get("taskId", "")).startswith(prefix):
            continue
        run_id = row["trialId"].rsplit("-", 1)[0]
        grouped.setdefault(family(row), {}).setdefault(run_id, {})[row["arm"]] = row
    return grouped


def excluded(row: dict) -> str | None:
    agent = row.get("agent") or {}
    if agent.get("workspaceAccess"):
        return "touched the workspace"
    return None


def effort(rows: list[dict], correct_key) -> dict:
    agents = [r.get("agent") or {} for r in rows]
    cost = [a.get("costUsd") for a in agents if a.get("costUsd") is not None]
    successes = sum(bool(correct_key(r)) for r in rows)
    pick = lambda key: [v for v in (key(a) for a in agents) if v is not None]
    med = lambda values: round(statistics.median(values), 2) if values else None
    return {"runs": len(rows), "medianCostUsd": med(cost), "totalCostUsd": round(sum(cost), 2) if cost else None,
            "costPerSuccessUsd": round(sum(cost) / successes, 2) if cost and successes else None,
            "medianInputTokens": med(pick(lambda a: a.get("inputTokens"))),
            "medianOutputTokens": med(pick(lambda a: a.get("outputTokens"))),
            "medianToolCalls": med(pick(lambda a: (a.get("effort") or {}).get("toolCalls"))),
            "medianFilesRead": med(pick(lambda a: (a.get("effort") or {}).get("distinctFilesRead"))),
            "medianTurns": med(pick(lambda a: a.get("turns"))),
            "medianDurationS": med(pick(lambda a: (a.get("durationMs") or 0) / 1000 or None))}


def efficiency(pairs: list[tuple[dict, dict]]) -> dict:
    diffs = [(b["agent"]["costUsd"] - f["agent"]["costUsd"]) for b, f in pairs
             if (b.get("agent") or {}).get("costUsd") is not None and (f.get("agent") or {}).get("costUsd") is not None]
    cheaper = sum(d > 0 for d in diffs)
    dearer = sum(d < 0 for d in diffs)
    ci = bootstrap_median(diffs)
    verdict = "no measurable difference"
    if diffs and cheaper >= math.ceil(2 * len(diffs) / 3) and ci and ci[0] > 0:
        verdict = "Playwright Agent adds efficiency"
    elif diffs and dearer >= math.ceil(2 * len(diffs) / 3) and ci and ci[1] < 0:
        verdict = "Playwright Agent costs more"
    return {"pairs": len(diffs), "frameworkCheaper": cheaper, "frameworkDearer": dearer,
            "medianSavingUsd": round(statistics.median(diffs), 4) if diffs else None, "medianSavingCI95": ci, "verdict": verdict}


def consistency(pairs: list[tuple[dict, dict]], correct_key) -> dict:
    by_task: dict[str, dict[str, list[bool]]] = {}
    for b, f in pairs:
        for arm, row in (("baseline", b), ("framework", f)):
            by_task.setdefault(row["taskId"], {}).setdefault(arm, []).append(bool(correct_key(row)))
    return {arm: {"tasksAllCorrect": sum(all(v[arm]) for v in by_task.values() if arm in v), "tasks": len(by_task)} for arm in ARMS}


def split(grouped_runs: dict[str, dict]) -> tuple[list[tuple[dict, dict]], list[dict]]:
    pairs, dropped = [], []
    for run_id, arms in sorted(grouped_runs.items()):
        if set(arms) != set(ARMS):
            dropped.append({"run": run_id, "reason": "incomplete pair"})
            continue
        reasons = [excluded(arms[a]) for a in ARMS]
        if any(reasons):
            dropped.append({"run": run_id, "reason": "; ".join(r for r in reasons if r)})
            continue
        pairs.append((arms["baseline"], arms["framework"]))
    return pairs, dropped


def assessment(runs: dict[str, dict]) -> dict:
    pairs, dropped = split(runs)
    totals = {arm: {"gaps": 0, "found": 0, "falseAlarms": 0, "covered": 0, "exact": 0} for arm in ARMS}
    wins = losses = ties = 0
    for b, f in pairs:
        for arm, row in (("baseline", b), ("framework", f)):
            t = totals[arm]
            t["gaps"] += row["gaps"]; t["found"] += row["gapsFound"]; t["falseAlarms"] += row["falseAlarms"]
            t["covered"] += row["covered"]; t["exact"] += bool(row["exact"])
        rb, rf = b["gapsFound"] / b["gaps"], f["gapsFound"] / f["gaps"]
        if (rf > rb and f["falseAlarms"] <= b["falseAlarms"]) or (rf == rb and f["falseAlarms"] < b["falseAlarms"]):
            wins += 1
        elif (rb > rf and b["falseAlarms"] <= f["falseAlarms"]) or (rf == rb and b["falseAlarms"] < f["falseAlarms"]):
            losses += 1
        else:
            ties += 1
    recall = {arm: (t["found"] / t["gaps"] if t["gaps"] else None) for arm, t in totals.items()}
    for arm, t in totals.items():
        t["recall"] = round(recall[arm], 3) if recall[arm] is not None else None
        t["recallCI95"] = wilson(t["found"], t["gaps"])
        t["falseAlarmRate"] = round(t["falseAlarms"] / t["covered"], 3) if t["covered"] else None
    ceiling = bool(pairs) and totals["baseline"]["found"] == totals["baseline"]["gaps"] and totals["baseline"]["falseAlarms"] == 0
    verdict = "no measurable difference"
    if pairs and recall["framework"] - recall["baseline"] >= 0.10 and wins > losses:
        verdict = "Playwright Agent adds accuracy"
    elif pairs and recall["baseline"] - recall["framework"] >= 0.10 and losses > wins:
        verdict = "Playwright Agent reduces accuracy"
    correct = lambda r: r["exact"]
    return {"pairs": len(pairs), "excluded": dropped, "totals": totals, "pairWins": wins, "pairLosses": losses, "pairTies": ties,
            "ceiling": ceiling, "verdict": verdict,
            "skillUsed": sum(bool((f.get("agent") or {}).get("guidanceReceived")) for _, f in pairs),
            "effort": {arm: effort([p[i] for p in pairs], correct) for i, arm in enumerate(ARMS)},
            "efficiency": efficiency(pairs) if verdict == "no measurable difference" else None,
            "consistency": consistency(pairs, correct)}


def authoring(runs: dict[str, dict]) -> dict:
    pairs, dropped = split(runs)
    fit = lambda r: bool(r["appUnchanged"] and not r["filesOutsideProject"] and r["usesProjectFixture"] and not r["rawRequestsInSpecs"])
    count = lambda key, i: sum(bool(key(p[i])) for p in pairs)
    correct = {arm: count(lambda r: r["correct"], i) for i, arm in enumerate(ARMS)}
    fits = {arm: count(fit, i) for i, arm in enumerate(ARMS)}
    verdict = "no measurable difference"
    if correct["framework"] - correct["baseline"] >= 2 or (abs(correct["framework"] - correct["baseline"]) <= 1 and fits["framework"] - fits["baseline"] >= 4):
        verdict = "Playwright Agent adds value"
    elif correct["baseline"] - correct["framework"] >= 2 or (abs(correct["framework"] - correct["baseline"]) <= 1 and fits["baseline"] - fits["framework"] >= 4):
        verdict = "Playwright Agent reduces value"
    detail = {arm: {"correct": correct[arm], "correctCI95": wilson(correct[arm], len(pairs)), "frameworkFit": fits[arm],
                    "appUnchanged": count(lambda r: r["appUnchanged"], i), "faultCaught": count(lambda r: r["faultCaught"], i),
                    "suiteGreen": count(lambda r: r["suiteGreen"], i), "usesProjectFixture": count(lambda r: r["usesProjectFixture"], i)}
              for i, arm in enumerate(ARMS)}
    ok = lambda r: r["correct"]
    return {"pairs": len(pairs), "excluded": dropped, "arms": detail, "verdict": verdict,
            "effort": {arm: effort([p[i] for p in pairs], ok) for i, arm in enumerate(ARMS)},
            "efficiency": efficiency(pairs) if verdict == "no measurable difference" else None,
            "consistency": consistency(pairs, ok)}


def mutation(runs: dict[str, dict]) -> dict:
    pairs, dropped = split(runs)
    proven = lambda r: bool(r["verdictCorrect"] and r["fullyProven"])
    count = lambda key, i: sum(bool(key(p[i])) for p in pairs)
    good = {arm: count(proven, i) for i, arm in enumerate(ARMS)}
    safe = {arm: count(lambda r: r["safeMethod"], i) for i, arm in enumerate(ARMS)}
    verdict = "no measurable difference"
    if good["framework"] - good["baseline"] >= 2 or (abs(good["framework"] - good["baseline"]) <= 1 and safe["framework"] - safe["baseline"] >= 4):
        verdict = "Playwright Agent adds value"
    elif good["baseline"] - good["framework"] >= 2 or (abs(good["framework"] - good["baseline"]) <= 1 and safe["baseline"] - safe["framework"] >= 4):
        verdict = "Playwright Agent reduces value"
    detail = {arm: {"correctVerdict": count(lambda r: r["verdictCorrect"], i), "fullyProvenCorrect": good[arm],
                    "fullyProvenCI95": wilson(good[arm], len(pairs)), "safeMethod": safe[arm],
                    "editedRealSource": count(lambda r: r["editedRealSource"], i),
                    "usedDisposableCopy": count(lambda r: r["usedDisposableCopy"], i),
                    "independentCheck": count(lambda r: r["independentCheck"], i),
                    "restored": count(lambda r: r["appAndTestsRestored"], i)} for i, arm in enumerate(ARMS)}
    return {"pairs": len(pairs), "excluded": dropped, "arms": detail, "verdict": verdict,
            "effort": {arm: effort([p[i] for p in pairs], proven) for i, arm in enumerate(ARMS)},
            "efficiency": efficiency(pairs) if verdict == "no measurable difference" else None,
            "consistency": consistency(pairs, proven)}


def main(argv: list[str] | None = None) -> int:
    # --prefix crm-tools analyses the tools-first extension (EXTENSION.md) separately; never pooled.
    argv = sys.argv[1:] if argv is None else argv
    base = argv[argv.index("--prefix") + 1] if "--prefix" in argv else "crm-scale"
    rules = "PREREGISTRATION.md" if base == "crm-scale" else "EXTENSION.md"
    report = {"schemaVersion": 1, "rules": f"evidence/trials/crm-scale/{rules}", "prefix": base, "models": {}}
    sources = {"assessment": ("assessments", f"{base}-assessment", assessment),
               "authoring": ("authoring", f"{base}-author", authoring),
               "mutation": ("mutation-proofs", f"{base}-mutation", mutation)}
    for skill, (folder, prefix, fn) in sources.items():
        for model, runs in load(folder, prefix).items():
            report["models"].setdefault(model, {})[skill] = fn(runs)
    out = RESULTS / f"{base}-analysis.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    for model, skills in report["models"].items():
        for skill, r in skills.items():
            eff = r.get("efficiency") or {}
            print(f"{model:6} {skill:10} pairs={r['pairs']:<3} {r['verdict']}" + (f" | efficiency: {eff.get('verdict')}" if eff else ""))
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
