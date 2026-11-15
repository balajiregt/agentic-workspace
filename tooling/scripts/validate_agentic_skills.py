#!/usr/bin/env python3
"""Validate local skill wiring and source integrity without running upstream code."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote


def validate(root: Path) -> dict:
    errors = []
    try:
        manifest = json.loads((root/'knowledge/docs/instagram/adoption-manifest.json').read_text())
    except (OSError, ValueError) as exc:
        return {'ok': False, 'errors': [str(exc)]}
    names = manifest['registered_existing_skills'] + manifest['active_new_skills']
    if len(names) != len(set(names)):
        errors.append('Duplicate active skill names')
    for name in names:
        for path in [root/'agent-system/skills'/name/'SKILL.md', root/'.agents/skills'/name/'SKILL.md']:
            if not path.is_file():
                errors.append(f'Missing skill: {path.relative_to(root)}')
                continue
            match = re.match(r'\A---\n(.*?)\n---(?:\n|$)', path.read_text(), re.S)
            fields = dict(re.findall(r'^(name|description):\s*(.+)$', match[1], re.M)) if match else {}
            if fields.get('name') != name or not re.fullmatch(r'[a-z0-9-]{1,64}', name):
                errors.append(f'Wrong skill name: {path.relative_to(root)}')
            if not fields.get('description') or len(fields['description']) > 1024:
                errors.append(f'Missing or oversized description: {path.relative_to(root)}')
        entry = root/'.agents/skills'/name/'SKILL.md'
        if entry.is_file() and f'../../../agent-system/skills/{name}/SKILL.md' not in entry.read_text():
            errors.append(f'Wrong discovery target: {name}')
    alias = root/'.claude/skills'
    if not alias.is_symlink() or alias.resolve() != (root/'.agents/skills').resolve():
        errors.append('Claude skills alias must resolve to shared discovery entries')
    paths = [root/'AGENTS.md', root/'CLAUDE.md', root/'.github/copilot-instructions.md', root/'.kilo/rules/agentic-workspace.md']
    paths += list((root/'knowledge/docs/instagram').glob('*.md'))
    for name in names:
        paths += list((root/'agent-system/skills'/name).rglob('*.md'))
        paths += [root/'.agents/skills'/name/'SKILL.md']
    for path in paths:
        if not path.is_file():
            errors.append(f'Missing guide: {path.relative_to(root)}')
            continue
        for raw in re.findall(r'\]\(([^\s)]+)\)', path.read_text()):
            if re.match(r'^[a-z][a-z0-9+.-]*:', raw, re.I) or raw.startswith('#'):
                continue
            resolved = (path.parent/unquote(raw.split('#',1)[0])).resolve()
            if not resolved.is_relative_to(root.resolve()):
                errors.append(f'Reference escapes workspace: {path.relative_to(root)} -> {raw}')
            elif not resolved.exists():
                errors.append(f'Broken reference: {path.relative_to(root)} -> {raw}')
    snapshots = entries = 0
    for source in manifest['sources']:
        directory = root/'knowledge/resources/instagram-sources'/source['name']
        try:
            receipt = json.loads((directory/'snapshot.json').read_text())
        except (OSError, ValueError) as exc:
            errors.append(f'Invalid snapshot {source["name"]}: {exc}')
            continue
        if receipt['revision'] != source['revision'] or not re.fullmatch('[a-f0-9]{40}',receipt['revision']):
            errors.append(f'Mismatched revision: {source["name"]}')
        if not (directory/'LICENSE').is_file():
            errors.append(f'Missing license: {source["name"]}')
        counted = 0
        for relative, expected in receipt['sha256'].items():
            p = directory/relative
            if not p.resolve().is_relative_to(directory.resolve()):
                errors.append(f'Escaping snapshot path: {source["name"]}/{relative}')
            elif not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                errors.append(f'Snapshot integrity failure: {source["name"]}/{relative}')
            counted += relative.endswith('/SKILL.md')
        if counted != source['skill_count'] or counted != receipt['skill_count']:
            errors.append(f'Skill count mismatch: {source["name"]}')
        snapshots += 1
        entries += counted
    return {'ok':not errors,'active_skills':len(names),'source_snapshots':snapshots,
            'reference_skill_entries':entries,'errors':errors,
            'scope':'Static format, references, discovery wiring, licenses and snapshot integrity; no runtime or model behavior claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    result = validate(parser.parse_args().root.resolve())
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
