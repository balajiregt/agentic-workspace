import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { loadConfiguration } from './lib.mjs';
import { adaptMapSource, mapVersion, ownershipPlan } from './map-adapter.mjs';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const workspaceRoot = path.resolve(projectRoot, '../..');
const config = await loadConfiguration(workspaceRoot, projectRoot, 'map');
const packageRoot = path.join(projectRoot, 'node_modules/agenttrail');
const metadata = JSON.parse(await fs.readFile(path.join(packageRoot, 'package.json'), 'utf8'));
if (metadata.version !== mapVersion) throw new Error('Unexpected Agenttrail Map package version.');
process.umask(0o077);
const runtime = path.join(projectRoot, '.runtime/map');
const stateDir = path.join(runtime, 'state');
await fs.mkdir(stateDir, { recursive: true, mode: 0o700 });
let planPath = path.join(workspaceRoot, 'PLAN.md');
try { await fs.access(planPath); }
catch {
  planPath = path.join(runtime, 'ownership-plan.md');
  const registry = JSON.parse(await fs.readFile(path.join(workspaceRoot, 'workspace.projects.json'), 'utf8'));
  await fs.writeFile(planPath, ownershipPlan(registry), { mode: 0o600 });
}
const source = await fs.readFile(path.join(packageRoot, 'bin/agenttrail.mjs'), 'utf8');
const adapter = adaptMapSource(source, { binDir: path.join(packageRoot, 'bin'), stateDir, planPath });
const entry = path.join(runtime, 'upstream-map.mjs');
await fs.writeFile(entry, adapter, { mode: 0o600 });
// Noninteractive observation only: never invoke init, hooks or autostart.
process.argv = [process.execPath, entry, workspaceRoot, '--port', String(config.port), '--no-open'];
await import(pathToFileURL(entry).href);
