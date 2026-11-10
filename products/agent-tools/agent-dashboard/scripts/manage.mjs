import fs from 'node:fs/promises';
import path from 'node:path';
import { spawn, execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dashboardUrl, hasProjects, loadConfiguration, ownedCommand, probe } from './lib.mjs';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const workspaceRoot = path.resolve(projectRoot, '../../..');
const view = process.argv.includes('--map') ? 'map' : 'kitchen';
const label = view === 'map' ? 'Agenttrail Map' : 'Agenttrail Kitchen';
const dependency = view === 'map' ? ['agenttrail', '0.2.0'] : ['agenttrail-kitchen', '0.1.0-alpha.3'];
const stateDir = path.join(projectRoot, '.runtime', ...(view === 'map' ? ['map'] : []));
const serverPath = path.join(projectRoot, 'scripts', view === 'map' ? 'map-server.mjs' : 'server.mjs');
const logPath = path.join(stateDir, view === 'map' ? 'map.log' : 'dashboard.log');
const managedPath = path.join(stateDir, 'managed.json');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const alive = pid => { try { process.kill(pid, 0); return true; } catch { return false; } };

async function installed() {
  const file = path.join(projectRoot, 'node_modules', dependency[0], 'package.json');
  try {
    const metadata = JSON.parse(await fs.readFile(file, 'utf8'));
    if (metadata.version !== dependency[1]) throw new Error('Unexpected Agenttrail version; run npm ci in the dashboard project.');
    return;
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  console.log('Installing the pinned dashboard package for first use...');
  const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
  await new Promise((resolve, reject) => {
    const child = spawn(npm, ['ci', '--omit=dev', '--ignore-scripts', '--no-audit', '--no-fund'], { cwd: projectRoot, stdio: 'inherit' });
    child.once('error', reject);
    child.once('exit', code => code === 0 ? resolve() : reject(new Error(`Dashboard dependency installation failed (${code}).`)));
  });
}

async function openBrowser(url) {
  const command = process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'cmd' : 'xdg-open';
  const args = process.platform === 'win32' ? ['/c', 'start', '', url] : [url];
  await new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: 'ignore' });
    child.once('error', reject);
    child.once('exit', code => code === 0 ? resolve() : reject(new Error(`Could not open the browser; open ${url} manually.`)));
  });
}

async function ready(config, pid) {
  for (let i = 0; i < 80; i++) {
    if (pid && !alive(pid)) throw new Error(`${label} exited before readiness. See ${logPath}.`);
    const state = await probe(config.port, view);
    if (state) {
      if (!hasProjects(state, config.roots)) throw new Error(`${label} is already running with a different project set. Stop its owning session before restarting.`);
      return state;
    }
    await pause(250);
  }
  throw new Error(`${label} did not become ready within 20 seconds. See ${logPath}.`);
}

async function start(config) {
  let state = await probe(config.port, view);
  if (state) {
    if (!hasProjects(state, config.roots)) throw new Error(`The existing ${label} watches a different project set; stop its owning session before restarting.`);
    console.log('Reusing the running dashboard.');
    return;
  }
  await fs.mkdir(stateDir, { recursive: true, mode: 0o700 });
  const lockPath = path.join(stateDir, 'launch.lock');
  let lock;
  try { lock = await fs.open(lockPath, 'wx', 0o600); }
  catch (error) {
    if (error.code !== 'EEXIST') throw error;
    const owner = JSON.parse(await fs.readFile(lockPath, 'utf8').catch(() => '{}'));
    if (!Number.isInteger(owner.pid) || !alive(owner.pid)) {
      throw new Error(`A stale launch lock exists. Remove ${lockPath} after checking no launch is in progress.`);
    }
    await ready(config);
    console.log('Reusing the dashboard started by the other launch.');
    return;
  }
  let child;
  try {
    await lock.writeFile(JSON.stringify({ pid: process.pid }));
    await installed();
    const log = await fs.open(logPath, 'a', 0o600);
    child = spawn(process.execPath, [serverPath], { cwd: projectRoot, detached: true, stdio: ['ignore', log.fd, log.fd] });
    await new Promise((resolve, reject) => { child.once('spawn', resolve); child.once('error', reject); });
    child.unref();
    await log.close();
    await fs.writeFile(managedPath, JSON.stringify({ pid: child.pid, serverPath, startedAt: new Date().toISOString() }), { mode: 0o600 });
    await ready(config, child.pid);
    console.log(`${label} started and readiness verified.`);
  } catch (error) {
    if (child?.pid && alive(child.pid)) process.kill(child.pid, 'SIGTERM');
    if (child?.pid) await fs.unlink(managedPath).catch(() => {});
    throw error;
  } finally {
    await lock.close();
    await fs.unlink(lockPath).catch(() => {});
  }
}

async function stop(config) {
  const record = JSON.parse(await fs.readFile(managedPath, 'utf8').catch(() => '{}'));
  if (!Number.isInteger(record.pid) || record.pid <= 1 || !alive(record.pid)) {
    console.log('No running dashboard owned by this launcher. Other services were left unchanged.');
    return;
  }
  let command = '';
  try { command = execFileSync('ps', ['-p', String(record.pid), '-o', 'command='], { encoding: 'utf8' }).trim(); } catch {}
  if (record.serverPath !== serverPath || !ownedCommand(command, serverPath)) {
    throw new Error('Recorded PID no longer belongs to this dashboard. It was not stopped.');
  }
  process.kill(record.pid, 'SIGTERM');
  for (let i = 0; i < 40; i++) {
    if (!alive(record.pid)) break;
    await pause(100);
  }
  if (await probe(config.port, view)) throw new Error('The dashboard is still responding; no force-kill was attempted.');
  await fs.unlink(managedPath).catch(() => {});
  console.log(`${label} stopped.`);
}

try {
  if (Number(process.versions.node.split('.')[0]) < 20) throw new Error('Node.js 20 or newer is required.');
  const args = process.argv.slice(2);
  const action = args[0] || 'start';
  if (!['start', 'status', 'stop'].includes(action) || args.slice(1).some(a => !['--open', '--example', '--map'].includes(a)) || view === 'map' && args.includes('--example')) {
    throw new Error('Usage: node scripts/manage.mjs start|status|stop [--open] [--example | --map]');
  }
  const config = await loadConfiguration(workspaceRoot, projectRoot, view);
  if (action === 'stop') await stop(config);
  else if (action === 'status') {
    const state = await probe(config.port, view);
    if (state && !hasProjects(state, config.roots)) throw new Error('This service observes a different project set.');
    console.log(state ? `Running: ${dashboardUrl(config.port, config.roots[0], false, view)}\nObserved project folders: ${view === 'map' ? 1 : state.projects.length}` : `${label} is stopped.`);
  } else {
    await start(config);
    const url = dashboardUrl(config.port, config.roots[0], args.includes('--example'), view);
    console.log(url);
    if (args.includes('--open')) await openBrowser(url);
  }
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
