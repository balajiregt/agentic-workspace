import { createHash } from 'node:crypto';
import path from 'node:path';

export const mapVersion = '0.2.0';
export const mapSourceHash = '85b4219691491412947332911ec4af9ea3b965dc2a09dd1574ab0416a87d9f55';

// The pinned CLI has no state-dir option. Keep its upstream frontend intact;
// adapt only local storage, file filtering, plan input and service identity.
export function adaptMapSource(source, { binDir, stateDir, planPath }) {
  if (createHash('sha256').update(source).digest('hex') !== mapSourceHash) {
    throw new Error('Agenttrail Map source changed; review the pinned adapter before starting.');
  }
  const replace = (from, to, count = 1) => {
    if (source.split(from).length - 1 !== count) throw new Error('Agenttrail Map adapter no longer matches its pinned source.');
    source = source.split(from).join(to);
  };
  replace('const __dirname = path.dirname(fileURLToPath(import.meta.url))', `const __dirname = ${JSON.stringify(binDir)}`);
  replace("const planPath = path.join(repo, 'PLAN.md')", `const planPath = ${JSON.stringify(planPath)}`);
  replace("path.join(os.homedir(), '.agenttrail'", `path.join(${JSON.stringify(stateDir)}`, 2);
  replace(String.raw`const IGNORE = /(^|\/)(\.git|`, String.raw`const IGNORE = /(^|\/)(artifacts|\.runtime|\.auth|\.aws|\.ssh|target|test-results|playwright-report|benchmark-results|coverage|\.git|`);
  replace('JSON.stringify({ project: session.project, port })', "JSON.stringify({ app: 'agenttrail-map', project: session.project, port, repoPath: repo })");
  replace('listenWithFallback()', 'listenWithFallback(0)');
  return source;
}

export function ownershipPlan(registry) {
  if (!registry.projects?.some(p => p.id === 'core' && p.path === '.')) throw new Error('Map requires the workspace core registry entry.');
  const ids = new Set();
  const sections = registry.projects.map(p => {
    if (!/^[a-z0-9][a-z0-9-]*$/.test(p.id) || ids.has(p.id) || /[\r\n{}]/.test(p.name)) throw new Error('Invalid map project identity.');
    ids.add(p.id);
    if (path.isAbsolute(p.path) || p.path.split(/[\\/]/).includes('..') || /[,\[\]\r\n]/.test(p.path)) throw new Error('Invalid map project path.');
    const files = p.path === '.' ? 'AGENTS.md, README.md, workspace.projects.json, package.json, .agents/**, agent-system/**, tooling/**, knowledge/docs/**' : p.path + '/**';
    const links = p.id === 'core' ? registry.projects.filter(x => x.id !== 'core').map(x => x.id) : ['core'];
    return `## ${p.name} {#${p.id}}\nfiles: [${files}]\nlinks: [${links.join(', ')}]\n`;
  });
  return '# Agentic workspace ownership\n\nGenerated from workspace.projects.json. Components show file ownership only; no task completion is claimed.\n\n' + sections.join('\n');
}
