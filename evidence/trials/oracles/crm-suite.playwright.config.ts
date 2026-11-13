// Runs the committed sample CRM suite (sample-crm and validation-login specs)
// against a fresh loopback CRM. Used to validate assessment answer keys.
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const port = process.env.EVIDENCE_ORACLE_PORT ?? '4298';
const appUrl = `http://127.0.0.1:${port}`;
process.env.APP_BASE_URL = appUrl;

export default defineConfig({
  testDir: path.join(root, 'tests'),
  testMatch: ['**/sample-crm.spec.ts', '**/validation-login.spec.ts'],
  outputDir: path.join(root, '.evidence/suite-results'),
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  reporter: [['json', { outputFile: process.env.EVIDENCE_REPORT ?? path.join(root, '.evidence/suite.json') }]],
  use: { baseURL: appUrl, trace: 'off', screenshot: 'off', video: 'off' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    cwd: root,
    command: `"${process.execPath}" examples/sample-crm-app/server.mjs`,
    env: { PORT: port },
    url: `${appUrl}/login`,
    reuseExistingServer: false,
    timeout: 30_000
  }
});
