"""Shared canonical folder selection for workspace infrastructure."""
from pathlib import Path


def ui_automation_root(workspace: Path) -> Path:
    """Prefer the current QA location while accepting the previous layout."""
    current = workspace / 'qa-projects/ui-automation'
    legacy = workspace / 'projects/ui-automation'
    if current.is_dir():
        return current
    return legacy if legacy.is_dir() else current
