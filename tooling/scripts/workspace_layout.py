"""Shared canonical folder selection for workspace infrastructure."""
from pathlib import Path

# Earlier layouts, newest first; kept so stale checkouts still resolve.
LEGACY_UI_AUTOMATION_ROOTS = ('qa-projects/ui-automation', 'projects/ui-automation')


def ui_automation_root(workspace: Path) -> Path:
    """Prefer the current QA location while accepting previous layouts."""
    current = workspace / 'qa/ui-automation'
    if current.is_dir():
        return current
    for legacy in LEGACY_UI_AUTOMATION_ROOTS:
        if (workspace / legacy).is_dir():
            return workspace / legacy
    return current
