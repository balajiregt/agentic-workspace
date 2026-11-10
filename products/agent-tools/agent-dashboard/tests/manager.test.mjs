import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import { dashboardUrl, hasProjects, loadConfiguration, ownedCommand, probe } from '../scripts/lib.mjs';

test('live and example URLs keep synthetic activity explicitly separate', () => {
  const live = new URL(dashboardUrl(4780, '/tmp/a project'));
  assert.equal(live.searchParams.get('mode'), 'live');
  assert.equal(live.searchParams.get('project'), '/tmp/a project');
  const example = new URL(dashboardUrl(4780, '/tmp/a project', true));
  assert.equal(example.searchParams.get('mode'), 'demo');
  assert.equal(example.searchParams.has('project'), false);
});

test('ownership guard rejects unrelated processes and missing project attachments', () => {
  assert.equal(ownedCommand('/usr/bin/python3 other-server.py', '/tmp/server.mjs'), false);
  assert.equal(ownedCommand('/opt/homebrew/bin/node /tmp/server.mjs', '/tmp/server.mjs'), true);
  assert.equal(hasProjects({ projects: [{ id: '/workspace' }] }, ['/other']), false);
});

test('project configuration resolves real folders and rejects escape or unknown IDs', async t => {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'agent-dashboard-test-'));
  t.after(() => fs.rm(root, { recursive: true, force: true }));
  const project = path.join(root, 'dashboard');
  await fs.mkdir(project);
  const registry = path.join(root, 'workspace.projects.json');
  const config = path.join(project, 'dashboard.config.json');
  await fs.writeFile(registry, JSON.stringify({ projects: [{ id: 'core', path: '.' }] }));
  await fs.writeFile(config, JSON.stringify({ port: 4780, watchProjects: ['core', 'core'] }));
  assert.equal((await loadConfiguration(root, project)).roots.length, 1);
  await fs.writeFile(config, JSON.stringify({ port: 4780, watchProjects: ['missing'] }));
  await assert.rejects(loadConfiguration(root, project), /Unknown watched project/);
  await fs.writeFile(registry, JSON.stringify({ projects: [{ id: 'outside', path: '..' }] }));
  await fs.writeFile(config, JSON.stringify({ port: 4780, watchProjects: ['outside'] }));
  await assert.rejects(loadConfiguration(root, project), /escapes this workspace/);
});

test('readiness probing rejects a different HTTP service', async t => {
  const server = http.createServer((req, res) => { res.setHeader('content-type', 'application/json'); res.end('{"app":"another-app"}'); });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => server.close(resolve)));
  await assert.rejects(probe(server.address().port), /occupied by another service/);
});
