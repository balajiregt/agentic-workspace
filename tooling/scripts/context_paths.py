"""Project-owned example task locations shared by workspace tools.

These defaults demonstrate the workflow; callers must select a different
--context for a real work item instead of replacing a workspace-wide task.
"""
from pathlib import Path
import hashlib

API_TASK = Path("services/microservices/contexts/tasks/ABC-123.yml")
UI_TASK = Path("qa/ui-automation/role-aware-mockserver/contexts/tasks/UI-ROLE-001.yml")


def resolved_path(context: Path) -> Path:
    """Keep generated output separate for each named task, beside its tasks dir."""
    owner = context.parent.parent if context.parent.name == "tasks" else context.parent
    return owner / ".resolved" / context.name


API_RESOLVED = resolved_path(API_TASK)
UI_RESOLVED = resolved_path(UI_TASK)


def load_resolved(path: Path, kind: str, workspace: Path) -> dict:
    """Fail on an unavailable, wrong-kind or task-stale map rather than guessing."""
    import yaml

    if not path.is_file():
        raise SystemExit(f"Resolved {kind} context not found: {path}; run the selected task resolver")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SystemExit(f"Invalid resolved {kind} context: {path}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected resolved {kind} context mapping: {path}")
    task = data.get("task_context")
    identity = "service_name" if kind == "api" else "ui_project_name"
    section = "service_context" if kind == "api" else "ui_context"
    if (not isinstance(task, dict) or not task.get(identity)
            or not isinstance(task.get("path"), str) or not task["path"]
            or not isinstance(data.get(section), dict)
            or not isinstance(data.get("resolved_files"), dict) or not data["resolved_files"]):
        raise SystemExit(f"Invalid resolved {kind} context shape: {path}")
    source = workspace / task["path"]
    if not source.is_file():
        raise SystemExit(f"Selected task input not found: {source}")
    if task.get("sha256") and hashlib.sha256(source.read_bytes()).hexdigest() != task["sha256"]:
        raise SystemExit(f"Stale resolved {kind} context: {path}; rerun the selected task resolver")
    return data
