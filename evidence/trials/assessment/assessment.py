#!/usr/bin/env python3
"""Coverage-assessment trials: variants, frozen answer key, scoring and key validation.

validate  proves each planted gap is real: on a fresh copy of the project, the
          weakened suite stays green under the matching app fault while the
          original suite fails it; every variant suite is green on the clean app.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
CASES = Path(__file__).resolve().parent / "cases.json"
STATUSES = ("covered", "partial", "missing")


def load_cases() -> dict:
    return json.loads(CASES.read_text())


def apply_edits(root: Path, edits: list[dict]) -> None:
    for edit in edits:
        path = root / edit["file"]
        text = path.read_text()
        count = text.count(edit["find"])
        if count != 1:
            raise SystemExit(f"Edit target must occur exactly once in {edit['file']} (found {count}): {edit['find'][:60]!r}")
        path.write_text(text.replace(edit["find"], edit["replace"]))


def truth(cases: dict, variant: str) -> dict[str, str]:
    result = dict(cases["baseTruth"])
    for criterion in cases["variants"][variant]["gaps"]:
        result[criterion] = "gap"
    return result


def criteria(cases: dict) -> list[dict]:
    return json.loads((WORKSPACE / cases["criteriaSource"]).read_text())["requirements"]


def normalise(status) -> str | None:
    text = str(status or "").strip().lower().replace("_", " ").replace("-", " ")
    if text in ("covered", "fully covered", "full", "pass", "yes"):
        return "covered"
    if text.startswith("partial"):
        return "partial"
    if text in ("missing", "not covered", "uncovered", "gap", "none", "no", "absent"):
        return "missing"
    return None


def normalise_verdict(value) -> str | None:
    text = str(value or "").strip().lower().replace("_", "-").replace(" ", "-")
    if text in ("caught", "detected", "killed", "yes"):
        return "caught"
    if text in ("not-caught", "not-detected", "undetected", "survived", "missed", "no"):
        return "not-caught"
    return None


def score(answer: dict, cases: dict, variant: str) -> dict:
    """Score one assessment.json against the frozen key for a variant."""
    key = truth(cases, variant)
    entries = {str(e.get("id")): e for e in (answer.get("criteria") or []) if isinstance(e, dict)}
    rows, gaps, found, covered, false_alarms, unanswered = [], 0, 0, 0, 0, 0
    for criterion, expected in key.items():
        entry = entries.get(criterion)
        status = normalise(entry.get("status")) if entry else None
        if status is None:
            unanswered += 1
        if expected == "gap":
            gaps += 1
            hit = status in ("partial", "missing")
            found += hit
            outcome = "found" if hit else ("unanswered" if status is None else "missed")
        elif expected == "covered":
            covered += 1
            alarm = status in ("partial", "missing")
            false_alarms += alarm
            outcome = "false-alarm" if alarm else ("unanswered" if status is None else "correct")
        else:
            outcome = "not-scored"
        rows.append({"criterion": criterion, "truth": expected, "answer": status, "outcome": outcome,
                     "test": (entry or {}).get("test"), "reason": (entry or {}).get("reason")})
    return {"variant": variant, "gaps": gaps, "gapsFound": found, "covered": covered, "falseAlarms": false_alarms,
            "unanswered": unanswered, "allCriteriaAnswered": unanswered == 0,
            "exact": found == gaps and false_alarms == 0 and unanswered == 0, "criteria": rows}


# ---------- key validation ----------

def _run_suite(root: Path) -> bool:
    report = root / ".evidence/suite.json"
    report.parent.mkdir(exist_ok=True)
    config = root / ".evidence/suite.config.ts"
    shutil.copy2(WORKSPACE / "evidence/trials/oracles/crm-suite.playwright.config.ts", config)
    env = {**os.environ, "EVIDENCE_REPORT": str(report)}
    subprocess.run([str(root / "node_modules/.bin/playwright"), "test", "-c", str(config)],
                   cwd=root, env=env, capture_output=True, text=True, timeout=600)
    data = json.loads(report.read_text())
    stats = data.get("stats", {})
    return stats.get("unexpected", 1) == 0 and stats.get("expected", 0) > 0


def _copy(source: Path, dest: Path, edits: list[dict], fault: dict | None) -> Path:
    sys.path.insert(0, str(WORKSPACE / "evidence/trials"))
    import runner  # noqa: E402

    dest.mkdir(parents=True)
    runner.snapshot(source, dest)
    (dest / "node_modules").symlink_to(source / "node_modules", target_is_directory=True)
    apply_edits(dest, edits)
    if fault:
        apply_edits(dest, [fault])
    return dest


def validate(output: Path | None = None) -> dict:
    cases = load_cases()
    source = WORKSPACE / "qa/playwright-agent"
    checks = []
    with tempfile.TemporaryDirectory(prefix="assessment-key-") as temp:
        base = Path(temp)
        for variant, spec in cases["variants"].items():
            green = _run_suite(_copy(source, base / f"{variant}-clean", spec["edits"], None))
            checks.append({"variant": variant, "check": "variant suite green on clean app", "expected": True, "observed": green})
            for gap in spec["gaps"]:
                fault = cases["faults"][gap]
                weak = _run_suite(_copy(source, base / f"{variant}-{gap}-weak", spec["edits"], fault))
                original = _run_suite(_copy(source, base / f"{variant}-{gap}-orig", [], fault))
                checks.append({"variant": variant, "check": f"{gap}: weakened suite stays green under fault",
                               "expected": True, "observed": weak})
                if gap != "DASHBOARD-METRIC":
                    checks.append({"variant": variant, "check": f"{gap}: original suite catches the fault",
                                   "expected": False, "observed": original})
        for case_id, case in cases.get("mutationCases", {}).items():
            spec = cases["variants"][case["variant"]]
            green = _run_suite(_copy(source, base / f"{case_id}-proof", spec["edits"], cases["faults"][case["fault"]]))
            checks.append({"variant": case["variant"], "check": f"{case_id} ({case['truth']}): suite under {case['fault']} fault",
                           "expected": case["truth"] == "not-caught", "observed": green})
    ok = all(c["expected"] == c["observed"] for c in checks)
    result = {"ok": ok, "checks": checks}
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--out", type=Path, default=WORKSPACE / "evidence/results/assessments/key-validation.json")
    args = parser.parse_args(argv)
    result = validate(args.out)
    for c in result["checks"]:
        mark = "ok " if c["expected"] == c["observed"] else "FAIL"
        print(f"{mark} {c['variant']}  {c['check']}  (observed {'green' if c['observed'] else 'red'})")
    print("answer key VALID" if result["ok"] else "answer key INVALID")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
