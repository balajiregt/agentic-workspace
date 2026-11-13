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
sys.path.insert(0, str(Path(__file__).resolve().parent / "assessment"))
import assessment  # noqa: E402

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
    # Claude Code reads CLAUDE.md and .claude/skills rather than AGENTS.md and .agents/skills.
    # Bridge them the same way the workspace does, so every agent sees the same guidance.
    if not (arm / "CLAUDE.md").exists():
        (arm / "CLAUDE.md").write_text("@AGENTS.md\n")
        added.append("CLAUDE.md")
    if (arm / ".agents/skills").is_dir() and not (arm / ".claude/skills").exists():
        (arm / ".claude").mkdir(exist_ok=True)
        (arm / ".claude/skills").symlink_to("../.agents/skills", target_is_directory=True)
        added.append(".claude/skills -> ../.agents/skills")
    return added


def init_repo(arm: Path, source_root: Path) -> None:
    git("init", "-q", cwd=arm)
    exclude = arm / ".git/info/exclude"
    exclude.write_text(exclude.read_text() + "\nnode_modules\n.evidence/\n")
    for modules in [source_root / "node_modules", *source_root.glob("*/node_modules")]:
        relative = modules.relative_to(source_root)
        if modules.is_dir() and (arm / relative.parent).is_dir() and not (arm / relative).exists():
            (arm / relative).symlink_to(modules, target_is_directory=True)
            with exclude.open("a") as handle:
                handle.write(f"{relative.as_posix()}\n")
    git("add", "-A", cwd=arm)
    git("-c", "user.name=evidence", "-c", "user.email=evidence@localhost", "commit", "-q",
        "-m", "Trial starting point", cwd=arm)


def prompt_text(task: dict) -> str:
    if task.get("kind") == "mutation-proof":
        return (f"# Task {task['id']}\n\n{task['intent']}\n\n"
                "Prove your answer by execution, not only by reading the code. When you finish, the application "
                "and the tests must be exactly as you found them.\n\n"
                "Write `verdict.json` at the repository root in exactly this shape:\n\n"
                '```json\n{"verdict": "caught | not-caught", "evidence": "what you ran and observed", '
                '"method": "how you introduced and observed the regression"}\n```\n\n'
                "Work only inside this folder. Do not create or edit anything under `.evidence/`.\n")
    if task.get("kind") == "assessment":
        return (f"# Task {task['id']}\n\n{task['intent']}\n\n"
                "Do not change, create or run tests, and do not modify any file except `assessment.json`.\n\n"
                "Write `assessment.json` at the repository root in exactly this shape, with one entry per criterion id:\n\n"
                '```json\n{"criteria": [{"id": "LOGIN-VALID", "status": "covered | partial | missing", '
                '"test": "test title or null", "assertion": "assertion or helper that proves it, or null", '
                '"reason": "one sentence"}]}\n```\n\n'
                "Work only inside this folder. Do not create or edit anything under `.evidence/`.\n")
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
    if task.get("kind") in ("assessment", "mutation-proof"):
        cases = assessment.load_cases()
        assessment.apply_edits(base, cases["variants"][task["variant"]]["edits"])
    if task.get("kind") == "assessment":
        items = [{"id": c["id"], "criterion": c["criterion"]} for c in assessment.criteria(cases)]
        (base / "criteria.json").write_text(json.dumps({"criteria": items}, indent=2) + "\n")
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


# Read-only inspection, running tests and type checks, and stopping the sample app.
# Agents chain commands (`cat a; head b`) and prefix env vars, so each piece must be allowed.
AGENT_TOOLS = ["Read", "Edit", "Write", "Glob", "Grep",
               "Bash(cat:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)", "Bash(ls:*)", "Bash(find:*)",
               "Bash(grep:*)", "Bash(rg:*)", "Bash(sed -n:*)", "Bash(sort:*)", "Bash(pwd)", "Bash(echo:*)",
               "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)",
               "Bash(node:*)", "Bash(npx playwright:*)", "Bash(npx tsc:*)", "Bash(npm run:*)", "Bash(npm test:*)",
               "Bash(cd:*)", "Bash(APP_BASE_URL=*)", "Bash(PORT=*)", "Bash(pkill -f:*)", "Bash(lsof:*)", "Bash(sleep:*)", "Bash(curl -s:*)"]


def primary_model(model_usage: dict) -> str | None:
    if not model_usage:
        return None
    return max(model_usage.items(), key=lambda kv: kv[1].get("outputTokens", 0))[0]


DENIAL_PHRASES = ("requires approval", "require approval", "can't be checked before it runs", "Brace expansion",
                  "Permission to use", "was denied", "not allowed")


def is_permission_denial(text: str) -> bool:
    """Claude Code denials are errors whose text is the denial itself, not command output."""
    return not text.startswith("Exit code") and any(phrase in text[:300] for phrase in DENIAL_PHRASES)


def blocked_tool_calls(session_id: str | None) -> list[str] | None:
    """Commands the agent tried but was not permitted to run, read from its transcript."""
    if not session_id:
        return None
    matches = list((Path.home() / ".claude/projects").glob(f"*/{session_id}.jsonl"))
    if not matches:
        return None
    calls, blocked = {}, []
    for line in matches[0].read_text().splitlines():
        content = (json.loads(line).get("message") or {}).get("content")
        for item in content if isinstance(content, list) else []:
            if item.get("type") == "tool_use":
                calls[item["id"]] = item.get("input", {}).get("command") or item.get("name")
            elif item.get("type") == "tool_result" and item.get("is_error"):
                text = item.get("content") if isinstance(item.get("content"), str) else json.dumps(item.get("content"))
                if is_permission_denial(text):
                    blocked.append(str(calls.get(item.get("tool_use_id"), "unknown"))[:200])
    return blocked


def guidance_received(arm: Path, session_id: str | None) -> bool | None:
    """True when a successful tool result contains the content of a skill in the arm."""
    if not session_id:
        return None
    matches = list((Path.home() / ".claude/projects").glob(f"*/{session_id}.jsonl"))
    skills = list(arm.glob(".agents/skills/*/SKILL.md")) + list(arm.glob(".workspace-context/**/SKILL.md"))
    if not matches or not skills:
        return None
    markers = []
    for skill in skills:
        body = [l.strip() for l in skill.read_text().split("---", 2)[-1].splitlines() if len(l.strip()) > 40]
        if body:
            markers.append(body[0][:50])
    for line in matches[0].read_text().splitlines():
        content = (json.loads(line).get("message") or {}).get("content")
        for item in content if isinstance(content, list) else []:
            if item.get("type") == "tool_result":
                text = item.get("content") if isinstance(item.get("content"), str) else json.dumps(item.get("content"))
                if not is_permission_denial(text) and any(marker in text for marker in markers):
                    return True
    return False


def execution_evidence(session_id: str | None, arm: Path | None = None) -> dict:
    """How the agent proved its answer, read from its transcript.

    editedRealSource: changed the real app files (in place) at some point.
    usedDisposableCopy: copied the app elsewhere, or used the mutation runner, to inject the fault.
    testRuns: completed Playwright runs (any outcome); independentCheck: probed the app outside the tests.
    """
    keys = ("ranTests", "usedMutationRunner", "editedRealSource", "usedDisposableCopy", "independentCheck")
    found = {k: False for k in keys}
    found["testRuns"] = 0
    matches = list((Path.home() / ".claude/projects").glob(f"*/{session_id}.jsonl")) if session_id else []
    if not matches:
        return {**{k: None for k in keys}, "testRuns": None}
    real_app = str(arm / "examples/sample-crm-app") if arm else "/examples/sample-crm-app/"
    calls = {}
    for line in matches[0].read_text().splitlines():
        content = (json.loads(line).get("message") or {}).get("content")
        for item in content if isinstance(content, list) else []:
            if item.get("type") == "tool_use":
                calls[item["id"]] = (item.get("name"), item.get("input", {}))
            elif item.get("type") == "tool_result" and item.get("tool_use_id") in calls:
                name, data = calls[item["tool_use_id"]]
                text = item.get("content") if isinstance(item.get("content"), str) else json.dumps(item.get("content"))
                if is_permission_denial(text):
                    continue
                if name in ("Edit", "Write", "MultiEdit") and str(data.get("file_path", "")).startswith(real_app):
                    found["editedRealSource"] = True
                if name != "Bash":
                    continue
                command = data.get("command", "")
                if "npm run mutation" in command or "mutation-cli" in command:
                    found.update(usedMutationRunner=True, usedDisposableCopy=True, ranTests=True)
                if "playwright test" in command and any(w in text for w in (" passed", " failed", "flaky")):
                    found["ranTests"] = True
                    found["testRuns"] += 1
                if re.search(r"\bcp\s+-[a-zA-Z]*R[a-zA-Z]*\s+\S*sample-crm-app", command) or "rsync" in command and "sample-crm-app" in command:
                    found["usedDisposableCopy"] = True
                if re.search(r"(sed|perl)\s+-i\S*.*sample-crm-app", command):
                    found["editedRealSource"] = True
                if re.search(r"\bcurl\b|probe", command) and "playwright test" not in command:
                    found["independentCheck"] = True
    return found


def stop_arm_processes(arm: Path) -> list[int]:
    """Stop processes the agent left running with their working directory inside the arm."""
    listing = subprocess.run(["lsof", "-d", "cwd", "-F", "pn"], capture_output=True, text=True).stdout
    stopped, pid = [], None
    for line in listing.splitlines():
        if line.startswith("p"):
            pid = int(line[1:])
        elif line.startswith("n") and pid and pid != os.getpid():
            path = Path(line[1:])
            if path == arm or arm in path.parents:
                try:
                    os.kill(pid, 15)
                    stopped.append(pid)
                except OSError:
                    pass
    return stopped


def cmd_run_agent(args) -> None:
    """Run a fresh, headless Claude Code session in one arm with the run's prompt."""
    run, record = load_run(args.run)
    arm_record = record["arms"][args.arm]
    if arm_record["startedAt"]:
        raise SystemExit(f"{args.arm} was already started; prepare a new run to repeat it.")
    arm = Path(arm_record["path"])
    prompt = (run / "PROMPT.md").read_text()
    command = ["claude", "-p", prompt, "--output-format", "json", "--permission-mode", "acceptEdits",
               "--setting-sources", "project,local", "--max-turns", str(args.max_turns),
               "--allowedTools", *AGENT_TOOLS]
    if args.model:
        command += ["--model", args.model]
    arm_record["startedAt"] = now()
    save_run(run, record)
    print(f"{args.arm}: agent started {arm_record['startedAt']} in {arm}")
    try:
        result = subprocess.run(command, cwd=arm, capture_output=True, text=True, timeout=args.timeout_minutes * 60)
        output, error, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        output, error, code = exc.stdout or "", f"timed out after {args.timeout_minutes} min", 124
    run, record = load_run(args.run)
    arm_record = record["arms"][args.arm]
    arm_record["finishedAt"] = now()
    (run / f"{args.arm}-agent.json").write_text(output if isinstance(output, str) else output.decode())
    (run / f"{args.arm}-agent.stderr.log").write_text(error if isinstance(error, str) else error.decode())
    try:
        data = json.loads(output)
    except (TypeError, ValueError):
        data = {}
    usage = data.get("usage") or {}
    arm_record["agent"] = {
        "tool": "claude-code-headless", "exitCode": code, "isError": data.get("is_error", code != 0),
        "subtype": data.get("subtype"), "turns": data.get("num_turns"),
        "model": primary_model(data.get("modelUsage") or {}), "costUsd": data.get("total_cost_usd"),
        "inputTokens": sum(int(usage.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")) if usage else None,
        "outputTokens": usage.get("output_tokens"),
        "blockedToolCalls": blocked_tool_calls(data.get("session_id")),
        "guidanceReceived": guidance_received(arm, data.get("session_id")) if args.arm == "framework" else None,
        "leftoverProcessesStopped": stop_arm_processes(arm),
    }
    save_run(run, record)
    a = arm_record["agent"]
    print(f"{args.arm}: agent finished {arm_record['finishedAt']} (exit {code}, {a['turns']} turns, model {a['model']}, "
          f"cost ${a['costUsd']}). Transcript summary: {run / (args.arm + '-agent.json')}")
    if args.arm == "framework" and a["guidanceReceived"] is False:
        print("WARNING framework: the agent never received its skill content; this run does not test guidance.")
    if a["blockedToolCalls"]:
        print(f"WARNING {args.arm}: {len(a['blockedToolCalls'])} blocked tool call(s); this arm may not be a fair run:")
        for item in a["blockedToolCalls"]:
            print(f"  - {item}")
    changed = subprocess.run(["git", "status", "--porcelain"], cwd=arm, capture_output=True, text=True).stdout.strip()
    print(f"{args.arm}: files changed by the agent:\n{changed or '  (none)'}")


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


def collect_assessment(args, run: Path, record: dict, task: dict, arm: Path) -> None:
    arm_record = record["arms"][args.arm]
    cases = assessment.load_cases()
    answer_path = arm / "assessment.json"
    try:
        answer = json.loads(answer_path.read_text())
    except (OSError, ValueError) as exc:
        answer, error = {}, f"assessment.json missing or invalid: {exc}"
    else:
        error = None
    result = assessment.score(answer, cases, task["variant"])
    documented = set(cases["variants"]["A"]["gaps"])
    planted = [r for r in result["criteria"] if r["truth"] == "gap" and r["criterion"] not in documented]
    changed = [line[3:] for line in subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=arm,
               capture_output=True, text=True).stdout.splitlines()
               if line[3:] != "assessment.json" and not line[3:].startswith((".evidence", "node_modules"))]
    agent = arm_record.get("agent") or {}
    row = {"schemaVersion": 1, "kind": "assessment", "trialId": f"{record['runId']}-{args.arm}",
           "taskId": record["taskId"], "variant": task["variant"], "arm": args.arm, "repeat": record["repeat"],
           "evidenceKind": args.evidence_kind, "model": args.model or ("claude-code" if agent else None),
           "modelVersion": args.model_version or agent.get("model"),
           "startedAt": arm_record["startedAt"], "finishedAt": arm_record["finishedAt"],
           "plantedGaps": len(planted), "plantedGapsFound": sum(r["outcome"] == "found" for r in planted),
           "documentedGapFound": any(r["criterion"] in documented and r["outcome"] == "found" for r in result["criteria"]),
           "answerError": error, "filesChangedOutsideAnswer": changed, "readOnlyRespected": not changed,
           "agent": agent, **result}
    out = Path(args.results_dir).resolve() if args.results_dir else WORKSPACE / "evidence/results"
    (out / "assessments").mkdir(parents=True, exist_ok=True)
    target = out / "assessments" / f"{row['trialId']}.json"
    if target.exists():
        raise SystemExit(f"{target.name} already collected.")
    target.write_text(json.dumps(row, indent=2) + "\n")
    print(json.dumps({k: row[k] for k in ("trialId", "plantedGapsFound", "plantedGaps", "documentedGapFound",
                                           "falseAlarms", "unanswered", "readOnlyRespected", "answerError")}))


def collect_mutation_proof(args, run: Path, record: dict, task: dict, arm: Path) -> None:
    arm_record = record["arms"][args.arm]
    cases = assessment.load_cases()
    case = cases["mutationCases"][task["case"]]
    try:
        answer, error = json.loads((arm / "verdict.json").read_text()), None
    except (OSError, ValueError) as exc:
        answer, error = {}, f"verdict.json missing or invalid: {exc}"
    verdict = assessment.normalise_verdict(answer.get("verdict"))
    status = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=arm, capture_output=True, text=True).stdout.splitlines()
    protected = ("examples/", "tests/", "pages/", "assertions/", "fixtures/", "playwright.config")
    left_changed = [line[3:] for line in status if line[3:].startswith(protected)]
    other = [line[3:] for line in status if not line[3:].startswith(protected) and line[3:] != "verdict.json"
             and not line[3:].startswith((".evidence", "node_modules", "artifacts/", "test-results", "playwright-report"))]
    agent = arm_record.get("agent") or {}
    execution = execution_evidence(json.loads((run / f"{args.arm}-agent.json").read_text() or "{}").get("session_id")
                                   if (run / f"{args.arm}-agent.json").exists() else None, arm)
    correct = verdict == case["truth"]
    row = {"schemaVersion": 1, "kind": "mutation-proof", "trialId": f"{record['runId']}-{args.arm}",
           "taskId": record["taskId"], "case": task["case"], "truth": case["truth"], "arm": args.arm, "repeat": record["repeat"],
           "evidenceKind": args.evidence_kind, "model": args.model or ("claude-code" if agent else None),
           "modelVersion": args.model_version or agent.get("model"),
           "startedAt": arm_record["startedAt"], "finishedAt": arm_record["finishedAt"],
           "verdict": verdict, "verdictCorrect": correct, "answerError": error,
           "evidenceText": str(answer.get("evidence") or "")[:600], "methodText": str(answer.get("method") or "")[:600],
           **execution, "appAndTestsRestored": not left_changed, "leftChanged": left_changed, "otherFilesCreated": other,
           "provenByExecution": bool(correct and execution.get("ranTests") and (execution.get("editedRealSource") or execution.get("usedDisposableCopy"))),
           "safeMethod": bool(execution.get("usedDisposableCopy") and not execution.get("editedRealSource")),
           "agent": agent}
    row["fullyProven"] = bool(row["provenByExecution"] and row["appAndTestsRestored"])
    out = Path(args.results_dir).resolve() if args.results_dir else WORKSPACE / "evidence/results"
    (out / "mutation-proofs").mkdir(parents=True, exist_ok=True)
    target = out / "mutation-proofs" / f"{row['trialId']}.json"
    if target.exists():
        raise SystemExit(f"{target.name} already collected.")
    target.write_text(json.dumps(row, indent=2) + "\n")
    print(json.dumps({k: row[k] for k in ("trialId", "truth", "verdict", "verdictCorrect", "testRuns", "usedMutationRunner",
                                           "editedRealSource", "usedDisposableCopy", "independentCheck", "appAndTestsRestored",
                                           "fullyProven", "safeMethod", "answerError")}))


def cmd_collect(args) -> None:
    run, record = load_run(args.run)
    arm_record = record["arms"][args.arm]
    if not (arm_record["startedAt"] and arm_record["finishedAt"]):
        raise SystemExit("Record `start` and `finish` for this arm before collecting.")
    task = load_task(record["taskId"])
    arm = Path(arm_record["path"])
    if task.get("kind") == "assessment":
        collect_assessment(args, run, record, task, arm)
        return
    if task.get("kind") == "mutation-proof":
        collect_mutation_proof(args, run, record, task, arm)
        return
    report = run_oracle(arm, record, task, args.report)
    agent = arm_record.get("agent") or {}
    model = args.model or ("claude-code" if agent else None)
    model_version = args.model_version or agent.get("model")
    if not (model and model_version):
        raise SystemExit("Pass --model and --model-version (they are recorded automatically only for run-agent runs).")
    usage = None
    if agent.get("inputTokens") is not None and agent.get("outputTokens") is not None and args.usage_input is None:
        usage = {"inputTokens": agent["inputTokens"], "outputTokens": agent["outputTokens"],
                 "source": "Claude Code headless JSON usage (input includes cache creation and cache reads)"}
    if args.usage_input is not None or args.usage_output is not None:
        usage = {"inputTokens": args.usage_input, "outputTokens": args.usage_output, "source": args.usage_source}
    metadata = {"trialId": f"{record['runId']}-{args.arm}", "taskId": record["taskId"], "arm": args.arm,
                "evidenceKind": args.evidence_kind, "model": model, "modelVersion": model_version,
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
    r = sub.add_parser("run-agent", help="run a fresh headless Claude Code session in one arm")
    r.add_argument("--run", required=True)
    r.add_argument("--arm", choices=ARMS, required=True)
    r.add_argument("--model", help="Claude model alias or ID; default is your Claude Code default")
    r.add_argument("--max-turns", type=int, default=60)
    r.add_argument("--timeout-minutes", type=int, default=45)
    c = sub.add_parser("collect")
    c.add_argument("--run", required=True)
    c.add_argument("--arm", choices=ARMS, required=True)
    c.add_argument("--model", help="defaults to claude-code for run-agent runs")
    c.add_argument("--model-version", help="defaults to the model recorded by run-agent")
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
    elif args.command == "run-agent":
        cmd_run_agent(args)
    else:
        cmd_collect(args)


if __name__ == "__main__":
    main()
