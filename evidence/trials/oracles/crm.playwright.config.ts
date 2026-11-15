// Independent trial oracle for Playwright Agent's sample CRM. It is copied into
// a trial arm only after the agent has finished, runs every spec under tests/
// against a fresh loopback CRM, and selects the task's required test titles.
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const armRoot = fileURLToPath(new URL('../', import.meta.url));
const port = process.env.EVIDENCE_ORACLE_PORT ?? '4297';
const appUrl = `http://127.0.0.1:${port}`;
const titles: string[] = JSON.parse(process.env.EVIDENCE_REQUIRED_TESTS ?? '[]');
const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

process.env.APP_BASE_URL = appUrl;

export default defineConfig({
  testDir: path.join(armRoot, 'tests'),
  testMatch: ['**/*.spec.ts'],
  // grep matches the joined title path (project, file, describes, test title).
  grep: titles.length ? new RegExp(`(?:^|\\s)(?:${titles.map(escape).join('|')})(?:\\s|$)`) : undefined,
  outputDir: path.join(armRoot, '.evidence/test-results'),
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: [['list'], ['json', { outputFile: process.env.EVIDENCE_REPORT ?? path.join(armRoot, '.evidence/report.json') }]],
  use: { baseURL: appUrl, trace: 'off', screenshot: 'off', video: 'off' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    cwd: armRoot,
    command: `"${process.execPath}" examples/sample-crm-app/server.mjs`,
    env: { PORT: port },
    url: `${appUrl}/login`,
    reuseExistingServer: false,
    timeout: 30_000
  }
});
