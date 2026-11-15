import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { startOffice } from '../node_modules/agenttrail-kitchen/src/server.mjs';
import { loadConfiguration } from './lib.mjs';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const workspaceRoot = path.resolve(projectRoot, '../../..');
const config = await loadConfiguration(workspaceRoot, projectRoot);
const stateDir = path.join(projectRoot, '.runtime');
const office = await startOffice({ roots: config.roots, home: os.homedir(), stateDir, port: config.port });
if (Number(new URL(office.url).port) !== config.port) {
  await office.close();
  throw new Error(`Port ${config.port} became occupied during startup. No alternate port was retained.`);
}
await fs.writeFile(path.join(stateDir, 'projects.json'), JSON.stringify(config.roots), { mode: 0o600 });
console.log(`Agenttrail Kitchen ready on ${office.url}; observing ${config.roots.length} workspace folders.`);
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.once(signal, async () => { await office.close(); process.exit(0); });
}
