#!/usr/bin/env python3
"""Read-only npm/OSV dependency gate. Never installs packages or runs lifecycle scripts."""
import argparse
import email
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PRUNE = {'.git', 'node_modules', '.venv', 'venv', 'artifacts', 'resources', 'target',
         'dist', 'build', '.runtime', 'models', 'cache', '.cache', 'llama.cpp', '__pycache__',
         'benchmark-results', 'graphify-out'}


def run(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, timeout=180, **kwargs)


def osv(queries):
    result = run(['curl', '--fail', '--silent', '--show-error', '--connect-timeout', '10',
                  '--max-time', '60', '-H', 'Content-Type: application/json', '--data-binary',
                  '@-', 'https://api.osv.dev/v1/querybatch'], input=json.dumps({'queries': queries}))
    if result.returncode:
        raise RuntimeError('OSV lookup failed; no clean result is available')
    data = json.loads(result.stdout)
    if len(data.get('results', [])) != len(queries):
        raise RuntimeError('Incomplete OSV response; no clean result is available')
    return data['results']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'artifacts/security-check')
    parser.add_argument('--include-global', action='store_true', help='also check installed npm tools and native Claude')
    parser.add_argument('--skip-java', action='store_true', help='explicitly omit Maven resolution for a narrow npm/Python check')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    coordinates = {}
    audits = []
    global_prefix = None

    def version_tuple(value):
        match = re.match(r'^v?(\d+)\.(\d+)\.(\d+)', value.strip())
        if not match:
            raise RuntimeError('Cannot identify the selected runtime version')
        return tuple(map(int, match.groups()))

    python_floor = version_tuple((ROOT / '.python-version').read_text())
    if sys.version_info[:3] < python_floor:
        raise RuntimeError('Select the Python version in .python-version before checking dependencies')
    node = run(['node', '--version'])
    if node.returncode or version_tuple(node.stdout) < version_tuple((ROOT / '.nvmrc').read_text()):
        raise RuntimeError('Select the Node version in .nvmrc before checking dependencies')

    def add(ecosystem, name, version, source):
        if name and version:
            coordinates.setdefault((ecosystem, name, version), set()).add(source)

    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in PRUNE and not Path(folder, d).is_symlink()]
        if 'package-lock.json' not in files:
            continue
        lock = Path(folder, 'package-lock.json')
        source = str(lock.relative_to(ROOT))
        data = json.loads(lock.read_text())
        for location, package in data.get('packages', {}).items():
            if location:
                add('npm', package.get('name') or location.rsplit('node_modules/', 1)[-1], package.get('version'), source)
        audit = run(['npm', 'audit', '--package-lock-only', '--ignore-scripts', '--json',
                     '--registry=https://registry.npmjs.org', '--fetch-retries=0', '--fetch-timeout=45000'], cwd=folder)
        data = json.loads(audit.stdout)
        if 'metadata' not in data or audit.returncode not in (0, 1):
            raise RuntimeError('npm audit could not complete for ' + source)
        (output / ('npm-' + str(len(audits) + 1) + '.json')).write_text(json.dumps(data, indent=2))
        audits.append({'source': source, 'vulnerabilities': data['metadata']['vulnerabilities']})

    # Locked dependencies are also checked on CI where optional local tools are not installed.
    for lock in [ROOT / 'tooling/scripts/requirements-graphify.lock', ROOT / 'tooling/scripts/requirements-python-build.lock',
                 ROOT / 'qa/playwright-agent/quality/python/requirements.lock']:
        if not lock.is_file():
            raise RuntimeError('Missing Python dependency lock: ' + str(lock.relative_to(ROOT)))
        for line in lock.read_text().splitlines():
            match = re.match(r'^([A-Za-z0-9_.-]+)==([^\s\\]+)', line)
            if match:
                add('PyPI', *match.groups(), str(lock.relative_to(ROOT)))
    for environment in [ROOT / 'artifacts/tools/graphify-venv', ROOT / 'qa/playwright-agent/quality/.venv']:
        config = environment / 'pyvenv.cfg'
        if not config.exists():
            continue
        if re.search(r'include-system-site-packages\s*=\s*true', config.read_text(), re.I):
            raise RuntimeError('Python environment inherits uncontrolled system packages: ' + str(environment))
        version = re.search(r'^version\s*=\s*(\S+)', config.read_text(), re.M)
        if not version or version_tuple(version.group(1)) < python_floor:
            raise RuntimeError('Rebuild the workspace Python environment using .python-version')
        for metadata in environment.glob('lib/python*/site-packages/*.dist-info/METADATA'):
            package = email.message_from_string(metadata.read_text(errors='replace'))
            add('PyPI', package['Name'], package['Version'], str(environment.relative_to(ROOT)))

    if not args.skip_java:
        for name, project, append in [('microservices', ROOT / 'services/microservices', True),
                                      ('kafka', ROOT / 'labs/kafka-test-project', False)]:
            tree = output / ('maven-' + name + '.txt')
            tree.unlink(missing_ok=True)
            command = ['mvn', '-B', '-ntp', 'org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree',
                       '-DoutputType=text', '-DoutputFile=' + str(tree)]
            if append:
                command.append('-DappendOutput=true')
            result = run(command, cwd=project)
            (output / ('maven-' + name + '.log')).write_text(result.stdout + result.stderr)
            if result.returncode or not tree.exists():
                raise RuntimeError('Maven dependency resolution failed for ' + name)
            for line in tree.read_text().splitlines():
                fields = re.sub(r'^[| +\\-]+', '', line).strip().split(':')
                if len(fields) in (5, 6):
                    add('Maven', ':'.join(fields[:2]), fields[-2], str(project.relative_to(ROOT)) + ' ' + fields[-1])

    if args.include_global:
        result = run(['npm', 'prefix', '--global'])
        if result.returncode:
            raise RuntimeError('Cannot identify the global npm prefix')
        global_prefix = Path(result.stdout.strip())
        base = global_prefix / 'lib/node_modules'
        active_npm = Path(shutil.which('npm')).resolve().parents[1]
        for package_base, prefix in [(base, 'global npm: '), (active_npm.parent, 'active npm: ')]:
            # A separate Homebrew npm installation may sit outside the global prefix.
            for folder, dirs, files in os.walk(package_base):
                if Path(folder) == package_base and prefix == 'active npm: ':
                    dirs[:] = [d for d in dirs if Path(folder, d) == active_npm]
                else:
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'test', 'tests', 'fixtures'}
                               and not Path(folder, d).is_symlink()]
                location = str(Path(folder).relative_to(package_base))
                if 'package.json' in files and re.fullmatch(r'(?:@[^/]+/)?[^/]+(?:/node_modules/(?:@[^/]+/)?[^/]+)*', location):
                    package = json.loads(Path(folder, 'package.json').read_text())
                    add('npm', package.get('name'), package.get('version'), prefix + location)
        claude = shutil.which('claude')
        if claude:
            version = Path(claude).resolve().name
            if re.fullmatch(r'\d+\.\d+\.\d+', version):
                add('npm', '@anthropic-ai/claude-code', version, 'active native Claude')

    entries = [{'ecosystem': eco, 'name': name, 'version': version, 'sources': sorted(sources)}
               for (eco, name, version), sources in sorted(coordinates.items())]
    results = []
    for start in range(0, len(entries), 300):
        batch = entries[start:start + 300]
        response = osv([{'package': {'ecosystem': p['ecosystem'], 'name': p['name']}, 'version': p['version']} for p in batch])
        results.extend({**package, 'advisories': data.get('vulns', [])} for package, data in zip(batch, response))
    raw_matches = [p for p in results if p['advisories']]
    findings = [{**p, 'advisories':p['advisories'][:]} for p in raw_matches]
    # Installed vendor backports retain their real upstream version. An exact
    # content receipt is required; changing/reinstalling the code invalidates it.
    patched = []
    if args.include_global:
        receipts = ROOT / 'tooling/scripts/global-tool-security-patches.json'
        for receipt in json.loads(receipts.read_text()) if receipts.exists() else []:
            if not receipt.get('files') or not all(
                    not Path(file['path']).is_absolute() and '..' not in Path(file['path']).parts
                    and file['path'].startswith('lib/node_modules/')
                    and (global_prefix / file['path']).is_file()
                    and hashlib.sha256((global_prefix / file['path']).read_bytes()).hexdigest() == file['sha256']
                    for file in receipt['files']):
                continue
            for finding in findings:
                if finding['ecosystem'] == 'npm' and finding['name'] == receipt['package'] and finding['version'] == receipt['version']:
                    # Do not waive another copy of the package outside the patched root.
                    parents = {str(Path(file['path']).parent).split('/node_modules/', 1)[-1].rsplit('/dist', 1)[0] for file in receipt['files']}
                    if not all(any(source == 'global npm: ' + parent for parent in parents) for source in finding['sources']):
                        continue
                    patched.extend({**finding, 'advisories':[a]} for a in finding['advisories'] if a['id'] == receipt['advisory'])
                    finding['advisories'] = [a for a in finding['advisories'] if a['id'] != receipt['advisory']]
        findings = [p for p in findings if p['advisories']]
    summary = {'coordinatesChecked': len(results), 'matchedCoordinates': len(raw_matches), 'unaddressedCoordinates':len(findings),
               'verifiedLocalBackports':patched, 'npmAudits': audits, 'javaSkipped': args.skip_java, 'globalToolsIncluded': args.include_global}
    (output / 'osv-results.json').write_text(json.dumps(results, indent=2))
    (output / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    for finding in findings:
        print(f"{finding['ecosystem']} {finding['name']}@{finding['version']}: " + ', '.join(a['id'] for a in finding['advisories']))
    return int(bool(findings) or any(a['vulnerabilities']['total'] for a in audits))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, RuntimeError) as error:
        detail = str(error) if isinstance(error, RuntimeError) else type(error).__name__ + '; inspect the local evidence/inputs.'
        print('Security check incomplete: ' + detail, file=sys.stderr)
        sys.exit(2)
