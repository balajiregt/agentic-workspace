import fs from 'node:fs/promises';
import path from 'node:path';

export async function loadConfiguration(workspaceRoot, projectRoot, view = 'kitchen') {
  const config = JSON.parse(await fs.readFile(path.join(projectRoot, 'dashboard.config.json'), 'utf8'));
  const registry = JSON.parse(await fs.readFile(path.join(workspaceRoot, 'workspace.projects.json'), 'utf8'));
  const port = view === 'map' ? config.mapPort : config.port;
  if (!['kitchen', 'map'].includes(view)) throw new Error('Unknown Agenttrail view.');
  if (!Number.isInteger(port) || port < 1024 || port > 65515 || view === 'map' && port === config.port) {
    throw new Error('Choose a dashboard port between 1024 and 65515.');
  }
  if (!Array.isArray(config.watchProjects) || !config.watchProjects.length || config.watchProjects.length > 12) {
    throw new Error('Choose between one and twelve project IDs to watch.');
  }
  const byId = new Map();
  for (const project of registry.projects) {
    if (byId.has(project.id)) throw new Error(`Duplicate project ID: ${project.id}`);
    byId.set(project.id, project);
  }
  const workspace = await fs.realpath(workspaceRoot);
  const roots = [];
  for (const id of config.watchProjects) {
    const project = byId.get(id);
    if (!project) throw new Error(`Unknown watched project: ${id}`);
    const root = await fs.realpath(path.resolve(workspace, project.path));
    const relative = path.relative(workspace, root);
    if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
      throw new Error(`Watched project escapes this workspace: ${id}`);
    }
    if (!(await fs.stat(root)).isDirectory()) throw new Error(`Not a project directory: ${id}`);
    if (!roots.includes(root)) roots.push(root);
  }
  return { port, roots: view === 'map' ? [workspace] : roots };
}

export function dashboardUrl(port, root, example = false, view = 'kitchen') {
  const url = new URL(`http://127.0.0.1:${port}/`);
  if (view === 'map') return url.href;
  url.searchParams.set('mode', example ? 'demo' : 'live');
  if (!example) url.searchParams.set('project', root);
  return url.href;
}

export async function probe(port, view = 'kitchen') {
  let response;
  try {
    response = await fetch(`http://127.0.0.1:${port}/${view === 'map' ? 'whoami' : 'api/state'}`, {
      signal: AbortSignal.timeout(1500), redirect: 'error'
    });
  } catch (error) {
    if (['ECONNREFUSED', 'ECONNRESET'].includes(error.cause?.code)) return null;
    throw new Error(`Port ${port} did not respond safely; no additional server was started.`, { cause: error });
  }
  const state = await response.json().catch(() => null);
  if (!response.ok || state?.app !== (view === 'map' ? 'agenttrail-map' : 'agenttrail-kitchen')) {
    throw new Error(`Port ${port} is occupied by another service. It was left running.`);
  }
  return state;
}

export function hasProjects(state, roots) {
  if (state.app === 'agenttrail-map') return roots.length === 1 && state.repoPath === roots[0];
  return roots.every(root => state.projects?.some(project => project.id === root));
}

export function ownedCommand(command, serverPath) {
  return typeof command === 'string' && command.includes(serverPath) && /(?:^|[ /])node(?:\s|$)/.test(command);
}
