#!/usr/bin/env python3
"""Prepare and collect with/without-workspace agent trials.

prepare  builds two clean copies of the task's project from its last commit, outside
         the workspace: `baseline` without agent guidance and `framework` with the
         project's guidance plus the workspace context profile. Both get one prompt.
start    records when the agent starts work in an arm.
finish   records when the agent has finished.
collect  adds the independent oracle only now, runs the required tests and passes the
         report and metadata to trials.mjs, which validates and stores the trial.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE / "evidence" / "context"))
from measure import load_manifest, resolved_file_list  # noqa: E402

TRIALS = WORKSPACE / "evidence" / "trials"
DEFAULT_OUT = Path.home() / "evidence-trials"
ARMS = ("baseline", "framework")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def load_task(task_id: str) -> dict:
    tasks = json.loads((TRIALS / "tasks.json").read_text())
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise SystemExit(f"Unknown task {task_id}; choose from: {', '.join(t['id'] for t in tasks)}")


def snapshot(root: Path, dest: Path) -> str:
    """Extract the project's committed tree into dest; return its commit."""
    top = Path(git("rev-parse", "--show-toplevel", cwd=root))
    prefix = git("rev-parse", "--show-prefix", cwd=root).rstrip("/")
    commit = git("rev-parse", "HEAD", cwd=top)
    tree = f"HEAD:{prefix}" if prefix else "HEAD"
    data = subprocess.run(["git", "archive", "--format=tar", tree], cwd=top, check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(dest, filter="data")
    return commit


def tree_hash(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file() and ".git" not in p.parts):
        digest.update(path.relative_to(folder).as_posix().encode() + b"\0" + sha256(path.read_bytes()).encode() + b"\n")
    return digest.hexdigest()


def remove_guidance(arm: Path, guidance: list[str]) -> list[str]:
    removed = []
    for name in guidance:
        target = arm / name
        if target.is_dir():
            shutil.rmtree(target)
            removed.append(name + "/")
        elif target.is_file():
            target.unlink()
            removed.append(name)
    for nested in sorted(arm.rglob("*")):  # nested AGENTS.md / CLAUDE.md files
        if nested.is_file() and nested.name in ("AGENTS.md", "CLAUDE.md"):
            removed.append(nested.relative_to(arm).as_posix())
            nested.unlink()
    return removed


def profile_files(profile: dict) -> list[str]:
    files = list(profile.get("instructions", [])) + [profile["task"]]
    if profile.get("resolved") and (WORKSPACE / profile["resolved"]).is_file():
        files.append(profile["resolved"])
        files.extend(resolved_file_list(WORKSPACE, profile["resolved"]))
    files.extend(profile.get("files", []))
    return list(dict.fromkeys(files))


def add_workspace_context(arm: Path, project_root: str, profile: dict) -> list[str]:
    """Copy profile files missing from the snapshot and list them for the agent."""
    added, listed = [], []
    for relative in profile_files(profile):
        source = WORKSPACE / relative
        if not source.is_file():
            continue
        if relative.startswith(project_root + "/"):
            inside = relative[len(project_root) + 1:]
            target = arm / inside
            listed.append(inside)
        else:
            inside = f".workspace-context/{relative}"
            target = arm / inside
            listed.append(inside)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            added.append(inside)
    readme = ["# Workspace context for this task", "",
              "Read these files before changing code. They are the workspace's routing,",
              "skill and task context for this work item.", ""]
    readme += [f"- `{path}`" for path in listed]
    (arm / ".workspace-context").mkdir(exist_ok=True)
    (arm / ".workspace-context/README.md").write_text("\n".join(readme) + "\n")
    pointer = "\n\n## Workspace context\n\nFor the current task, read `.workspace-context/README.md` first.\n"
    agents = arm / "AGENTS.md"
    agents.write_text((agents.read_text() if agents.exists() else "# Agent instructions\n") + pointer)
    return added


def init_repo(arm: Path, source_root: Path) -> None:
    git("init", "-q", cwd=arm)
    exclude = arm / ".git/info/exclude"
    exclude.write_text(exclude.read_text() + "\nnode_modules\n.evidence/\n")
    modules = source_root / "node_modules"
    if modules.is_dir():
        (arm / "node_modules").symlink_to(modules, target_is_directory=True)
    git("add", "-A", cwd=arm)
    git("-c", "user.name=evidence", "-c", "user.email=evidence@localhost", "commit", "-q",
        "-m", "Trial starting point", cwd=arm)


def prompt_text(task: dict) -> str:
    titles = "\n".join(f"- `{t}`" for t in task["requiredTests"])
    return (f"# Task {task['id']}\n\n{task['intent']}\n\n"
            f"Name the required tests exactly as follows, and make them pass:\n\n{titles}\n\n"
            "Work only inside this folder. Do not create or edit anything under `.evidence/`.\n")


def cmd_prepare(args) -> None:
    task = load_task(args.task)
    manifest = load_manifest(WORKSPACE)
    project = task["target"]["evidenceProject"]
    config = manifest["projects"][project]
    profile = config["contextProfiles"][task["target"]["contextProfile"]]
    source_root = WORKSPACE / config["root"]
    out = Path(args.out).expanduser().resolve()
    if out == WORKSPACE or WORKSPACE in out.parents:
        raise SystemExit("Choose an output folder outside the workspace, so the baseline agent cannot read workspace guidance.")
    run_id = re.sub(r"[^a-zA-Z0-9_-]", "-", f"{task['id']}-r{args.repeat}-{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}")
    run = out / run_id
    base = run / ".snapshot"
    base.mkdir(parents=True)
    commit = snapshot(source_root, base)
    target_revision = tree_hash(base)
    prompt = prompt_text(task)
    (run / "PROMPT.md").write_text(prompt)
    arms = {}
    for arm_name in ARMS:
        arm = run / arm_name
        shutil.copytree(base, arm)
        if arm_name == "baseline":
            changed = {"guidanceRemoved": remove_guidance(arm, manifest["guidancePaths"])}
        else:
            changed = {"contextAdded": add_workspace_context(arm, config["root"], profile)}
        init_repo(arm, source_root)
        arms[arm_name] = {"path": str(arm), **changed, "startedAt": None, "finishedAt": None}
    shutil.rmtree(base)
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=source_root,
                                capture_output=True, text=True).stdout.strip())
    record = {"schemaVersion": 1, "runId": run_id, "taskId": task["id"], "project": project,
              "repeat": args.repeat, "sourceCommit": commit, "sourceHadUncommittedChanges": dirty,
              "targetRevision": target_revision, "promptSha256": sha256(prompt.encode()),
              "contextProfile": task["target"]["contextProfile"], "oracle": task["target"]["oracle"],
              "createdAt": now(), "arms": arms}
    (run / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    order = list(ARMS) if args.repeat % 2 == 0 else list(reversed(ARMS))
    print(f"Prepared {run}\n")
    print(f"Prompt: {run / 'PROMPT.md'} (identical for both arms)")
    print(f"Suggested order for repeat {args.repeat}: {' then '.join(order)}\n")
    for arm_name in order:
        print(f"  npm run evidence:trial -- start  --run {run} --arm {arm_name}")
        print(f"  # open {run / arm_name} in your agent, paste PROMPT.md, let it finish")
        print(f"  npm run evidence:trial -- finish --run {run} --arm {arm_name}")
        print(f"  npm run evidence:trial -- collect --run {run} --arm {arm_name} --model MODEL --model-version VERSION\n")
    if dirty:
        print("Note: the source project has uncommitted changes; the trial uses its last commit.")


def load_run(path: str) -> tuple[Path, dict]:
    run = Path(path).expanduser().resolve()
    return run, json.loads((run / "run.json").read_text())


def save_run(run: Path, record: dict) -> None:
    (run / "run.json").write_text(json.dumps(record, indent=2) + "\n")


def cmd_mark(args, field: str) -> None:
    run, record = load_run(args.run)
    arm = record["arms"][args.arm]
    if field == "finishedAt" and not arm["startedAt"]:
        raise SystemExit("Run `start` for this arm first.")
    if arm[field]:
        raise SystemExit(f"{field} is already recorded for {args.arm}; prepare a new run to repeat it.")
    arm[field] = now()
    save_run(run, record)
    print(f"{args.arm} {field} = {arm[field]}")


def run_oracle(arm: Path, record: dict, task: dict, report_arg: str | None) -> Path:
    evidence = arm / ".evidence"
    evidence.mkdir(exist_ok=True)
    report = evidence / "report.json"
    oracle = record["oracle"]
    if oracle["type"] == "playwright":
        shutil.copy2(WORKSPACE / oracle["config"], evidence / "oracle.config.ts")
        env = {**os.environ, "EVIDENCE_REQUIRED_TESTS": json.dumps(task["requiredTests"]), "EVIDENCE_REPORT": str(report)}
        binary = arm / "node_modules/.bin/playwright"
        if not binary.exists():
            raise SystemExit("Playwright is not installed for this project; run npm ci in the source project first.")
        subprocess.run([str(binary), "test", "-c", ".evidence/oracle.config.ts"], cwd=arm, env=env)
    elif oracle["type"] == "junit":
        if not report_arg:
            steps = "\n  ".join(oracle["steps"])
            raise SystemExit(f"This task's oracle is run by hand in the arm:\n  {steps}\nThen pass --report <surefire XML>.")
        subprocess.run([sys.executable, str(TRIALS / "junit_to_report.py"), str(report), report_arg], check=True)
    else:
        raise SystemExit(f"Unknown oracle type {oracle['type']}")
    if not report.is_file():
        raise SystemExit("The oracle produced no report; the trial cannot be collected.")
    return report


def cmd_collect(args) -> None:
    run, record = load_run(args.run)
    arm_record = record["arms"][args.arm]
    if not (arm_record["startedAt"] and arm_record["finishedAt"]):
        raise SystemExit("Record `start` and `finish` for this arm before collecting.")
    task = load_task(record["taskId"])
    arm = Path(arm_record["path"])
    report = run_oracle(arm, record, task, args.report)
    usage = None
    if args.usage_input is not None or args.usage_output is not None:
        usage = {"inputTokens": args.usage_input, "outputTokens": args.usage_output, "source": args.usage_source}
    metadata = {"trialId": f"{record['runId']}-{args.arm}", "taskId": record["taskId"], "arm": args.arm,
                "evidenceKind": args.evidence_kind, "model": args.model, "modelVersion": args.model_version,
                "targetRevision": record["targetRevision"], "promptSha256": record["promptSha256"],
                "repeat": record["repeat"], "startedAt": arm_record["startedAt"], "finishedAt": arm_record["finishedAt"],
                "humanCorrectionMs": None, "incorrectChanges": None, "reviewerEvidence": None,
                "usage": usage, "pricing": None}
    metadata_path = arm / ".evidence/metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    env = {**os.environ, "EVIDENCE_RESULTS": str(Path(args.results_dir).resolve()) if args.results_dir else str(WORKSPACE / "evidence/results")}
    result = subprocess.run(["node", str(TRIALS / "trials.mjs"), "collect", str(metadata_path), str(report)],
                            cwd=WORKSPACE, env=env, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(result.stderr.strip() or "Trial collection failed")
    print(result.stdout.strip())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--task", required=True)
    p.add_argument("--repeat", type=int, default=0)
    p.add_argument("--out", default=str(DEFAULT_OUT))
    for name in ("start", "finish"):
        s = sub.add_parser(name)
        s.add_argument("--run", required=True)
        s.add_argument("--arm", choices=ARMS, required=True)
    c = sub.add_parser("collect")
    c.add_argument("--run", required=True)
    c.add_argument("--arm", choices=ARMS, required=True)
    c.add_argument("--model", required=True)
    c.add_argument("--model-version", required=True)
    c.add_argument("--evidence-kind", choices=("live-agent", "scripted-validation"), default="live-agent")
    c.add_argument("--report", help="JUnit/Surefire XML for tasks whose oracle is run by hand")
    c.add_argument("--usage-input", type=int)
    c.add_argument("--usage-output", type=int)
    c.add_argument("--usage-source")
    c.add_argument("--results-dir")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        cmd_prepare(args)
    elif args.command == "start":
        cmd_mark(args, "startedAt")
    elif args.command == "finish":
        cmd_mark(args, "finishedAt")
    else:
        cmd_collect(args)


if __name__ == "__main__":
    main()
