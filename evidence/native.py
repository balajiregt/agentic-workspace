"""Import each project's own evidence as it is: read the latest output, never rerun or reimplement it."""
from __future__ import annotations

import datetime as dt
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def _mtime(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds")


def read_mutation_campaign(path: Path) -> dict:
    data = json.loads(path.read_text())
    faults = data.get("faults", [])
    outcomes: dict[str, int] = {}
    for fault in faults:
        outcomes[fault.get("status", "unknown")] = outcomes.get(fault.get("status", "unknown"), 0) + 1
    baselines = data.get("baseline") or []
    return {
        "generatedAt": data.get("createdAt"),
        "evidenceKind": "recorded-mutation-campaign",
        "headline": {
            "faults": len(faults), "killed": outcomes.get("killed", 0), "survived": outcomes.get("survived", 0),
            "otherOutcomes": {k: v for k, v in outcomes.items() if k not in ("killed", "survived")},
            "greenBaselines": sum(1 for b in baselines if b.get("status") == "passed"),
            "testsPerBaseline": len(baselines[0].get("tests", [])) if baselines else None,
            "restoredGreen": (data.get("restored") or {}).get("status") == "passed",
            "originalUnchanged": data.get("originalUnchanged"),
        },
        "details": [{"fault": f.get("id"), "requirement": f.get("requirementId"), "outcome": f.get("status"),
                     "attempts": len(f.get("attempts", []))} for f in faults],
    }


def read_pa_evaluation(path: Path) -> dict:
    data = json.loads(path.read_text())
    assessed = [c for c in data.get("capabilities", []) if c.get("cases")]
    return {
        "generatedAt": data.get("generatedAt"),
        "evidenceKind": data.get("evidenceKind"),
        "headline": {"task": data.get("taskId"), "cases": len(data.get("cases", [])),
                     "capabilities": {c["capability"]: {k: c.get(k) for k in ("cases", "pass", "fail", "needsReview", "notAssessed")}
                                      for c in assessed}},
        "limitations": data.get("limitations", [])[:3],
    }


def read_mockserver_benchmark(path: Path) -> dict:
    data = json.loads(path.read_text())
    return {
        "generatedAt": data.get("generatedAt"),
        "evidenceKind": data.get("evidenceKind"),
        "headline": {"groups": data.get("groups"), "revision": data.get("revision"), "dirty": data.get("dirty")},
        "limitations": data.get("limitations", [])[:3],
    }


def read_junit(path: Path) -> dict:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    count = lambda attr: sum(int(s.get(attr, 0)) for s in suites)  # noqa: E731
    tests, failures, errors, skipped = count("tests"), count("failures"), count("errors"), count("skipped")
    return {
        "generatedAt": suites[0].get("timestamp") if suites else None,
        "evidenceKind": "test-execution",
        "headline": {"tests": tests, "passed": tests - failures - errors - skipped,
                     "failures": failures, "errors": errors, "skipped": skipped},
    }


READERS = {"mutation-campaign": read_mutation_campaign, "pa-evaluation": read_pa_evaluation,
           "mockserver-benchmark": read_mockserver_benchmark, "junit": read_junit}


def import_source(workspace: Path, project: str, root: str, source: dict) -> dict:
    record = {"kind": "native", "project": project, "profile": source["name"], "description": source["description"],
              "refreshCommand": source["refreshCommand"]}
    project_root = workspace / root
    matches = sorted((p for p in project_root.glob(source["glob"]) if p.is_file()), key=lambda p: p.stat().st_mtime)
    if not project_root.is_dir():
        return {**record, "status": "unavailable", "notes": ["Project folder is not present in this checkout."]}
    if not matches:
        return {**record, "status": "not-run", "notes": [f"No local output yet; run: {source['refreshCommand']}"]}
    latest = matches[-1]
    try:
        summary = READERS[source["reader"]](latest)
    except (ValueError, KeyError, ET.ParseError) as exc:
        return {**record, "status": "unreadable", "source": str(latest.relative_to(workspace)), "notes": [str(exc)]}
    return {**record, "status": "imported", "source": str(latest.relative_to(workspace)),
            "sourceModifiedAt": _mtime(latest), "available": len(matches), **summary}
