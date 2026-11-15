// Independent trial oracle for CRM-Scale. It is copied into a disposable copy of a
// trial arm only after the agent has finished. It runs the arm's CRM-Scale specs
// against a fresh CRM-Scale server and, when EVIDENCE_REQUIRED_TESTS is set, selects
// the task's required test titles.
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const armRoot = fileURLToPath(new URL('../', import.meta.url));
const appRoot = path.join(armRoot, 'examples/crm-scale');
const port = process.env.EVIDENCE_ORACLE_PORT ?? '4296';
const appUrl = `http://127.0.0.1:${port}`;
const titles: string[] = JSON.parse(process.env.EVIDENCE_REQUIRED_TESTS ?? '[]');
const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

export default defineConfig({
  testDir: path.join(appRoot, 'tests'),
  testMatch: ['**/*.spec.ts'],
  grep: titles.length ? new RegExp(`(?:^|\\s)(?:${titles.map(escape).join('|')})(?:\\s|$)`) : undefined,
  outputDir: path.join(armRoot, '.evidence/test-results'),
  fullyParallel: true,
  forbidOnly: true,
  retries: 0,
  workers: 3,
  timeout: 20_000,
  expect: { timeout: 4_000 },
  reporter: [['json', { outputFile: process.env.EVIDENCE_REPORT ?? path.join(armRoot, '.evidence/report.json') }]],
  use: { baseURL: appUrl, trace: 'off', screenshot: 'off', video: 'off' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    cwd: appRoot,
    command: `"${process.execPath}" app/server.mjs`,
    env: { PORT: port },
    url: `${appUrl}/login`,
    reuseExistingServer: false,
    timeout: 30_000
  }
});
