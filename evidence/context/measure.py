"""Per-project context measurement.

Selected context is what a workspace-guided agent loads for one task: routing
instructions, one skill, the task input, its resolved files and any listed files.
The comparison corpus is every Git-tracked text file in the project. Token counts
use the same approximation as context_efficiency_report.py and are for relative
comparison only.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from context_efficiency_report import estimate_tokens  # noqa: E402

METHOD = ("Approximate tokens (max of chars/4 and words*1.3). Selected = routing instructions, "
          "one skill, the task and its resolved files. Corpus = the project's Git-tracked text files.")


def load_manifest(workspace: Path) -> dict:
    return json.loads((workspace / "evidence/projects.json").read_text(encoding="utf-8"))


def file_entry(workspace: Path, relative: str) -> dict:
    text = (workspace / relative).read_text(encoding="utf-8", errors="ignore")
    return {"path": relative, "tokens": estimate_tokens(text), "lines": text.count("\n") + (1 if text else 0)}


def corpus_files(workspace: Path, root: str, suffixes: list[str]) -> list[str]:
    result = subprocess.run(["git", "-C", str(workspace / root), "ls-files", "-z"],
                            capture_output=True, text=True, check=True)
    wanted = {s.lower() for s in suffixes}
    files = []
    for name in filter(None, result.stdout.split("\0")):
        relative = f"{root}/{name}"
        path = workspace / relative
        if Path(name).suffix.lower() in wanted and path.is_file() and not path.is_symlink():
            files.append(relative)
    return sorted(files)


def resolved_file_list(workspace: Path, resolved: str) -> list[str]:
    import yaml

    data = yaml.safe_load((workspace / resolved).read_text(encoding="utf-8")) or {}
    found: list[str] = []

    def walk(value):
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)

    walk(data.get("resolved_files", {}))
    return found


def revision(workspace: Path, root: str) -> dict:
    head = subprocess.run(["git", "-C", str(workspace / root), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True)
    dirty = subprocess.run(["git", "-C", str(workspace / root), "status", "--porcelain", "--", "."],
                           capture_output=True, text=True)
    return {"commit": head.stdout.strip() or None, "uncommittedChanges": bool(dirty.stdout.strip())}


def measure(workspace: Path, project: str, profile_name: str, manifest: dict | None = None) -> dict:
    manifest = manifest or load_manifest(workspace)
    config = manifest["projects"][project]
    profile = config["contextProfiles"][profile_name]
    wanted = list(profile.get("instructions", [])) + [profile["task"]]
    missing: list[str] = []
    notes: list[str] = []
    if profile.get("resolved"):
        wanted.append(profile["resolved"])
        if (workspace / profile["resolved"]).is_file():
            wanted.extend(resolved_file_list(workspace, profile["resolved"]))
        else:
            notes.append(f"Resolved context missing; run `{profile.get('resolveCommand', 'the resolver')}` first.")
    wanted.extend(profile.get("files", []))

    seen: set[str] = set()
    selected = []
    for relative in wanted:
        if relative in seen:
            continue
        seen.add(relative)
        if (workspace / relative).is_file():
            selected.append(file_entry(workspace, relative))
        else:
            missing.append(relative)

    corpus = [file_entry(workspace, f) for f in corpus_files(workspace, config["root"], manifest["corpusSuffixes"])]
    instruction_paths = set(profile.get("instructions", []))
    for item in selected:
        item["role"] = "instructions" if item["path"] in instruction_paths else "task"
    selected_tokens = sum(f["tokens"] for f in selected)
    instruction_tokens = sum(f["tokens"] for f in selected if f["role"] == "instructions")
    corpus_tokens = sum(f["tokens"] for f in corpus)
    complete = not missing and not notes
    return {
        "kind": "context",
        "project": project,
        "profile": profile_name,
        "description": profile["description"],
        "status": "complete" if complete else "incomplete",
        "method": METHOD,
        "source": revision(workspace, config["root"]),
        "selected": {"files": len(selected), "tokens": selected_tokens,
                     "instructionTokens": instruction_tokens, "taskTokens": selected_tokens - instruction_tokens,
                     "items": selected},
        "corpus": {"root": config["root"], "files": len(corpus), "tokens": corpus_tokens},
        "selectedAsPercentOfCorpus": round(selected_tokens / corpus_tokens * 100, 1) if corpus_tokens and complete else None,
        "corpusToSelectedRatio": round(corpus_tokens / selected_tokens, 2) if selected_tokens and complete else None,
        "missing": missing,
        "notes": notes,
    }
