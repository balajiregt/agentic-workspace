#!/usr/bin/env python3
"""Check the workspace registry, editor folders, launchers, and UI routing."""
import argparse
import json
from pathlib import Path

from context_paths import API_TASK, UI_TASK


def check(root: Path, overlay: Path | None = None) -> dict:
    errors = []
    def locate(relative):
        candidate = overlay/relative if overlay else root/relative
        return candidate if candidate.exists() else root/relative
    try:
        registry = json.loads(locate('workspace.projects.json').read_text())
        editor = json.loads(locate('agentic-workspace.code-workspace').read_text())
        package = json.loads(locate('package.json').read_text())
        config = json.loads(locate('products/agent-tools/agent-dashboard/dashboard.config.json').read_text())
    except (OSError, ValueError) as exc:
        return {'ok':False,'errors':[str(exc)]}
    ids = set()
    project_paths = {}
    for project in registry['projects']:
        if project['id'] in ids:
            errors.append('Duplicate project: '+project['id'])
        ids.add(project['id'])
        target = (root/project['path']).resolve()
        if target in project_paths:
            errors.append('Duplicate project path: '+project['path']+' (already owned by '+project_paths[target]+')')
        project_paths[target] = project['id']
        if not target.is_relative_to(root.resolve()):
            errors.append('Project escapes workspace: '+project['id'])
        elif not locate(project['path']).is_dir():
            errors.append('Missing project: '+project['path'])
    for retired in ['qa-projects/plawright-role-aware-mockserver',
                    'evaluation/playwright-decision-bench',
                    'projects/qa-dashboard-viewer', 'qa-projects/xyz-service-api-tests']:
        if locate(retired).exists():
            errors.append('Retired duplicate project root exists: '+retired)
    if locate('agent-system/contexts').exists():
        errors.append('Retired shared context directory exists: agent-system/contexts')
    groups = registry['groups']
    group_ids = set()
    for group in groups:
        if group['id'] in group_ids:
            errors.append('Duplicate group: '+group['id'])
        group_ids.add(group['id'])
        target = (root/group['path']).resolve()
        if not target.is_relative_to(root.resolve()) or not locate(group['path']).is_dir():
            errors.append('Invalid group directory: '+group['path'])
    group_paths = {g['id']: g['path'] for g in groups}
    conventions = registry.get('conventions', {})
    gitignore = set(locate('.gitignore').read_text().splitlines()) if locate('.gitignore').is_file() else set()
    for project in registry['projects']:
        if project['path'] != '.' and not any(Path(project['path']).is_relative_to(Path(g['path'])) for g in groups):
            errors.append('Project is outside the category folders: '+project['id'])
        missing = [field for field in ('group', 'domain', 'kind', 'status', 'purpose', 'repository') if not project.get(field)]
        if missing:
            errors.append('Project '+project['id']+' lacks metadata: '+', '.join(missing))
            continue
        if project['kind'] not in conventions.get('kinds', []) or project['status'] not in conventions.get('statuses', []):
            errors.append('Project '+project['id']+' uses an unknown kind or status')
        if project['group'] != 'core' and (project['group'] not in group_paths
                                           or not Path(project['path']).is_relative_to(Path(group_paths[project['group']]))):
            errors.append('Project '+project['id']+' is not inside its declared group')
        if project['repository'].get('nested') and '/'+project['path']+'/' not in gitignore:
            errors.append('Nested repository is not ignored by the workspace: '+project['path'])
    for legacy_root in ['projects', 'qa-projects', 'evaluation']:
        if locate(legacy_root).exists():
            errors.append('Retired category root exists: '+legacy_root)
    expected = {('Workspace core', '.')} | {(g['name'],g['path']) for g in groups}
    actual = {(p['name'],p['path']) for p in editor['folders']}
    if actual != expected:
        errors.append('Editor folders do not match the category registry')
    if not set(config['watchProjects']).issubset(ids) or not 1 <= len(config['watchProjects']) <= 12:
        errors.append('Invalid dashboard project selection')
    for relative in ['Open-Agent-Dashboard.command','Open-Agent-Example.command','Stop-Agent-Dashboard.command',
                     'Open-Agent-Map.command','Stop-Agent-Map.command',
                     'Open-Workspace.command','.vscode/tasks.json','products/agent-tools/agent-dashboard/package-lock.json',
                     'tooling/docker/Dockerfile.graphs','tooling/docker/docker-compose.graphs.yml',
                     'knowledge/docs/agent-workflow/LOOP.md','knowledge/docs/agent-workflow/STATE.md',
                     'knowledge/docs/agent-workflow/loop-budget.md',
                     'knowledge/docs/project-workflow.md',
                     'agent-system/skills/microservice-change/examples/service-context.microservice.yml',
                     'agent-system/skills/microservice-change/examples/service-context.service-owned-tests.yml',
                     'agent-system/skills/microservice-change/examples/service-context.monolithic.yml',
                     'qa/playwright-agent/AGENTS.md',
                     'qa/ui-automation/role-aware-mockserver/AGENTS.md',
                     'services/microservices/AGENTS.md',str(API_TASK),str(UI_TASK)]:
        if not locate(relative).is_file():
            errors.append('Missing workspace file: '+relative)
    dashboard_package = json.loads(locate('products/agent-tools/agent-dashboard/package.json').read_text())
    if dashboard_package.get('dependencies',{}).get('agenttrail-kitchen') != '0.1.0-alpha.3':
        errors.append('Dashboard dependency is not pinned to the reviewed version')
    if dashboard_package.get('dependencies',{}).get('agenttrail') != '0.2.0':
        errors.append('Map dependency is not pinned to the reviewed version')
    for name in ['ui:test','ui:test:roles','ui:test:legacy-interception']:
        if 'qa/ui-automation/' not in package['scripts'][name]:
            errors.append('Stale UI command: '+name)
    return {'ok':not errors,'groups':len(groups),'projects':len(ids),'watched_projects':len(config['watchProjects']),
            'dashboard_port':config['port'],'errors':errors}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--overlay',type=Path)
    args = parser.parse_args()
    result = check(args.root.resolve(),args.overlay.resolve() if args.overlay else None)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['ok'] else 1)
