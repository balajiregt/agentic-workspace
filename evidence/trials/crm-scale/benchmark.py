#!/usr/bin/env python3
"""CRM-Scale benchmark: prove the frozen answer key with faults, before any agent runs.

Every check runs the CRM-Scale suite in a disposable copy of examples/crm-scale with
exact edits applied: suite variants from cases.json and/or one fault from faults.json.
The real source is never changed.

validate  runs five kinds of check and writes a JSON report:
  clean       every variant suite is green on the unchanged app
  natural     the unweakened suite stays green under each natural-gap fault (a real gap)
  active      an independent oracle fails under each natural-gap fault, so the fault is
              really active (a no-op fault would also leave the suite green)
  covered     the unweakened suite fails under each covered criterion's fault
  planted     each variant suite stays green under the fault of each gap it plants
  collateral  each variant suite still fails under every other covered fault
              (so a variant weakens only what the key says it weakens)
  mutation    each mutation question's truth (caught / not caught) on its variant
sweep     runs the unweakened suite against every fault and lists the failing tests
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PROJECT = WORKSPACE / "qa/playwright-agent"
APP_DIR = "examples/crm-scale"
RESULTS = WORKSPACE / "evidence/results/assessments"


def load(name: str) -> dict:
    return json.loads((HERE / name).read_text())


def apply_edits(root: Path, edits: list[dict]) -> None:
    for edit in edits:
        path = root / edit["file"]
        text = path.read_text()
        count = text.count(edit["find"])
        if count != 1:
            raise RuntimeError(f"edit target must occur exactly once in {edit['file']} (found {count}): {edit['find'][:60]!r}")
        path.write_text(text.replace(edit["find"], edit["replace"]))


def committed_copy(dest: Path) -> str:
    """Extract the committed examples/crm-scale tree (never the working tree) into dest."""
    sys.path.insert(0, str(WORKSPACE / "evidence/trials"))
    import runner  # noqa: E402

    (dest / APP_DIR).mkdir(parents=True)
    commit = runner.snapshot(PROJECT / APP_DIR, dest / APP_DIR)
    (dest / "node_modules").symlink_to(PROJECT / "node_modules", target_is_directory=True)
    return commit


class Runner:
    """Runs suites in parallel, one port and one copy per job."""

    def __init__(self, base: Path, pristine: Path, jobs: int, workers: int):
        self.base, self.pristine, self.workers = base, pristine, workers
        self.ports = list(range(4310, 4310 + jobs))
        self.lock = threading.Lock()
        self.count = 0

    def run(self, name: str, edits: list[dict], oracle: bool = False, specs: list[str] | None = None) -> dict:
        with self.lock:
            port = self.ports.pop()
            self.count += 1
        try:
            root = self.base / name
            shutil.copytree(self.pristine, root, symlinks=True)
            apply_edits(root, edits)
            spec_args = list(specs or [])
            if oracle:
                shutil.copy2(HERE / "oracles/natural-gaps.spec.ts", root / APP_DIR / "tests/zz-oracle.spec.ts")
                spec_args = ["tests/zz-oracle.spec.ts"]
            report = root / "report.json"
            env = {**os.environ, "CRM_SCALE_PORT": str(port), "CRM_SCALE_REPORT": str(report),
                   "CRM_SCALE_WORKERS": str(self.workers), "CI": ""}
            subprocess.run([str(root / "node_modules/.bin/playwright"), "test", "-c", str(root / APP_DIR / "playwright.config.ts"), *spec_args],
                           cwd=root / APP_DIR, env=env, capture_output=True, text=True, timeout=900)
            data = json.loads(report.read_text())
            failed = []

            def walk(suite):
                for child in suite.get("suites", []):
                    walk(child)
                for spec in suite.get("specs", []):
                    for t in spec["tests"]:
                        if any(r["status"] not in ("passed", "skipped") for r in t["results"]):
                            failed.append(f"{spec['file']} › {spec['title']}")
            for s in data.get("suites", []):
                walk(s)
            stats = data.get("stats", {})
            shutil.rmtree(root, ignore_errors=True)
            return {"green": not failed and stats.get("expected", 0) > 0, "failed": failed,
                    "passed": stats.get("expected", 0), "skipped": stats.get("skipped", 0)}
        finally:
            with self.lock:
                self.ports.append(port)


def plan(cases: dict, faults: dict, kinds: set[str]) -> list[dict]:
    fault_edits = lambda f: faults[f]["edits"]
    checks = []
    variants = cases["variants"]
    if "clean" in kinds:
        for v, spec in variants.items():
            checks.append({"kind": "clean", "variant": v, "fault": None, "expectGreen": True, "edits": spec["edits"]})
    if "natural" in kinds:
        for crit, f in cases["naturalGaps"].items():
            checks.append({"kind": "natural", "variant": "A", "criterion": crit, "fault": f, "expectGreen": True, "edits": fault_edits(f)})
    if "active" in kinds:
        for crit, f in cases["naturalGaps"].items():
            checks.append({"kind": "active", "variant": "-", "criterion": crit, "fault": f, "expectGreen": False,
                           "edits": fault_edits(f), "oracle": True})
        checks.append({"kind": "active", "variant": "-", "criterion": None, "fault": None, "expectGreen": True, "edits": [], "oracle": True})
    if "covered" in kinds:
        for crit, f in cases["coveredFaults"].items():
            checks.append({"kind": "covered", "variant": "A", "criterion": crit, "fault": f, "expectGreen": False, "edits": fault_edits(f)})
    for v, spec in variants.items():
        for crit, f in cases["coveredFaults"].items():
            planted = crit in spec["gaps"]
            kind = "planted" if planted else "collateral"
            if kind in kinds and spec["edits"]:
                checks.append({"kind": kind, "variant": v, "criterion": crit, "fault": f, "expectGreen": planted,
                               "edits": spec["edits"] + fault_edits(f)})
    if "mutation" in kinds:  # each mutation question's truth, proven on its own variant
        for case_id, case in cases.get("mutationCases", {}).items():
            checks.append({"kind": "mutation", "variant": case["variant"], "criterion": case_id, "fault": case["fault"],
                           "expectGreen": case["truth"] == "not-caught",
                           "edits": variants[case["variant"]]["edits"] + fault_edits(case["fault"])})
    return checks


def validate(kinds: set[str], jobs: int, workers: int, out: Path | None) -> dict:
    cases, faults = load("cases.json"), load("faults.json")["faults"]
    checks = plan(cases, faults, kinds)
    with tempfile.TemporaryDirectory(prefix="crm-scale-key-") as temp:
        base = Path(temp)
        commit = committed_copy(base / "pristine")
        runner = Runner(base, base / "pristine", jobs, workers)

        def one(i_check):
            i, c = i_check
            name = f"{i:03d}-{c['kind']}-{c['variant']}-{c.get('criterion') or 'suite'}"
            result = runner.run(name, c["edits"], c.get("oracle", False), c.get("specs"))
            if c.get("specs") and result["green"]:  # the subset passed: confirm on the full suite
                result = runner.run(name + "-full", c["edits"], c.get("oracle", False))
            ok = result["green"] == c["expectGreen"]
            if c.get("oracle") and c.get("criterion"):  # the failing oracle test must be this criterion's
                ok = ok and all(c["criterion"] in t for t in result["failed"])
            print(f"{'ok  ' if ok else 'FAIL'} {c['kind']:<10} {c['variant']}  {c.get('criterion') or '-':<26} "
                  f"{c['fault'] or 'no fault':<28} expected {'green' if c['expectGreen'] else 'red'}, "
                  f"observed {'green' if result['green'] else 'red'}"
                  + (f"  [{'; '.join(result['failed'][:2])}]" if result["failed"] and c["expectGreen"] else ""), flush=True)
            return {**{k: v for k, v in c.items() if k not in ("edits", "oracle", "specs")}, "observedGreen": result["green"], "ok": ok,
                    "failedTests": result["failed"], "passed": result["passed"], "skipped": result["skipped"]}

        first = [c for c in checks if c["kind"] != "collateral"]
        later = [c for c in checks if c["kind"] == "collateral"]
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            results = list(pool.map(one, enumerate(first)))
        # A collateral check only needs to show the variant still fails under the fault, so it
        # runs the spec files that caught that fault in the unweakened suite (full suite if green).
        caught_by = {r["fault"]: sorted({t.split(" › ")[0] for t in r["failedTests"]})
                     for r in results if r["kind"] == "covered"}
        for c in later:
            files = caught_by.get(c["fault"])
            if files:
                c["specs"] = [f"tests/{f}" for f in files]
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            results += list(pool.map(one, enumerate(later, start=len(first))))
    report = {"ok": all(r["ok"] for r in results), "commit": commit, "kinds": sorted(kinds),
              "checks": len(results), "failures": sum(not r["ok"] for r in results), "results": results}
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"answer key {'VALID' if report['ok'] else 'INVALID'}: {report['checks'] - report['failures']}/{report['checks']} checks as expected")
    return report


def sweep(jobs: int, workers: int) -> None:
    faults = load("faults.json")["faults"]
    with tempfile.TemporaryDirectory(prefix="crm-scale-sweep-") as temp:
        base = Path(temp)
        committed_copy(base / "pristine")
        runner = Runner(base, base / "pristine", jobs, workers)

        def one(f):
            r = runner.run(f, faults[f]["edits"])
            print(f"{f:<30} {'NOT CAUGHT' if r['green'] else 'caught by ' + str(len(r['failed']))}", flush=True)
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            list(pool.map(one, sorted(faults)))


def freeze() -> dict:
    """Record SHA-256 hashes of every pre-registered input, plus the key validation result."""
    import hashlib
    sys.path.insert(0, str(WORKSPACE / "evidence/trials"))
    import runner  # noqa: E402

    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    tasks = [t for t in json.loads((WORKSPACE / "evidence/trials/tasks.json").read_text()) if t["id"].startswith("crm-scale-")]
    validation = RESULTS / "crm-scale-key-validation.json"
    report = json.loads(validation.read_text()) if validation.is_file() else {}
    frozen = {"schemaVersion": 1, "frozenAt": runner.now(),
              "playwrightAgentCommit": runner.git("rev-parse", "HEAD", cwd=PROJECT),
              "appTreeHash": runner.git("rev-parse", f"HEAD:{APP_DIR}", cwd=PROJECT),
              "files": {name: digest(path) for name, path in {
                  "cases.json": HERE / "cases.json", "faults.json": HERE / "faults.json",
                  "PREREGISTRATION.md": HERE / "PREREGISTRATION.md", "analyze.py": HERE / "analyze.py",
                  "oracles/natural-gaps.spec.ts": HERE / "oracles/natural-gaps.spec.ts",
                  "crm-scale.playwright.config.ts": WORKSPACE / "evidence/trials/oracles/crm-scale.playwright.config.ts",
                  "acceptance-criteria.json": PROJECT / APP_DIR / "requirements/acceptance-criteria.json"}.items()},
              "tasksSha256": hashlib.sha256(json.dumps(tasks, sort_keys=True).encode()).hexdigest(), "tasks": len(tasks),
              "keyValidation": {"ok": report.get("ok"), "checks": report.get("checks"), "commit": report.get("commit")}}
    if not frozen["keyValidation"]["ok"]:
        raise SystemExit("The answer key has not been validated; run `benchmark.py validate` first.")
    if frozen["keyValidation"]["commit"] != frozen["playwrightAgentCommit"]:
        raise SystemExit("The key was validated against a different Playwright Agent commit; validate again.")
    (HERE / "freeze.json").write_text(json.dumps(frozen, indent=2) + "\n")
    return frozen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--kinds", default="clean,natural,active,covered,planted,collateral,mutation")
    v.add_argument("--jobs", type=int, default=2)
    v.add_argument("--workers", type=int, default=3)
    v.add_argument("--out", type=Path, default=RESULTS / "crm-scale-key-validation.json")
    s = sub.add_parser("sweep")
    s.add_argument("--jobs", type=int, default=2)
    s.add_argument("--workers", type=int, default=3)
    sub.add_parser("freeze", help="hash the pre-registered inputs after a VALID key validation")
    args = parser.parse_args(argv)
    if args.command == "freeze":
        print(json.dumps(freeze(), indent=2))
        return 0
    if args.command == "sweep":
        sweep(args.jobs, args.workers)
        return 0
    report = validate(set(args.kinds.split(",")), args.jobs, args.workers, args.out)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
