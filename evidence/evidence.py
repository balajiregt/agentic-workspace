#!/usr/bin/env python3
"""Workspace evidence runner: measure one project, or all, and save private results."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "evidence" / "context"))
from measure import load_manifest, measure  # noqa: E402


def results_dir(base: Path | None) -> Path:
    return (base or WORKSPACE / "evidence" / "results").resolve()


def write_result(base: Path, record: dict) -> Path:
    folder = base / record["project"]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{record['kind']}-{record['profile']}.json"
    record = {**record, "recordedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def run_context(projects: list[str], base: Path, manifest: dict) -> list[dict]:
    records = []
    for project in projects:
        for profile in manifest["projects"][project]["contextProfiles"]:
            record = measure(WORKSPACE, project, profile, manifest)
            write_result(base, record)
            records.append(record)
    return records


def print_context(records: list[dict]) -> None:
    print(f"{'project':18} {'profile':18} {'instructions':>12} {'task files':>11} {'selected':>9} {'project corpus':>15} {'share':>7} {'ratio':>7}  status")
    for r in records:
        share = f"{r['selectedAsPercentOfCorpus']}%" if r["selectedAsPercentOfCorpus"] is not None else "n/a"
        ratio = f"{r['corpusToSelectedRatio']}x" if r["corpusToSelectedRatio"] is not None else "n/a"
        s = r["selected"]
        print(f"{r['project']:18} {r['profile']:18} {s['instructionTokens']:>12} {s['taskTokens']:>11} {s['tokens']:>9} {r['corpus']['tokens']:>15} {share:>7} {ratio:>7}  {r['status']}")
        for item in r["missing"]:
            print(f"    missing: {item}")
        for note in r["notes"]:
            print(f"    note: {note}")


def main(argv: list[str] | None = None) -> int:
    manifest = load_manifest(WORKSPACE)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="run", choices=["run", "context"],
                        help="run = all measurements available for the project; context = context only")
    parser.add_argument("--project", default="all", choices=["all", *manifest["projects"]])
    parser.add_argument("--results-dir", type=Path)
    args = parser.parse_args(argv)
    projects = list(manifest["projects"]) if args.project == "all" else [args.project]
    base = results_dir(args.results_dir)
    records = run_context(projects, base, manifest)
    print_context(records)
    print(f"\nSaved to {base.relative_to(WORKSPACE) if base.is_relative_to(WORKSPACE) else base}")
    return 0 if all(r["status"] == "complete" for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
