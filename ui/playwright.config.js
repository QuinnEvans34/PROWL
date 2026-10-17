import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/browser',
  outputDir: '../outputs/prowl/testing/ui-browser',
  fullyParallel: false, workers: 1, retries: 0,
  use: { browserName: 'chromium', baseURL: 'http://127.0.0.1:5179', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: [{
    command: 'npm run test:fixture', url: 'http://127.0.0.1:5179',
    reuseExistingServer: false, timeout: 30000,
  }, {
    command: '../.venv-prowl/bin/python ../scripts/serve_evidence_fixture.py --port 8012 --output-dir ../outputs/prowl/testing/evidence-fixture/responses',
    url: 'http://127.0.0.1:8012/evidence-fixture/health',
    reuseExistingServer: false, timeout: 30000,
  }],
})
